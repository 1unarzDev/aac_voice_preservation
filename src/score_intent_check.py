"""Score Part 18 returns (annotation_package/intent_check.html CSVs): WRITER-INTENT AGREEMENT.

This reports whether the people who wrote a pair say a model sentence carries the meaning they
intended. It is writer-intent agreement. It is NOT validation by AAC users and must not be reported
as such.

usage: python src/score_intent_check.py [CSV ...]     (default: annotation/returns_intent/*.csv)
          [--key annotation/intent_check_key.csv] [--out analysis/intent_check]
       python src/score_intent_check.py --self-check

Items: each writer rated 10 outputs from their own kept pairs (run hw1, P0, 5 `bare` + 5 `chip1`).
Answers: q1 `says` in {version A, version B, something else, unclear}; q2 `accept` in
{yes, with a small edit, no}. "Can't judge" and missing answers are unknown (excluded from that
denominator, counted), never coded as success or failure. Practice rows are dropped.

Reported (each overall and by channel; Wilson 95% CI over items plus a writer-cluster bootstrap
CI, 4000 resamples of writers, seed 20261102):
  1. match rate: share of rated items where the writer says the output is the variant it was
     generated from (version A/B == the intended variant). By channel, bare vs chip1, with the
     chip1 - bare difference (cluster bootstrap). In `bare` the keywords are identical for A and B,
     so the "intended variant" is only the drawn side: its match rate is a reference level, not a
     success rate; the better bare numbers are "commits to A or B" and the A/B split.
  2. writer-judge agreement on q1: the writer's answer mapped to the judge's `chose` labels
     (version A -> A, version B -> B, something else -> other, unclear -> unclear): percent
     agreement and Cohen's kappa on 4 labels, and on the binary "matches the intended variant"
     (writer vs judge chose == intended), with the confusion table. The judge labels only the
     family's critical dimension; the writer judges the whole message.
  3. acceptability: yes / with a small edit / no, by channel, and "yes or small edit"; also by
     whether the writer said the output matches the intended variant.
  Per-writer table. Outputs: <out>/report.md, items.csv, summary.json.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import glob
import io
import json
import random
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agree_stats import cohen_kappa  # noqa: E402
from score_gold import wilson  # noqa: E402

SAYS = {"version A": "A", "version B": "B", "something else": "other", "unclear": "unclear"}
ACCEPT = ["yes", "with a small edit", "no"]
CHANNELS = ("chip1", "bare")
SEED = 20261102
NOTE = ("Writer-intent agreement: the writers of the pairs say whether a sentence carries what they meant. "
        "This is not validation by AAC users.")


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_returns(paths, key):
    out, problems = {}, []
    for p in paths:
        for r in read_csv(p):
            if r.get("practice") == "1" or r["item_id"].startswith("prac-"):
                continue
            if r["item_id"] not in key:
                problems.append(f"{p}: unknown item {r['item_id']}")
                continue
            a = r["annotator"].strip().upper()
            if a != key[r["item_id"]]["writer_id"]:
                problems.append(f"{p}: {r['item_id']} rated by {a} but belongs to {key[r['item_id']]['writer_id']}; dropped")
                continue
            uns = set(filter(None, (r.get("unsure") or "").split("|")))
            says = None if "says" in uns else (r.get("says") or None)
            acc = None if "accept" in uns else (r.get("accept") or None)
            if says is not None and says not in SAYS:
                problems.append(f"{p}: {r['item_id']} says={says!r} invalid; unknown"); says = None
            if acc is not None and acc not in ACCEPT:
                problems.append(f"{p}: {r['item_id']} accept={acc!r} invalid; unknown"); acc = None
            if r["item_id"] in out:
                problems.append(f"{p}: duplicate rating {r['item_id']}; keeping the later export")
            out[r["item_id"]] = {"says": says, "accept": acc, "note": r.get("note", ""),
                                 "time_ms": float(r["time_ms"]) if r.get("time_ms") else None}
    return out, problems


def rate(vals):
    known = [v for v in vals if v is not None]
    k, n = sum(known), len(known)
    return {"k": k, "n": n, "unknown": len(vals) - n, "p": (k / n) if n else None, "ci": wilson(k, n)}


def fmt(r):
    if not r or not r["n"]:
        return "n/a (0 known)"
    s = f"{r['k']}/{r['n']} = {100 * r['p']:.1f}% [{100 * r['ci'][0]:.1f}, {100 * r['ci'][1]:.1f}]"
    if r.get("boot"):
        s += f"; writer-cluster CI [{100 * r['boot'][0]:.1f}, {100 * r['boot'][1]:.1f}]"
    return s + (f"; {r['unknown']} unknown" if r["unknown"] else "")


def boot_ci(rows, stat, reps=4000, seed=SEED):
    """Resample writers (clusters) with replacement; stat(list_of_rows) -> float|None."""
    by_w = defaultdict(list)
    for r in rows:
        by_w[r["writer_id"]].append(r)
    ws = sorted(by_w)
    if len(ws) < 2:
        return None
    rng = random.Random(seed)
    draws = []
    for _ in range(reps):
        s = stat([x for w in (rng.choice(ws) for _ in ws) for x in by_w[w]])
        if s is not None:
            draws.append(s)
    if len(draws) < reps // 2:
        return None
    draws.sort()
    return [round(draws[int(0.025 * len(draws))], 3), round(draws[int(0.975 * len(draws)) - 1], 3)]


def match_of(r):
    return None if r["says"] is None else r["says"] == "version " + r["intended_variant"]


def p_of(rows, f):
    v = [f(r) for r in rows]
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else None


def with_boot(rows, f):
    x = rate([f(r) for r in rows])
    x["boot"] = boot_ci(rows, lambda rs: p_of(rs, f)) if x["n"] else None
    return x


def agreement(rows):
    """Writer vs judge on q1 (4 labels) and on the binary 'matches the intended variant'."""
    pairs = [(SAYS[r["says"]], r["judge_chose"]) for r in rows if r["says"] is not None and r["judge_chose"]]
    bin_ = [((r["says"] == "version " + r["intended_variant"]), (r["judge_chose"] == r["intended_variant"]))
            for r in rows if r["says"] is not None and r["judge_chose"]]
    def block(p):
        if not p:
            return {"n": 0, "agree": None, "kappa": None}
        return {"n": len(p), "agree": round(sum(a == b for a, b in p) / len(p), 3),
                "kappa": cohen_kappa([a for a, _ in p], [b for _, b in p])}
    conf = Counter(pairs)
    return {"q1_four_labels": block(pairs), "match_binary": block(bin_),
            "confusion_writer_x_judge": {f"{w}|{j}": c for (w, j), c in sorted(conf.items())}}


def analyse(items, ratings, problems, paths):
    rows = []
    for iid, k in items.items():
        r = ratings.get(iid)
        rows.append({**k, "says": r["says"] if r else None, "accept": r["accept"] if r else None,
                     "note": r["note"] if r else "", "rated": r is not None})
    S = {"note": NOTE, "returns": paths, "problems": problems, "n_items_key": len(items),
         "n_rated": sum(r["rated"] for r in rows), "writers": sorted({r["writer_id"] for r in rows if r["rated"]})}
    live = [r for r in rows if r["rated"]]
    S["match_rate"], S["commits_to_A_or_B"], S["says_split"], S["acceptability"], S["agreement"] = {}, {}, {}, {}, {}
    groups = {"all": live, **{c: [r for r in live if r["channel"] == c] for c in CHANNELS}}
    commit = lambda r: None if r["says"] is None else r["says"] in ("version A", "version B")  # noqa: E731
    for g, rs in groups.items():
        S["match_rate"][g] = with_boot(rs, match_of)
        S["commits_to_A_or_B"][g] = with_boot(rs, commit)
        S["says_split"][g] = dict(Counter(r["says"] or "(unknown)" for r in rs))
        S["acceptability"][g] = {
            "yes": with_boot(rs, lambda r: None if r["accept"] is None else r["accept"] == "yes"),
            "yes_or_small_edit": with_boot(rs, lambda r: None if r["accept"] is None else r["accept"] != "no"),
            "no": with_boot(rs, lambda r: None if r["accept"] is None else r["accept"] == "no"),
            "counts": dict(Counter(r["accept"] or "(unknown)" for r in rs)),
            "yes_when_matches_intended": rate([r["accept"] == "yes" if r["accept"] else None
                                               for r in rs if match_of(r) is True]),
            "yes_when_not_matching": rate([r["accept"] == "yes" if r["accept"] else None
                                           for r in rs if match_of(r) is False])}
        S["agreement"][g] = agreement(rs)
    ch, ba = groups["chip1"], groups["bare"]
    diff = None
    if S["match_rate"]["chip1"]["n"] and S["match_rate"]["bare"]["n"]:
        d = S["match_rate"]["chip1"]["p"] - S["match_rate"]["bare"]["p"]
        bd = boot_ci(ch + ba, lambda rs: (None if p_of([r for r in rs if r["channel"] == "chip1"], match_of) is None
                                         or p_of([r for r in rs if r["channel"] == "bare"], match_of) is None else
                                         p_of([r for r in rs if r["channel"] == "chip1"], match_of)
                                         - p_of([r for r in rs if r["channel"] == "bare"], match_of)))
        diff = {"diff": round(d, 3), "writer_cluster_ci": bd}
    S["match_rate_chip1_minus_bare"] = diff
    S["per_writer"] = {}
    for w in S["writers"]:
        rs = [r for r in live if r["writer_id"] == w]
        S["per_writer"][w] = {"n": len(rs),
                              **{f"match_{c}": rate([match_of(r) for r in rs if r["channel"] == c]) for c in CHANNELS},
                              "accept_yes": rate([None if r["accept"] is None else r["accept"] == "yes" for r in rs])}
    return rows, S


def report(S, rows, out):
    L = ["# Part 18: did it say what you meant? (writer-intent agreement)\n", f"**{NOTE}**\n",
         f"Returns: {len(S['returns'])} file(s); writers: {', '.join(S['writers'])}; {S['n_rated']} of "
         f"{S['n_items_key']} items rated. Items come from the writers' own kept pairs (run hw1, prompt P0, "
         "5 `bare` + 5 `chip1` per writer; declared seeded draw in `annotation/intent_check_sample.json`). "
         "CIs: Wilson over items, plus a resample of writers (clusters) because each writer rates 10 items.\n",
         "## 1. Output matches the variant it was generated from\n",
         "| channel | writer says it is the intended variant | commits to A or B | says split |", "|---|---|---|---|"]
    lab = {"all": "all", "chip1": "chip1 (critical chip given)", "bare": "bare (keywords only; reference level)"}
    for g in ("all", "chip1", "bare"):
        L.append(f"| {lab[g]} | {fmt(S['match_rate'][g])} | {fmt(S['commits_to_A_or_B'][g])} | {S['says_split'][g]} |")
    d = S["match_rate_chip1_minus_bare"]
    L.append("\nchip1 - bare difference in match rate: " + ("n/a" if not d else
             f"{100 * d['diff']:+.1f} pp" + (f" [writer-cluster 95% {100 * d['writer_cluster_ci'][0]:+.1f}, "
                                              f"{100 * d['writer_cluster_ci'][1]:+.1f}]" if d["writer_cluster_ci"] else "")) + "\n")
    L.append("In `bare` the keywords do not say whether version A or B was meant, so its match rate is a reference "
             "level (a model cannot know the intended side), not a failure rate.\n")
    L += ["## 2. Writer vs judge\n", "| channel | q1 four labels: n, agree, kappa | binary 'matches intended': n, agree, kappa |", "|---|---|---|"]
    for g in ("all", "chip1", "bare"):
        a = S["agreement"][g]
        f = lambda b: f"n={b['n']}, " + ("n/a" if b["agree"] is None else f"{100 * b['agree']:.1f}%") + f", kappa={b['kappa']}"  # noqa: E731
        L.append(f"| {g} | {f(a['q1_four_labels'])} | {f(a['match_binary'])} |")
    L.append("\nWriter x judge (all channels), `writer|judge`: " + ", ".join(
        f"{k}={v}" for k, v in S["agreement"]["all"]["confusion_writer_x_judge"].items()) + "\n")
    L += ["The judge labels only the critical dimension; the writer judges the whole message.\n",
          "## 3. Would you accept it as your message?\n",
          "| channel | yes | yes or small edit | no | counts | yes when writer says it matches | yes when it does not |", "|---|---|---|---|---|---|---|"]
    for g in ("all", "chip1", "bare"):
        a = S["acceptability"][g]
        L.append(f"| {g} | {fmt(a['yes'])} | {fmt(a['yes_or_small_edit'])} | {fmt(a['no'])} | {a['counts']} | "
                 f"{fmt(a['yes_when_matches_intended'])} | {fmt(a['yes_when_not_matching'])} |")
    L += ["\n## Per writer\n", "| writer | items | match chip1 | match bare | accept yes |", "|---|---|---|---|---|"]
    for w, x in S["per_writer"].items():
        L.append(f"| {w} | {x['n']} | {fmt(x['match_chip1'])} | {fmt(x['match_bare'])} | {fmt(x['accept_yes'])} |")
    L += ["\n## Items where the writer did not say it matches the intended variant (chip1 only)\n",
          "| item | writer | model | version A | version B | intended | tool wrote | says | accept | judge chose | note |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["writer_id"], r["item_id"])):
        if r["rated"] and r["channel"] == "chip1" and match_of(r) is False:
            L.append(f"| {r['item_id']} | {r['writer_id']} | {r['model']} | {r['version_A']} | {r['version_B']} | "
                     f"{r['intended_variant']} | {r['text']} | {r['says']} | {r['accept']} | {r['judge_chose']} | "
                     f"{(r['note'] or '').replace('|', '/')} |")
    if S["problems"]:
        L += ["\n## Problems in returns\n"] + [f"- {p}" for p in S["problems"]]
    out.joinpath("report.md").write_text("\n".join(L) + "\n")
    return L


def run(paths, keyp, out):
    items = {r["item_id"]: r for r in read_csv(keyp)}
    ratings, problems = load_returns(paths, items)
    out.mkdir(parents=True, exist_ok=True)
    rows, S = analyse(items, ratings, problems, [str(p) for p in paths])
    with open(out / "items.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")
    return S, report(S, rows, out)


def self_check() -> int:
    """Simulated writers: chip1 outputs match the intended variant 85%, bare outputs 'say' A/B at random."""
    keyp = ROOT / "annotation" / "intent_check_key.csv"
    key = read_csv(keyp)
    assert len(key) == 200 and len({r["writer_id"] for r in key}) == 20
    rng = random.Random(11)
    by_w = defaultdict(list)
    for r in key:
        if r["channel"] == "chip1":
            says = ("version " + r["intended_variant"]) if rng.random() < 0.85 else rng.choice(
                ["version " + "AB".replace(r["intended_variant"], ""), "something else", "unclear"])
        else:
            says = rng.choice(["version A", "version B", "version A", "version B", "something else", "unclear"])
        acc = rng.choice(["yes", "yes", "with a small edit", "no"])
        by_w[r["writer_id"]].append({"item_id": r["item_id"], "annotator": r["writer_id"], "practice": 0, "says": says,
                                     "accept": acc, "unsure": "", "note": "n" if says == "something else" else "",
                                     "time_ms": 3000})
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for w, rs in by_w.items():
            p = Path(td) / f"intent_check_{w}.csv"
            with open(p, "w", newline="", encoding="utf-8") as fh:
                wr = csv.DictWriter(fh, fieldnames=list(rs[0])); wr.writeheader(); wr.writerows(rs)
            paths.append(p)
        S, _ = run(paths, keyp, Path(td) / "out")
        # wrong-writer rows must be dropped
        bad = Path(td) / "intent_check_P01.csv"
        rows = read_csv(bad); rows[0]["annotator"] = "P02"
        with open(bad, "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
        S2, _ = run(paths, keyp, Path(td) / "out2")
    assert S["n_rated"] == 200 and len(S["writers"]) == 20
    m = S["match_rate"]
    assert m["chip1"]["n"] == 100 and m["bare"]["n"] == 100
    assert m["chip1"]["p"] > 0.75 and m["bare"]["p"] < 0.5, (m["chip1"]["p"], m["bare"]["p"])
    d = S["match_rate_chip1_minus_bare"]
    assert d["diff"] > 0.3 and d["writer_cluster_ci"][0] > 0, d
    assert S["agreement"]["all"]["q1_four_labels"]["n"] == 200
    assert S["acceptability"]["all"]["yes"]["n"] == 200
    assert S2["n_rated"] == 199 and any("belongs to" in p for p in S2["problems"])
    print(f"self-check OK: chip1 match {100 * m['chip1']['p']:.0f}%, bare {100 * m['bare']['p']:.0f}%, "
          f"diff {100 * d['diff']:+.1f} pp {d['writer_cluster_ci']}; writer-judge agree "
          f"{100 * S['agreement']['all']['q1_four_labels']['agree']:.0f}%")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "intent_check_key.csv"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "intent_check"))
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / "returns_intent" / "*.csv")))
    if not paths:
        print("no return CSVs found (annotation/returns_intent/*.csv)", file=sys.stderr)
        return 1
    _, L = run(paths, a.key, Path(a.out))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())

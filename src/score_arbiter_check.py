"""Score Part 19 returns: people vs the arbiter, vs each judge, and how people code "Can you ...?".

usage: python src/score_arbiter_check.py [CSV ...]     (default: annotation/returns_arbiter_check/labels_part19_*.csv)
          [--key annotation/arbiter_check_key.csv] [--out analysis/arbiter_check]
       python src/score_arbiter_check.py --self-check    (simulated returns on the real key; writes nothing)

Input: the CSVs annotate.html exports for the part file stage4/<ID>_part19.json (run tag part19). Only the first
question (the critical question of the item) is scored here; the other answers are ignored. Practice rows are dropped.
A blank answer or a question marked unsure is missing, never a disagreement. A coding by someone who is not a coder of
that item, or who is on its blocked list (wrote / checked the pair, chose the keywords), is reported as a problem and
dropped.

Units. "arbiter" items are units on which the two judges disagreed on the critical label and the arbiter decided;
"canyou" items are "Can you ...?" / "Could you ...?" outputs on which the judges agreed (production label usually
request/command). Per coding = one person's label for one item (the main unit; CIs are Wilson and treat codings as
independent, so they are descriptive: the same unit is coded twice). Per item = the label both coders gave, "split"
when they differ (reported separately, never dropped).

Reports (report.md, summary.json, items.csv):
  * human vs arbiter agreement, overall, per precedent tag, per run, per dimension (per coding and per item, plus
    Cohen's kappa);
  * human vs J1 and human vs J2 on the arbiter items (the judges disagreed there, so the two cannot both match);
    also whether the arbiter sided with J1, J2 or neither;
  * human-human agreement on the same items;
  * "Can you": share of codings that say request/command vs question vs other (per coding and per item, by run and
    by typed-or-keyword input), and agreement with the production label.
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
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agree_stats import cohen_kappa  # noqa: E402
from score_gold import wilson  # noqa: E402

REQ, QUE = "request/command", "question"


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_returns(paths, key):
    codings, problems = {}, []
    for p in paths:
        for r in read_csv(p):
            iid = r["item_id"]
            if r.get("practice") == "1" or iid.startswith("practice"):
                continue
            if iid not in key:
                problems.append(f"{Path(p).name}: unknown item {iid}"); continue
            k = key[iid]
            who = r["annotator"].strip()
            if who not in k["coders"].split("|"):
                problems.append(f"{Path(p).name}: {who} is not a coder of {iid}; dropped"); continue
            if who in k["blocked_people"].split("|"):
                problems.append(f"{Path(p).name}: {who} is blocked for {iid}; dropped"); continue
            uns = {u.strip() for u in (r.get("unsure_dims") or "").replace(";", ",").replace("|", ",").split(",")}
            lab = (r.get("critical") or "").strip() or None
            if "critical" in uns:
                lab = None
            if lab is not None and lab not in k["critical_options"].split("|"):
                problems.append(f"{Path(p).name}: {who} {iid} label {lab!r} not an option; treated as missing"); lab = None
            if (who, iid) in codings:
                problems.append(f"{Path(p).name}: duplicate coding {who}/{iid}; keeping the later row")
            gsa = (r.get("speech_act") or "").strip() or None
            if "speech_act" in uns:
                gsa = None
            codings[(who, iid)] = {"annotator": who, "item_id": iid, "label": lab, "general_speech_act": gsa,
                                   "time_ms": float(r["time_ms"]) if r.get("time_ms") else None}
    return codings, problems


def rate(flags):
    """flags: list of bool (missing already removed)."""
    n = len(flags); k = sum(flags)
    return {"k": k, "n": n, "p": (k / n) if n else None, "ci": wilson(k, n)}


def fmt(x):
    if not x or not x["n"]:
        return "n/a"
    lo, hi = x["ci"]
    return f"{x['k']}/{x['n']} = {100 * x['p']:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}]"


def item_label(labs):
    labs = [l for l in labs if l is not None]
    if not labs:
        return None
    return labs[0] if len(set(labs)) == 1 and len(labs) >= 2 else ("split" if len(set(labs)) > 1 else "single:" + labs[0])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "arbiter_check_key.csv"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "arbiter_check"))
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    key = {r["item_id"]: r for r in read_csv(a.key)}
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / "returns_arbiter_check" / "labels_part19_*.csv")))
    if not paths:
        print("no return CSVs found (annotation/returns_arbiter_check/labels_part19_*.csv)", file=sys.stderr)
        return 1
    codings, problems = load_returns(paths, key)
    by_item = defaultdict(list)
    for c in codings.values():
        by_item[c["item_id"]].append(c)
    S = {"returns": [Path(p).name for p in paths], "annotators": sorted({c["annotator"] for c in codings.values()}),
         "problems": problems, "n_items_key": len(key), "codings_expected": 2 * len(key),
         "codings_received": len(codings), "codings_with_label": sum(c["label"] is not None for c in codings.values())}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    rows = []
    for iid, k in key.items():
        cs = sorted(by_item.get(iid, []), key=lambda c: c["annotator"])
        labs = [c["label"] for c in cs]
        rows.append({**{c: k[c] for c in ("item_id", "source", "run", "dimension", "precedent_tag", "arbiter_label", "J1",
                                          "J2", "production_label", "text")},
                     "coder_labels": "|".join(f"{c['annotator']}:{c['label'] or ''}" for c in cs),
                     "human_item_label": item_label(labs), "n_codings": len(cs)})
    with open(out / "items.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    arb = {i: k for i, k in key.items() if k["source"] == "arbiter"}
    can = {i: k for i, k in key.items() if k["source"] == "canyou"}

    def agree_block(sel, ref):
        """per coding and per item agreement of the human label with column `ref` of the key, over items `sel`."""
        pc = [c["label"] == key[i][ref] for i in sel for c in by_item.get(i, []) if c["label"] is not None]
        pi = []
        for i in sel:
            il = item_label([c["label"] for c in by_item.get(i, [])])
            if il in (None,) or il.startswith("single:"):
                continue
            pi.append(il == key[i][ref])
        split = sum(item_label([c["label"] for c in by_item.get(i, [])]) == "split" for i in sel)
        pairs = [(c["label"], key[i][ref]) for i in sel for c in by_item.get(i, []) if c["label"] is not None]
        return {"per_coding": rate(pc), "per_item_when_coders_agree": rate(pi), "items_with_split_coders": split,
                "kappa": cohen_kappa([x for x, _ in pairs], [y for _, y in pairs]) if pairs else None}

    # ---- human vs arbiter, J1, J2
    S["arbiter_items"] = len(arb)
    S["human_vs_arbiter"] = agree_block(arb, "arbiter_label")
    S["human_vs_J1"] = agree_block(arb, "J1")
    S["human_vs_J2"] = agree_block(arb, "J2")
    S["arbiter_sided_with"] = dict(Counter("J1" if k["arbiter_label"] == k["J1"] else "J2" if k["arbiter_label"] == k["J2"]
                                           else "neither" for k in arb.values()))
    # human matches arbiter / J1 / J2 / neither, per coding, by who the arbiter sided with
    side = {}
    for s in ("J1", "J2", "neither"):
        ids = [i for i, k in arb.items() if ("J1" if k["arbiter_label"] == k["J1"] else "J2" if k["arbiter_label"] == k["J2"] else "neither") == s]
        side[s] = {"items": len(ids), **{ref: rate([c["label"] == key[i][ref] for i in ids for c in by_item.get(i, []) if c["label"]])
                                        for ref in ("arbiter_label", "J1", "J2")}}
    S["human_match_by_arbiter_side"] = side
    for dim_name, f in (("by_tag", "precedent_tag"), ("by_run", "run"), ("by_dimension", "dimension")):
        S["human_vs_arbiter_" + dim_name] = {
            g: {"items": sum(1 for k in arb.values() if k[f] == g), **agree_block([i for i, k in arb.items() if k[f] == g], "arbiter_label")}
            for g in sorted({k[f] for k in arb.values()})}
    # human-human
    pairs = []
    for i in key:
        cs = [c["label"] for c in by_item.get(i, []) if c["label"] is not None]
        if len(cs) == 2:
            pairs.append((cs[0], cs[1], key[i]["source"]))
    S["human_human"] = {src: {"items": sum(1 for p in pairs if p[2] == src),
                              "agree": rate([p[0] == p[1] for p in pairs if p[2] == src]),
                              "kappa": cohen_kappa([p[0] for p in pairs if p[2] == src], [p[1] for p in pairs if p[2] == src])
                              if any(p[2] == src for p in pairs) else None} for src in ("arbiter", "canyou")}

    # ---- "Can you"
    def share(items, label):
        return rate([c["label"] == label for i in items for c in by_item.get(i, []) if c["label"] is not None])

    def item_share(items, label):
        ils = [item_label([c["label"] for c in by_item.get(i, [])]) for i in items]
        ils = [x for x in ils if x and not x.startswith("single:")]
        return {"n_items_with_two_codings": len(ils), "agree_on_label": rate([x == label for x in ils if x != "split"]),
                "split": sum(x == "split" for x in ils), "of_all": rate([x == label for x in ils])}
    cy_all = list(can)
    sp = ROOT / "annotation" / "arbiter_check_sample.json"
    exp = set(json.loads(sp.read_text()).get("labelled_sentences_before", [])) if sp.exists() else set()

    def gshare(items, label, who=None):
        return rate([c["general_speech_act"] == label for i in items for c in by_item.get(i, [])
                     if c["general_speech_act"] is not None and (who is None or who(c["annotator"]))])

    def share_by(items, label, who):
        return rate([c["label"] == label for i in items for c in by_item.get(i, [])
                     if c["label"] is not None and who(c["annotator"])])
    typed = {i: k["input_text"].startswith("The user typed") for i, k in can.items()}
    labs_seen = sorted({c["label"] for i in can for c in by_item.get(i, []) if c["label"]})
    S["can_you"] = {
        "items": len(can), "codings_with_label": sum(1 for i in can for c in by_item.get(i, []) if c["label"]),
        "per_coding_share": {"request/command": share(cy_all, REQ), "question": share(cy_all, QUE),
                             **{l: share(cy_all, l) for l in labs_seen if l not in (REQ, QUE)}},
        "per_item": {"request/command": item_share(cy_all, REQ), "question": item_share(cy_all, QUE)},
        "general_speech_act_question_share": {"request/command": gshare(cy_all, REQ), "question": gshare(cy_all, QUE)},
        "by_prior_labelling_experience": ({
            grp: {"request": share_by(cy_all, REQ, f), "question": share_by(cy_all, QUE, f),
                  "general_request": gshare(cy_all, REQ, f), "general_question": gshare(cy_all, QUE, f)}
            for grp, f in (("labelled sentences in Stages 1-3", lambda a_: a_ in exp),
                           ("had not labelled sentences before", lambda a_: a_ not in exp))} if exp else {}),
        "agree_with_production_label": agree_block(cy_all, "production_label"),
        "by_run": {run: {"items": sum(1 for k in can.values() if k["run"] == run),
                         "request": share([i for i, k in can.items() if k["run"] == run], REQ),
                         "question": share([i for i, k in can.items() if k["run"] == run], QUE)}
                   for run in sorted({k["run"] for k in can.values()})},
        "by_input": {nm: {"items": sum(1 for i in can if typed[i] == t),
                          "request": share([i for i in can if typed[i] == t], REQ),
                          "question": share([i for i in can if typed[i] == t], QUE)}
                     for nm, t in (("typed input", True), ("keyword input", False)) if any(typed[i] == t for i in can)},
        "also_in_arbiter_items_tagged": {t: {"items": sum(1 for k in arb.values() if k["precedent_tag"] == t),
                                             "request": share([i for i, k in arb.items() if k["precedent_tag"] == t], REQ),
                                             "question": share([i for i, k in arb.items() if k["precedent_tag"] == t], QUE)}
                                         for t in ("can_could_you", "will_you_request")},
    }
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")

    L = ["# Part 19: human check of arbitrated labels\n",
         f"Generated by `src/score_arbiter_check.py`. Returns: {len(paths)} file(s), {len(S['annotators'])} annotators; "
         f"{S['codings_received']} of {S['codings_expected']} expected codings received, {S['codings_with_label']} with a label. "
         f"Key: `annotation/arbiter_check_key.csv` ({len(arb)} arbiter units, {len(can)} \"Can you\" outputs).\n",
         "Per coding = one person's label for one item (Wilson 95% CI; codings are not independent, the CIs are descriptive). "
         "Per item (coders agree) = the label both coders gave; items where the two coders differ are counted as split and shown. "
         "Missing or unsure answers are excluded, not counted as disagreement.\n",
         "## Human vs arbiter, J1 and J2 (arbiter units; the judges disagreed on every one of these)\n",
         "| reference | per coding | per item (coders agree) | split items | Cohen kappa (codings) |", "|---|---|---|---|---|"]
    for nm, k in (("arbiter", "human_vs_arbiter"), ("J1", "human_vs_J1"), ("J2", "human_vs_J2")):
        b = S[k]
        L.append(f"| {nm} | {fmt(b['per_coding'])} | {fmt(b['per_item_when_coders_agree'])} | {b['items_with_split_coders']} | {b['kappa']} |")
    L += ["", f"The arbiter sided with: {S['arbiter_sided_with']}.\n",
          "Human match by whom the arbiter sided with (per coding):\n", "| arbiter sided with | items | human = arbiter | human = J1 | human = J2 |", "|---|---|---|---|---|"]
    for s, x in side.items():
        L.append(f"| {s} | {x['items']} | {fmt(x['arbiter_label'])} | {fmt(x['J1'])} | {fmt(x['J2'])} |")
    for title, k in (("precedent tag", "by_tag"), ("run", "by_run"), ("dimension", "by_dimension")):
        L += [f"\n## Human vs arbiter, by {title}\n", f"| {title} | items | per coding | per item (coders agree) | split | kappa |", "|---|---|---|---|---|---|"]
        for g, x in S["human_vs_arbiter_" + k].items():
            L.append(f"| {g} | {x['items']} | {fmt(x['per_coding'])} | {fmt(x['per_item_when_coders_agree'])} | "
                     f"{x['items_with_split_coders']} | {x['kappa']} |")
    L += ["\n## Human vs human (the two coders of an item)\n", "| items | n items | % agree | kappa |", "|---|---|---|---|"]
    for src, x in S["human_human"].items():
        L.append(f"| {src} | {x['items']} | {fmt(x['agree'])} | {x['kappa']} |")
    cy = S["can_you"]
    L += ["\n## \"Can you ...?\" / \"Could you ...?\" (speech-act rule: request, not question)\n",
          f"{cy['items']} outputs, {cy['codings_with_label']} labelled codings. Share of codings:\n", "| label | per coding |", "|---|---|"]
    for l, x in cy["per_coding_share"].items():
        L.append(f"| {l} | {fmt(x)} |")
    g = cy["general_speech_act_question_share"]
    L += ["", f"Cross-check with the tool's general speech-act question (asked on every item, no examples): request/command "
              f"{fmt(g['request/command'])}, question {fmt(g['question'])}.",
          "The \"Can you\" items showed the main question without its \"'Can you ...?' is a request\" example, and the practice "
          "items did not teach it.", ""]
    if cy["by_prior_labelling_experience"]:
        L += ["| coders | request (main question) | question (main question) | request (general question) | question (general question) |",
              "|---|---|---|---|---|"]
        for grp, x in cy["by_prior_labelling_experience"].items():
            L.append(f"| {grp} | {fmt(x['request'])} | {fmt(x['question'])} | {fmt(x['general_request'])} | {fmt(x['general_question'])} |")
    L += ["", "Per item: " + "; ".join(f"{l}: coders agree on it for {fmt(x['agree_on_label'])}, {x['split']} split"
                                       for l, x in cy["per_item"].items()), "",
          f"Agreement with the production label (request/command, from the judges): {fmt(cy['agree_with_production_label']['per_coding'])}.\n",
          "| group | items | request | question |", "|---|---|---|---|"]
    for g, x in {**{f"run {r}": v for r, v in cy["by_run"].items()}, **cy["by_input"],
                 **{f"arbiter units tagged {t}": v for t, v in cy["also_in_arbiter_items_tagged"].items()}}.items():
        L.append(f"| {g} | {x['items']} | {fmt(x['request'])} | {fmt(x['question'])} |")
    L += ["\n## Items where people disagree with the arbiter (per item, both coders agree on another label)\n",
          "| item | run | tag | arbiter | J1 | J2 | humans | sentence |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["source"] == "arbiter" and r["human_item_label"] not in (None, "split") and not r["human_item_label"].startswith("single:") \
                and r["human_item_label"] != r["arbiter_label"]:
            L.append(f"| {r['item_id']} | {r['run']} | {r['precedent_tag']} | {r['arbiter_label']} | {r['J1']} | {r['J2']} | "
                     f"{r['human_item_label']} | {r['text']} |")
    if problems:
        L += ["\n## Problems in returns\n"] + [f"- {p}" for p in problems]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


def self_check() -> int:
    """Simulate returns on the real key (people agree with the arbiter 80%, "Can you" read as request 85%) and score them."""
    keyp = ROOT / "annotation" / "arbiter_check_key.csv"
    key = read_csv(keyp)
    rng = random.Random(11)
    ids = sorted({c for k in key for c in k["coders"].split("|")})
    assert len(key) == 130 and len(ids) == 20
    assert all(len(k["coders"].split("|")) == 2 and not set(k["coders"].split("|")) & set(filter(None, k["blocked_people"].split("|")))
               for k in key)
    rows = {x: [] for x in ids}
    for k in key:
        opts = k["critical_options"].split("|")
        for x in k["coders"].split("|"):
            if k["source"] == "arbiter":
                r = rng.random()
                lab = k["arbiter_label"] if r < 0.8 else (k["J1"] if k["J1"] != k["arbiter_label"] else k["J2"]) if r < 0.93 else rng.choice(opts)
            else:
                lab = REQ if rng.random() < 0.85 else (QUE if rng.random() < 0.8 else "unclear/mixed")
            unsure = "critical" if rng.random() < 0.02 else ""
            rows[x].append({"item_id": k["item_id"], "annotator": x, "practice": 0, "critical_dimension": k["dimension"],
                            "critical": "" if unsure else lab, "polarity": "", "speech_act": REQ if rng.random() < 0.8 else "question", "agent": "", "certainty": "",
                            "politeness": "", "added_content": "", "skip": 1 if unsure else 0, "unsure_dims": unsure,
                            "time_ms": 7000, "exported_at": "x"})
    for x in ids:    # practice rows and one stray row must be handled
        rows[x].insert(0, {"item_id": "practice-1", "annotator": x, "practice": 1, "critical_dimension": "polarity",
                           "critical": "negated", "polarity": "", "speech_act": "", "agent": "", "certainty": "",
                           "politeness": "", "added_content": "", "skip": 0, "unsure_dims": "", "time_ms": 1, "exported_at": "x"})
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for x, rs in rows.items():
            p = Path(td) / f"labels_part19_{x}.csv"
            with open(p, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rs[0])); w.writeheader(); w.writerows(rs)
            paths.append(str(p))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main([*paths, "--key", str(keyp), "--out", str(Path(td) / "out")])
        S = json.loads((Path(td) / "out" / "summary.json").read_text())
        assert (Path(td) / "out" / "report.md").exists() and (Path(td) / "out" / "items.csv").exists()
    assert rc == 0 and S["problems"] == [], S["problems"]
    assert S["codings_received"] == 260 and 240 < S["codings_with_label"] <= 260
    ha = S["human_vs_arbiter"]["per_coding"]
    assert 0.65 < ha["p"] < 0.95 and ha["n"] > 150, ha
    j1, j2 = S["human_vs_J1"]["per_coding"], S["human_vs_J2"]["per_coding"]
    assert j1["n"] == j2["n"] == ha["n"]
    assert ha["k"] > j1["k"] and ha["k"] > j2["k"]
    assert set(S["human_vs_arbiter_by_tag"]) >= {"no_time_word_unclear", "hope_hedged", "sure_emphatic", "other"}
    assert sum(x["items"] for x in S["human_vs_arbiter_by_tag"].values()) == 100
    cy = S["can_you"]
    assert cy["items"] == 30 and 0.7 < cy["per_coding_share"]["request/command"]["p"] < 0.97
    assert abs(cy["per_coding_share"]["request/command"]["p"] + cy["per_coding_share"]["question"]["p"]
               + cy["per_coding_share"].get("unclear/mixed", {"p": 0})["p"] - 1) < 1e-9
    print(f"self-check OK: human vs arbiter {100 * ha['p']:.0f}% of {ha['n']} codings; vs J1 {100 * j1['p']:.0f}%, vs J2 {100 * j2['p']:.0f}%; "
          f"Can you read as request {100 * cy['per_coding_share']['request/command']['p']:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())

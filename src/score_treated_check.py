"""Score Part 20 returns: automatic judge vs human consensus on treated outputs, per label field and per output class.

usage: python src/score_treated_check.py [CSV ...]   (default: annotation/returns_treated_check/labels_part20_*.csv)
          [--key annotation/treated_check_key.csv] [--out analysis/treated_check]
       python src/score_treated_check.py --self-check    (simulated returns on the real key; writes nothing)

Input: the CSVs annotate.html exports for the part files stage5/<ID>_part20.json (run tag part20). Practice rows are dropped.
All seven fields are scored: critical (the item's own question), polarity, speech_act, agent, certainty, politeness,
added_content. A blank answer, or a field listed in unsure_dims, is missing (never a disagreement). A coding by someone who
is not a coder of that item, or who is on its blocked list (wrote / checked the pair, chose the keywords), is reported as a
problem and dropped.

Reference ("human consensus", fixed in COORDINATOR_STEPS section 4, "Part 20", before any return):
  primary      per item and field, BOTH coders gave a label and the labels are equal. Items where they differ, or where one
               coder is missing/unsure, have no consensus for that field; they are counted and listed, never dropped silently.
  sensitivity  plurality: a single labelled coder counts as the consensus; ties are still excluded.
Judge = the production label stored in the key (critical: the arbiter's label where J1 and J2 disagreed).

Reports (report.md, summary.json, items.csv):
  * per field, pooled and per output class (G1, G1r, chip1, nlcue, newmodel, gemini): n, accuracy (Wilson 95% CI), Cohen kappa
    (item-bootstrap 95% CI); per class the accuracy re-weighted over dimensions by the key's weight (frame size / drawn);
  * critical field in detail: per class x family dimension counts, the list of items where the human consensus differs
    from the judge, J1 and J2 alone against the consensus;
  * human-human agreement (accuracy, kappa) on the same fields, as the ceiling;
  * verdict agreement per class: Violation / constraint_preserving (cue channels) and Assumption (bare / noncrit channels),
    recomputed with the production rules (score_gold._verdicts) from the human consensus and from the judge labels, as in the
    earlier gold checks; agreement (Wilson), kappa, 2x2 counts, undetermined counts; plus a check that the recomputed
    judge verdicts equal the stored production verdicts.
No pass/fail threshold is set here; the H7 gate (kappa >= 0.6) is reported next to the critical result for reference.
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
from labels import ADDED_CONTENT_OPTIONS, GENERAL_DIMS, GENERAL_OPTIONS  # noqa: E402
from score_gold import H7_KAPPA, _verdicts, kappa_boot, kappa_w, n_eff, wilson  # noqa: E402

FIELDS = ["critical"] + GENERAL_DIMS + ["added_content"]
CLASSES = ["G1", "G1r", "chip1", "nlcue", "newmodel", "gemini"]
CLASS_TEXT = {"G1": "guard repairs (G1)", "G1r": "no-feedback retries (G1r)", "chip1": "chip1 outputs", "nlcue": "plain-word cue (nlcue)",
              "newmodel": "Qwen2.5-14B / Mistral-Nemo-12B", "gemini": "Gemini 3.1 flash-lite"}
VERDICTS = ["violation", "constraint_preserving", "assumption"]


def read_csv(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_returns(paths, key):
    """(annotator, item) -> {field: label or None}; problems list."""
    codings, problems = {}, []
    for p in paths:
        for r in read_csv(p):
            iid = r["item_id"]
            if str(r.get("practice", "0")) == "1" or iid.startswith("practice"):
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
            lab = {}
            for d in FIELDS:
                v = (r.get(d) or "").strip() or None
                if v is not None and d == "critical":
                    opts = k["critical_options"].split("|")
                    if v == "mixed/unclear" and "unclear/mixed" in opts:
                        v = "unclear/mixed"
                    if v not in opts:
                        problems.append(f"{Path(p).name}: {who} {iid} critical {v!r} not an option; treated as missing"); v = None
                elif v is not None and d in GENERAL_OPTIONS and v not in GENERAL_OPTIONS[d]:
                    problems.append(f"{Path(p).name}: {who} {iid} {d} {v!r} out of schema; treated as missing"); v = None
                elif v is not None and d == "added_content" and v not in ADDED_CONTENT_OPTIONS:
                    problems.append(f"{Path(p).name}: {who} {iid} added_content {v!r} out of schema; treated as missing"); v = None
                lab[d] = None if d in uns else v
            if (who, iid) in codings:
                problems.append(f"{Path(p).name}: duplicate coding {who}/{iid}; keeping the later row")
            codings[(who, iid)] = lab
    return codings, problems


def consensus(votes: list, rule: str):
    """votes: labels of the coders (None removed by the caller). primary: both coders, equal; plurality: single allowed."""
    if rule == "strict":
        return votes[0] if len(votes) == 2 and votes[0] == votes[1] else None
    c = Counter(votes).most_common()
    if not c or (len(c) > 1 and c[0][1] == c[1][1]):
        return None
    return c[0][0]


def stat(pred, gold, w=None, seed=20261102):
    n = len(pred)
    if not n:
        return {"n": 0}
    k = sum(p == g for p, g in zip(pred, gold))
    m = {"n": n, "k": k, "acc": round(k / n, 3), "acc_ci": wilson(k, n), "kappa": cohen_kappa(pred, gold),
         "kappa_ci": kappa_boot(pred, gold, seed=seed)}
    if w:
        tw = sum(w)
        a = sum(wi for p, g, wi in zip(pred, gold, w) if p == g) / tw
        m.update(acc_w=round(a, 3), acc_w_ci=wilson(a * n_eff(w), n_eff(w)), kappa_w=kappa_w(pred, gold, w))
    return m


def fmt(m, kappa=True):
    if not m or not m.get("n"):
        return "n/a"
    lo, hi = m["acc_ci"]
    s = f"{m['k']}/{m['n']} = {100 * m['acc']:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}]"
    if kappa:
        ci = m.get("kappa_ci")
        s += f"; kappa {m['kappa']}" + (f" [{ci[0]}, {ci[1]}]" if ci else "")
    return s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "treated_check_key.csv"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "treated_check"))
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    key = {r["item_id"]: r for r in read_csv(a.key)}
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / "returns_treated_check" / "labels_part20_*.csv")))
    if not paths:
        print("no return CSVs found (annotation/returns_treated_check/labels_part20_*.csv)", file=sys.stderr)
        return 1
    codings, problems = load_returns(paths, key)
    by_item = defaultdict(list)
    for (who, iid), lab in codings.items():
        by_item[iid].append((who, lab))
    S = {"returns": [Path(p).name for p in paths], "annotators": sorted({w for w, _ in codings}), "problems": problems,
         "n_items_key": len(key), "codings_expected": 2 * len(key), "codings_received": len(codings),
         "codings_with_critical": sum(l["critical"] is not None for l in codings.values()), "H7_kappa": H7_KAPPA}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    cons = {rule: {f: {} for f in FIELDS} for rule in ("strict", "plurality")}
    for iid in key:
        for f in FIELDS:
            votes = [l[f] for _, l in by_item.get(iid, []) if l[f] is not None]
            for rule in cons:
                c = consensus(votes, rule)
                if c is not None:
                    cons[rule][f][iid] = c
    S["consensus_counts"] = {rule: {f: len(cons[rule][f]) for f in FIELDS} for rule in cons}
    classes = [c for c in CLASSES if any(k["class"] == c for k in key.values())]

    def fieldstats(rule, f, sel, ref="final", w=False):
        col = f if ref == "final" else f"{ref}_{f}"
        ids = [i for i in sel if i in cons[rule][f] and key[i].get(col) not in (None, "")]
        return stat([key[i][col] for i in ids], [cons[rule][f][i] for i in ids],
                    [float(key[i]["weight"]) for i in ids] if w else None)

    pooled = list(key)
    S["per_field"] = {rule: {f: {"pooled": fieldstats(rule, f, pooled),
                                 **{c: fieldstats(rule, f, [i for i in pooled if key[i]["class"] == c], w=True) for c in classes}}
                             for f in FIELDS} for rule in cons}
    # critical in detail
    crit = {"by_class_dimension": {}, "judge_J1_J2_vs_consensus": {}, "disagreements": []}
    for c in classes:
        for d in sorted({k["dimension"] for k in key.values() if k["class"] == c}):
            ids = [i for i in key if key[i]["class"] == c and key[i]["dimension"] == d]
            crit["by_class_dimension"][f"{c}|{d}"] = {"items": len(ids), **fieldstats("strict", "critical", ids)}
    for src in ("J1", "J2"):
        crit["judge_J1_J2_vs_consensus"][src] = {c: fieldstats("strict", "critical", [i for i in key if key[i]["class"] == c], src)
                                                 for c in classes}
    for i, k in key.items():
        h = cons["strict"]["critical"].get(i)
        if h is not None and h != k["critical"]:
            crit["disagreements"].append({"item_id": i, "class": k["class"], "run": k["run"], "model": k["model"], "channel": k["channel"],
                                          "dimension": k["dimension"], "judge": k["critical"], "J1": k["J1_critical"], "J2": k["J2_critical"],
                                          "human": h, "critical_source": k["critical_source"], "text": k["text"]})
    S["critical_detail"] = crit
    # human-human
    hh = {}
    for f in FIELDS:
        pr = []
        for iid in key:
            cs = sorted(by_item.get(iid, []), key=lambda x: x[0])
            if len(cs) == 2 and cs[0][1][f] is not None and cs[1][1][f] is not None:
                pr.append((cs[0][1][f], cs[1][1][f]))
        k_ = sum(x == y for x, y in pr)
        hh[f] = {"n": len(pr), "agree": round(k_ / len(pr), 3) if pr else None, "agree_ci": wilson(k_, len(pr)),
                 "kappa": cohen_kappa([x for x, _ in pr], [y for _, y in pr])}
    S["human_human"] = hh
    # verdicts
    from build_requests import custom_spec
    from make_treated_check import load_all_items
    items = load_all_items()
    vrows = {v: [] for v in VERDICTS}; check = Counter()
    for iid, k in key.items():
        human = {f: cons["strict"][f].get(iid) for f in FIELDS}
        if human["critical"] is None:
            continue
        judge = {f: (k[f] or None) for f in FIELDS}
        it = items[k["family_id"]]; var = it["variants"][k["variant"]]
        cust = custom_spec(it, k["variant"], k["channel"]) if it.get("custom_channels") else None
        vh, vj = _verdicts(it["dimension"], var, k["channel"], human, cust), _verdicts(it["dimension"], var, k["channel"], judge, cust)
        for v in VERDICTS:
            st = {"True": True, "False": False}.get(k[v])
            if vj[v] is not None and st is not None:
                check["judge_recomputed_matches_stored" if st == vj[v] else "judge_recomputed_differs"] += 1
            if vj[v] is None and vh[v] is None:
                continue
            vrows[v].append({"class": k["class"], "judge": vj[v], "human": vh[v], "item": iid})

    def vtable(rows):
        det = [r for r in rows if r["judge"] is not None and r["human"] is not None]
        k_ = sum(r["judge"] == r["human"] for r in det)
        two = Counter((r["judge"], r["human"]) for r in det)
        return {"n_determined": len(det), "agree": k_, "agree_rate": round(k_ / len(det), 3) if det else None, "agree_ci": wilson(k_, len(det)),
                "kappa": cohen_kappa([r["judge"] for r in det], [r["human"] for r in det]),
                "judge_true_human_true": two[(True, True)], "judge_true_human_false": two[(True, False)],
                "judge_false_human_true": two[(False, True)], "judge_false_human_false": two[(False, False)],
                "human_undetermined": sum(r["human"] is None for r in rows), "judge_undetermined": sum(r["judge"] is None for r in rows)}
    S["verdict_agreement"] = {v: {"pooled": vtable(vrows[v]), **{c: vtable([r for r in vrows[v] if r["class"] == c]) for c in classes}}
                              for v in VERDICTS}
    S["verdict_consistency_check"] = dict(check)
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")

    rows = []
    for iid, k in key.items():
        row = {c: k[c] for c in ("item_id", "class", "run", "model", "channel", "dimension", "text")}
        for f in FIELDS:
            row[f"judge_{f}"] = k[f]; row[f"human_{f}"] = cons["strict"][f].get(iid, "")
        row["coder_critical"] = "|".join(f"{w}:{l['critical'] or ''}" for w, l in sorted(by_item.get(iid, [])))
        rows.append(row)
    with open(out / "items.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    L = ["# Part 20: judge vs human labels on treated outputs\n",
         f"Generated by `src/score_treated_check.py`. Returns: {len(paths)} file(s), {len(S['annotators'])} annotators; "
         f"{S['codings_received']} of {S['codings_expected']} expected codings received. Key: `annotation/treated_check_key.csv` "
         f"({len(key)} outputs, classes {', '.join(classes)}).\n",
         "Human consensus (primary) = both coders gave the same label for that field; items where they differ or one is missing have "
         "no consensus for that field. Accuracy has Wilson 95% CIs, kappa has item-bootstrap 95% CIs. Items per class are few (about 20): "
         "read the intervals, not the point estimates. Judge = production label (arbiter where J1 and J2 disagreed).\n",
         f"Reference: the earlier gold gate H7 is kappa >= {H7_KAPPA}; no threshold is set for Part 20.\n",
         "## Critical field (the question each item asked), by output class\n",
         "| class | n with consensus | judge vs human | J1 vs human | J2 vs human | acc re-weighted over dimensions |", "|---|---|---|---|---|---|"]
    P = S["per_field"]["strict"]
    for c in ["pooled"] + classes:
        m = P["critical"][c]
        aw = f"{100 * m['acc_w']:.0f}%" if m.get("acc_w") is not None else "-"
        L.append(f"| {CLASS_TEXT.get(c, 'all classes')} | {m.get('n', 0)} | {fmt(m)} | "
                 f"{fmt(crit['judge_J1_J2_vs_consensus']['J1'].get(c) if c != 'pooled' else None)} | "
                 f"{fmt(crit['judge_J1_J2_vs_consensus']['J2'].get(c) if c != 'pooled' else None)} | {aw} |")
    L += ["\n## All fields, judge vs human consensus (primary rule)\n", "| field | " + " | ".join(["all classes"] + [CLASS_TEXT[c] for c in classes]) + " |",
          "|---|" + "---|" * (len(classes) + 1)]
    for f in FIELDS:
        L.append(f"| {f} | " + " | ".join(fmt(P[f][c], kappa=False) for c in ["pooled"] + classes) + " |")
    L += ["\nKappa by field:\n", "| field | " + " | ".join(["all classes"] + classes) + " |", "|---|" + "---|" * (len(classes) + 1)]
    for f in FIELDS:
        L.append(f"| {f} | " + " | ".join(str(P[f][c].get("kappa")) if P[f][c].get("n") else "n/a" for c in ["pooled"] + classes) + " |")
    L += ["\n## Sensitivity: plurality (a single labelled coder counts)\n", "| field | all classes | " + " | ".join(classes) + " |",
          "|---|---|" + "---|" * len(classes)]
    for f in FIELDS:
        L.append(f"| {f} | " + " | ".join(fmt(S["per_field"]["plurality"][f][c], kappa=False) for c in ["pooled"] + classes) + " |")
    L += ["\n## Critical field by class and dimension\n", "| class | dimension | items | n with consensus | judge vs human |", "|---|---|---|---|---|"]
    for cd, m in crit["by_class_dimension"].items():
        c, d = cd.split("|")
        L.append(f"| {c} | {d} | {m['items']} | {m.get('n', 0)} | {fmt(m, kappa=False)} |")
    L += ["\n## Human vs human (the two coders of an item; the ceiling)\n", "| field | n | agree | kappa |", "|---|---|---|---|"]
    for f in FIELDS:
        x = hh[f]
        L.append(f"| {f} | {x['n']} | {x['agree']} | {x['kappa']} |")
    L += ["\n## Verdict agreement (recomputed from labels with the production rules)\n",
          "Violation / constraint_preserving apply to cue channels, Assumption to bare / noncrit channels. A verdict is undetermined when "
          "the human consensus lacks a label it needs. 2x2 cells are judge x human (T = verdict true).\n",
          "| verdict | class | determined | agree | kappa | TT | TF | FT | FF | human undetermined |", "|---|---|---|---|---|---|---|---|---|---|"]
    for v in VERDICTS:
        for c in ["pooled"] + classes:
            x = S["verdict_agreement"][v][c]
            if not (x["n_determined"] or x["human_undetermined"]):
                continue
            ag = f"{x['agree']}/{x['n_determined']} = {100 * x['agree_rate']:.0f}% [{100 * x['agree_ci'][0]:.0f}, {100 * x['agree_ci'][1]:.0f}]" if x["n_determined"] else "n/a"
            L.append(f"| {v} | {CLASS_TEXT.get(c, 'all classes')} | {x['n_determined']} | {ag} | {x['kappa']} | {x['judge_true_human_true']} | "
                     f"{x['judge_true_human_false']} | {x['judge_false_human_true']} | {x['judge_false_human_false']} | {x['human_undetermined']} |")
    L += ["", f"Recomputed judge verdicts vs the stored production verdicts: {S['verdict_consistency_check']}.",
          "\n## Items where the human consensus on the critical field differs from the judge\n",
          "| item | class | run | model | channel | dimension | judge | J1 | J2 | human | sentence |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in crit["disagreements"]:
        L.append(f"| {d['item_id']} | {d['class']} | {d['run']} | {d['model']} | {d['channel']} | {d['dimension']} | {d['judge']} | "
                 f"{d['J1']} | {d['J2']} | {d['human']} | {d['text']} |")
    if problems:
        L += ["\n## Problems in returns\n"] + [f"- {p}" for p in problems]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


def self_check() -> int:
    """Simulate returns on the real key: coders match the judge on each field with probability .9 (critical) / .85 (others)."""
    keyp = ROOT / "annotation" / "treated_check_key.csv"
    key = read_csv(keyp)
    rng = random.Random(5)
    ids = sorted({c for k in key for c in k["coders"].split("|")})
    assert len(key) == 120 and len(ids) == 20, (len(key), len(ids))
    assert Counter(k["class"] for k in key) == {c: 20 for c in CLASSES}
    assert all(len(k["coders"].split("|")) == 2 and not set(k["coders"].split("|")) & set(filter(None, k["blocked_people"].split("|")))
               for k in key)
    rows = {x: [] for x in ids}
    biased = {k["item_id"] for k in key if k["class"] == "gemini"}.__iter__()
    biased = {next(biased) for _ in range(6)}          # both coders give the same non-judge critical label: must show as disagreement
    for k in key:
        opts = k["critical_options"].split("|")
        alt = next(o for o in opts if o != k["critical"])
        for x in k["coders"].split("|"):
            r = {"item_id": k["item_id"], "annotator": x, "practice": 0, "critical_dimension": k["dimension"], "skip": 0,
                 "unsure_dims": "", "time_ms": 5000, "exported_at": "x"}
            for f in FIELDS:
                pool = opts if f == "critical" else (GENERAL_OPTIONS[f] if f in GENERAL_OPTIONS else ADDED_CONTENT_OPTIONS)
                p = 0.9 if f == "critical" else 0.85
                truth = k[f] if k[f] in pool else pool[0]
                r[f] = truth if rng.random() < p else rng.choice(pool)
            if rng.random() < 0.03:
                r["critical"] = ""; r["unsure_dims"] = "critical"
            if k["item_id"] in biased:
                r["critical"] = alt; r["unsure_dims"] = ""
            rows[x].append(r)
    for x in ids:
        rows[x].insert(0, {"item_id": "practice-1", "annotator": x, "practice": 1, "critical_dimension": "polarity", "critical": "negated",
                           "polarity": "", "speech_act": "", "agent": "", "certainty": "", "politeness": "", "added_content": "",
                           "skip": 0, "unsure_dims": "", "time_ms": 1, "exported_at": "x"})
    bad = key[0]; stranger = next(x for x in ids if x not in bad["coders"].split("|"))
    rows[stranger].append({**{f: "" for f in FIELDS}, "item_id": bad["item_id"], "annotator": stranger, "practice": 0,
                           "critical_dimension": bad["dimension"], "critical": bad["critical"], "skip": 0, "unsure_dims": "",
                           "time_ms": 1, "exported_at": "x"})
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for x, rs in rows.items():
            p = Path(td) / f"labels_part20_{x}.csv"
            with open(p, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rs[0])); w.writeheader(); w.writerows(rs)
            paths.append(str(p))
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main([*paths, "--key", str(keyp), "--out", str(Path(td) / "out")])
        S = json.loads((Path(td) / "out" / "summary.json").read_text())
        assert (Path(td) / "out" / "report.md").exists() and (Path(td) / "out" / "items.csv").exists()
    assert rc == 0 and len(S["problems"]) == 1 and "not a coder" in S["problems"][0], S["problems"]
    assert S["codings_received"] == 240
    pc = S["per_field"]["strict"]["critical"]
    assert pc["pooled"]["n"] > 60 and set(CLASSES) <= set(pc), pc["pooled"]
    assert 0.85 < pc["pooled"]["acc"] < 1.0, pc["pooled"]
    assert len(S["critical_detail"]["disagreements"]) >= 5 and pc["gemini"]["acc"] < 1.0, S["critical_detail"]["disagreements"]
    assert all(pc[c]["n"] > 0 for c in CLASSES)
    for f in FIELDS:
        assert S["per_field"]["strict"][f]["pooled"]["n"] > 30, f
    assert S["human_human"]["critical"]["n"] > 80
    va = S["verdict_agreement"]
    assert va["violation"]["pooled"]["n_determined"] > 0 and va["assumption"]["pooled"]["n_determined"] > 0, va["violation"]["pooled"]
    assert S["verdict_consistency_check"].get("judge_recomputed_differs", 0) <= 2, S["verdict_consistency_check"]
    print(f"self-check OK: critical judge vs consensus {pc['pooled']['k']}/{pc['pooled']['n']}, kappa {pc['pooled']['kappa']}; "
          f"verdict violation agree {va['violation']['pooled']['agree']}/{va['violation']['pooled']['n_determined']}; "
          f"recompute check {S['verdict_consistency_check']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

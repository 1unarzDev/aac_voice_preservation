"""Score the judge oracle and the two baseline oracles on real-output mutants/controls and on the W-A sets."""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oracle_baselines as B  # noqa: E402
import runio  # noqa: E402
from labels import critical_match  # noqa: E402
from oracle_real import OUT, OUTRUN, ROOT, wilson  # noqa: E402

ORACLES = ["judge", "surface", "overlap"]


def frac(k, n):
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": round(k / n, 4) if n else None, "lo": lo, "hi": hi}


def fmt(d):
    return "n/a" if not d["n"] else f"{d['k']}/{d['n']} ({100*d['rate']:.1f}%) [{max(0, 100*d['lo']):.0f}, {100*d['hi']:.0f}]"


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tf(x):
    return {"True": True, "False": False}.get(x, None)


def judge_results():
    j = {(r["family_id"], r["text_id"], r["input_text"]): r for r in runio.read_jsonl(OUTRUN / "judgments.jsonl")}
    arb = {}
    ap = OUTRUN / "arbiter.jsonl"
    if ap.exists():
        arb = {(a["text_id"], a["family_id"], a["input_text"]): a["critical"] for a in runio.read_jsonl(ap)}
    return j, arb


def main():
    rows = runio.read_jsonl(OUT / "sample.jsonl")
    j, arb = judge_results()
    jb = {(r["family_id"], r["input_text"]): r for r in j.values()}
    out = []
    for r in rows:
        jr = jb[(r["rid"], r["input_text"])]
        crit, src = jr.get("critical"), "agree"
        if crit is None:
            k = (jr["text_id"], r["rid"], r["input_text"])
            crit, src = (arb[k], "arbiter") if k in arb else (None, "unresolved")
        dim, ref = r["dimension"], r["ref"]
        d = dict(r)
        d.update(judge_critical=crit, judge_source=src, J1=jr.get("J1_critical"), J2=jr.get("J2_critical"),
                 judge_pass=None if crit is None else bool(critical_match(dim, ref, crit)),
                 surface_label=B.surface_label(dim, r["text"], ref),
                 surface_pass=B.surface_pass(dim, ref, r["text"]),
                 overlap_pass=B.overlap_pass(r["text"], r["ref_source"], r["other_source"]),
                 orig_surface_pass=B.surface_pass(dim, ref, r["orig_text"]),
                 orig_overlap_pass=B.overlap_pass(r["orig_text"], r["ref_source"], r["other_source"]),
                 judge_exact=(crit == r["expected"]))
        out.append(d)
    keys = ["rid", "kind", "dimension", "ref", "op", "orig_text", "text", "expected", "judge_critical", "judge_source", "J1", "J2",
            "judge_pass", "judge_exact", "surface_label", "surface_pass", "overlap_pass", "orig_surface_pass", "orig_overlap_pass",
            "src_family", "variant", "model", "channel"]
    with open(OUT / "real_rows.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, keys, extrasaction="ignore"); w.writeheader(); w.writerows(out)

    def passes(rs, o):
        return [r[f"{o}_pass"] for r in rs]

    def catch(rs, o, unresolved=None):
        """caught = oracle says NOT preserved; unresolved judge rows counted as `unresolved`."""
        k = 0
        for r in rs:
            p = r[f"{o}_pass"]
            if p is None:
                k += 1 if unresolved else 0
            else:
                k += (not p)
        return k

    mut = [r for r in out if r["kind"] == "mutant"]
    ctl = [r for r in out if r["kind"] == "control"]
    head = [r for r in mut if r["op"] != "booster_insert"]
    S = {"seed": json.loads((OUT / "draw.json").read_text())["seed"], "n_mutants": len(mut), "n_controls": len(ctl),
         "n_unresolved_judge": sum(r["judge_pass"] is None for r in out)}
    tab = []

    def row(label, rs_m, rs_c=None):
        e = {"group": label, "n_mut": len(rs_m)}
        for o in ORACLES:
            n = len(rs_m)
            e[f"{o}_mut"] = frac(catch(rs_m, o, False), n)
            if o == "judge":
                e["judge_mut_hi"] = frac(catch(rs_m, o, True), n)
            if rs_c is not None:
                e[f"{o}_fa"] = frac(catch(rs_c, o, False), len(rs_c))
        return e

    S["headline"] = row("all mutants (excl. booster)", head, ctl)
    S["incl_booster"] = row("all mutants (incl. booster)", mut, ctl)
    S["booster_only"] = row("booster_insert", [r for r in mut if r["op"] == "booster_insert"])
    S["by_dim"], S["by_op"], S["fa_by_dim"], S["fa_by_type"] = {}, {}, {}, {}
    for dim in sorted({r["dimension"] for r in mut}):
        S["by_dim"][dim] = row(dim, [r for r in head if r["dimension"] == dim], [r for r in ctl if r["dimension"] == dim])
    for op in sorted({r["op"] for r in mut}):
        S["by_op"][op] = row(op, [r for r in mut if r["op"] == op])
    for t in sorted({r["op"] for r in ctl}):
        sub = [r for r in ctl if r["op"] == t]
        S["fa_by_type"][t] = {o: frac(catch(sub, o, False), len(sub)) for o in ORACLES}
    S["judge_exact_expected"] = frac(sum(r["judge_exact"] for r in head), len(head))
    # originals (unmutated): judge passes by construction; baselines' false-alarm rate on the very sentences
    origs = {}
    for r in out:
        origs.setdefault((r["src_family"], r["orig_text"]), r)
    S["originals"] = {"n": len(origs),
                      "surface_fa": frac(sum(not r["orig_surface_pass"] for r in origs.values()), len(origs)),
                      "overlap_fa": frac(sum(not r["orig_overlap_pass"] for r in origs.values()), len(origs))}
    S["originals_by_dim"] = {}
    for dim in sorted({r["dimension"] for r in out}):
        sub = [r for r in origs.values() if r["dimension"] == dim]
        S["originals_by_dim"][dim] = {"n": len(sub), "surface_fa": frac(sum(not r["orig_surface_pass"] for r in sub), len(sub)),
                                      "overlap_fa": frac(sum(not r["orig_overlap_pass"] for r in sub), len(sub))}
    # agreement of baselines with judge on real rows (judged rows only)
    S["agree_with_judge"] = {}
    for o in ("surface", "overlap"):
        rs = [r for r in out if r["judge_pass"] is not None]
        S["agree_with_judge"][o] = frac(sum(r[f"{o}_pass"] == r["judge_pass"] for r in rs), len(rs))
    S["judge_missed_mutants"] = [{k: r[k] for k in ("rid", "dimension", "op", "orig_text", "text", "expected", "judge_critical")}
                                 for r in mut if r["judge_pass"] is True]
    S["judge_false_alarms"] = [{k: r[k] for k in ("rid", "dimension", "op", "orig_text", "text", "ref", "judge_critical")}
                               for r in ctl if r["judge_pass"] is False]

    # ---- W-A comparison
    tests = runio.load_items(ROOT / "data/items/test.jsonl")
    wa = []
    for r in read_csv(ROOT / "analysis/oracle/injection_results.csv"):
        it = tests[r["family_id"]]
        var, other = it["variants"][r["variant"]], next(v for k, v in it["variants"].items() if k != r["variant"])
        wa.append({"set": "W-A injection", "kind": "control" if r["model"] == "identity" else "mutant", "group": r["dimension"],
                   "dimension": r["dimension"], "ref": r["variant_value"], "text": r["text"],
                   "judge_pass": tf(r["critical_match"]), "ref_source": var["source"], "other_source": other["source"]})
    chal = read_csv(ROOT / "analysis/oracle/challenge_results.csv")
    texts = {c["cid"]: c["text"] for c in chal}
    r2 = {c["cid"]: c for c in runio.read_jsonl(ROOT / "annotation/challenge_items_r2.jsonl")}
    partner_of = {c["pair"]: cid for cid, c in r2.items() if c.get("pair")}
    for r in chal:
        if r["role"] not in ("control", "mutant"):
            continue
        cid = r["cid"]
        ctrl_id = r2[cid]["pair"] if r["role"] == "mutant" else cid
        mut_id = cid if r["role"] == "mutant" else partner_of.get(cid)
        wa.append({"set": "W-A challenge", "kind": r["role"], "group": r["group"], "dimension": r["dimension"], "ref": r["contract"],
                   "text": r["text"], "judge_pass": tf(r["match_prod"]), "ref_source": texts[ctrl_id],
                   "other_source": texts.get(mut_id, "")})
    for w in wa:
        w["surface_pass"] = B.surface_pass(w["dimension"], w["ref"], w["text"])
        w["overlap_pass"] = B.overlap_pass(w["text"], w["ref_source"], w["other_source"])
    with open(OUT / "wa_rows.csv", "w", newline="", encoding="utf-8") as fh:
        ks = ["set", "kind", "group", "dimension", "ref", "text", "judge_pass", "surface_pass", "overlap_pass"]
        w_ = csv.DictWriter(fh, ks, extrasaction="ignore"); w_.writeheader(); w_.writerows(wa)
    S["wa"] = {}
    for st in ("W-A injection", "W-A challenge"):
        for g in [None] + sorted({w["group"] for w in wa if w["set"] == st}):
            sub = [w for w in wa if w["set"] == st and (g is None or w["group"] == g)]
            m, c = [w for w in sub if w["kind"] == "mutant"], [w for w in sub if w["kind"] == "control"]
            S["wa"][f"{st} / {g or 'all'}"] = {"n_mut": len(m), "n_ctl": len(c), **{
                f"{o}_mut": frac(sum(not w[f"{o}_pass"] for w in m), len(m)) for o in ORACLES} | {
                f"{o}_fa": frac(sum(not w[f"{o}_pass"] for w in c), len(c)) for o in ORACLES}}
    (OUT / "summary.json").write_text(json.dumps(S, indent=1))
    # by-operator csv
    with open(OUT / "by_operator.csv", "w", newline="") as fh:
        w_ = csv.writer(fh)
        w_.writerow(["group", "n_mut"] + [f"{o}_mut_score" for o in ORACLES])
        for k, e in {**S["by_op"], **{"DIM:" + d: v for d, v in S["by_dim"].items()}}.items():
            w_.writerow([k, e["n_mut"]] + [e[f"{o}_mut"]["rate"] for o in ORACLES])
    report(S)
    print(json.dumps({k: S[k] for k in ("headline",)}, indent=1)[:1500])


def report(S):
    L = ["# Oracle mutation analysis on real outputs, with baseline oracles", "",
         f"Seed {S['seed']}. {S['n_mutants']} mutants, {S['n_controls']} controls from real hw1 outputs the production oracle scored as preserving "
         "the critical commitment (cue-bearing channels, one per family). Plan: `PLAN.md`. Intervals are Wilson 95%.",
         "W-A had no mutation code (its mutants were hand-written), so the same operator families were re-implemented in "
         "`src/oracle_real_ops.py`.", "",
         "Definitions. Mutation score = share of meaning-changing mutants an oracle rejects (says the commitment is not preserved). "
         "False alarm = share of meaning-preserving controls an oracle rejects. Judge = production J1+J2 judge with arbiter; "
         f"{S['n_unresolved_judge']} rows were unresolved (J1 != J2, no arbiter).", "",
         "## Headline (booster mutants excluded, see below)", "",
         "| oracle | mutation score | false alarm (controls) |", "|---|---|---|"]
    h = S["headline"]
    for o in ORACLES:
        L.append(f"| {o} | {fmt(h[o+'_mut'])} | {fmt(h[o+'_fa'])} |")
    L += ["", f"Judge mutation score if unresolved rows are counted as caught: {fmt(h['judge_mut_hi'])}. "
          f"Judge returns exactly the expected new label on {fmt(S['judge_exact_expected'])} of mutants.",
          f"Booster mutants (plain -> 'Definitely, ...') are tolerated by the production contract (plain is honoured by emphatic) "
          f"and are excluded: judge {fmt(S['booster_only']['judge_mut'])}, surface {fmt(S['booster_only']['surface_mut'])}, "
          f"overlap {fmt(S['booster_only']['overlap_mut'])}.", "", "## By dimension (mutation score; false alarm on that dimension's controls)", "",
          "| dimension | n mut | judge | surface | overlap | n ctl | judge FA | surface FA | overlap FA |", "|---|---|---|---|---|---|---|---|---|"]
    for d, e in S["by_dim"].items():
        L.append(f"| {d} | {e['n_mut']} | " + " | ".join(fmt(e[f"{o}_mut"]) for o in ORACLES) + f" | {e['judge_fa']['n']} | " +
                 " | ".join(fmt(e[f"{o}_fa"]) for o in ORACLES) + " |")
    L += ["", "## By operator (mutation score)", "", "| operator | n | judge | surface | overlap |", "|---|---|---|---|---|"]
    for o_, e in S["by_op"].items():
        L.append(f"| {o_} | {e['n_mut']} | " + " | ".join(fmt(e[f"{o}_mut"]) for o in ORACLES) + " |")
    L += ["", "## Control edit types (false alarm)", "", "| edit | n | judge | surface | overlap |", "|---|---|---|---|---|"]
    for t, e in S["fa_by_type"].items():
        L.append(f"| {t} | {e['judge']['n']} | " + " | ".join(fmt(e[o]) for o in ORACLES) + " |")
    L += ["", "## Baselines on the unmutated originals", "",
          f"On the {S['originals']['n']} unmutated source outputs (which the judge scored as preserving by construction): "
          f"surface false alarm {fmt(S['originals']['surface_fa'])}, overlap {fmt(S['originals']['overlap_fa'])}. "
          "A baseline's false alarm on controls therefore partly reflects its failure on the original sentence.", "",
          "| dimension | n | surface FA | overlap FA |", "|---|---|---|---|"]
    for d, e in S["originals_by_dim"].items():
        L.append(f"| {d} | {e['n']} | {fmt(e['surface_fa'])} | {fmt(e['overlap_fa'])} |")
    L += ["", f"Agreement with the judge on all judged real rows: surface {fmt(S['agree_with_judge']['surface'])}, "
          f"overlap {fmt(S['agree_with_judge']['overlap'])}.", "", "## Comparison with W-A authored sentences", "",
          "| set / group | n mut | n ctl | judge mut | surface mut | overlap mut | judge FA | surface FA | overlap FA |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, e in S["wa"].items():
        L.append(f"| {k} | {e['n_mut']} | {e['n_ctl']} | " + " | ".join(fmt(e[f"{o}_mut"]) for o in ORACLES) + " | " +
                 " | ".join(fmt(e[f"{o}_fa"]) for o in ORACLES) + " |")
    L += ["", "Real-output rows above use the same judge, the same contract and the same production critical_match. "
          "The W-A challenge set is scored as in `analysis/oracle/report.md` (production rule). Overlap on W-A challenge uses the paired "
          "control/mutant text as the minimal pair.", "", "## Judge misses and false alarms", ""]
    for m in S["judge_missed_mutants"]:
        L.append(f"- missed mutant {m['rid']} ({m['dimension']}/{m['op']}): `{m['orig_text']}` -> `{m['text']}`; expected {m['expected']}, judge {m['judge_critical']}")
    for m in S["judge_false_alarms"]:
        L.append(f"- false alarm {m['rid']} ({m['dimension']}/{m['op']}): `{m['orig_text']}` -> `{m['text']}`; ref {m['ref']}, judge {m['judge_critical']}")
    L += ["", "## Caveats", "",
          "- Circularity of the surface baseline: its lexicons (not/n't, maybe, please/thanks/sorry, tense and time words, '?') are the very cues the "
          "operators insert or delete, so its high mutation score shows that these operators are lexically shallow, not that a lexicon oracle is adequate. "
          "The judge's edge over it is small here (mutation score) and shows up on controls (surface false alarms on agent, case-initial and the W-A "
          "embedded-actor group) and on cases where meaning is not lexically marked. An independent surface baseline would need a second author.",
          "- One equivalent mutant: R134's source output is a question written without '?', so the operator's statement-to-question edit did not change the "
          "value; excluding it the judge's score is 193/195. Headline numbers keep it. Two time-shift misses (R173, R187) keep an explicit 'in the past' / "
          "past-tense word beside the shifted verb, so the mutant is mixed-signal and the judge followed the explicit phrase.",
          "- Mutants are rule-generated and some are unnatural (e.g. 'I did call you yesterday'); the judge sees only the output, so naturalness does not leak the key, but it limits realism.",
          "- Draw rule: first N sentences in a seeded shuffle that the operator can mutate; applicability by dimension is in `draw.json`.",
          "- The overlap baseline uses key information (minimal-pair source difference) and is generous; the surface baseline was written before seeing scores and not tuned.",
          "- NLI baseline (iii) skipped: no NLI model or transformers install is available locally and no download was made.",
          "- Controls are mostly punctuation, case and contraction edits because model outputs are short plain sentences; the synonym lexicon rarely applies.",
          "- Judge false-alarm rate here is on surface-edited controls only; it is not a false-alarm rate on unedited outputs (those are scored by the human gate)."]
    (OUT / "report.md").write_text("\n".join(L) + "\n")

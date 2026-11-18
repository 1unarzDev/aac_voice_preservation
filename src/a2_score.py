"""A2 scoring (analysis/oracle_indep2/PLAN.md). Run with .venv python."""
import json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, "src")
from score_oracle_indep import wilson, mcnemar_exact, load_key, oracle_rows, KEY, JUDGE
O = Path("analysis/oracle_indep2")
conf = pd.read_csv("analysis/oracle_indep/confirmation.csv"); c = conf[conf.scored].copy()
key = load_key(); orc = oracle_rows(key, JUDGE)
nli = pd.read_csv(O / "nli_raw.csv").set_index("id")
cl = {}
for l in open(O / "claude_labels.jsonl"):
    x = json.loads(l); cl[x["uid"]] = x["label"]
refs = key.drop_duplicates("cand_id").set_index("cand_id")["target_ref"].to_dict()
def flags(i):
    n = nli.loc[i]
    return {"gpt_judge": orc[i]["judge_pass"] is False,
            "nli_primary": n.fwd == "CONTRADICTION" or n.bwd == "CONTRADICTION",
            "nli_secondary": not (n.fwd == "ENTAILMENT" and n.bwd == "ENTAILMENT"),
            "claude_change": cl[i + "_o"] != cl[i + "_m"],
            "claude_ref": cl[i + "_m"] != refs[i]}
F = pd.DataFrame([flags(i) for i in c.cand_id], index=c.cand_id)
for o in ("nli_primary", "nli_secondary", "claude_change", "claude_ref"):
    F[f"either_{o}"] = F.gpt_judge | F[o]; F[f"both_{o}"] = F.gpt_judge & F[o]
c = c.set_index("cand_id").join(F)
cols = list(F.columns)
mut = c[c.kind == "mutant"]; ctl = c[c.kind == "control"]; lex = mut[mut.lex_visible.astype(str) == "False"]
def fr(s):
    k, n = int(s.sum()), len(s); lo, hi = wilson(k, n); return {"k": k, "n": n, "rate": round(k / n, 4), "lo": lo, "hi": hi}
res = {"n_mut": len(mut), "n_ctl": len(ctl), "n_mut_lexblind": len(lex), "oracles": {}}
rows = []
for o in cols:
    d = {"mut_all": fr(mut[o]), "mut_lexblind": fr(lex[o]), "false_alarm": fr(ctl[o])}
    if o != "gpt_judge":
        for nm, g in (("all", mut), ("lexblind", lex)):
            b = int((g.gpt_judge & ~g[o]).sum()); cc = int((~g.gpt_judge & g[o]).sum())
            d[f"mcnemar_{nm}"] = {"judge_only": b, "oracle_only": cc, "p": round(mcnemar_exact(b, cc), 4)}
    res["oracles"][o] = d
    rows.append({"oracle": o, **{f"{k}_{m}": v for k, dd in d.items() if isinstance(dd, dict) and "rate" in dd for m, v in dd.items()},
                 **{f"{k}_{m}": v for k, dd in d.items() if k.startswith("mcnemar") for m, v in dd.items()}})
fb = [u for u in cl]  # fallbacks
res["claude_fallback_units"] = sum(1 for l in open(O / "claude_labels.jsonl") if json.loads(l)["fallback"])
res["claude_by_op"] = {op: {"n": int(len(g)), "claude_change": int(g.claude_change.sum()), "gpt": int(g.gpt_judge.sum()), "nli": int(g.nli_primary.sum())} for op, g in mut.groupby("op")}
pd.DataFrame(rows).to_csv(O / "scores.csv", index=False); (O / "summary.json").write_text(json.dumps(res, indent=1))
def p(x): return f"{100*x['rate']:.1f} ({x['k']}/{x['n']}; {100*x['lo']:.0f}-{100*x['hi']:.0f})"
L = ["# A2 fast: second-family (Claude) and NLI oracles on the independent mutants", "",
     "Sensitivity analysis on the human-confirmed set (75 mutants, 53 lexicon-blind, 46 controls); the frozen headline is the GPT judge row. Plan: PLAN.md (declared before scoring).",
     "Disclosure: Claude also arbitrated and assisted elsewhere in this pipeline; it is a second model family relative to the GPT judge, not independent of the authors' tooling.", "",
     "| oracle | mutation score, all | lexicon-blind | false alarms (46 controls) | McNemar vs GPT judge, all (judge-only/oracle-only, p) |", "|---|---|---|---|---|"]
for o in cols:
    d = res["oracles"][o]; mc = d.get("mcnemar_all")
    L.append(f"| {o} | {p(d['mut_all'])} | {p(d['mut_lexblind'])} | {p(d['false_alarm'])} | " + (f"{mc['judge_only']}/{mc['oracle_only']}, p={mc['p']}" if mc else "-") + " |")
L += ["", "Rates in % (k/n; Wilson 95% CI). claude_change = label(original) != label(mutant) on the confirmed dimension (primary); claude_ref = label(mutant) != reference value (the GPT judge's rule).",
      "nli_primary = contradiction either direction (declared primary); nli_secondary = not mutually entailed. either_/both_ = ensemble with the GPT judge.",
      f"Claude out-of-option fallbacks: {res['claude_fallback_units']} units.", "", "By operator (confirmed mutants): " + json.dumps(res["claude_by_op"])]
(O / "report.md").write_text("\n".join(L) + "\n"); print("\n".join(L))

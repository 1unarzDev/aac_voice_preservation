"""default_profiles round 3 (R3-1): G1 check() with a REAL keyword-plus-intent spec on stored elic1 P0 outputs (no generation).
Spec = interventions.supplied("The user typed: <source message>"): the intent labels the user would have committed to (oracle intent; upper bound on what G1 can detect).
Reports, per dimension, flagged share of reversal outputs (detection; repair would need regeneration, NOT run) and false-flag rate on correct outputs, HT-weighted by 1/inclusion_prob.
Output: analysis/frontier/default_profiles/g1_spec_check.json, g1_spec_check.csv.   . .venv/bin/activate && python src/frontier_default_profiles_g1spec.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); OUT = ROOT / "analysis/frontier/default_profiles"
import interventions as I
sc = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); sc = sc[sc.prompt_id.eq("P0") & sc.channel.str.startswith("human_")].copy()
msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv"); msg["fam"] = "elic-" + msg.source_id
srct = dict(zip(msg.fam, msg.text)); wm = dict(zip(msg.fam, 1 / msg.inclusion_prob)); sc["w"] = sc.family_id.map(wm)
spec = {f: I.supplied("The user typed: " + t) for f, t in srct.items()}
sc["src_neg"] = [spec[f].get("polarity") == frozenset({"negated"}) for f in sc.family_id]
sc["src_polite"] = [bool(spec[f].get("polite_ok")) for f in sc.family_id]
sc["src_nonstmt"] = [spec[f].get("speech_act") not in (None, frozenset({"statement"})) for f in sc.family_id]
sc["flg"] = [I.check(r.text, spec[r.family_id]) if r.text else ["empty"] for r in sc.itertuples()]
has = lambda p: sc.flg.apply(lambda x: any(s.startswith(p) for s in x))
sc["f_pol"] = has("polarity:"); sc["f_act"] = has("speech_act:"); sc["f_polite_req"] = has("politeness:") & ~has("politeness:added"); sc["f_added"] = has("politeness:added"); sc["any"] = sc.flg.str.len() > 0
sc["rev_neg"] = sc.src_neg & ~sc.polarity.eq("negated"); sc["rev_polite"] = sc.src_polite & sc.politeness.eq("none"); sc["rev_act"] = sc.src_nonstmt & sc.speech_act.eq("statement")
def ht(x): return float(1000 * np.average(x.astype(float), weights=sc.w))
rows = []
for dim, rev, fl in (("polarity", "rev_neg", "f_pol"), ("politeness", "rev_polite", "f_polite_req"), ("speech_act", "rev_act", "f_act")):
    r = sc[rev]; rows.append(dict(dimension=dim, reversal_outputs_per_1000=ht(sc[rev]), flagged_reversal_per_1000=ht(sc[rev] & sc[fl]), detection_share=float(np.average(sc[fl][r], weights=sc.w[r])) if r.sum() else np.nan,
                                  n_reversal_outputs=int(r.sum()), n_flagged=int((r & sc[fl]).sum()), note="detection only; repair needs regeneration (not run); spec is oracle intent"))
res = dict(spec="supplied('The user typed: '+source)", n_outputs=int(len(sc)), flag_rate_any_per_1000=ht(sc["any"]), politeness_added_flag_per_1000=ht(sc.f_added),
           politeness_added_flag_on_nonpolite_source_per_1000=ht(sc.f_added & ~sc.src_polite), false_flag_correct_outputs_share=float(np.average(sc["any"][~(sc.rev_neg | sc.rev_polite | sc.rev_act)], weights=sc.w[~(sc.rev_neg | sc.rev_polite | sc.rev_act)])),
           per_dimension=rows, flag_rate_by_model=sc.groupby("model")["any"].mean().to_dict())
pd.DataFrame(rows).to_csv(OUT / "g1_spec_check.csv", index=False); json.dump(res, open(OUT / "g1_spec_check.json", "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))

"""default_profiles round 2 (R2-4): MEASURE G1 inertness on the elicitation keyword units. Runs the real interventions.supplied + interventions.check
on every stored elic1 P0 output of the 4 models (human keyword channels), no generation. Output: analysis/frontier/default_profiles/g1_inertness.csv/json.
    . .venv/bin/activate && python src/frontier_default_profiles_g1check.py"""
import json, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); OUT = ROOT / "analysis/frontier/default_profiles"
import interventions as I, layer0
sc = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); sc = sc[sc.prompt_id.eq("P0") & sc.channel.str.startswith("human_")].copy()
key = {j["item_id"]: j for j in map(json.loads, open(ROOT / "annotation/elicitation_key.jsonl"))}
msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv"); msg["fam"] = "elic-" + msg.source_id
det = {r.fam: key[r.item_id]["detector_labels"] for r in msg.itertuples()}
cache = {}
def flags(r):
    k = (r.input_text, r.text)
    if k not in cache: cache[k] = I.check(r.text, I.supplied(r.input_text)) if r.text else ["empty"]
    return cache[k]
sc["flg"] = [flags(r) for r in sc.itertuples()]; sc["flagged"] = sc["flg"].str.len() > 0
sc["src_polite"] = [det[f]["politeness"] != "none" for f in sc.family_id]; sc["src_neg"] = [det[f]["polarity"] == "negated" for f in sc.family_id]
sc["flag_types"] = sc["flg"].apply(lambda x: ",".join(sorted(set(s.split(":")[0] + ":" + s.split(":")[1] for s in x))))
import numpy as np
wm = dict(zip(msg.fam, 1 / msg.inclusion_prob)); sc['w'] = sc.family_id.map(wm)
res = dict(n_outputs=int(len(sc)), flag_rate=float(sc.flagged.mean()), flag_rate_HT_weighted=float(np.average(sc.flagged, weights=sc.w)),
           correct_polite_flagged_HT_per_1000_outputs=float(1000 * np.average(sc.src_polite & ~sc.politeness.eq('none') & sc.flagged, weights=sc.w)),
           src_polite_output_polite_HT_per_1000=float(1000 * np.average(sc.src_polite & ~sc.politeness.eq('none'), weights=sc.w)), flag_types=sc.flag_types.value_counts().to_dict(),
           flagged_only_politeness_added=bool(set(sc.flag_types[sc.flagged]) <= {"politeness:added"}),
           flagged_on_src_polite=int((sc.flagged & sc.src_polite).sum()), flagged_on_src_not_polite=int((sc.flagged & ~sc.src_polite).sum()),
           flagged_on_src_neg=int((sc.flagged & sc.src_neg).sum()),
           flag_rate_by_model=sc.groupby("model").flagged.mean().to_dict(),
           polarity_reversal_outputs=int((sc.src_neg & ~sc.polarity.eq("negated")).sum()),
           polarity_reversal_outputs_flagged=int((sc.src_neg & ~sc.polarity.eq("negated") & sc.flagged).sum()),
           politeness_reversal_outputs=int((sc.src_polite & sc.politeness.eq("none")).sum()),
           politeness_reversal_outputs_flagged=int((sc.src_polite & sc.politeness.eq("none") & sc.flagged).sum()),
           correct_polite_outputs_flagged=int((sc.src_polite & ~sc.politeness.eq("none") & sc.flagged).sum()))
json.dump(res, open(OUT / "g1_inertness.json", "w"), indent=1); sc[["model", "family_id", "channel", "input_text", "text", "flagged", "flag_types", "src_polite", "src_neg"]].to_csv(OUT / "g1_inertness_rows.csv", index=False)
print(json.dumps(res, indent=1))

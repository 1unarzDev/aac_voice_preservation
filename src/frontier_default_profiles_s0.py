"""Frontier default_profiles, S0 inventory + H3 placebo check on stored hw1/hwctl outputs (0 generation).
Writes analysis/frontier/default_profiles/{pilot_inventory.md, placebo_h3.csv, s0_summary.json}.  Plan: PLAN.md sections 3, 4, 8."""
import json, sys, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/default_profiles"; OUT.mkdir(parents=True, exist_ok=True)
def md(df):
    c = list(df.columns); L = ["| " + " | ".join(map(str, c)) + " |", "|" + "---|" * len(c)]
    for r in df.itertuples(index=False): L.append("| " + " | ".join(f"{x:.3f}" if isinstance(x, float) else str(x) for x in r) + " |")
    return "\n".join(L)
rng = np.random.default_rng(20261101); B = 2000

# ---------- (a) cue-positive human units
msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv"); rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv")
key = {j["item_id"]: j for j in map(json.loads, open(ROOT / "annotation/elicitation_key.jsonl"))}
dl = {"polarity": ("polarity", "negated"), "speech_act": ("speech_act", None), "politeness": ("politeness", None)}
inv = {}
for d, col in (("polarity", "polarity"), ("speech_act", "speech_act"), ("politeness", "politeness"), ("certainty", "certainty"), ("quantity", "quantity")):
    present = msg[msg[f"{col}_present"].fillna(False).astype(bool)].item_id
    r = rat[rat.item_id.isin(present)]
    lost = r[f"{col}_lenient_lost"].fillna(0).astype(float)
    inv[d] = dict(messages_with_cue=int(len(present)), human_sets_with_cue=int(len(r)), human_sets_cue_dropped_lenient=int((lost > 0).sum()))
# ---------- (b/c) channels per model
runs = {"hw1": "hw1", "hwctl1": "hwctl1", "ext_hw_qwen14": "ext_hw_qwen14", "ext_hwctl_qwen14": "ext_hwctl_qwen14", "ext_hw_nemo": "ext_hw_nemo", "ext_hwctl_nemo": "ext_hwctl_nemo"}
S = pd.concat([pd.read_parquet(ROOT / f"runs/{r}/scored.parquet").assign(run=r) for r in runs.values()], ignore_index=True)
S = S[S.prompt_id.eq("P0") & ~S.quarantine_refusal_acceptance.fillna(False).astype(bool)]
chan = S.groupby(["model", "channel"]).size().unstack(fill_value=0)
# ---------- H3 placebo
S = S.assign(cm=S.critical_match.astype(float))
rows = []
for d in sorted(S.dimension.unique()):
    D = S[S.dimension.eq(d)]
    wide = D.pivot_table(index=["model", "family_id", "variant"], columns="channel", values="cm", aggfunc="first")
    wide = wide.dropna(subset=["noncrit", "irrel", "chip1", "nlcue"])
    fam = wide.index.get_level_values("family_id").to_numpy(); ufam = np.unique(fam)
    for scope in ["ALL"] + sorted(wide.index.get_level_values("model").unique()):
        w = wide if scope == "ALL" else wide[wide.index.get_level_values("model") == scope]
        f = w.index.get_level_values("family_id").to_numpy(); uf = np.unique(f)
        idx = {u: np.where(f == u)[0] for u in uf}
        arr = w[["noncrit", "irrel", "chip1", "nlcue"]].to_numpy()
        def est(a): return np.array([a[:, 1].mean() - a[:, 0].mean(), a[:, 2].mean() - a[:, 1].mean(), a[:, 2].mean() - a[:, 3].mean(), a[:, 2].mean() - a[:, 0].mean(), a[:, 0].mean()])
        pt = est(arr); bs = []
        for _ in range(B):
            pick = rng.choice(uf, len(uf)); sel = np.concatenate([idx[p] for p in pick]); bs.append(est(arr[sel]))
        lo, hi = np.quantile(np.array(bs), [.025, .975], axis=0)
        for k, nm in enumerate(["placebo_irrel_minus_noncrit", "chip1_minus_irrel", "chip1_minus_nlcue", "chip1_minus_noncrit", "noncrit_rate"]):
            rows.append(dict(dimension=d, scope=scope, contrast=nm, est=pt[k], lo=lo[k], hi=hi[k], n_units=len(w), n_families=len(uf)))
H = pd.DataFrame(rows); H.to_csv(OUT / "placebo_h3.csv", index=False)
def verdict(d):
    g = H[(H.dimension == d) & (H.scope == "ALL")].set_index("contrast")
    pl, ch = g.loc["placebo_irrel_minus_noncrit"], g.loc["chip1_minus_irrel"]
    pl_ok = abs(pl.est) <= .02 and pl.lo >= -.04 and pl.hi <= .04
    gain_ok = ch.est >= .10 and ch.lo > 0
    return dict(placebo_ok=bool(pl_ok), gain_ge_10pp=bool(gain_ok), assumption_credited=bool(pl_ok and gain_ok),
                placebo=[pl.est, pl.lo, pl.hi], gain=[ch.est, ch.lo, ch.hi])
V = {d: verdict(d) for d in sorted(S.dimension.unique())}
# per-model credit count on the primary dims
perm = {}
for d in ["polarity", "speech_act"]:
    n = 0; tot = 0
    for m in sorted(S.model.unique()):
        g = H[(H.dimension == d) & (H.scope == m)].set_index("contrast")
        if "placebo_irrel_minus_noncrit" not in g.index: continue
        tot += 1; pl, ch = g.loc["placebo_irrel_minus_noncrit"], g.loc["chip1_minus_irrel"]
        n += int(abs(pl.est) <= .02 and pl.lo >= -.04 and pl.hi <= .04 and ch.est >= .10 and ch.lo > 0)
    perm[d] = (n, tot)
# ---------- (d) gold n for RG
gold = pd.read_csv(ROOT / "annotation/judge_validation_elic.csv")
g1 = gold[(gold.reference_set == "human") & (gold.source == "final") & gold.subset.str.startswith("sampled@elic1#")][["dimension", "subset", "n", "acc", "acc_ci", "kappa"]]
gate = {"polarity_cue_pos_units_ge60": inv["polarity"]["human_sets_with_cue"] >= 60 and True,
        "speech_act_cue_pos_units_ge60": inv["speech_act"]["human_sets_with_cue"] >= 60,
        "placebo_models": int(sum(1 for m in chan.index if all(c in chan.columns and chan.loc[m, c] > 0 for c in ["irrel", "noncrit"]))) }
gate["GO"] = bool(gate["polarity_cue_pos_units_ge60"] and gate["speech_act_cue_pos_units_ge60"] and gate["placebo_models"] >= 4)
json.dump(dict(cue_units=inv, gate=gate, verdicts=V, per_model_credit_primary=perm), open(OUT / "s0_summary.json", "w"), indent=1, default=float)
with open(OUT / "pilot_inventory.md", "w") as f:
    f.write("# S0 pilot inventory (default_profiles, round 1). Zero generation; stored outputs only.\n\n")
    f.write("## (a) Cue-positive human units (elicitation: 600 messages x 3 human keyword sets)\n\n| dimension | messages with cue | human sets with cue | of which cue dropped (lenient flag) |\n|---|---|---|---|\n")
    for d, v in inv.items(): f.write(f"| {d} | {v['messages_with_cue']} | {v['human_sets_with_cue']} | {v['human_sets_cue_dropped_lenient']} |\n")
    f.write("\nQuantity is descriptive only (not tested), per PLAN. Note the exposure units E (cue in source AND dropped in keywords) are the 'dropped' column; these are the positives every policy comparison rests on.\n\n")
    f.write("## (b,c) Stored channel counts (P0, quarantine rows removed) for hw1-family runs\n\n" + md(chan.reset_index()) + "\n\nGemini flash-lite hw/hwctl runs are partial (2 / 86 rows scored): excluded.\n\n")
    f.write("## (d) Human gold for judge error rates (elic1 sample, final labels vs 4-annotator plurality)\n\n" + md(g1) + "\n\n")
    f.write("## H3 placebo check (stored data, ALL = 6 models pooled, family-cluster bootstrap 2,000, seed 20261101)\n\nCriterion (PLAN s1): |irrel - noncrit| <= 2 pp with CI inside +-4 pp AND chip1 - irrel >= 10 pp with CI > 0.\n\n| dimension | placebo diff [CI] | chip1 - irrel [CI] | placebo ok | gain >= 10 pp | assumption credited |\n|---|---|---|---|---|---|\n")
    for d, v in V.items():
        f.write(f"| {d} | {100*v['placebo'][0]:+.1f} [{100*v['placebo'][1]:+.1f}, {100*v['placebo'][2]:+.1f}] | {100*v['gain'][0]:+.1f} [{100*v['gain'][1]:+.1f}, {100*v['gain'][2]:+.1f}] | {v['placebo_ok']} | {v['gain_ge_10pp']} | {v['assumption_credited']} |\n")
    f.write(f"\nPer-model credit count (placebo and gain both pass), polarity {perm['polarity'][0]}/{perm['polarity'][1]}, speech act {perm['speech_act'][0]}/{perm['speech_act'][1]} models.\n\n")
    f.write(f"## GO / NO-GO\n\n{json.dumps(gate)}\n")
print(open(OUT / "pilot_inventory.md").read())

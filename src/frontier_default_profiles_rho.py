"""default_profiles round 3 (R3-2): resample hw1/hwctl1 pairs (writer-cluster bootstrap, as analysis/chip_controls) to give rho-draws for chip and plain-word cue-honouring rates,
pooled over models, per dimension. Draw 0 = point estimate; draws 1..B = writer resamples (seed 20261101). Output: analysis/frontier/default_profiles/rho_draws.csv.
    . .venv/bin/activate && python src/frontier_default_profiles_rho.py [B]"""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); OUT = ROOT / "analysis/frontier/default_profiles"
B = int(sys.argv[1]) if len(sys.argv) > 1 else 300
import analyze as A, analyze_hw1 as H
kept, raw_hw1 = H.kept, H.raw0
ctl = pd.read_parquet(ROOT / "runs/hwctl1/scored.parquet")
ctl2 = ctl.assign(channel_real=ctl.channel, channel={"irrel": "noncrit", "nlcue": "chip1"}.get(0, None) if False else ctl.channel.map({"irrel": "noncrit", "nlcue": "chip1"}))
d_ctl, ex = H.build(kept, ctl2); d_ctl["channel"] = d_ctl.channel_real
d_hw1, _ = H.build(kept, raw_hw1); d_hw1 = d_hw1[d_hw1.channel.isin(["noncrit", "chip1"])]
d = pd.concat([d_hw1[d_hw1.prompt_id == "P0"], d_ctl[d_ctl.prompt_id == "P0"]], ignore_index=True)
w = d.pivot(index=["family_id", "writer_id", "variant", "dimension", "model"], columns="channel", values="critical_match").reset_index()
for c in ("chip1", "nlcue"): w[c] = pd.to_numeric(w[c]).astype(float)
rng = np.random.default_rng(20261101); rows = []
for dim in ("polarity", "politeness", "speech_act"):
    g = w[w.dimension.eq(dim)]; wr = g.writer_id.unique(); grp = {k: v for k, v in g.groupby("writer_id")}
    for ch in ("chip1", "nlcue"):
        s = {k: (v[ch].sum(), v[ch].notna().sum()) for k, v in grp.items()}
        rows.append(dict(dimension=dim, channel=ch, draw=0, rho=g[ch].mean(), n_pairs=int(g[ch].notna().sum()), n_writers=len(wr)))
        r2 = np.random.default_rng(20261101 + hash(ch) % 1 + (0 if ch == "chip1" else 1) + 10 * ["polarity", "politeness", "speech_act"].index(dim))
        for b in range(1, B + 1):
            pick = r2.choice(wr, len(wr)); num = sum(s[k][0] for k in pick); den = sum(s[k][1] for k in pick)
            rows.append(dict(dimension=dim, channel=ch, draw=b, rho=num / den if den else np.nan, n_pairs=int(g[ch].notna().sum()), n_writers=len(wr)))
R = pd.DataFrame(rows); R.to_csv(OUT / "rho_draws.csv", index=False)
print(R[R.draw.eq(0)]); print(R[R.draw > 0].groupby(["dimension", "channel"]).rho.agg(["mean", lambda x: x.quantile(.025), lambda x: x.quantile(.975)]))

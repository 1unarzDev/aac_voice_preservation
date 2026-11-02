"""E0 pilot analysis (descriptive; plan section 4/5 formulas, no thresholds applied for decisions). Paired family bootstrap, 10,000, seed 20261102.
  python src/frontier_partner_context_analyze_e0.py"""
import json, sys, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/frontier/partner_context"; RUN = ROOT / "runs/frontier_partner_context_e0"
df = pd.read_parquet(RUN / "scored.parquet")
df[["kind", "turn"]] = df["channel"].str.split("|", expand=True)
rng = np.random.default_rng(20261102); B = 10000
def ci(x):  # x: (families,) paired differences or rates
    x = np.asarray(x, float); n = len(x); idx = rng.integers(0, n, (B, n)); m = x[idx].mean(1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
rows, gate = [], {}
for model, g in df.groupby("model"):
    g = g[g.valid.fillna(False)] if False else g
    gate[model] = {"n_rows": int(len(g)), "n_invalid": int((~g.valid.fillna(False).astype(bool)).sum()),
                   "n_label_missing": int(g.critical.isna().sum()), "valid_label_share": float(g.critical.notna().mean()),
                   "parse_fail": int((~g.parse_ok.fillna(False).astype(bool)).sum())}
    fams = sorted(g.family_id.unique())
    def vec(kind, turn, variant, f):  # label per family
        s = g[(g.kind == kind) & (g.turn == turn) & (g.variant == variant)].set_index("family_id").critical
        return s.reindex(fams)
    def ind(s, fn): return np.array([np.nan if pd.isna(v) else float(fn(v)) for v in s])
    # bare: output intent-independent; use variant A
    for t in "0NDXQ":
        s = vec("bare", t, "A", fams)
        for lab in ("negated", "affirmative", "unclear/mixed"):
            m, lo, hi = ci(np.nan_to_num(ind(s, lambda v: v == lab)))
            rows.append(dict(model=model, channel="bare", turn=t, metric=f"share_{lab}", est=m, lo=lo, hi=hi, n=len(fams)))
    # chip: per variant
    for t in "0NDXQ":
        for vn, cue in (("A", "affirmative"), ("B", "negated")):
            s = vec("chip", t, vn, fams)
            for nm, fn in (("exact_match", lambda v: v == cue), ("override", lambda v: v not in (cue, "unclear/mixed")), ("violation", lambda v: v != cue), ("uncommitted", lambda v: v == "unclear/mixed")):
                m, lo, hi = ci(np.nan_to_num(ind(s, fn)))
                rows.append(dict(model=model, channel=f"chip_{vn}", turn=t, metric=nm, est=m, lo=lo, hi=hi, n=len(fams)))
    # contrasts (paired; NaN -> 0 handled by treating missing as not-event; missing share reported in gate)
    def d(a, b): return ci(np.nan_to_num(a) - np.nan_to_num(b))
    bN = {lab: ind(vec("bare", "N", "A", fams), lambda v, l=lab: v == l) for lab in ("negated", "affirmative")}
    bX = ind(vec("bare", "X", "A", fams), lambda v: v == "negated"); bQ = ind(vec("bare", "Q", "A", fams), lambda v: v == "affirmative")
    # C1 override: incongruent turn (A+X, B+D) minus N, pooled over variants
    inc = (np.nan_to_num(ind(vec("chip", "X", "A", fams), lambda v: v not in ("affirmative", "unclear/mixed"))) + np.nan_to_num(ind(vec("chip", "D", "B", fams), lambda v: v not in ("negated", "unclear/mixed")))) / 2
    neu = (np.nan_to_num(ind(vec("chip", "N", "A", fams), lambda v: v not in ("affirmative", "unclear/mixed"))) + np.nan_to_num(ind(vec("chip", "N", "B", fams), lambda v: v not in ("negated", "unclear/mixed")))) / 2
    C = {"C1_override_incongruent_minus_N(chip)": ci(inc - neu),
         "C2_frame_following_bare_X_minus_N(share negated)": d(bX, bN["negated"]),
         "C3_question_bare_Q_minus_N(share affirmative)": d(bQ, bN["affirmative"]),
         "C4_benefit_bare_X_minus_N(exact-match negated-intended)": d(bX, bN["negated"]),
         "bare_D_minus_N(share affirmative)": d(ind(vec("bare", "D", "A", fams), lambda v: v == "affirmative"), bN["affirmative"]),
         "bare_X_minus_0(share negated)": d(bX, ind(vec("bare", "0", "A", fams), lambda v: v == "negated"))}
    for k, (m, lo, hi) in C.items(): rows.append(dict(model=model, channel="contrast", turn="-", metric=k, est=m, lo=lo, hi=hi, n=len(fams)))
res = pd.DataFrame(rows); res.to_csv(OUT / "e0_results.csv", index=False)
(OUT / "e0_gate_inputs.json").write_text(json.dumps(gate, indent=1))
print(json.dumps(gate, indent=1)); pd.set_option("display.width", 200)
print(res[res.channel == "contrast"].round(3).to_string())

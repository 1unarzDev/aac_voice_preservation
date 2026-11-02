"""E1 analysis (T1 legend test). Decision rule: analysis/legend_test/PLAN.md (written before generation).

    . .venv/bin/activate && python src/analyze_legend.py

Reads runs/legend1/scored.parquet (attribute.py WITHOUT fallback, items data/items_ext/legend_items.jsonl) and
runs/requests/legend1.jsonl (arm = prompt_id, draw = namespace; no namespace = d0, the cached original hw1/r2c1 draw).
Writes analysis/legend_test/{report.md,summary.json,arm_share.csv,arm_diff.csv,per_draw.csv}.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A  # noqa: E402

OUT = ROOT / "analysis/legend_test"; B = 10000; SEED = 20261031
ARM = {"P0": "a_legend", "P0n": "b_nolegend", "P0m": "c_markers_missing"}
sc = pd.read_parquet(ROOT / "runs/legend1/scored.parquet")
assert not sc.critical_source.isin(["J1", "J2"]).any(), "fallback labels present"
req = {}
for l in (ROOT / "runs/requests/legend1.jsonl").open():
    r = json.loads(l); req[r["request_key"]] = (r["prompt_id"], r.get("namespace") or "d0")
items = {}
for l in (ROOT / "data/items_ext/legend_items.jsonl").open():
    d = json.loads(l); items[d["family_id"]] = d
sc["arm"] = sc.request_key.map(lambda k: ARM[req[k][0]]); sc["draw"] = sc.request_key.map(lambda k: req[k][1])
sc["source_set"] = sc.family_id.map(lambda f: items[f]["source_set"])
sc["writer_id"] = sc.family_id.map(lambda f: items[f].get("writer_id", f))
# one row per (family, model, arm, draw, request, suggestion): A/B share the bare request
sc = sc.sort_values("variant").drop_duplicates(["family_id", "model", "arm", "draw", "request_key", "suggestion_idx"]).copy()
sc["valid_b"] = sc.valid.astype(bool)
unresolved = int((sc.valid_b & sc.critical.isna()).sum())
cm = sc.valid_b & sc.critical.isin(["affirmative", "negated"])
sc["aff"] = np.where(cm, (sc.critical == "affirmative").astype(float), np.nan)               # primary: among committed
sc["aff_all"] = np.where(sc.valid_b & sc.critical.notna(), (sc.critical == "affirmative").astype(float), np.nan)
sc["neg_all"] = np.where(sc.valid_b & sc.critical.notna(), (sc.critical == "negated").astype(float), np.nan)
sc["commit"] = np.where(sc.valid_b & sc.critical.notna(), sc.critical.isin(["affirmative", "negated"]).astype(float), np.nan)
sc["unclear_all"] = 1 - sc.commit


def boot(g, col, cluster="family_id"):
    x = g.copy(); x["family_id"] = x[cluster]
    r = A.family_bootstrap(x, col, n_boot=B, seed=SEED)
    r["n_clusters"] = r.pop("n_families"); r.pop("n_families_observed", None); return r


def cell(g, tag):
    out = {}
    for col in ("aff", "aff_all", "neg_all", "commit", "unclear_all"):
        r = boot(g, col); out[col] = r
    return out


rows = []
sets = {"pooled": sc, "hw1": sc[sc.source_set == "hw1"], "WC": sc[sc.source_set == "WC"]}
for draw in ["d1", "d2", "d0"]:
    for sname, s in sets.items():
        for arm in ARM.values():
            for model in ["ALL"] + sorted(s.model.unique()):
                g = s[(s.draw == draw) & (s.arm == arm)]
                if model != "ALL": g = g[g.model == model]
                if g.empty: continue
                c = cell(g, "")
                row = dict(draw=draw, source=sname, arm=arm, model=model, n_rows=len(g), n_families=g.family_id.nunique())
                for col, r in c.items():
                    row |= {f"{col}": r["estimate"], f"{col}_lo": r["ci_low"], f"{col}_hi": r["ci_high"], f"{col}_n": r["n"]}
                if sname == "hw1":
                    w = boot(g, "aff", "writer_id"); row |= dict(aff_writer_lo=w["ci_low"], aff_writer_hi=w["ci_high"], n_writers=w["n_clusters"])
                rows.append(row)
share = pd.DataFrame(rows); share.to_csv(OUT / "arm_share.csv", index=False)

# arm differences, paired by (family, model), per draw
drows = []
for draw in ["d1", "d2"]:
    for sname, s in sets.items():
        for model in ["ALL"] + sorted(s.model.unique()):
            g = s[s.draw == draw]
            if model != "ALL": g = g[g.model == model]
            for col in ("aff", "aff_all", "commit"):
                p = g.groupby(["family_id", "model", "arm"])[col].mean().unstack("arm").reset_index()
                for lhs, rhs in (("b_nolegend", "a_legend"), ("c_markers_missing", "a_legend"), ("c_markers_missing", "b_nolegend")):
                    q = p.dropna(subset=[lhs, rhs]).copy(); q["d"] = q[lhs] - q[rhs]
                    q = q.rename(columns={}); r = boot(q, "d")
                    drows.append(dict(draw=draw, source=sname, model=model, metric=col, contrast=f"{lhs} - {rhs}",
                                      estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"], n=r["n"]))
diff = pd.DataFrame(drows); diff.to_csv(OUT / "arm_diff.csv", index=False)

# ---------- decision rule (PLAN.md), draw d1, pooled over models and sources
def cls(v):
    return "not_artifact" if v >= .90 else "reframe" if v < .70 else "partly_induced"
d1 = share[(share.draw == "d1") & (share.source == "pooled")]
pooled = {r.arm: r for r in d1[d1.model == "ALL"].itertuples()}
b, c = pooled["b_nolegend"].aff, pooled["c_markers_missing"].aff
if b >= .90 and c >= .90: verdict = "default is NOT a legend artifact (b and c both >= 90%)"
elif b < .70 or c < .70: verdict = "default claim must be REFRAMED (b or c < 70%)"
else: verdict = "PARTLY INDUCED (an arm between 70% and 90%)"
per_model = {m: {arm: dict(aff=float(x.aff), cls=cls(x.aff)) for arm, x in zip(g.arm, g.itertuples()) if arm != "a_legend"}
             for m, g in d1[d1.model != "ALL"].groupby("model")}
summary = dict(n_scored_rows=len(sc), unresolved_valid_rows=unresolved, verdict_d1=verdict,
               pooled_d1={a: dict(aff=float(r.aff), lo=float(r.aff_lo), hi=float(r.aff_hi), aff_all=float(r.aff_all),
                                  commit=float(r.commit), n=int(r.aff_n)) for a, r in pooled.items()},
               per_model_class_d1=per_model,
               d2_pooled={r.arm: float(r.aff) for r in share[(share.draw == "d2") & (share.source == "pooled") & (share.model == "ALL")].itertuples()},
               d0_arm_a_pooled=float(share[(share.draw == "d0") & (share.source == "pooled") & (share.model == "ALL")].aff.iloc[0]))
(OUT / "summary.json").write_text(json.dumps(summary, indent=1))


def pct(x): return f"{100 * x:.1f}"


def tab(draw, sname):
    s = share[(share.draw == draw) & (share.source == sname)]
    lines = ["| model | arm | n | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |", "|---|---|---|---|---|---|---|"]
    for m in ["ALL"] + sorted(set(s.model) - {"ALL"}):
        for arm in ARM.values():
            x = s[(s.model == m) & (s.arm == arm)]
            if x.empty: continue
            x = x.iloc[0]
            lines.append(f"| {m} | {arm} | {int(x.aff_n)} | {pct(x.aff)} [{pct(x.aff_lo)}, {pct(x.aff_hi)}] | {pct(x.aff_all)} | {pct(x.commit)} | {pct(x.unclear_all)} |")
    return "\n".join(lines)


def dtab(draw, sname, metric="aff"):
    s = diff[(diff.draw == draw) & (diff.source == sname) & (diff.metric == metric)]
    lines = ["| model | contrast | difference pp [95% CI, family-cluster] | n pairs |", "|---|---|---|---|"]
    for m in ["ALL"] + sorted(set(s.model) - {"ALL"}):
        for ct in s.contrast.unique():
            x = s[(s.model == m) & (s.contrast == ct)].iloc[0]
            lines.append(f"| {m} | {ct} | {100*x.estimate:+.1f} [{100*x.ci_low:+.1f}, {100*x.ci_high:+.1f}] | {int(x.n)} |")
    return "\n".join(lines)


md = [f"# E1: prompt-legend test on bare polarity inputs (T1)\n",
      f"Decision rule: `analysis/legend_test/PLAN.md` (written before generation). Run `runs/legend1`; labels J1==J2 else blind arbiter, **no fallback**; "
      f"{unresolved} valid rows unresolved. Primary draw d1, pooled over 4 models and both source sets (hw1 104 families, W-C 80 families); family-cluster 95% bootstrap CIs (10,000).\n",
      f"## Verdict (pre-declared rule, draw d1): **{verdict}**\n",
      f"Pooled affirmative share among committed outputs, d1: a (legend) {pct(pooled['a_legend'].aff)}%, b (no legend) {pct(b)}%, c (markers may be missing) {pct(c)}%. "
      f"d2 replication: " + ", ".join(f"{k} {pct(v)}%" for k, v in summary['d2_pooled'].items()) + f"; arm a original draw d0 (the published number): {pct(summary['d0_arm_a_pooled'])}%.\n",
      "## Per arm x model x source, draw d1 (primary)\n### Pooled over sources\n", tab("d1", "pooled"), "\n### hw1 only (human-written; writer-cluster CI in arm_share.csv)\n", tab("d1", "hw1"),
      "\n### W-C only\n", tab("d1", "WC"), "\n## Arm differences (paired by family x model), draw d1, pooled sources, affirmative share among committed\n", dtab("d1", "pooled"),
      "\n### Commitment rate differences (share of valid outputs with a definite polarity)\n", dtab("d1", "pooled", "commit"),
      "\n## Replication draw d2, pooled sources\n", tab("d2", "pooled"), "\n", dtab("d2", "pooled"),
      "\n## Original draw d0 (arm a only; reused cache)\n", tab("d0", "pooled")]
(OUT / "report.md").write_text("\n".join(md) + "\n")
print(json.dumps(summary, indent=1))

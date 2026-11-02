"""T6: small-cluster inference for the human-written replication (hw1; rerunnable with hw2 added).

    . .venv/bin/activate && python src/robust_t6_small_cluster.py
    python src/robust_t6_small_cluster.py --items data/items/hw.jsonl data/items/hw2.jsonl --runs runs/hw1 runs/hw2 --name hw12

Reuses the loaders and frame builders of src/analyze_hw1.py (build, frames; writers are the clusters). Stored data only.
For each registered contrast P1 (speech-act chip gain), P2 (full-input politeness addition - removal) and P3 (bare affirmative share - 0.5):
  * pooled row-weighted estimate with CR1 cluster-robust SE and a t interval, df = writers - 1 (linearised ratio estimator);
  * mean of writer-level means with t interval, df = writers - 1 (equal-weight writers);
  * wild-cluster bootstrap-t (restricted residuals for p; unrestricted for the interval), Rademacher (exact enumeration of all 2^G sign
    patterns when G <= 14) and Webb six-point weights (random, 19,999 draws, seed 20261101);
  * writer-level randomization (sign-flip) test, exact over 2^G, one-sided as in the registration; the minimum attainable p is 1/2^G;
  * per-model estimates (t, df = writers - 1) and a within-block model-label permutation test of heterogeneity (9,999 draws);
  * leave-one-writer-out estimates.
Comparison with the stored writer-cluster percentile bootstrap (analysis/hw1/primary_contrasts.csv) is included.
"""
from __future__ import annotations
import argparse, itertools, json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A                    # noqa: E402
import analyze_hw1 as H1               # noqa: E402  (loaders and frame builders; module-level hw1 loads are cheap)
from robust_common import outdir, write_json, md_table, pct   # noqa: E402

SEED = 20261101; NPERM = 9999; NWEBB = 19999
WEBB = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])


def load(items_paths, run_dirs):
    items = {}
    for p in items_paths:
        for f, it in A.load_items(str(ROOT / p)).items():
            assert f not in items, f"duplicate family {f}"
            items[f] = it
    raws = [pd.read_parquet(ROOT / r / "scored.parquet") for r in run_dirs]
    raw = pd.concat(raws, ignore_index=True)
    assert set(items) <= set(raw.family_id), "items without scored rows"
    return items, raw


def agg(g, col="value"):
    x = g[g[col].notna()]
    a = x.groupby("writer_id")[col].agg(S="sum", n="count"); return a


def ratio(a):
    est = a.S.sum() / a.n.sum(); G = len(a)
    e = a.S - est * a.n; var = (G / (G - 1)) * (e ** 2).sum() / a.n.sum() ** 2
    return est, np.sqrt(var), e


def tci(est, se, G):
    q = stats.t.ppf(.975, G - 1); return est - q * se, est + q * se, 2 * stats.t.sf(abs(est / se), G - 1) if se > 0 else np.nan


def wild(a, kind, rng):
    est, se, e = ratio(a); G = len(a); n = a.n.to_numpy(float); S = a.S.to_numpy(float); N = n.sum()
    if kind == "rademacher" and G <= 14:
        V = np.array(list(itertools.product([-1., 1.], repeat=G))); exact = True
    elif kind == "rademacher":
        V = rng.choice([-1., 1.], size=(NWEBB, G)); exact = False
    else:
        V = rng.choice(WEBB, size=(NWEBB, G)); exact = False
    # restricted (H0: theta = 0) residuals: y itself; statistic t* = est*/se*
    St = V * S; est_b = St.sum(1) / N; e_b = St - est_b[:, None] * n; se_b = np.sqrt((G / (G - 1)) * (e_b ** 2).sum(1)) / N
    with np.errstate(divide="ignore", invalid="ignore"):
        t_b = np.where(se_b > 0, est_b / se_b, 0.); t_obs = est / se if se > 0 else np.inf
    p_two = float((np.abs(t_b) >= abs(t_obs) - 1e-12).mean())
    p_one = float((t_b >= t_obs - 1e-12).mean())
    # unrestricted residuals around the estimate for the percentile-t interval
    eb_u = V * e.to_numpy(); est_u = eb_u.sum(1) / N; e2 = eb_u - est_u[:, None] * n; se_u = np.sqrt((G / (G - 1)) * (e2 ** 2).sum(1)) / N
    with np.errstate(divide="ignore", invalid="ignore"):
        tu = np.where(se_u > 0, est_u / se_u, 0.)
    lo_q, hi_q = np.quantile(tu, [.025, .975])
    return dict(p_two_sided=p_two, p_one_sided=p_one, ci_low=float(est - hi_q * se), ci_high=float(est - lo_q * se), draws=int(len(V)), exact=exact,
                min_attainable_p_two_sided=float(2 / len(V)) if exact else float(1 / (len(V) + 1)))


def signflip(a):
    G = len(a); S = a.S.to_numpy(float); n = a.n.to_numpy(float)
    V = np.array(list(itertools.product([-1., 1.], repeat=G))); stat = (V * S).sum(1) / n.sum(); obs = S.sum() / n.sum()
    return dict(p_one_sided=float((stat >= obs - 1e-12).mean()), p_two_sided=float((np.abs(stat) >= abs(obs) - 1e-12).mean()), n_patterns=int(len(V)),
                min_attainable_one_sided=float(1 / len(V)), all_writer_signs_positive=bool((S > 0).all()))


def block_cols(name, f):
    return ["family_id", "variant"] if (name == "P1" and "variant" in f) else ["family_id"]


def het_test(f, name, rng):
    x = f[f.value.notna()].copy(); models = sorted(x.model.unique())
    if len(models) < 2: return None
    def stat(y, m):
        t = pd.DataFrame({"y": y, "m": m}).groupby("m").y.mean(); w = pd.DataFrame({"m": m}).groupby("m").size()
        return float((w * (t - np.average(t, weights=w)) ** 2).sum())
    keys = x[block_cols(name, x)].astype(str).agg("|".join, axis=1).to_numpy(); y = x.value.to_numpy(float); m0 = x.model.to_numpy()
    obs = stat(y, m0); idx = pd.Series(range(len(x))).groupby(keys).apply(list).tolist(); cnt = 0
    for _ in range(NPERM):
        m = m0.copy()
        for ix in idx:
            if len(ix) > 1: m[ix] = m0[ix][rng.permutation(len(ix))]
        cnt += stat(y, m) >= obs - 1e-12
    return dict(statistic=obs, p=(1 + cnt) / (NPERM + 1), permutations=NPERM, models=models)


def analyse(f, name, rng, stored):
    a = agg(f); est, se, _ = ratio(a); G = len(a)
    lo, hi, pt = tci(est, se, G)
    wm = a.S / a.n; mm = wm.mean(); sem = wm.std(ddof=1) / np.sqrt(G); q = stats.t.ppf(.975, G - 1)
    res = dict(contrast=name, writers=G, rows=int(a.n.sum()), estimate=est, se_cr1=se, t_ci_low=lo, t_ci_high=hi, t_p_two_sided=pt, t_p_one_sided=pt / 2 if est > 0 else 1 - pt / 2,
               mean_of_writer_means=mm, writer_mean_t_ci_low=mm - q * sem, writer_mean_t_ci_high=mm + q * sem,
               writer_means={w: float(v) for w, v in wm.items()}, writer_rows={w: int(v) for w, v in a.n.items()},
               share_of_rows_largest_writer=float(a.n.max() / a.n.sum()), effective_writers=float(a.n.sum() ** 2 / (a.n ** 2).sum()))
    res["wild_rademacher"] = wild(a, "rademacher", rng); res["wild_webb"] = wild(a, "webb", rng); res["sign_flip_randomization"] = signflip(a)
    loo = {}
    for w in a.index:
        b = a.drop(w); e, s, _ = ratio(b); l, h, _ = tci(e, s, len(b)); loo[w] = dict(estimate=float(e), t_ci_low=float(l), t_ci_high=float(h))
    res["leave_one_writer_out"] = loo
    res["loo_range"] = [min(v["estimate"] for v in loo.values()), max(v["estimate"] for v in loo.values())]
    res["loo_t_ci_excludes_zero_all"] = all(v["t_ci_low"] > 0 for v in loo.values())
    res["stored_percentile_bootstrap"] = stored.get(name)
    pm = {}
    for m, g in f.groupby("model"):
        am = agg(g); e, s, _ = ratio(am); l, h, p = tci(e, s, len(am))
        pm[m] = dict(estimate=float(e), t_ci_low=float(l), t_ci_high=float(h), t_p_two_sided=float(p), rows=int(am.n.sum()), writers=int(len(am)),
                     sign_flip_p_one_sided=signflip(am)["p_one_sided"], all_writer_means_positive=bool(((am.S / am.n) > 0).all()))
    res["per_model"] = pm; res["heterogeneity_model_permutation"] = het_test(f, name, rng)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="+", default=["data/items/hw.jsonl"]); ap.add_argument("--runs", nargs="+", default=["runs/hw1"]); ap.add_argument("--name", default="hw1")
    a = ap.parse_args()
    OUT = outdir(f"t6_small_cluster" if a.name == "hw1" else f"t6_small_cluster_{a.name}")
    if a.name == "hw1":
        items, raw = H1.kept, H1.raw0                    # the exact hw1 loaders (cross-checked against the --items default below)
        chk, _ = load(a.items, a.runs); assert set(chk) == set(items)
    else:
        items, raw = load(a.items, a.runs)
    d, excl = H1.build(items, raw)
    fr = H1.frames(d); rng = np.random.default_rng(SEED)
    stored = {}
    try:
        pc = pd.read_csv(ROOT / "analysis/hw1/primary_contrasts.csv"); pc = pc[pc.cluster == "writer"]
        stored = {r.contrast: dict(estimate=r.estimate, ci_low=r.ci_low, ci_high=r.ci_high, p_holm=r.p_holm) for r in pc.itertuples()} if a.name == "hw1" else {}
    except Exception:
        pass
    out = {"name": a.name, "items": a.items, "runs": a.runs, "seed": SEED, "writers_by_contrast": {}, "contrasts": {}}
    rows = []
    for k, f in fr.items():
        r = analyse(f, k, rng, stored); out["contrasts"][k] = r
        rows.append(dict(contrast=k, writers=r["writers"], rows=r["rows"], estimate_pp=100 * r["estimate"], percentile_boot_lo=100 * (stored.get(k) or {}).get("ci_low", np.nan),
                         percentile_boot_hi=100 * (stored.get(k) or {}).get("ci_high", np.nan), t_lo=100 * r["t_ci_low"], t_hi=100 * r["t_ci_high"], writer_mean_t_lo=100 * r["writer_mean_t_ci_low"],
                         writer_mean_t_hi=100 * r["writer_mean_t_ci_high"], wild_rad_lo=100 * r["wild_rademacher"]["ci_low"], wild_rad_hi=100 * r["wild_rademacher"]["ci_high"],
                         wild_webb_lo=100 * r["wild_webb"]["ci_low"], wild_webb_hi=100 * r["wild_webb"]["ci_high"], t_p2=r["t_p_two_sided"], wild_rad_p2=r["wild_rademacher"]["p_two_sided"],
                         wild_webb_p2=r["wild_webb"]["p_two_sided"], signflip_p1=r["sign_flip_randomization"]["p_one_sided"], signflip_min_p1=r["sign_flip_randomization"]["min_attainable_one_sided"],
                         het_p=(r["heterogeneity_model_permutation"] or {}).get("p")))
    T = pd.DataFrame(rows); T.to_csv(OUT / "contrasts.csv", index=False)
    pm = [dict(contrast=k, model=m, **v) for k, r in out["contrasts"].items() for m, v in r["per_model"].items()]
    pd.DataFrame(pm).to_csv(OUT / "per_model.csv", index=False)
    # Holm over t-based p and over sign-flip p
    def holm(ps):
        order = sorted(ps, key=ps.get); prev = 0; o = {}
        for j, k in enumerate(order): prev = max(prev, min(1., (len(order) - j) * ps[k])); o[k] = prev
        return o
    out["holm_t_two_sided"] = holm({k: r["t_p_two_sided"] for k, r in out["contrasts"].items()})
    out["holm_wild_webb_two_sided"] = holm({k: r["wild_webb"]["p_two_sided"] for k, r in out["contrasts"].items()})
    out["holm_signflip_one_sided"] = holm({k: r["sign_flip_randomization"]["p_one_sided"] for k, r in out["contrasts"].items()})
    write_json(OUT / "summary.json", out)
    L = [f"# T6: small-cluster inference for {a.name} (writer = cluster; stored data only, 0 generation / 0 judge calls)", "",
         f"Script `src/robust_t6_small_cluster.py` (items {a.items}, runs {a.runs}). Loaders/frames reused from `src/analyze_hw1.py`. Rerun with hw2: "
         "`python src/robust_t6_small_cluster.py --items data/items/hw.jsonl data/items/hw2.jsonl --runs runs/hw1 runs/hw2 --name hw12`. Seed 20261101.", "",
         "Estimates are pooled row-weighted means (as in `analyze_hw1.py`), in percentage points; P3 is the bare affirmative share minus 50 pp. "
         "`t` = CR1 cluster-robust SE with t(writers-1); `writer-mean t` = unweighted mean of writer means; `wild` = wild-cluster bootstrap-t (Rademacher exact over all 2^G patterns; Webb 6-point, 19,999 draws); "
         "sign-flip = exact writer-level randomization test, one-sided, whose smallest possible p is 1/2^G.", "",
         "## Intervals (pp)", "", "| contrast | writers | rows | estimate | stored percentile bootstrap | t (CR1) | writer-mean t | wild Rademacher | wild Webb |", "|---|---|---|---|---|---|---|---|---|"]
    for r in T.itertuples():
        L.append(f"| {r.contrast} | {r.writers} | {r.rows} | {r.estimate_pp:+.1f} | [{r.percentile_boot_lo:.1f}, {r.percentile_boot_hi:.1f}] | [{r.t_lo:.1f}, {r.t_hi:.1f}] | [{r.writer_mean_t_lo:.1f}, {r.writer_mean_t_hi:.1f}] | "
                 f"[{r.wild_rad_lo:.1f}, {r.wild_rad_hi:.1f}] | [{r.wild_webb_lo:.1f}, {r.wild_webb_hi:.1f}] |")
    L += ["", "## p-values", "", "| contrast | t two-sided | Holm(t) | wild Rademacher two-sided (min attainable) | wild Webb two-sided | sign-flip one-sided (min attainable) | Holm(sign-flip) | stored bootstrap Holm |", "|---|---|---|---|---|---|---|---|"]
    for k, r in out["contrasts"].items():
        L.append(f"| {k} | {r['t_p_two_sided']:.4f} | {out['holm_t_two_sided'][k]:.4f} | {r['wild_rademacher']['p_two_sided']:.4f} ({r['wild_rademacher']['min_attainable_p_two_sided']:.4f}) | "
                 f"{r['wild_webb']['p_two_sided']:.4f} | {r['sign_flip_randomization']['p_one_sided']:.4f} ({r['sign_flip_randomization']['min_attainable_one_sided']:.4f}) | {out['holm_signflip_one_sided'][k]:.4f} | "
                 f"{(r['stored_percentile_bootstrap'] or {}).get('p_holm', float('nan')):.4f} |")
    L += ["", "## Writer-level means (pp) and leave-one-writer-out", ""]
    for k, r in out["contrasts"].items():
        L += [f"**{k}**: writer means " + ", ".join(f"{w} {100*v:+.1f} (n={r['writer_rows'][w]})" for w, v in r["writer_means"].items()) +
              f"; effective writers {r['effective_writers']:.2f}; largest writer {100*r['share_of_rows_largest_writer']:.0f}% of rows; leave-one-out estimates {100*r['loo_range'][0]:+.1f} to {100*r['loo_range'][1]:+.1f}; "
              f"t-CI excludes 0 in every leave-one-out: {r['loo_t_ci_excludes_zero_all']}; all writer signs positive: {r['sign_flip_randomization']['all_writer_means_positive'] if 'all_writer_means_positive' in r['sign_flip_randomization'] else r['sign_flip_randomization']['all_writer_signs_positive']}.", ""]
    L += ["## Per-model estimates (pp, t df = writers-1) and heterogeneity", "",
          "| contrast | model | estimate | t CI | t p (2-sided) | sign-flip p (1-sided) | all writer means > 0 |", "|---|---|---|---|---|---|---|"]
    for k, r in out["contrasts"].items():
        for m, v in r["per_model"].items():
            L.append(f"| {k} | {m} | {100*v['estimate']:+.1f} | [{100*v['t_ci_low']:.1f}, {100*v['t_ci_high']:.1f}] | {v['t_p_two_sided']:.3f} | {v['sign_flip_p_one_sided']:.3f} | {v['all_writer_means_positive']} |")
        h = r["heterogeneity_model_permutation"]
        L.append(f"| {k} | heterogeneity (within-family model-label permutation, {h['permutations']} draws) | SS={h['statistic']:.2f} | | p={h['p']:.4f} | | |")
    L += ["", "## Caveats", "",
          "* With G = 6-7 writers per contrast, every method here is conditional on very few clusters; the exact sign-flip test cannot return p below 1/2^G (about .016 one-sided for 6 writers), so Holm p = .0003 from the percentile bootstrap is a resampling floor rather than evidence at that level; the number to quote is the smallest attainable p when all writer signs agree.",
          "* Writer-clustering does not remove family or item dependence inside a writer; family counts per writer vary and one writer can dominate rows (see effective writers).",
          "* Writers were volunteers working to a protocol; P06's speech-act pair is excluded as in `analyze_hw1.py`; no hw preregistration exists, so all inference is exploratory.",
          "* The heterogeneity test permutes model labels within family blocks (models see the same inputs) and tests equality of pooled model means, not writer-by-model interactions."]
    (OUT / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:45]))


if __name__ == "__main__":
    main()

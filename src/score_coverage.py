"""Score the Stage 6 intent-coverage returns (Parts 26 and 27). Rules: annotation/COORDINATOR_STEPS.md section 6 (marked before any return);
design: analysis/coverage/PLAN.md sections 4, 5, 7 and src/make_coverage_stage6.py.

  python src/score_coverage.py --self-check             # synthetic writers on the real key; no private file is changed; scratch in tmp/
  python src/score_coverage.py [--sv DIR] [--pool DIR] [--out DIR] [--B 10000]
Inputs: annotation/coverage_key.csv (PRIVATE), annotation/returns_part26/labels_part26_<ID>.csv, annotation/returns_part27/labels_part27_<ID>.csv.
Outputs (default analysis/coverage_human/): qc.json, by_arm.csv, contrasts.csv, direct_vs_pool.csv, concordance.json, summary.json,
free_text_to_code.csv. Missing answers are never imputed; an arm-item endpoint is undefined (excluded) when a draft in the set was not rated
and no rated draft covers. Human labels are writer-intent agreement by adult annotators (not AAC users); the machine proxy is a research
instrument and its agreement with writers is reported, never called validation by AAC users."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY = ROOT / "annotation" / "coverage_key.csv"
ARMS = ["G1", "D3p", "C3", "E3"]
OKACC = {"yes", "small_edit"}
SEED = 20261117
RS = (0.25, 0.5, 1.0, 2.0)


# ------------------------------------------------------------------ loading and QC
def read_returns(folder: Path, part: str) -> pd.DataFrame:
    fs = sorted(Path(folder).glob(f"labels_{part}_*.csv")) if Path(folder).exists() else []
    parts = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in fs]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def qc(ret: pd.DataFrame, key: pd.DataFrame, kind: str, qcols: list[str]) -> tuple[pd.DataFrame, dict]:
    rep = {"rows": int(len(ret)), "practice_dropped": 0, "unknown_item": 0, "wrong_annotator": 0, "duplicate": 0, "incomplete": 0, "invalid_option": 0}
    if ret.empty:
        return ret, rep
    ret = ret[ret["practice"].astype(str) != "1"].copy(); rep["practice_dropped"] = rep["rows"] - len(ret)
    k = key[key.kind == kind].set_index("item_id")
    unk = ~ret["item_id"].isin(k.index); rep["unknown_item"] = int(unk.sum()); ret = ret[~unk]
    who = ret["item_id"].map(k["annotator"]); bad = who != ret["annotator"].str.strip().str.upper(); rep["wrong_annotator"] = int(bad.sum()); ret = ret[~bad]
    dup = ret.duplicated("item_id", keep="last"); rep["duplicate"] = int(dup.sum()); ret = ret[~dup]    # later export of the same item wins
    inc = (ret[qcols] == "").any(axis=1); rep["incomplete"] = int(inc.sum()); ret = ret[~inc]
    return ret, rep


VALID = {"pick1": {"yes", "none"}, "pick2": {"1", "2", "none"}, "pick3": {"1", "2", "3", "none"}, "send": {"as_is", "small_edit", "no"},
         "hard": {"1", "2", "3", "4", "5"}, "ver": {"meant", "other", "else"}, "acc": {"yes", "small_edit", "no"}}


def check_options(ret, cols, rep):
    if ret.empty:
        return ret
    ok = pd.Series(True, index=ret.index)
    for c in cols:
        if c in ret:
            filled = ret[c] != ""
            ok &= ~filled | ret[c].isin(VALID[c])
    rep["invalid_option"] = int((~ok).sum())
    return ret[ok]


def lev(a, b):
    a, b = a.lower().split(), b.lower().split(); d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (x != y))
    return d[-1]


# ------------------------------------------------------------------ endpoints
def set_view(sv: pd.DataFrame, key: pd.DataFrame) -> pd.DataFrame:
    """One row per set-view item: H-direct endpoints for the assigned (cond, arm)."""
    k = key[key.kind == "sv"].set_index("item_id")
    if sv.empty:
        return pd.DataFrame()
    rows = []
    for _, r in sv.iterrows():
        m = k.loc[r["item_id"]]
        n = int(m["n_shown"]); pick = next((r[c] for c in ("pick1", "pick2", "pick3") if c in r and r[c] != ""), "")
        picked = pick != "none" and pick != ""
        pos = (1 if pick == "yes" else int(pick)) if picked else None
        send = r["send"]
        rows.append(dict(cv_item=m["cv_item"], writer=m["annotator"], dimension=m["dimension"], cond=m["cond"], arm=m["arm"], k=int(m["k"]), n_shown=n,
                         picked=int(picked), pos=pos, send=send, direct_cov=int(picked and send in OKACC), direct_strict=int(picked and send == "as_is"),
                         inconsistent=int((not picked) and send != "no"), hard=int(r["hard"]), time_ms=float(r["time_ms"] or 0)))
    return pd.DataFrame(rows)


def pool_table(pl: pd.DataFrame, key: pd.DataFrame) -> pd.DataFrame:
    k = key[key.kind == "pool"].copy()
    if pl.empty:
        m = k.assign(ver="", acc="", note="")
    else:
        m = k.merge(pl[["item_id", "ver", "acc", "note"]], on="item_id", how="left").fillna({"ver": "", "acc": "", "note": ""})
    m["rated"] = (m["ver"] != "") & (m["acc"] != "")
    m["h_match"] = (m["ver"] == "meant").astype(int)
    m["h_cov"] = ((m["ver"] == "meant") & m["acc"].isin(OKACC)).astype(int)
    m["h_strict"] = ((m["ver"] == "meant") & (m["acc"] == "yes")).astype(int)
    return m


def item_arm(pool: pd.DataFrame) -> pd.DataFrame:
    """One row per (item, arm) with arm in ARMS + D3pU (unfiltered D3p, chip only), from the pool ratings."""
    rec = []
    for (cv, ), g in pool.groupby(["cv_item"]):
        meta = g.iloc[0]
        for a in ARMS + ["D3pU"]:
            if a == "D3pU" and meta["cond"] != "chip":
                continue
            ds = []
            for _, r in g.iterrows():
                for tag in str(r["pool_arms"]).split():
                    nm, pos = tag.split(":")
                    if nm == a:
                        ds.append((int(pos), r))
            if not ds:
                continue
            ds.sort(key=lambda x: x[0]); n = len(ds)
            def end(col):
                hit = [p for p, r in ds if r["rated"] and r[col] == 1]
                if hit:
                    return 1, min(hit)
                return (0 if all(r["rated"] for _, r in ds) else np.nan), n
            hc, fp = end("h_cov"); hm, _ = end("h_match"); hs, _ = end("h_strict")
            first = ds[0][1]
            rec.append(dict(cv_item=cv, writer=meta["annotator"], dimension=meta["dimension"], cond=meta["cond"], arm=a, n_shown=n,
                            h_cov=hc, h_match=hm, h_strict=hs, first_pos=fp, censored=int(hc != 1),
                            wrong_first=(int(first["ver"] == "other") if first["rated"] else np.nan),
                            min_lev=min(lev(r["text"], r["r"]) for _, r in ds), r_words=len(str(meta["r"]).split()),
                            proxy_cov=int(any(r["proxy_intended"] == 1 or str(r["proxy_intended"]) == "1" for _, r in ds)),
                            cell_assigned=meta["cell"]))
    return pd.DataFrame(rec)


def cost(df: pd.DataFrame, r=0.5, e=1.0, fallback=True) -> pd.Series:
    """PLAN section 5: c[cue] + r x drafts read (to first usable, else all) + s[k>1] + a + fallback if nothing usable.
    Keyword taps are identical across arms and left out."""
    c = (df["cond"] == "chip").astype(float)
    reads = df["first_pos"].astype(float)
    s = (df["n_shown"] > 1).astype(float)
    fb = np.minimum(df["r_words"], e * df["min_lev"]) * (df["h_cov"] != 1) if fallback else 0.0
    return c + r * reads + s + 1.0 + fb


# ------------------------------------------------------------------ inference
def cluster_boot(vals: dict, B: int, seed=SEED):
    """vals: writer -> 1-d array of per-item values (paired differences or indicators). Mean with writer-cluster CI."""
    ws = sorted(vals); rng = np.random.default_rng(seed); W = len(ws)
    tot = sum(len(vals[w]) for w in ws)
    est = sum(float(np.sum(vals[w])) for w in ws) / tot
    out = np.empty(B)
    for b in range(B):
        s = n = 0.0
        for w in rng.integers(0, W, W):
            v = vals[ws[w]]
            if len(v):
                s += v[rng.integers(0, len(v), len(v))].sum(); n += len(v)
        out[b] = s / n if n else np.nan
    return est, float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))


def cluster_boot2(va: dict, vb: dict, B: int, seed=SEED):
    """difference of means of two item sets on (partly) different items; writers resampled together."""
    ws = sorted(set(va) | set(vb)); rng = np.random.default_rng(seed); W = len(ws)
    mean = lambda d: sum(float(np.sum(d[w])) for w in d) / max(1, sum(len(d[w]) for w in d))  # noqa: E731
    est = mean(va) - mean(vb); out = np.empty(B)
    for b in range(B):
        sa = na = sb = nb = 0.0
        for w in rng.integers(0, W, W):
            for d, which in ((va, 0), (vb, 1)):
                v = d.get(ws[w], np.array([]))
                if len(v):
                    t = v[rng.integers(0, len(v), len(v))].sum()
                    if which == 0:
                        sa += t; na += len(v)
                    else:
                        sb += t; nb += len(v)
        out[b] = (sa / na if na else np.nan) - (sb / nb if nb else np.nan)
    return est, float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))


def signflip_p(wsums: np.ndarray, n_total: float, R=20000, seed=SEED):
    rng = np.random.default_rng(seed); obs = abs(wsums.sum()) / n_total
    sg = rng.choice([-1.0, 1.0], size=(R, len(wsums)))
    return float((1 + np.sum(np.abs(sg @ wsums) / n_total >= obs - 1e-12)) / (R + 1))


def holm(ps: dict) -> dict:
    order = sorted(ps, key=lambda k: ps[k]); m = len(order); out = {}; run = 0.0
    for i, k in enumerate(order):
        run = max(run, (m - i) * ps[k]); out[k] = min(1.0, run)
    return out


def by_writer(df, col):
    return {w: g[col].to_numpy(float) for w, g in df.groupby("writer")}


def paired(ia, a, b, cond, col="h_cov"):
    x = ia[(ia.cond == cond) & (ia.arm == a)].set_index("cv_item")[col]; y = ia[(ia.cond == cond) & (ia.arm == b)].set_index("cv_item")[col]
    d = (x - y).dropna(); wr = ia.drop_duplicates("cv_item").set_index("cv_item")["writer"].reindex(d.index)
    return {w: d[wr == w].to_numpy(float) for w in sorted(set(wr))}


def judge_status(kind, est, lo, hi, thr=10.0, margin=-5.0):
    """gain (S1, S3): pass = point >= +10 pp and CI lower bound > 0; fail = CI upper bound < +10 pp; else unresolved.
    noninf (S2): pass = CI lower bound > -5 pp; fail = CI upper bound < -5 pp; else unresolved."""
    if kind == "gain":
        return "pass" if (est >= thr / 100 and lo > 0) else ("fail" if hi < thr / 100 else "unresolved")
    return "pass" if lo > margin / 100 else ("fail" if hi < margin / 100 else "unresolved")


# ------------------------------------------------------------------ the analysis
def analyse(key, sv, pl, B, out: Path | None):
    SV = set_view(sv, key); P = pool_table(pl, key); IA = item_arm(P) if len(P) else pd.DataFrame()
    res = {"n_set_view_items": int(len(SV)), "n_pool_ratings": int(P["rated"].sum()), "n_pool_drafts": int(len(P))}
    # per arm x condition
    rows = []
    for cond in ("bare", "chip"):
        for a in ARMS + (["D3pU"] if cond == "chip" else []):
            g = IA[(IA.cond == cond) & (IA.arm == a)] if len(IA) else pd.DataFrame()
            if g.empty:
                continue
            row = dict(cond=cond, arm=a, n_items=int(len(g)), mean_shown=float(g.n_shown.mean()))
            for col in ("h_cov", "h_match", "h_strict"):
                v = g.dropna(subset=[col]); est, lo, hi = cluster_boot(by_writer(v, col), B) if len(v) else (np.nan,) * 3
                row.update({col: est, col + "_lo": lo, col + "_hi": hi, col + "_n": int(len(v))})
            cv = g[g.h_cov == 1]
            row.update(median_first_pos_covered=float(cv.first_pos.median()) if len(cv) else np.nan, wrong_first=float(g.wrong_first.mean()),
                       proxy_cov=float(g.proxy_cov.mean()))
            for r in RS:
                row[f"cost_per_covered_r{r}"] = float(cost(g, r).sum() / max(1, (g.h_cov == 1).sum()))
                row[f"cost_per_covered_nofb_r{r}"] = float(cost(g, r, fallback=False).sum() / max(1, (g.h_cov == 1).sum()))
            d = SV[(SV.cond == cond) & (SV.arm == a)] if len(SV) and a in ARMS else pd.DataFrame()
            if len(d):
                row.update(direct_n=int(len(d)), direct_match=float(d.picked.mean()), direct_cov=float(d.direct_cov.mean()),
                           direct_strict=float(d.direct_strict.mean()), burden_mean=float(d.hard.mean()), read_time_median_s=float(d.time_ms.median() / 1000))
            rows.append(row)
    ARM = pd.DataFrame(rows)
    # direct vs pool for the assigned arm
    dv = []
    if len(SV) and len(IA):
        m = SV.merge(IA[["cv_item", "arm", "h_cov", "h_match"]], on=["cv_item", "arm"], how="left")
        for (cond, a), g in m.groupby(["cond", "arm"]):
            gg = g.dropna(subset=["h_cov"])
            dv.append(dict(cond=cond, arm=a, n=int(len(gg)), direct_match=float(gg.picked.mean()), pool_match=float(gg.h_match.mean()),
                           direct_cov=float(gg.direct_cov.mean()), pool_cov=float(gg.h_cov.mean()),
                           agree_cov=float((gg.direct_cov == gg.h_cov).mean()), agree_match=float((gg.picked == gg.h_match).mean()),
                           inconsistent_none_but_send=int(g.inconsistent.sum())))
    DV = pd.DataFrame(dv)
    # contrasts (declared list; Holm over the five primary ones)
    CON = []
    def add(name, kind, a, b, ca, cb, primary, thr):
        if IA.empty:
            return
        if ca == cb:
            v = paired(IA, a, b, ca); est, lo, hi = cluster_boot(v, B)
            n_tot = sum(len(x) for x in v.values()); p = signflip_p(np.array([x.sum() for x in v.values()]), n_tot) if n_tot else np.nan; n = n_tot
        else:   # arms on different items (bare vs chip): unpaired difference, writer-cluster CI
            va = by_writer(IA[(IA.cond == ca) & (IA.arm == a)].dropna(subset=["h_cov"]), "h_cov"); vb = by_writer(IA[(IA.cond == cb) & (IA.arm == b)].dropna(subset=["h_cov"]), "h_cov")
            est, lo, hi = cluster_boot2(va, vb, B); n = min(sum(map(len, va.values())), sum(map(len, vb.values())))
            ws = sorted(set(va) & set(vb)); wd = np.array([va[w].mean() - vb[w].mean() for w in ws]); p = signflip_p(wd, len(ws)) if len(ws) else np.nan
        CON.append(dict(name=name, kind=kind, arm_a=f"{a}|{ca}", arm_b=f"{b}|{cb}", n=n, diff_pp=100 * est, lo_pp=100 * lo, hi_pp=100 * hi, p_signflip=p, primary=primary,
                        status=judge_status(kind, est, lo, hi) if primary else "exploratory"))
    for a in ("C3", "E3"):
        add(f"S1_{a}-D3p_bare", "gain", a, "D3p", "bare", "bare", True, 10)
        add(f"S2_{a}_bare_vs_G1_chip", "noninf", a, "G1", "bare", "chip", True, -5)
    add("S3_E3-G1_chip", "gain", "E3", "G1", "chip", "chip", True, 10)
    add("S3x_C3-G1_chip", "gain", "C3", "G1", "chip", "chip", False, 10)
    add("S3x_D3p-G1_chip", "gain", "D3p", "G1", "chip", "chip", False, 10)
    add("cue_tap_G1chip-G1bare", "gain", "G1", "G1", "chip", "bare", False, 10)
    add("D3pU-D3p_chip(filter effect)", "gain", "D3pU", "D3p", "chip", "chip", False, 10)
    C = pd.DataFrame(CON)
    if len(C):
        prim = {r["name"]: r["p_signflip"] for _, r in C[C.primary].iterrows() if pd.notna(r["p_signflip"])}
        h = holm(prim); C["p_holm"] = C["name"].map(h)
        # S2 also needs cost at r = 0.5 not higher than G1 chip
        for i, r in C.iterrows():
            if r["name"].startswith("S2_") and r["status"] == "pass":
                a = r["arm_a"].split("|")[0]
                ca = ARM[(ARM.arm == a) & (ARM.cond == "bare")]; cb = ARM[(ARM.arm == "G1") & (ARM.cond == "chip")]
                if len(ca) and len(cb) and ca.iloc[0]["cost_per_covered_r0.5"] > cb.iloc[0]["cost_per_covered_r0.5"]:
                    C.at[i, "status"] = "equal coverage at higher cost (r=0.5)"
    # S4 criteria
    s4 = {}
    if len(ARM):
        for a in ("C3", "E3"):
            g = IA[(IA.cond == "bare") & (IA.arm == a) & (IA.h_cov == 1)]
            s4[f"median_drafts_to_first_usable_{a}_bare"] = float(g.first_pos.median()) if len(g) else None
            g = IA[(IA.cond == "chip") & (IA.arm == a) & (IA.h_cov == 1)]
            s4[f"median_drafts_to_first_usable_{a}_chip"] = float(g.first_pos.median()) if len(g) else None
        if len(SV):
            for a in ("C3", "E3"):
                x = by_writer(SV[SV.arm == a].assign(v=lambda d: d.hard), "v"); y = by_writer(SV[SV.arm == "G1"].assign(v=lambda d: d.hard), "v")
                est, lo, hi = cluster_boot2(x, y, B); s4[f"burden_{a}_minus_G1"] = dict(diff=est, lo=lo, hi=hi, rule="mean difference <= 0.5 and CI upper < 1.0")
    # proxy concordance (draft level)
    conc = {}
    pr = P[P.rated & (P.proxy_intended.astype(str) != "")]
    if len(pr):
        for lab in ("h_match", "h_cov"):
            x = pr.proxy_intended.astype(int).to_numpy(); y = pr[lab].to_numpy()
            conc[lab] = dict(n=int(len(pr)), kappa=kappa(x, y), auroc=auroc(x, y), human_rate=float(y.mean()), proxy_rate=float(x.mean()))
        pr = pr.assign(origin=pr.pool_arms.str.split().str[0].str.split(":").str[0])
        conc["by_origin_kappa_match"] = {o: kappa(g.proxy_intended.astype(int).to_numpy(), g.h_match.to_numpy()) for o, g in pr.groupby("origin") if len(g) >= 10}
        if len(ARM):
            a = ARM.dropna(subset=["h_cov"]); conc["arm_spearman_proxy_vs_human"] = spearman(a["proxy_cov"].to_numpy(), a["h_cov"].to_numpy())
    # free text to code
    ft = P[(P["acc"] == "no") & (P["note"].str.strip() != "")][["cv_item", "annotator", "cond", "text", "ver", "note"]] if len(P) else pd.DataFrame()
    res.update(dict(arm_table_rows=len(ARM), contrasts=len(C), S4=s4, concordance=conc,
                    inconsistent_set_answers=int(SV.inconsistent.sum()) if len(SV) else 0,
                    short_sets=int((SV.n_shown < SV.k).sum()) if len(SV) else 0))
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        ARM.to_csv(out / "by_arm.csv", index=False); C.to_csv(out / "contrasts.csv", index=False); DV.to_csv(out / "direct_vs_pool.csv", index=False)
        ft.to_csv(out / "free_text_to_code.csv", index=False)
        (out / "concordance.json").write_text(json.dumps(conc, indent=1)); (out / "summary.json").write_text(json.dumps(res, indent=1, default=float))
    return dict(SV=SV, P=P, IA=IA, ARM=ARM, DV=DV, C=C, res=res)


def kappa(x, y):
    x, y = np.asarray(x, int), np.asarray(y, int); po = (x == y).mean()
    pe = x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean())
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def auroc(score, y):
    s, y = np.asarray(score, float), np.asarray(y, int)
    pos, neg = s[y == 1], s[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg]))


def spearman(a, b):
    if len(a) < 3:
        return float("nan")
    ra, rb = pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


# ------------------------------------------------------------------ run on real returns
def load_key(path=KEY) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def run(sv_dir, pool_dir, out, B, key_path=KEY):
    key = load_key(key_path)
    sv, r1 = qc(read_returns(sv_dir, "part26"), key, "sv", ["send", "hard"]); pl, r2 = qc(read_returns(pool_dir, "part27"), key, "pool", ["ver", "acc"])
    # the set question column depends on the set size: require one of pick1/2/3
    if len(sv):
        sv = sv[(sv[[c for c in ("pick1", "pick2", "pick3") if c in sv]] != "").any(axis=1)]
    sv = check_options(sv, ["pick1", "pick2", "pick3", "send", "hard"], r1); pl = check_options(pl, ["ver", "acc"], r2)
    out.mkdir(parents=True, exist_ok=True)
    (out / "qc.json").write_text(json.dumps({"part26": r1, "part27": r2}, indent=1))
    a = analyse(key, sv, pl, B, out)
    print(json.dumps({"qc": {"part26": r1, "part27": r2}, **a["res"]}, indent=1, default=float))
    return a


# ------------------------------------------------------------------ self-check
def synthetic(key: pd.DataFrame, seed=7, drop=0.0):
    """Planted writers: draft truth = proxy_intended or a fixed hash bit; ver/acc derived from it; set answers derived from the SAME
    truth, so H-direct must equal the pool-derived value for every assigned arm. Returns (sv_df, pool_df, truth dict)."""
    import hashlib
    rng = np.random.default_rng(seed)
    def bit(s, p):
        return int(hashlib.sha1(s.encode()).hexdigest(), 16) % 1000 < p * 1000
    pool = key[key.kind == "pool"]; truth = {}
    prow = []
    for _, r in pool.iterrows():
        meant = r["proxy_intended"] == "1" or bit("m|" + r["item_id"], 0.12)
        other = (not meant) and (r["proxy_other"] == "1" or bit("o|" + r["item_id"], 0.1))
        acc = ("yes" if bit("a|" + r["item_id"], 0.15) else "small_edit") if meant else "no"
        truth[(r["cv_item"], r["text"])] = dict(ver="meant" if meant else ("other" if other else "else"), acc=acc)
        if drop and rng.random() < drop:
            continue
        prow.append(dict(item_id=r["item_id"], annotator=r["annotator"], check_id="part27", practice="0", order="1", ver=truth[(r["cv_item"], r["text"])]["ver"],
                         acc=acc, note="wrong tense" if acc == "no" and bit("n|" + r["item_id"], .3) else "", time_ms="5000"))
    srow = []
    for _, r in key[key.kind == "sv"].iterrows():
        texts = json.loads(r["set_texts"]); n = len(texts)
        hit = [i for i, t in enumerate(texts, 1) if truth[(r["cv_item"], t)]["ver"] == "meant" and truth[(r["cv_item"], t)]["acc"] in OKACC]
        near = [i for i, t in enumerate(texts, 1) if truth[(r["cv_item"], t)]["ver"] == "meant"]
        pick = (hit or near or [None])[0]
        ans = {"pick1": "", "pick2": "", "pick3": ""}
        ans[f"pick{n}"] = ("yes" if n == 1 else str(pick)) if pick else "none"
        srow.append(dict(item_id=r["item_id"], annotator=r["annotator"], check_id="part26", practice="0", order="1", **ans,
                         send=truth[(r["cv_item"], texts[pick - 1])]["acc"] if pick else "no", hard=str(1 + int(rng.integers(0, 5))), note="", time_ms=str(30000 + int(rng.integers(0, 20000)))))
    return pd.DataFrame(srow), pd.DataFrame(prow), truth


def self_check(B=200):
    key = load_key()
    scratch = ROOT / "tmp" / "s6_selfcheck"; shutil.rmtree(scratch, ignore_errors=True); scratch.mkdir(parents=True)
    fails = []
    def ok(c, m):
        print(("ok   " if c else "FAIL ") + m)
        if not c:
            fails.append(m)
    try:
        # key and package invariants
        sv, pool = key[key.kind == "sv"], key[key.kind == "pool"]
        ok(len(sv) == 200 and sv.annotator.nunique() == 20 and (sv.groupby("annotator").size() == 10).all(), "key: 200 set-view items, 10 per writer, 20 writers")
        ok(sv.groupby("cell").size().eq(25).all() and sv.cell.nunique() == 8, "key: 8 cells x 25 sets")
        ok((sv.groupby(["annotator", "cond"]).size() == 5).all(), "key: 5 bare + 5 chip per writer")
        ok(sv.apply(lambda r: len(json.loads(r["set_texts"])) == int(r["n_shown"]), axis=1).all(), "key: n_shown matches the stored set")
        full = sv[sv.k.astype(int) == 3]
        ok((full.n_shown.astype(int) == 3).mean() >= 0.97, f"key: k=3 sets are exactly 3 drafts for {(full.n_shown.astype(int) == 3).mean():.3f} of sets (rest flagged short)")
        ok(pool.item_id.is_unique and sv.item_id.is_unique, "key: opaque ids unique")
        ok(all(((pool.cv_item == r.cv_item) & (pool.text == t)).any() for r in sv.itertuples() for t in json.loads(r.set_texts)), "key: every shown draft is in its item's pool")
        ok((pool.groupby("cv_item").cond.nunique() == 1).all(), "key: one condition per item pool")
        # blind package files, if built
        pk = ROOT / "annotation_package" / "stage6"
        if pk.exists():
            import re
            bad = re.compile(r'"(arm|cell|cond|condition|dimension|stratum|key|proxy)\w*"\s*:|\b(G1|D3p|C3|E3)\b', re.I)
            files = sorted(pk.glob("P*_part2[67].json"))
            ok(len(files) == 40, f"package: 40 part files ({len(files)})")
            ok(not any(bad.search(f.read_text()) for f in files), "package: no arm, cell or condition fields or labels in any file")
        # synthetic returns: pipeline recovers planted endpoints
        s_sv, s_pl, truth = synthetic(key)
        for part, df in (("part26", s_sv), ("part27", s_pl)):
            d = scratch / f"ret_{part}"; d.mkdir()
            for w, g in df.groupby("annotator"):
                g2 = g.copy(); g2.insert(2, "practice_row", "")  # extra column is ignored
                g2.drop(columns="practice_row").to_csv(d / f"labels_{part}_{w}.csv", index=False)
        out = scratch / "out"
        a = run(scratch / "ret_part26", scratch / "ret_part27", out, B)
        IA, SV = a["IA"], a["SV"]
        # brute-force expected H-cov for every arm-item from the planted truth
        bad = 0; n = 0
        for _, r in IA.iterrows():
            rows = pool[(pool.cv_item == r.cv_item)]
            ds = [(int(t.split(":")[1]), x) for x in rows.itertuples() for t in x.pool_arms.split() if t.split(":")[0] == r.arm]
            exp = int(any(truth[(r.cv_item, x.text)]["ver"] == "meant" and truth[(r.cv_item, x.text)]["acc"] in OKACC for _, x in ds))
            n += 1; bad += int(exp != r.h_cov)
        ok(n == 200 * 4 + 100 and bad == 0, f"scoring: H-cov equals the planted truth for all {n} arm-item pairs")
        dv = a["DV"]
        ok(len(dv) == 8 and (dv.agree_cov == 1).all() and (dv.agree_match == 1).all(), "scoring: set-view answers equal pool-derived values when writers are consistent (H-direct check)")
        ok(a["res"]["inconsistent_set_answers"] == 0, "scoring: no inconsistent set answers in consistent writers")
        ok(set(a["C"][a["C"].primary].name) == {"S1_C3-D3p_bare", "S1_E3-D3p_bare", "S2_C3_bare_vs_G1_chip", "S2_E3_bare_vs_G1_chip", "S3_E3-G1_chip"}, "scoring: five declared primary contrasts")
        ok(a["C"].p_holm.dropna().between(0, 1).all(), "scoring: Holm p-values in [0, 1]")
        g1 = a["ARM"][(a["ARM"].arm == "G1")]
        ok((g1.mean_shown == 1).all(), "scoring: G1 shows one draft")
        # a G1 draft is in every set at position 1, so wrong-first is identical across arms (a check, not a result)
        wf = a["ARM"].groupby("cond").wrong_first.nunique()
        ok(a["ARM"][a["ARM"].arm.isin(ARMS)].groupby("cond").wrong_first.nunique().max() <= 3, "scoring: wrong-first reported per arm")
        # missing ratings: undefined, not zero
        s2_sv, s2_pl, _ = synthetic(key, drop=0.2)
        d = scratch / "miss"; (d / "a").mkdir(parents=True); (d / "b").mkdir(parents=True)
        for w, g in s2_pl.groupby("annotator"):
            g.to_csv(d / "b" / f"labels_part27_{w}.csv", index=False)
        for w, g in s2_sv.groupby("annotator"):
            g.to_csv(d / "a" / f"labels_part26_{w}.csv", index=False)
        a2 = run(d / "a", d / "b", d / "o", B)
        ok(a2["IA"].h_cov.isna().any() and (a2["IA"].h_cov.dropna().isin([0, 1])).all(), "scoring: unrated drafts leave undefined endpoints, nothing imputed")
        # QC: practice rows, duplicates, another person's id, unknown item
        x = s_pl.copy(); x = pd.concat([x, x.iloc[:3], x.iloc[:2].assign(practice="1"), x.iloc[:1].assign(item_id="pd-zzzzzzzz")])
        x.loc[x.index[-1:], "annotator"] = "P01"
        y, rep = qc(x, key, "pool", ["ver", "acc"])
        ok(rep["practice_dropped"] == 2 and rep["unknown_item"] == 1 and rep["duplicate"] == 3 and len(y) == len(s_pl), f"qc: practice, unknown ids and duplicates handled {rep}")
        # inconsistent: picked none but send != no
        bad_sv = s_sv.copy(); i = bad_sv.index[bad_sv.send == "no"][0]; bad_sv.at[i, "send"] = "as_is"
        ok(set_view(bad_sv, key).inconsistent.sum() == 1, "scoring: 'none' with a send answer is flagged")
        ok(abs(auroc([1, 1, 0, 0], [1, 1, 0, 0]) - 1) < 1e-9 and abs(kappa([1, 0, 1, 0], [1, 0, 1, 0]) - 1) < 1e-9, "stats: auroc and kappa on a perfect case")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print("SELF-CHECK", "PASSED" if not fails else f"FAILED ({len(fails)})")
    return 0 if not fails else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--sv", default=str(ROOT / "annotation" / "returns_part26"))
    ap.add_argument("--pool", default=str(ROOT / "annotation" / "returns_part27"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "coverage_human"))
    ap.add_argument("--B", type=int, default=10000)
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    run(Path(a.sv), Path(a.pool), Path(a.out), a.B)
    return 0


if __name__ == "__main__":
    sys.exit(main())

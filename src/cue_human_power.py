"""Problem #6 power simulation for the human-label validation of the hw12 speech-act cue gain (P1). Frozen in analysis/cue_human/PLAN.md.
Uses ONLY machine labels and the declared allocation; no human data exist. Writes analysis/cue_human/power.json. Run: python src/cue_human_power.py"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A, analyze_hw1 as H

N_PAIRS, FLOOR, SEED = 120, 4, 20261118

def population():
    items = {}
    for p in ["data/items/hw.jsonl", "data/items/hw2.jsonl"]: items.update(A.load_items(str(ROOT / p)))
    raw = pd.concat([pd.read_parquet(ROOT / f"runs/{r}/scored.parquet") for r in ("hw1", "hw2")], ignore_index=True)
    d, _ = H.build(items, raw)
    p = d[d.prompt_id.eq("P0") & d.dimension.eq("speech_act") & d.channel.isin(["chip1", "noncrit"])]
    a = p.pivot(index=["family_id", "writer_id", "variant", "model"], columns="channel", values="critical_match").reset_index()
    a["m_chip1"] = a.chip1.astype(int); a["m_non"] = a.noncrit.astype(int); a["Dm"] = a.m_chip1 - a.m_non
    a["pattern"] = a.m_chip1.astype(str) + a.m_non.astype(str)      # chip1 match, noncrit match
    a["stratum"] = a.model + "|" + a.pattern
    return a.drop(columns=["chip1", "noncrit"])

def allocate(pop, n=N_PAIRS, floor=FLOOR):
    """floor of min(N_h, FLOOR) per stratum, remainder proportional to N_h (largest remainder, ties by stratum name)."""
    N = pop.stratum.value_counts().sort_index()
    base = N.clip(upper=floor); rest = n - base.sum()
    room = N - base; share = room / room.sum() * rest
    add = np.floor(share).astype(int).clip(upper=room); left = int(rest - add.sum())
    for s in (share - add).sort_values(ascending=False, kind="stable").index:
        if left <= 0: break
        if add[s] < room[s]: add[s] += 1; left -= 1
    return (base + add).astype(int)

def draw(pop, alloc, rng):
    idx = []
    for s, k in alloc.items():
        idx += list(rng.choice(pop.index[pop.stratum == s], size=k, replace=False))
    return pop.loc[sorted(idx)].assign(pi=lambda x: x.stratum.map(alloc) / x.stratum.map(pop.stratum.value_counts()))

def ppi(pop, S, Dh):
    """Horvitz-Thompson PPI, lambda = 1; writer-clustered CR1 / t(G-1). Dh is indexed like S."""
    N = len(pop); psi = pop.Dm.astype(float).copy()
    corr = ((Dh - S.Dm) / S.pi)
    psi.loc[S.index] += corr
    th = psi.sum() / N; e = (psi - th).groupby(pop.writer_id).sum(); G = len(e)
    se = np.sqrt(G / (G - 1) * (e ** 2).sum()) / N
    rect = corr.sum() / N
    # rectifier SE (cluster): only sampled units carry it
    r = pd.Series(0.0, index=pop.index); r.loc[S.index] = corr; r = r - 0  # centred below
    er = (r - rect).groupby(pop.writer_id).sum(); ser = np.sqrt(G / (G - 1) * (er ** 2).sum()) / N
    q = stats.t.ppf(.975, G - 1)
    return th, se, th - q * se, th + q * se, rect, ser, q

def simulate(pop, alloc, nsim=2000, e_chip=.05, e_non=.05, bias_chip=0., bias_non=0., seed=SEED):
    """Human match indicator = machine indicator flipped with prob e (symmetric noise) plus differential over-credit:
    bias_chip = P(machine says match, human says no match) extra for chip1; bias_non likewise for noncrit."""
    rng = np.random.default_rng(seed); out = []
    for _ in range(nsim):
        S = draw(pop, alloc, rng)
        def hum(m, e, b):
            flip = rng.random(len(S)) < e; y = np.where(flip, 1 - m, m)
            drop = (m == 1) & (rng.random(len(S)) < b); return np.where(drop, 0, y)
        hc, hn = hum(S.m_chip1.values, e_chip, bias_chip), hum(S.m_non.values, e_non, bias_non)
        Dh = pd.Series(hc - hn, index=S.index)
        th, se, lo, hi, rect, ser, q = ppi(pop, S, Dh)
        out.append((th, se, lo, hi, rect, ser, abs(rect) / ser > q))
    o = np.array(out); q90 = stats.t.ppf(.95, 9)
    return dict(mean_ppi_pp=100 * o[:, 0].mean(), mean_se_pp=100 * o[:, 1].mean(), ci_halfwidth_pp=100 * q * o[:, 1].mean(),
                p_lower_gt0=float((o[:, 2] > 0).mean()), p_rect_detected=float(o[:, 6].mean()),
                p_equiv10=float(((o[:, 4] - q90 * o[:, 5] > -.10) & (o[:, 4] + q90 * o[:, 5] < .10)).mean()), mean_rect_pp=100 * o[:, 4].mean(), mean_rect_se_pp=100 * o[:, 5].mean())

if __name__ == "__main__":
    pop = population(); alloc = allocate(pop)
    res = {"N_pairs": len(pop), "N_writers": int(pop.writer_id.nunique()), "machine_P1_pp": 100 * pop.Dm.mean(), "alloc": alloc.to_dict(),
           "strata_N": pop.stratum.value_counts().sort_index().to_dict(), "scenarios": {}}
    for name, kw in {"noise5": dict(e_chip=.05, e_non=.05), "noise10": dict(e_chip=.10, e_non=.10),
                     "noise15": dict(e_chip=.15, e_non=.15),
                     "chip1_overcredited10": dict(e_chip=.03, e_non=.03, bias_chip=.12),
                     "chip1_overcredited20": dict(e_chip=.03, e_non=.03, bias_chip=.24)}.items():
        res["scenarios"][name] = simulate(pop, alloc, **kw)
    (ROOT / "analysis/cue_human/power.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))

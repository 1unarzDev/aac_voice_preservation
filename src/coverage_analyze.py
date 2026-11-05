"""Machine coverage proxy per method (PLAN sections 2, 3, 5, 5b, 7). Reads analysis/coverage/{items_draw.json, drafts_main.jsonl,
selector_main.jsonl, proxy_validity.json}; writes coverage_by_arm.csv, contrasts.csv, frontier.csv, selector_recall.csv, summary.json.
The proxy gate failed (proxy_validity.json), so every number here is descriptive; machine-only arm claims are not made."""
from __future__ import annotations
import json, sys, itertools
from collections import defaultdict
import numpy as np, pandas as pd
import coverage_lib as L
SEED = 20261117; B = 10000
K = {"G1": 1, "W1": 1, "D3s": 3, "D5s": 5, "D3p": 3, "D5p": 5, "C3": 3, "C5": 5, "C3o": 3, "E3": 3, "E5": 5, "R3": 3, "C3f": 3}
ARMS = list(K)

def lev(a, b):
    a, b = a.lower().split(), b.lower().split(); d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (x != y))
    return d[-1]

def jacc(a, b):
    a, b = set(L.norm(a).split()), set(L.norm(b).split()); return len(a & b) / len(a | b) if a | b else 1.0

def load(which="main", drafts_file=None):
    doc = json.load(open(L.OUT / "items_draw.json")); items = {x["item_id"]: x for x in doc["items"]}
    J = {}
    for l in open(L.OUT / (drafts_file or f"drafts_{which}.jsonl")):
        o = json.loads(l); J[(o["item_id"], o["text"])] = o
    S = {}
    for l in open(L.OUT / f"selector_{which}.jsonl"):
        o = json.loads(l); S[o["item_id"]] = o
    return items, J, S

def pairj(j):
    return j.get("") or next(iter(j.values()))

def build_sets(items, J, S):
    """returns rows: one per (item, cond, arm): list of draft texts (deployed order) + diagnostics."""
    rows, diag = [], []
    for iid, s in S.items():
        it = items[iid]; pdim = it["dimension"]
        for cond in ("bare", "chip"):
            c = s[cond]; g = c["g1"]; seen_norm = {L.norm(g)}
            def get(t): return J.get((iid, t))
            def edit_slot(d):
                """first valid of attempt 0 / regen; returns (text or None, attempts, raw_violation)"""
                res = None; att = 0; viol0 = None
                for key in (d, d + "|regen"):
                    o = c["edits"].get(key)
                    if o is None: continue
                    att += 1
                    t = L.clean_sentence(o["sentence"]); v = get(t)
                    if v is None: continue
                    j = v["judge"]; pj = pairj(j)
                    val = pj["value"] if d == pdim else (j.get(d) or {}).get("extra_value")
                    viol = cond == "chip" and pj["value"] != it["intended_value"]
                    if key == d: viol0 = viol
                    if val == o["new_value"] and o["new_value"] != o.get("current_value") and not viol and L.norm(t) != L.norm(g):
                        return t, att, viol0
                return None, att, viol0
            es = {}
            for d in set(c["sel"][:4] + c["static"][:2] + c["rnd"][:2]) :
                es[d] = edit_slot(d)
            def dimslots(order, n):
                out = []
                for d in order[:n]:
                    t, att, _ = es[d]; out.append(t)
                return out
            def dedupe(first, rest):
                out = [first]; sn = {L.norm(first)}
                for t in rest:
                    if t and L.norm(t) not in sn: sn.add(L.norm(t)); out.append(t)
                return out
            arms = {"G1": [g]}
            arms["D3s"] = dedupe(g, c["smp"][:2] if len(c["smp"]) >= 2 else c["smp"]); arms["D5s"] = dedupe(g, c["smp"][:4])
            arms["D3p"] = dedupe(g, c["div2"]); arms["D5p"] = dedupe(g, c["div4"])
            arms["C3"] = dedupe(g, dimslots(c["sel"], 2)); arms["C5"] = dedupe(g, dimslots(c["sel"], 4))
            ev = [t for t in c["event"]]
            if cond == "chip":   # cue-violating event drafts dropped (hard filter)
                ev = [t for t in ev if (get(t) and pairj(get(t)["judge"])["value"] == it["intended_value"])]
            arms["E3"] = dedupe(g, dimslots(c["sel"], 1) + ev[:1]); arms["E5"] = dedupe(g, dimslots(c["sel"], 2) + ev[:2])
            arms["R3"] = dedupe(g, dimslots(c["rnd"], 2)); arms["C3f"] = dedupe(g, dimslots(c["static"], 2))
            if cond == "bare" and c.get("oracle"):
                orc = []
                for o in c["oracle"]:
                    if not o: orc.append(None); continue
                    t = L.clean_sentence(o["sentence"]); v = get(t)
                    ok = bool(v) and pairj(v["judge"])["value"] == o["new_value"] != o.get("current_value")
                    orc.append(t if ok else None)
                arms["C3o"] = dedupe(g, orc)
            for a, ts in arms.items(): rows.append(dict(item_id=iid, cond=cond, arm=a, texts=ts))
            # diagnostics: edits fill
            for d, (t, att, v0) in es.items():
                diag.append(dict(item_id=iid, cond=cond, dim=d, filled=t is not None, regen=att > 1 and t is not None, attempts=att, viol0=v0))
        r = s["word"]; rows.append(dict(item_id=iid, cond="word", arm="W1", texts=[r["g1"]]))
    return rows, pd.DataFrame(diag)

def judge_cov(it, v, loose=False):
    pj = pairj(v["judge"]); out = {}
    for side in "AB":
        e = pj["event_" + side]
        out[side] = pj["value"] == it["values"][side] and (e == "yes" or (loose and e == "partly"))
    out["val"] = pj["value"]
    return out

def score_rows(rows, items, J, loose=False):
    recs = []
    for r in rows:
        it = items[r["item_id"]]; cov = []
        for t in r["texts"]:
            v = J.get((r["item_id"], t))
            cov.append(judge_cov(it, v, loose) if v else {"A": False, "B": False, "val": None})
        ci = it["intended"]; co = "B" if ci == "A" else "A"
        flags = [c[ci] for c in cov]
        k = K[r["arm"]]; n = len(r["texts"])
        first = next((i + 1 for i, f in enumerate(flags) if f), None)
        recs.append(dict(item_id=r["item_id"], writer_id=it["writer_id"], dimension=it["dimension"], cond=r["cond"], arm=r["arm"], k=k, n_shown=n,
                         covered=int(any(flags)), covers_other=int(any(c[co] for c in cov)), covers_both=int(any(flags) and any(c[co] for c in cov)),
                         first_pos=first if first else k, wrong_first=int(cov[0]["val"] == it["other_value"]),
                         first_ok=int(cov[0]["val"] == it["intended_value"]), short=int(n < k),
                         min_lev=min(lev(t, it["r"]) for t in r["texts"]), r_words=len(it["r"].split()),
                         sim=(float(np.mean([jacc(a, b) for a, b in itertools.combinations(r["texts"], 2)])) if n > 1 else np.nan),
                         seen=int(it["seen_in_part18"]), hw2=int(it["hw2"])))
    return pd.DataFrame(recs)

def cost(df, r=0.5, e=1.0):
    cue = (df.cond != "bare").astype(float)   # chip or word cue = 1 tap
    read = np.where(df.covered == 1, df.first_pos, df.k.clip(upper=df.n_shown.clip(lower=1)))
    s = (df.k > 1).astype(float)
    fb = np.where(df.covered == 1, 0.0, np.minimum(df.r_words, e * df.min_lev))
    return cue + r * read + s + 1.0 + fb

def boot(df, fn, B=B, seed=SEED):
    """writer-cluster bootstrap: resample writers, then items within writer. fn(df)->float."""
    rng = np.random.default_rng(seed); g = {w: x for w, x in df.groupby("writer_id")}; ws = list(g); out = []
    for _ in range(B):
        parts = []
        for w in rng.choice(ws, len(ws)):
            x = g[w]; parts.append(x.iloc[rng.integers(0, len(x), len(x))])
        out.append(fn(pd.concat(parts)))
    return [float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))]

def boot_mean(vals, writers, B=B, seed=SEED):
    """vectorised writer-cluster bootstrap of a mean (resample writers, then items within writer)."""
    rng = np.random.default_rng(seed); vals = np.asarray(vals, float); writers = np.asarray(writers)
    groups = [vals[writers == w] for w in sorted(set(writers))]; est = np.empty(B)
    for b in range(B):
        tot = 0.0; n = 0
        for gi in rng.integers(0, len(groups), len(groups)):
            g = groups[gi]; tot += g[rng.integers(0, len(g), len(g))].sum(); n += len(g)
        est[b] = tot / n
    return [float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]

def paired(sc, a, b, ca, cb, col="covered", B=B):
    x = sc[(sc.arm == a) & (sc.cond == ca)].set_index("item_id"); y = sc[(sc.arm == b) & (sc.cond == cb)].set_index("item_id")
    ix = x.index.intersection(y.index); d = pd.DataFrame({"writer_id": x.loc[ix, "writer_id"], "d": x.loc[ix, col].astype(float) - y.loc[ix, col].astype(float)})
    est = float(d.d.mean()); ci = boot_mean(d.d.values, d.writer_id.values, B)
    wm = d.groupby("writer_id").d.mean().values; rng = np.random.default_rng(SEED); sgn = rng.choice([-1, 1], size=(50000, len(wm)))
    p = float((np.abs((sgn * wm).mean(1)) >= abs(wm.mean()) - 1e-12).mean())
    return est, ci, p, len(d)

def main(which="main"):
    global OUTD
    OUTD = L.OUT if which == "main" else (L.OUT / "dry_run_reserve")
    OUTD.mkdir(exist_ok=True)
    items, J, S = load(which); rows, diag = build_sets(items, J, S)
    sc = score_rows(rows, items, J); sc_loose = score_rows(rows, items, J, loose=True)
    sc.to_csv(OUTD / "set_scores.csv", index=False)
    summ = {"n_items": len(S), "gate": json.load(open(L.OUT / "proxy_validity.json"))}
    # coverage by arm x condition
    out = []
    for (cond, arm), x in sc.groupby(["cond", "arm"]):
        ci = boot_mean(x.covered.values, x.writer_id.values, 2000)
        c5 = cost(x, 0.5)
        out.append(dict(cond=cond, arm=arm, k=int(x.k.iloc[0]), n=len(x), coverage=x.covered.mean(), ci_lo=ci[0], ci_hi=ci[1],
                        coverage_loose=sc_loose[(sc_loose.cond == cond) & (sc_loose.arm == arm)].covered.mean(),
                        first_ok=x.first_ok.mean(), wrong_first=x.wrong_first.mean(), covers_other=x.covers_other.mean(), covers_both=x.covers_both.mean(),
                        mean_shown=x.n_shown.mean(), short_rate=x.short.mean(), mean_first_pos_covered=x[x.covered == 1].first_pos.mean(),
                        mean_sim=x.sim.mean(), cost_r05=c5.mean(), cost_per_covered_r05=c5.mean() / max(x.covered.mean(), 1e-9)))
    cba = pd.DataFrame(out).sort_values(["cond", "k", "arm"]); cba.to_csv(OUTD / "coverage_by_arm.csv", index=False)
    # per dimension (direction only)
    pdm = sc.groupby(["cond", "arm", "dimension"]).covered.agg(["mean", "size"]).reset_index(); pdm.to_csv(OUTD / "coverage_by_dimension.csv", index=False)
    # contrasts
    cons = []
    def add(name, a, b, ca, cb):
        if (sc[(sc.arm == a) & (sc.cond == ca)].shape[0] == 0): return
        est, ci, p, n = paired(sc, a, b, ca, cb); cons.append(dict(contrast=name, arm_a=f"{a}/{ca}", arm_b=f"{b}/{cb}", diff_pp=100 * est, ci_lo_pp=100 * ci[0], ci_hi_pp=100 * ci[1], p_signflip=p, n=n))
    for a in ("E3", "C3", "C3f", "R3", "C3o"): add(f"S1 {a} - D3p (bare)", a, "D3p", "bare", "bare")
    for a in ("E3", "C3", "D3p", "D3s"): add(f"{a} bare - G1 bare", a, "G1", "bare", "bare")
    add("G1 chip - G1 bare (cue tap)", "G1", "G1", "chip", "bare"); add("W1 word - G1 chip", "W1", "G1", "word", "chip")
    for a in ("E3", "C3", "D3p", "C3f", "R3"): add(f"S2 {a} bare - G1 chip", a, "G1", "bare", "chip")
    for a in ("E3", "C3", "D3p", "E5", "C5", "D5p"): add(f"S3 {a} chip - G1 chip", a, "G1", "chip", "chip")
    add("E3 chip - D3p chip", "E3", "D3p", "chip", "chip"); add("C3 chip - D3p chip", "C3", "D3p", "chip", "chip")
    add("E5 bare - D5p bare", "E5", "D5p", "bare", "bare"); add("C5 bare - D5p bare", "C5", "D5p", "bare", "bare"); add("E5 chip - D5p chip", "E5", "D5p", "chip", "chip")
    add("wrong-first E3 - G1 (chip, same first draft)", "E3", "G1", "chip", "chip")
    con = pd.DataFrame(cons); con.to_csv(OUTD / "contrasts.csv", index=False)
    # sensitivities for headline contrasts
    sens = []
    for lab, f in (("all", sc), ("no_seen_part18", sc[sc.seen == 0]), ("no_hw2", sc[sc.hw2 == 0]), ("no_short_sets", sc[sc.short == 0])):
        for a, b, ca, cb in (("E3", "D3p", "bare", "bare"), ("C3", "D3p", "bare", "bare"), ("E3", "G1", "chip", "chip"), ("G1", "G1", "chip", "bare")):
            e, ci, p, n = paired(f, a, b, ca, cb, B=2000); sens.append(dict(sample=lab, contrast=f"{a}/{ca}-{b}/{cb}", diff_pp=100 * e, ci_lo=100 * ci[0], ci_hi=100 * ci[1], n=n))
    pd.DataFrame(sens).to_csv(OUTD / "sensitivity.csv", index=False)
    # frontier: cost grid
    fr = []
    for r in (0.25, 0.5, 1.0, 2.0):
        for e in (0.5, 1.0, 2.0):
            for (cond, arm), x in sc.groupby(["cond", "arm"]):
                if arm == "C3o": continue
                c = cost(x, r, e); fr.append(dict(r=r, e=e, cond=cond, arm=arm, coverage=x.covered.mean(), cost=c.mean(), cost_per_covered=c.mean() / max(x.covered.mean(), 1e-9)))
    fr = pd.DataFrame(fr); fr.to_csv(OUTD / "frontier.csv", index=False)
    # break-even r*: arm (bare or chip) vs G1 chip cost per covered, scanning r
    be = []
    base = sc[(sc.arm == "G1") & (sc.cond == "chip")]
    for (cond, arm), x in sc.groupby(["cond", "arm"]):
        if arm in ("G1", "W1", "C3o"): continue
        rs = np.linspace(0, 4, 161); win = [r for r in rs if cost(x, r).mean() / max(x.covered.mean(), 1e-9) <= cost(base, r).mean() / max(base.covered.mean(), 1e-9)]
        be.append(dict(cond=cond, arm=arm, wins_up_to_r=max(win) if win else None, wins_at_r0=bool(win and win[0] == 0)))
    pd.DataFrame(be).to_csv(OUTD / "breakeven.csv", index=False)
    # selector recall (bare, pair dimension) vs static vs random
    sr = []
    for kk in (1, 2):
        hit_s = np.mean([s["dimension"] in s["bare"]["sel"][:kk] for s in S.values()])
        hit_t = np.mean([s["dimension"] in s["bare"]["static"][:kk] for s in S.values()])
        hit_r = np.mean([s["dimension"] in s["bare"]["rnd"][:kk] for s in S.values()])
        sr.append(dict(k=kk, selector=hit_s, static=hit_t, random_draw=hit_r, random_expected=kk / 6))
    pd.DataFrame(sr).to_csv(OUTD / "selector_recall.csv", index=False)
    byd = defaultdict(list)
    for s in S.values(): byd[s["dimension"]].append(s["dimension"] in s["bare"]["sel"][:2])
    summ["selector_recall_by_dim_at2"] = {d: float(np.mean(v)) for d, v in byd.items()}
    summ["selector_recall"] = sr
    summ["fill"] = {"edit_slots": int(len(diag)), "filled_after_regen": float(diag.filled.mean()), "regenerated_rate": float(diag.regen.mean()),
                    "needed_regen_rate": float((diag.attempts > 1).mean()),
                    "chip_unfiltered_cue_violation_edits": float(diag[diag.cond == "chip"].viol0.dropna().astype(float).mean())}
    # unfiltered cue-violation rate of non-G1 drafts in chip, by arm
    cv = {}
    for r in rows:
        if r["cond"] != "chip" or r["arm"] in ("G1", "W1"): continue
        it = items[r["item_id"]]
        for t in r["texts"][1:]:
            v = J.get((r["item_id"], t)); cv.setdefault(r["arm"], []).append(pairj(v["judge"])["value"] != it["intended_value"] if v else True)
    summ["chip_cue_violation_shown_nonG1"] = {a: float(np.mean(v)) for a, v in cv.items()}
    # raw (unfiltered) cue violation of every distinct chip draft by kind
    rawv = defaultdict(list)
    for (iid, t), v in J.items():
        it = items[iid]
        for u in v["uses"]:
            if u["cond"] == "chip" and u["kind"] != "g1": rawv[u["kind"]].append(pairj(v["judge"])["value"] != it["intended_value"])
    summ["chip_cue_violation_raw_by_kind"] = {a: float(np.mean(v)) for a, v in rawv.items()}
    # ceilings: any-arm coverage
    best = sc.groupby(["item_id", "cond"]).covered.max().groupby("cond").mean()
    summ["ceiling_any_arm"] = {c: float(v) for c, v in best.items()}
    sizes = sc.groupby(["cond", "arm"]).n_shown.mean().unstack(0)
    summ["mean_shown"] = {f"{a}/{c}": float(sizes.loc[a, c]) for a in sizes.index for c in sizes.columns if sizes.loc[a, c] == sizes.loc[a, c]}
    summ["coverage_by_arm"] = {f"{r.arm}/{r.cond}": dict(coverage=r.coverage, ci=[r.ci_lo, r.ci_hi], coverage_loose=r.coverage_loose, k=r.k, n=r.n) for r in cba.itertuples()}
    summ["contrasts"] = {r.contrast: dict(diff_pp=r.diff_pp, ci=[r.ci_lo_pp, r.ci_hi_pp], p=r.p_signflip, n=r.n) for r in con.itertuples()}
    s2c = {}
    for k_, v in summ["contrasts"].items(): s2c[k_] = v
    # S4 machine analog
    c3 = sc[(sc.arm == "E3") & (sc.cond == "chip") & (sc.covered == 1)]; summ["median_drafts_read_E3_chip_covered"] = float(c3.first_pos.median()) if len(c3) else None
    c3b = sc[(sc.arm == "E3") & (sc.cond == "bare") & (sc.covered == 1)]; summ["median_drafts_read_E3_bare_covered"] = float(c3b.first_pos.median()) if len(c3b) else None
    summ["models"] = json.load(open(L.OUT / "models_used.json"))
    (OUTD / "summary.json").write_text(json.dumps(summ, indent=1, default=float))
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(cba[["cond", "arm", "k", "n", "coverage", "ci_lo", "ci_hi", "coverage_loose", "wrong_first", "covers_both", "mean_shown", "mean_first_pos_covered", "cost_per_covered_r05"]].round(3).to_string())
    print(con.round(2).to_string()); print(pd.DataFrame(sr).round(3)); print(json.dumps({k: summ[k] for k in ("fill", "chip_cue_violation_shown_nonG1", "chip_cue_violation_raw_by_kind", "ceiling_any_arm")}, indent=1))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")

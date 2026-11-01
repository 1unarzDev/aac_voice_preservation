"""CALE-AI evidence layer: one place that turns STORED scored tables into the numbers,
harm ledger and gallery rows used by the paper. No generation, no judging, no network.

Inputs (read-only):
  analysis/interventions/report.json    refreshed ACTION-2 intervention summary (src/interventions.py)
  runs/{main1,guard1,span1}/scored.parquet, runs/{guard1,span1}/generations.jsonl
Pending inputs are detected by file existence only (see PENDING below).

Output: paper/caleai/evidence.json (consumed by make_macros.py and figs/make_caleai_figs.py).
Run from anywhere:  ~/aac-voice-preservation/.venv/bin/python paper/caleai/caleai_evidence.py

Bootstrap: whole-family percentile bootstrap, 2,000 resamples, seed 20261031
(src/analyze.family_bootstrap), the same estimator as the intervention report. Primary population
excludes the refusal/acceptance quarantine (act-10, act-16; D-024).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import interventions as I  # noqa: E402  (read-only helpers: guard_frame, span_sets, sha1)
from analyze import family_bootstrap  # noqa: E402

OUT = Path(__file__).resolve().parent / "evidence.json"
SEED, NB = 20261031, 2000
MANIFEST: dict[str, str] = {}


def h(path: Path) -> Path:
    MANIFEST[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return path


def fb(df: pd.DataFrame, col: str) -> dict:
    r = family_bootstrap(df, col, n_boot=NB, seed=SEED)
    x = pd.to_numeric(df[col], errors="coerce").dropna()
    r["k"] = float(x.sum())
    return r


def jl(path: Path) -> list[dict]:
    return [json.loads(x) for x in h(path).read_text().splitlines() if x.strip()]


def ratio_contrast(d, col, group, left, right):
    """Edit-type rate difference; families resampled jointly (both groups move together)."""
    c = d.assign(_n=1).groupby(["family_id", group]).agg(k=(col, "sum"), n=("_n", "sum"))
    fs = sorted(d.family_id.unique())
    a = np.zeros((len(fs), 4))
    for i, f in enumerate(fs):
        for j, g in enumerate((left, right)):
            if (f, g) in c.index:
                a[i, 2 * j:2 * j + 2] = c.loc[(f, g), ["k", "n"]]
    w = np.random.default_rng(SEED).multinomial(len(fs), np.full(len(fs), 1 / len(fs)), size=NB)
    z = w @ a
    ok = (z[:, 1] > 0) & (z[:, 3] > 0)
    diff = z[ok, 0] / z[ok, 1] - z[ok, 2] / z[ok, 3]
    t = a.sum(axis=0)
    return dict(estimate=float(t[0] / t[1] - t[2] / t[3]), ci_low=float(np.quantile(diff, .025)),
                ci_high=float(np.quantile(diff, .975)), n_families=len(fs))


# --------------------------------------------------------------------------------------------
def guard_part(rep: dict) -> dict:
    g = rep["guard"]
    out = {"report": {k: g[k] for k in ("population", "P0", "G1", "G1s", "G1_cue", "G1_ambiguous", "G1_all",
                                        "G1s_cue", "G1s_ambiguous", "G1s_all", "cost", "agree_repaired",
                                        "l0_vs_judge")}}
    current = json.loads(h(ROOT / 'analysis/evidence_c3/current.json').read_text())
    out['increment_vs_strip'] = current['evidence']['C35']
    sc, pairs = I.guard_frame(ROOT / "runs/guard1")
    h(ROOT / "runs/guard1/scored.parquet"); h(ROOT / "runs/guard1/generations.jsonl")
    j = pairs["G1"]
    j = j[j.channel.isin(I.CUE) & j.strict_fail.notna() & j.strict_fail_G1.notna()].copy()
    j["fail0"] = j.strict_fail.astype(bool)
    j["fail1"] = j.strict_fail_G1.astype(bool)
    fixed = j[j.fail0 & ~j.fail1]
    # residual failures after the guard (C20 refreshed), and whether the monitor still flags them
    z = j.copy()
    z["residual"] = z.fail1.astype(float)
    z["flag_final"] = z.flags_final_G1.map(lambda f: bool(f))
    res = z[z.fail1]
    res_act = (res.contra_speech_act_G1.eq(True) | (res.dimension.eq("speech_act") & ~res.critical_match_G1.eq(True)))
    out["residual"] = fb(z, "residual")
    out["residual_flagged"] = {"k": int(res.flag_final.sum()), "n": int(len(res))}
    out["residual_act"] = {"k": int(res_act.sum()), "n": int(len(res))}
    out["unfixed_of_bad"] = {"k": int((j.fail0 & j.fail1).sum()), "n": int(j.fail0.sum())}
    # post hoc lexical diagnostic only (chip echo); NOT a fluency measure
    out["ask_you_prefix"] = {"k": int(fixed.text_G1.str.startswith("Ask you ").sum()), "n": int(len(fixed))}
    # cue-only changed-correct, and the ambiguous-channel share
    ok = j[~j.fail0]
    out["changed_correct_cue"] = {"k": int(ok.changed_G1.astype(bool).sum()), "n": int(len(ok))}
    out["by_model"] = {m: {"bad": int(t.fail0.sum()), "fixed": int((t.fail0 & ~t.fail1).sum()),
                           "ok": int((~t.fail0).sum()), "changed_ok": int((~t.fail0 & t.changed_G1.astype(bool)).sum()),
                           "sp0": float(1 - t.fail0.mean()), "sp1": float(1 - t.fail1.mean()), "n": int(len(t))}
                       for m, t in j.groupby("model")}
    out["n_cue_targets"] = int(len(j))
    out["n_families"] = int(j.family_id.nunique())
    # deterministic gallery rows (same rule as the intervention report / story.md E5-E7)
    j["h"] = [I.sha1(*t) for t in zip(j.base_key, j.family_id, j.variant, j.channel)]
    j = j.sort_values(["h", "output_id"])
    cats = {"fixed": j[j.fail0 & ~j.fail1], "unfixed": j[j.fail0 & j.fail1],
            "changed_correct": j[~j.fail0 & j.changed_G1.astype(bool)]}
    gal = []
    for cat, take in (("fixed", 0), ("unfixed", 0), ("fixed", 1), ("changed_correct", 0)):
        r = cats[cat].iloc[take]
        gal.append(dict(category=cat, rank=take + 1, model=r.model, family_id=r.family_id, variant=r.variant,
                        channel=r.channel, input=r.input_text, before=r.text, after=r.text_G1,
                        flags_before=list(r.flags_initial or []), flags_after=list(r.flags_final_G1 or []),
                        target=r.variant_value, critical_before=r.critical, critical_after=r.critical_G1,
                        politeness_before=r.politeness, politeness_after=r.politeness_G1,
                        output_id_before=r.output_id, output_id_after=r.output_id_G1,
                        pool_k=int(len(cats[cat])), pool_n=int(len(j[j.fail0]) if cat != "changed_correct" else len(ok))))
    out["gallery"] = gal
    return out


def span_part(rep: dict) -> dict:
    s = rep["span"]
    out = {"report": {k: s[k] for k in ("polarity+certainty", "polarity", "certainty", "agent", "speech_act",
                                        "politeness", "time_quantity", "all", "cost_I2", "cost_I2t")}}
    h(ROOT / "runs/span1/scored.parquet")
    sc, sets = I.span_sets(ROOT / "runs/span1")
    w = sets.pivot_table(index=["model", "family_id", "dimension"], columns="prompt_id",
                         values="coverage").reset_index()
    cnt = {}
    for lab, dims in (("polarity+certainty", ["polarity", "certainty"]), ("speech_act", ["speech_act"]),
                      ("politeness", ["politeness"]), ("agent", ["agent"]), ("time_quantity", ["time_quantity"])):
        x = w[w.dimension.isin(dims)].dropna(subset=["P2", "I2"])
        cnt[lab] = dict(n=int(len(x)), p2=int(x.P2.sum()), i2=int(x.I2.sum()),
                        gained=int(((x.P2 == 0) & (x.I2 == 1)).sum()), lost=int(((x.P2 == 1) & (x.I2 == 0)).sum()),
                        p2_uncovered=int((x.P2 == 0).sum()), p2_covered=int((x.P2 == 1).sum()))
    out["set_counts"] = cnt
    # collateral: non-targeted dimensions pooled
    x = w[~w.dimension.isin(["polarity", "certainty"])].dropna(subset=["P2", "I2"]).copy()
    x["lost"] = ((x.P2 == 1) & (x.I2 == 0)).astype(float)
    x["gained"] = ((x.P2 == 0) & (x.I2 == 1)).astype(float)
    out["collateral_lost"] = fb(x, "lost")
    out["collateral_lost_of_covered"] = {"k": int(x.lost.sum()), "n": int((x.P2 == 1).sum())}
    out["collateral_gained"] = {"k": int(x.gained.sum()), "n": int((x.P2 == 0).sum())}

    # act drift of actual I2 edits (C18, refreshed on current labels; same join as mine_hyp.py H3)
    gens = jl(ROOT / "runs/span1/generations.jsonl")
    idx = sc.set_index(["family_id", "model", "prompt_id", "suggestion_idx"])
    rows, plans = [], {}
    for g in gens:
        if g["prompt_id"] not in {"I2"}:
            continue
        plans[(g["family_id"], g["model"])] = g.get("span_plan", [])
        for e in g.get("span_plan", []):
            if not e.get("rewritten"):
                continue
            k0 = (g["family_id"], g["model"], "P2", e["slot"])
            k1 = (g["family_id"], g["model"], "I2", e["slot"])
            if k0 not in idx.index or k1 not in idx.index:
                continue  # quarantined family (not in primary frame)
            a, b = idx.loc[k0], idx.loc[k1]
            lab = b[e["dim"]]
            ach = lab == e["target"] if e["dim"] == "polarity" else (
                lab == "hedged/uncertain" if e["target"] == "hedged" else lab in {"plain assertion", "strongly certain/emphatic"})
            rows.append(dict(family_id=g["family_id"], model=g["model"], dim=e["dim"], slot=e["slot"],
                             verified=bool(e.get("verified")), achieved=bool(ach),
                             act_change=float(a.speech_act != b.speech_act), before_act=a.speech_act,
                             after_act=b.speech_act, before=a.text, after=b.text, output_id=b.output_id))
    r = pd.DataFrame(rows)
    out["edits"] = dict(n=int(len(r)), families=int(r.family_id.nunique()), verified=int(r.verified.sum()),
                        achieved=int(r.achieved.sum()))
    out["act_drift"] = fb(r, "act_change")
    out["act_drift_by_dim"] = {d: fb(t, "act_change") for d, t in r.groupby("dim")}
    out["act_drift_cer_minus_pol"] = ratio_contrast(r, "act_change", "dim", "certainty", "polarity")
    out["act_drift_achieved"] = fb(r[r.achieved], "act_change")
    out["act_drift_to_statement"] = int(((r.act_change == 1) & r.after_act.eq("statement")).sum())
    out["act_drift_by_model"] = {m: {"k": int(t.act_change.sum()), "n": int(len(t))} for m, t in r.groupby("model")}
    ex = r[(r.dim == "certainty") & (r.act_change == 1)].sort_values(["family_id", "model", "slot"]).iloc[0]
    out["act_drift_example"] = {**ex.to_dict(), "bare": I.runio.load_items()[ex.family_id]["bare"]}

    # gallery: same rules as story.md E8/E9 on the CURRENT labels; all three slots, both arms
    w["h"] = [I.sha1(m, f) for m, f in zip(w.model, w.family_id)]
    w = w.sort_values("h")
    gain = w[w.dimension.isin(["polarity", "certainty"]) & (w.P2 == 0) & (w.I2 == 1)].iloc[0]
    loss = w[w.dimension.eq("politeness") & (w.P2 == 1) & (w.I2 == 0)].iloc[0]
    items = I.runio.load_items()
    gal = []
    for kind, row in (("gain", gain), ("loss", loss)):
        it = items[row.family_id]
        arms = {}
        for arm in ("P2", "I2"):
            t = sets[(sets.model == row.model) & (sets.family_id == row.family_id) & (sets.prompt_id == arm)].iloc[0]
            arms[arm] = dict(texts=list(t.texts), chose=list(t.chose))
        rew = sorted(e["slot"] for e in plans.get((row.family_id, row.model), []) if e.get("rewritten"))
        gal.append(dict(kind=kind, model=row.model, family_id=row.family_id, dimension=row.dimension,
                        bare=it["bare"], reading_A=it["variants"]["A"]["critical_value"],
                        reading_B=it["variants"]["B"]["critical_value"], rewritten_slots=rew, **arms))
    out["gallery"] = gal
    return out


def chips_part() -> dict:
    """User-side intervention: one commitment chip, P0, primary 58 families (main1)."""
    m = pd.read_parquet(h(ROOT / "runs/main1/scored.parquet"))
    m = m[(m.prompt_id == "P0") & ~m.quarantine_refusal_acceptance.fillna(False).astype(bool) & m.valid]
    keys = ["model", "family_id", "variant"]
    w = m.pivot_table(index=keys, columns="channel", values="critical_match", aggfunc="first").reset_index()
    w = w.dropna(subset=["noncrit", "chip1", "full", "bare"])
    for c in ("bare", "noncrit", "chip1", "chipall", "full"):
        w[c] = w[c].astype(float)
    w["d_chip1_noncrit"] = w.chip1 - w.noncrit
    w["lost_with_chip"] = np.where(w.noncrit == 1, (w.chip1 == 0).astype(float), np.nan)
    w["miss_persists"] = np.where(w.bare == 0, (w.chip1 == 0).astype(float), np.nan)
    out = {k: fb(w, k) for k in ("bare", "noncrit", "chip1", "chipall", "full", "d_chip1_noncrit",
                                  "lost_with_chip", "miss_persists")}
    out["by_model"] = {mm: {"noncrit": float(t.noncrit.mean()), "chip1": float(t.chip1.mean()), "n": int(len(t))}
                       for mm, t in w.groupby("model")}
    out["n_targets"] = int(len(w)); out["n_families"] = int(w.family_id.nunique())
    c1 = m[m.channel.eq("chip1")].copy()
    nc = m[m.channel.eq("noncrit")].copy()
    for d in (c1, nc):
        d["contra"] = d.any_contra.astype(float)
        d["pol_add"] = d.politeness_added.astype(float)
        d["cp"] = d.constraint_preserving.astype(float)
    out["chip1_contra"] = fb(c1, "contra")
    out["chip1_pol_add"] = fb(c1, "pol_add")
    out["noncrit_pol_add"] = fb(nc, "pol_add")
    out["chip1_joint"] = fb(c1, "cp")
    ca = m[m.channel.eq("chipall")].drop_duplicates(["model", "family_id", "variant"])
    out["chipall_mean_chips"] = float(ca.input_text.map(lambda s: len(re.findall(r"\[[^\]]+\]", s))).mean())
    by = {}
    for dim, t in w.merge(m[["family_id", "dimension"]].drop_duplicates(), on="family_id").groupby("dimension"):
        by[dim] = {"noncrit": float(t.noncrit.mean()), "chip1": float(t.chip1.mean()), "n": int(len(t))}
    out["by_dim"] = by
    # gallery: story.md E1 rule (first negated polarity target, model order Qwen, Llama, Gemma, Terra)
    order = {"qwen2.5-7b": 0, "llama3.1-8b": 1, "gemma3-4b": 2, "gpt-6.1-terra": 3}
    p = m[m.dimension.eq("polarity") & m.variant_value.eq("negated")].copy()
    p["mo"] = p.model.map(order)
    first = p.sort_values(["family_id", "variant", "mo", "output_id"]).iloc[0]
    rows = []
    for ch in ("bare", "noncrit", "chip1"):
        t = p[(p.family_id == first.family_id) & (p.variant == first.variant) & (p.model == first.model) & (p.channel == ch)].iloc[0]
        rows.append(dict(channel=ch, input=t.input_text, output=t.text, critical=t.critical, output_id=t.output_id))
    # first speech-act chip1 failure (story E4 rule)
    a = m[m.dimension.eq("speech_act") & m.channel.eq("chip1") & ~m.critical_match.astype(bool)].copy()
    a["mo"] = a.model.map(order)
    fa = a.sort_values(["family_id", "variant", "mo", "output_id"]).iloc[0]
    fn = m[(m.family_id == fa.family_id) & (m.variant == fa.variant) & (m.model == fa.model) & (m.channel == "noncrit")].iloc[0]
    out["gallery"] = dict(model=first.model, family_id=first.family_id, variant=first.variant, rows=rows,
                          failure=dict(model=fa.model, family_id=fa.family_id, variant=fa.variant, input=fa.input_text,
                                       output=fa.text, target=fa.variant_value, critical=fa.critical,
                                       noncrit_input=fn.input_text, noncrit_output=fn.text, noncrit_critical=fn.critical,
                                       output_id=fa.output_id))
    return out


def nondeterminism_part() -> dict:
    """Same greedy request issued twice (namespaces d1/d2) in Exp B/C: share of identical texts per run x model."""
    from collections import defaultdict
    agree = defaultdict(lambda: [0, 0])
    for run in ("expB1", "expC1"):
        by = defaultdict(dict)
        for r in jl(ROOT / f"runs/{run}/generations.jsonl"):
            by[(r["model"], r["prompt_id"], r["input_text"], r["sample_idx"])][r.get("namespace")] = r["raw_text"].strip()
        for k, v in by.items():
            if "d1" in v and "d2" in v:
                agree[(run, k[0])][0] += v["d1"] == v["d2"]
                agree[(run, k[0])][1] += 1
    rates = {f"{run}|{m}": a / n for (run, m), (a, n) in agree.items() if n}
    api = [v for k, v in rates.items() if k.endswith("gpt-6.1-terra")]
    loc = [v for k, v in rates.items() if not k.endswith("gpt-6.1-terra")]
    return {"rates": rates, "api_min": min(api), "api_max": max(api), "local_min": min(loc), "local_max": max(loc)}


PENDING = {  # conditional inputs: present -> macros switch on; absent -> paper prints the pending slot
    "wc": "analysis/r2c/report.json",
    "wd": "analysis/r2d/report.json",
    "wb": "analysis/wb/report.md",
    "human_gold": "annotation/returns",
    "repair_audit": "annotation/repair_audit/results.json",
    "t3": "analysis/t3/report.json",
}


def pending_part() -> dict:
    st = {}
    for k, p in PENDING.items():
        q = ROOT / p
        if q.is_dir():  # a directory counts only once it holds a non-hidden, non-empty file
            st[k] = any(f.is_file() and not f.name.startswith(".") and f.stat().st_size > 0 for f in q.rglob("*"))
        else:
            st[k] = bool(q.exists() and q.stat().st_size > 0)
    return st


def main() -> None:
    rep = json.loads(h(ROOT / "analysis/interventions/report.json").read_text())
    ev = {"guard": guard_part(rep), "span": span_part(rep), "chips": chips_part(),
          "sensitivity_inclusive": {"guard_fix": rep["sensitivity_including_quarantine"]["guard"]["G1_cue"]["fix"],
                                    "cost": rep["sensitivity_including_quarantine"]["guard"]["cost"]},
          "copy_full_mode": rep["copy_full_mode"], "nondeterminism": nondeterminism_part(), "pending": pending_part(),
          "meta": {"seed": SEED, "n_boot": NB, "manifest": MANIFEST,
                   "population": "primary: 58 test families, act-10/act-16 quarantined (D-024)"}}
    OUT.write_text(json.dumps(ev, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else str(x)) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()

"""Build analysis/oracle/report.md (PREREG_R2 W-A) from frozen keys and production labels.

  python src/oracle_report.py

Reads runs/oracle_inject, runs/oracle_challenges (src/oracle_wa.py), runs/main1,
annotation/judge_validation_main1.json and annotation/panel_majority_main1.csv
(src/score_gold.py --panel ...). Writes analysis/oracle/report.md plus CSVs.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attribute  # noqa: E402
import runio  # noqa: E402
from agree_stats import cohen_kappa  # noqa: E402
from labels import GENERAL_DIMS  # noqa: E402
from oracle_wa import CHAL, INJ, OUT, crit_match, load_challenges, verdict  # noqa: E402
from score_gold import kappa_w, wilson  # noqa: E402

ROOT = runio.ROOT
DIMS = ["critical"] + GENERAL_DIMS + ["added_content"]
L = []   # report lines


def w(*a):
    L.append(" ".join(str(x) for x in a))


def ci(k, n):
    c = wilson(k, n)
    return f"{k}/{n} [{c[0]:.2f}, {c[1]:.2f}]" if n else "0/0"


def table(rows, cols):
    w("| " + " | ".join(cols) + " |")
    w("|" + "---|" * len(cols))
    for r in rows:
        w("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |")
    w("")


def jkey(r):
    return (r["text_id"], r["family_id"], r["input_text"])


# ------------------------------------------------------------------ injection

def injection():
    df = attribute.score(INJ, resolution=ROOT / "annotation/label_resolution.jsonl")
    muts = {(m["family_id"], m["variant"]): m for m in runio.read_jsonl(OUT / "source_mutations.jsonl")}
    judg = {jkey(j): j for j in runio.read_jsonl(INJ / "judgments.jsonl")}
    df["raw_match"] = [crit_match(d, v, c, raw=True) for d, v, c in zip(df.dimension, df.variant_value, df.critical)]
    df["J1J2_disagree"] = df["needs_arbiter"].astype(bool)
    contra_cols = [f"contra_{d}" for d in GENERAL_DIMS]
    df["contra_dims"] = [",".join(d for d in GENERAL_DIMS if r[f"contra_{d}"] is True) for _, r in df.iterrows()]
    df["mutant_expected"] = [muts[(f, v)]["mutant_expected_critical"] if m == "mutant" else None
                             for f, v, m in zip(df.family_id, df.variant, df.model)]
    df["same_as_partner"] = [muts[(f, v)]["same_as_partner"] if m == "mutant" else None
                             for f, v, m in zip(df.family_id, df.variant, df.model)]
    df["J1_critical"] = [judg[k]["J1_critical"] for k in zip(df.text_id, df.family_id, df.input_text)]
    df["J2_critical"] = [judg[k]["J2_critical"] for k in zip(df.text_id, df.family_id, df.input_text)]
    keep = ["family_id", "variant", "dimension", "model", "text", "variant_value", "critical", "critical_source",
            "J1_critical", "J2_critical", "critical_match", "raw_match", "violation", "constraint_preserving",
            "contra_dims", "added_content", "mutant_expected", "same_as_partner"] + GENERAL_DIMS
    df[keep].to_csv(OUT / "injection_results.csv", index=False)
    idn, mut = df[df.model == "identity"], df[df.model == "mutant"]

    w("## 2. Identity and scoped-mutation injection (120 test sources)\n")
    w("Every source sentence of data/items/test.jsonl was given to the production judge as if it were the "
      "`full`-channel output for its own source (input `The user typed: <source>`), then scored by the unchanged "
      "src/attribute.py (J1/J2, layer0 tiebreak for general dims, arbiter for critical J1!=J2). One hand-written, "
      "scoped mutation per source (analysis/oracle/source_mutations.jsonl, frozen before judging) flips the critical "
      "value and is scored against the *unmutated* source's contract. "
      f"{int(mut.same_as_partner.sum())}/120 mutations coincide with the family's partner source (minimal pairs "
      "admit few other scoped flips); the rest are new wordings.\n")
    w(f"Critical J1!=J2 disagreements: identity {int(idn.J1J2_disagree.sum())}/120, mutants "
      f"{int(mut.J1J2_disagree.sum())}/120; these went to the arbiter (critical_source=arbiter).\n")
    rows = []
    for d, g in list(idn.groupby("dimension")) + [("ALL", idn)]:
        n = len(g)
        fa_c = int((g.critical_match == False).sum())  # noqa: E712
        fa_raw = int((g.raw_match == False).sum())  # noqa: E712
        fa_cp = int((g.constraint_preserving == False).sum())  # noqa: E712
        unres = int(g.critical.isna().sum())
        rows.append({"dimension": d, "n": n, "critical false alarms (production)": ci(fa_c, n),
                     "critical false alarms (raw, ORACLE_RAW=1)": ci(fa_raw, n),
                     "contract false alarms (constraint_preserving=False)": ci(fa_cp, n),
                     "added_content=yes": int((g.added_content == "yes").sum()), "unresolved": unres})
    w("### 2a. Identity relation: every scored commitment of a verbatim source must pass\n")
    table(rows, list(rows[0]))
    bad = idn[(idn.constraint_preserving == False) | (idn.critical_match == False) | (idn.raw_match == False)  # noqa: E712
              | (idn.added_content == "yes")]
    if len(bad):
        w("Identity failures (any of: critical mismatch, raw-rule mismatch, contradicted general dim, added content):\n")
        table([{"family": r.family_id, "var": r.variant, "source": r.text, "target": r.variant_value,
                "judge critical": f"{r.critical} ({r.critical_source})", "contra dims": r.contra_dims,
                "added": r.added_content,
                "general": f"pol={r.polarity}, act={r.speech_act}, agt={r.agent}, cert={r.certainty}, polite={r.politeness}"}
               for r in bad.itertuples()], ["family", "var", "source", "target", "judge critical", "contra dims", "added", "general"])
    rows = []
    for d, g in list(mut.groupby("dimension")) + [("ALL", mut)]:
        n = len(g)
        det = int((g.violation == True).sum())  # noqa: E712
        det_raw = int((g.raw_match == False).sum())  # noqa: E712
        det_cp = int((g.constraint_preserving == False).sum())  # noqa: E712
        lab = int((g.critical == g.mutant_expected).sum())
        rows.append({"dimension": d, "n": n, "detected: Violation (production)": ci(det, n),
                     "detected (raw rule)": ci(det_raw, n),
                     "detected: constraint_preserving=False": ci(det_cp, n),
                     "misses (production)": n - det - int(g.violation.isna().sum()),
                     "label = my expected value": ci(lab, n)})
    w("### 2b. Scoped mutation: the oracle must flag a flipped critical value\n")
    table(rows, list(rows[0]))
    miss = mut[mut.violation != True]  # noqa: E712
    if len(miss):
        w("Missed mutations:\n")
        table([{"family": r.family_id, "var": r.variant, "source target": r.variant_value, "mutant": r.text,
                "expected": r.mutant_expected, "judge critical": f"{r.critical} ({r.critical_source})",
                "J1/J2": f"{r.J1_critical} / {r.J2_critical}"} for r in miss.itertuples()],
              ["family", "var", "source target", "mutant", "expected", "judge critical", "J1/J2"])
    off = mut[(mut.violation == True) & (mut.critical != mut.mutant_expected)]  # noqa: E712
    if len(off):
        w(f"Detected, but the judge's label differs from the value I keyed ({len(off)}; detection is unaffected):\n")
        table([{"family": r.family_id, "var": r.variant, "mutant": r.text, "expected": r.mutant_expected,
                "judge": r.critical} for r in off.itertuples()], ["family", "var", "mutant", "expected", "judge"])
    return idn, mut


# ----------------------------------------------------------------- challenges

def challenges():
    ch = {c["cid"]: c for c in load_challenges()}
    judg = {j["family_id"]: j for j in runio.read_jsonl(CHAL / "judgments.jsonl")}
    ap = CHAL / "arbiter.jsonl"
    arb = {a["family_id"]: a["critical"] for a in runio.read_jsonl(ap)} if ap.exists() else {}
    recs = []
    for cid, c in ch.items():
        j = judg[cid]
        crit, src = j["critical"], "agree"
        if crit is None:
            crit, src = arb.get(cid), "arbiter" if cid in arb else "unresolved"
        r = {"cid": cid, "group": c["group"], "role": c["role"], "text": c["text"], "dimension": c["dimension"],
             "contract": c["contract_value"], "key_critical": c["key"]["critical"], "judge_critical": crit,
             "source": src, "J1": j["J1_critical"], "J2": j["J2_critical"],
             "match_prod": crit_match(c["dimension"], c["contract_value"], crit),
             "match_raw": crit_match(c["dimension"], c["contract_value"], crit, raw=True),
             "label_ok": crit == c["key"]["critical"]}
        gk = {d: v for d, v in c["key"].items() if d != "critical"}
        r["general_keyed"] = len(gk)
        r["general_ok"] = sum((j.get(d) == v) for d, v in gk.items())
        r["general_errors"] = "; ".join(f"{d}: key={v} judge={j.get(d)}" for d, v in gk.items() if j.get(d) != v)
        recs.append(r)
    df = pd.DataFrame(recs)
    df.to_csv(OUT / "challenge_results.csv", index=False)
    new = df[df.role.isin(["control", "mutant"])]
    w("## 3. Challenge items (24 round-1 + 48 new)\n")
    w("The 48 new sentences (annotation/challenge_items_r2.jsonl) were written by hand, without LLM help, with keys "
      "frozen before any judge call (sha256 in analysis/oracle/challenge_keys_frozen.sha256). Each control is a valid "
      "instance of its contract value. Each mutant changes one feature of its paired control and is scored against "
      "the *control's* contract value. A control fails (false alarm) when the production critical_match rejects it. "
      "A mutant is detected when critical_match rejects it. `raw` is the same rule without the D-015 "
      "acceptance~statement relaxation.\n")
    rows = []
    for grp, g in list(new.groupby("group")) + [("ALL new (gate)", new)]:
        c, m = g[g.role == "control"], g[g.role == "mutant"]
        rows.append({"group": grp,
                     "false alarms (prod)": ci(int((c.match_prod == False).sum()), len(c)),  # noqa: E712
                     "mutants detected (prod)": ci(int((m.match_prod == False).sum()), len(m)),  # noqa: E712
                     "false alarms (raw)": ci(int((c.match_raw == False).sum()), len(c)),  # noqa: E712
                     "mutants detected (raw)": ci(int((m.match_raw == False).sum()), len(m)),  # noqa: E712
                     "critical label = key": ci(int(g.label_ok.sum()), len(g)),
                     "keyed general labels correct": ci(int(g.general_ok.sum()), int(g.general_keyed.sum())),
                     "J1!=J2": int((g.J1 != g.J2).sum())})
    table(rows, list(rows[0]))
    c, m = new[new.role == "control"], new[new.role == "mutant"]
    det, fa = int((m.match_prod == False).sum()), int((c.match_prod == False).sum())  # noqa: E712
    det_r, fa_r = int((m.match_raw == False).sum()), int((c.match_raw == False).sum())  # noqa: E712
    w(f"**Gate (PREREG_R2: mutants detected >= 22/24, false alarms <= 1/24):** production oracle {det}/24 detected, "
      f"{fa}/24 false alarms -> **{'PASS' if det >= 22 and fa <= 1 else 'FAIL'}**. Raw oracle {det_r}/24, "
      f"{fa_r}/24 -> **{'PASS' if det_r >= 22 and fa_r <= 1 else 'FAIL'}**. The prereg says '22/24 per new group' "
      "but each group has only 6 mutants and 6 controls, so I read the gate as pooled over the 24 new mutants and "
      "24 new controls. Per-group counts are in the table; no group can be certified with n=6 (a 6/6 Wilson lower "
      "bound is 0.61).\n")
    per_group_pass = {g: (int((x[x.role == "mutant"].match_prod == False).sum()), int((x[x.role == "control"].match_prod == False).sum()))  # noqa: E712
                      for g, x in new.groupby("group")}
    w("Per-group strict reading (all 6 mutants detected and 0 false alarms): "
      + ", ".join(f"{g} {d}/6 det, {f}/6 FA -> {'ok' if d == 6 and f == 0 else 'not met'}" for g, (d, f) in per_group_pass.items()) + ".\n")
    bad = new[((new.role == "control") & (new.match_prod == False)) | ((new.role == "mutant") & (new.match_prod != False))]  # noqa: E712
    if len(bad):
        w("Failures (control false alarms and missed mutants):\n")
        table([{"cid": r.cid, "role": r.role, "text": r.text, "contract": r.contract, "key": r.key_critical,
                "judge": f"{r.judge_critical} ({r.source})", "J1/J2": f"{r.J1} / {r.J2}"} for r in bad.itertuples()],
              ["cid", "role", "text", "contract", "key", "judge", "J1/J2"])
    old = df[df.role == "r1"]
    w(f"Round-1 challenges (24, keyed in round 1, not control/mutant balanced): critical label = key "
      f"{ci(int(old.label_ok.sum()), len(old))}; keyed general labels "
      f"{ci(int(old.general_ok.sum()), int(old.general_keyed.sum()))}.\n")
    ob = old[~old.label_ok | (old.general_errors != "")]
    if len(ob):
        table([{"cid": r.cid, "text": r.text, "key": r.key_critical, "judge": f"{r.judge_critical} ({r.source})",
                "general errors": r.general_errors} for r in ob.itertuples()], ["cid", "text", "key", "judge", "general errors"])
    ge = new[new.general_errors != ""]
    if len(ge):
        w("New challenges, keyed general-dimension disagreements (not part of the gate):\n")
        table([{"cid": r.cid, "text": r.text, "errors": r.general_errors} for r in ge.itertuples()], ["cid", "text", "errors"])
    return df, det, fa, det_r, fa_r


# ---------------------------------------------------------------------- panel

def panel():
    rep = json.loads((ROOT / "annotation/judge_validation_main1.json").read_text())
    P = rep["panel"]
    w("## 4. Codex annotator panel vs the production judge (main1 gold, 163 sampled + 24 round-1 challenges)\n")
    w(f"Panel: {', '.join(P['members'])} (machine annotators; none is the judge gpt-6.1-sol or the tested "
      "gpt-6.1-terra). **This is machine-machine agreement, not human validation. The PREREG kappa>=0.6 gate "
      "applies to human gold only, and no human returns exist yet (annotation/returns/ is absent).** Production "
      "labels: J1==J2, else the arbiter (13 sampled critical labels were null in gold_key_main1.csv and are now "
      "filled from runs/main1/arbiter.jsonl), general dims use the layer0 tiebreak. Labels the panel member listed in "
      "`unsure_dims` are treated as missing, which matches the annotate.html export. Majority means at least 2 of 3 "
      "members, and more than half of the non-missing votes. Design weights are 1/pi from gold_key_main1.csv "
      "(Horvitz-Thompson); weighted CIs use the Kish effective n. Challenge items have no pi and are scored "
      "unweighted, in a separate subset.\n")
    w(f"Data notes: {json.dumps({k: v for k, v in P['notes'].items() if k != 'files'})}. The 43 rows with an extra "
      "column are all of C_gpt-6-luna_extraB.csv, which has one surplus empty field after added_content. The label "
      "columns parse correctly. Out-of-schema general labels are kept as given (speech_act=acceptance, "
      "politeness=plain) and count as disagreements.\n")
    rows = []
    for d in DIMS:
        a = P["alpha_nominal"][d]
        m = P["judge"][d].get("sampled/final", {})
        mc = P["judge"][d].get("challenge/final", {})
        rows.append({"dimension": d, "panel alpha (3 members)": f"{a['alpha']} {a['ci95']}",
                     "n (majority, judge non-null)": m.get("n"), "no majority": P["judge"][d]["no_consensus_excluded"],
                     "judge null": m.get("n_judge_null"),
                     "acc": f"{m.get('acc')} {m.get('acc_ci')}", "kappa": f"{m.get('kappa')} {m.get('kappa_ci')}",
                     "acc_w": f"{m.get('acc_w')} {m.get('acc_w_ci')}", "kappa_w": f"{m.get('kappa_w')} {m.get('kappa_w_ci')}",
                     "n_eff": m.get("n_eff"),
                     "challenge acc (n)": f"{mc.get('acc')} ({mc.get('n')})" if mc else ""})
    w("### 4a. Judge (final) vs panel majority, sampled items\n")
    table(rows, list(rows[0]))
    S = json.loads((ROOT / "annotation/judge_validation_main1_sens_sol_astra.json").read_text())["panel"]
    w("Sensitivity: the reference is gpt-5.6-sol + gpt-6-astra only (both must agree). gpt-6-luna is dropped because "
      "its core file gave 28 critical answers that are not options of the item (dropped as invalid above) and has "
      "low agreement with every other rater on general dims (core file only, see 4b).\n")
    rows = []
    for d in DIMS:
        m, m2 = P["judge"][d].get("sampled/final", {}), S["judge"][d].get("sampled/final", {})
        rows.append({"dimension": d, "3-member majority: n / kappa / kappa_w": f"{m.get('n')} / {m.get('kappa')} / {m.get('kappa_w')}",
                     "sol+astra agree: n / kappa / kappa_w": f"{m2.get('n')} / {m2.get('kappa')} {m2.get('kappa_ci')} / {m2.get('kappa_w')}",
                     "sol~astra alpha": S["alpha_nominal"][d]["alpha"]})
    table(rows, list(rows[0]))
    w("### 4b. Pairwise raw agreement / Cohen kappa (sampled items)\n")
    pairs = sorted({k.split("|")[0] for d in DIMS for k in P["pairwise"][d] if k.endswith("|sampled")})
    rows = []
    for d in DIMS:
        r = {"dimension": d}
        for pr in pairs:
            x = P["pairwise"][d].get(f"{pr}|sampled")
            r[pr.replace("C-gpt-", "").replace("judge(final)", "judge")] = f"{x['agree']:.2f} / {x['kappa']}" if x else ""
        rows.append(r)
    table(rows, list(rows[0]))
    # critical split by item dimension, with weights
    key = {r["item_id"]: r for r in csv.DictReader(open(ROOT / "annotation/gold_key_main1.csv"))}
    maj = {r["item_id"]: r for r in csv.DictReader(open(ROOT / "annotation/panel_majority_main1.csv"))}
    arb = {jkey(a): a["critical"] for a in runio.read_jsonl(ROOT / "runs/main1/arbiter.jsonl")}
    rows = []
    for dim in sorted({k["dimension"] for k in key.values()}):
        pr = []
        for i, k in key.items():
            if k["dimension"] != dim or i not in maj or not maj[i]["critical"]:
                continue
            jc = k["critical"] or arb.get(jkey(k))
            pr.append((jc, maj[i]["critical"], 1 / float(k["pi"])))
        p, g, ww = [x[0] for x in pr], [x[1] for x in pr], [x[2] for x in pr]
        ok = sum(a == b for a, b in zip(p, g))
        rows.append({"critical dimension": dim, "n": len(pr), "acc": ci(ok, len(pr)), "kappa": cohen_kappa(p, g),
                     "kappa_w": kappa_w(p, g, ww),
                     "disagreements (judge->panel)": "; ".join(f"{a}->{b}" for a, b in zip(p, g) if a != b)})
    w("### 4c. Critical label by family dimension (sampled; judge final incl. arbiter vs panel majority)\n")
    table(rows, list(rows[0]))
    w("Critical confusion matrices by family dimension (rows = panel majority, columns = judge):\n")
    for dim in sorted({k["dimension"] for k in key.values()}):
        cm = Counter()
        for i, k in key.items():
            if k["dimension"] == dim and i in maj and maj[i]["critical"]:
                cm[(maj[i]["critical"], k["critical"] or arb.get(jkey(k)))] += 1
        labs = sorted({a for a, _ in cm} | {b for _, b in cm})
        w(f"**critical / {dim}**\n")
        table([{"panel \\ judge": g, **{p: cm[(g, p)] for p in labs}} for g in labs], ["panel \\ judge"] + labs)
    w("### 4d. Per-label precision / recall of the judge, design-weighted (sampled, final)\n")
    rows = []
    for d in DIMS:
        m = P["judge"][d].get("sampled/final", {})
        for lab, x in m.get("per_label", {}).items():
            rows.append({"dimension": d, "label": lab, "n panel": x["n_reference"],
                         "precision": f"{x['precision']} {x['precision_ci']}", "recall": f"{x['recall']} {x['recall_ci']}",
                         "precision_w": f"{x.get('precision_w')} {x.get('precision_w_ci')}",
                         "recall_w": f"{x.get('recall_w')} {x.get('recall_w_ci')}"})
    table(rows, list(rows[0]))
    w("### 4e. Confusion matrices (rows = panel majority, columns = judge final; sampled, unweighted counts)\n")
    for d in DIMS[1:]:
        cm = P["judge"][d].get("sampled/final", {}).get("confusion_rows_reference")
        if not cm:
            continue
        labs = list(cm)
        w(f"**{d}**\n")
        table([{"panel \\ judge": g, **{p: cm[g][p] for p in labs}} for g in labs], ["panel \\ judge"] + labs)
    return P


# ------------------------------------------------------------------- verdicts

def verdicts(tag="", title="panel majority (3 members)", include_quarantine=False):
    items = runio.load_items(ROOT / "data/items/test.jsonl")
    key = {r["item_id"]: r for r in csv.DictReader(open(ROOT / "annotation/gold_key_main1.csv"))}
    maj = {r["item_id"]: r for r in csv.DictReader(open(ROOT / f"annotation/panel_majority_main1{tag}.csv"))}
    sc = pd.read_parquet(ROOT / "runs/main1/scored.parquet")
    sc = sc[sc.judged]
    if not include_quarantine:
        sc = sc[~sc.quarantine_refusal_acceptance.fillna(False).astype(bool)]
    by = defaultdict(list)
    for r in sc.to_dict("records"):
        by[(r["text_id"], r["family_id"], r["input_text"])].append(r)
    recs, sanity = [], Counter()
    V = ["violation", "assumption", "constraint_preserving"]
    for i, k in key.items():
        rows = by.get(jkey(k), [])
        m = maj.get(i)
        for r in rows:
            it = items[r["family_id"]]
            var = it["variants"][r["variant"]]
            LJ = {"critical": r["critical"], **{d: r[d] for d in GENERAL_DIMS}}
            vj = verdict(it["dimension"], var, r["channel"], LJ)
            for v in V:   # recomputation must reproduce production
                pv = r[v]
                sanity["ok" if (None if pd.isna(pv) else bool(pv)) == vj[v] else "mismatch"] += 1
            LP = {d: (m[d] or None) if m else None for d in ["critical"] + GENERAL_DIMS}
            vp = verdict(it["dimension"], var, r["channel"], LP)
            vps = verdict(it["dimension"], var, r["channel"], LP, strict=True)
            rec = {"item_id": i, "pi": float(k["pi"]), "family_id": r["family_id"], "dimension": it["dimension"],
                   "channel": r["channel"], "variant": r["variant"], "model": r["model"], "prompt_id": r["prompt_id"],
                   "text": r["text"], "judge_critical": r["critical"], "panel_critical": LP["critical"],
                   "quarantine": attribute.quarantined(it)}
            for v in V:
                rec[f"judge_{v}"], rec[f"panel_{v}"], rec[f"panel_strict_{v}"] = vj[v], vp[v], vps[v]
            recs.append(rec)
    df = pd.DataFrame(recs)
    suffix = "_inclusive" if include_quarantine else ""
    df.to_csv(OUT / f"verdict_validation{tag}{suffix}.csv", index=False)
    w(f"### Reference: {title}\n")
    w("Each sampled gold unit (text, family, visible input) maps to one or more scored occurrences in "
      "runs/main1/scored.parquet: different variants share bare/noncrit inputs, and models and prompts can produce "
      "the same text. For every occurrence I recomputed Violation (cue channels), Assumption (bare/noncrit) and "
      "constraint_preserving (cue channels) twice. The first run used the production judge labels; recomputing them "
      f"reproduces the stored production verdicts exactly ({dict(sanity)}). The second run used panel-majority labels "
      "for the critical and general dims. A verdict *flips* when the two runs give different non-missing values. When "
      "the panel has no majority on a needed label, that verdict is unresolved, not a flip. Production semantics "
      "ignore a missing general label; the `strict` columns in the CSV treat it as unresolved instead.\n")
    rows = []
    units = df.groupby("item_id")
    for v in V:
        sub = df[df[f"judge_{v}"].notna()]
        both = sub[sub[f"panel_{v}"].notna()]
        flips = both[both[f"judge_{v}"] != both[f"panel_{v}"]]
        u_both = both.groupby("item_id")
        u_flip = flips.item_id.nunique()
        pis = both.groupby("item_id").pi.first()
        fl_u = set(flips.item_id)
        wsum = (1 / pis).sum()
        wflip = sum(1 / pis[i] for i in fl_u)
        jp = both[f"judge_{v}"].astype(bool)
        pp = both[f"panel_{v}"].astype(bool)
        tp, fp, fn, tn = int((jp & pp).sum()), int((jp & ~pp).sum()), int((~jp & pp).sum()), int((~jp & ~pp).sum())
        rows.append({"verdict": v, "occurrences (both defined)": len(both),
                     "unresolved (no panel majority)": len(sub) - len(both),
                     "occurrence flips": ci(len(flips), len(both)),
                     "units with >=1 flip": ci(u_flip, u_both.ngroups),
                     "units flipped, design-weighted": f"{wflip / wsum:.3f}" if wsum else "",
                     "judge T/panel T": tp, "judge T/panel F": fp, "judge F/panel T": fn, "judge F/panel F": tn,
                     "judge sens vs panel": ci(tp, tp + fn), "judge spec vs panel": ci(tn, tn + fp)})
    table(rows, list(rows[0]))
    anyflip = df[[any((not pd.isna(r[f"judge_{v}"])) and (not pd.isna(r[f"panel_{v}"])) and r[f"judge_{v}"] != r[f"panel_{v}"]
                      for v in V) for _, r in df.iterrows()]]
    w(f"Flipped units ({anyflip.item_id.nunique()} distinct gold units, {len(anyflip)} occurrences). By family "
      f"dimension: {dict(Counter(anyflip.drop_duplicates('item_id').dimension))}.\n")
    ex = anyflip.drop_duplicates("item_id")
    table([{"item": r.item_id, "family": r.family_id, "channel": r.channel, "text": r.text,
            "judge crit": r.judge_critical, "panel crit": r.panel_critical,
            "judge V/A/CP": f"{r.judge_violation}/{r.judge_assumption}/{r.judge_constraint_preserving}",
            "panel V/A/CP": f"{r.panel_violation}/{r.panel_assumption}/{r.panel_constraint_preserving}"}
           for r in ex.itertuples()], ["item", "family", "channel", "text", "judge crit", "panel crit", "judge V/A/CP", "panel V/A/CP"])
    return df


def main():
    idn, mut = injection()
    inj = list(L); L.clear()
    chdf, det, fa, det_r, fa_r = challenges()
    chl = list(L); L.clear()
    P = panel()
    pl = list(L); L.clear()
    w("## 5. Contract-verdict validation (gold items, main1)\n")
    primary_verdicts = verdicts()
    verdicts("_sens_sol_astra", "gpt-5.6-sol + gpt-6-astra agreement (sensitivity)")
    inclusive_verdicts = verdicts(title="panel majority, quarantine-inclusive sensitivity", include_quarantine=True)
    vl = list(L); L.clear()
    intro = (OUT / "report_intro.md").read_text() if (OUT / "report_intro.md").exists() else ""
    metrics = {}
    for name, frame in [("primary", primary_verdicts), ("quarantine_inclusive", inclusive_verdicts)]:
        metrics[name] = {}
        for v in ["violation", "constraint_preserving", "assumption"]:
            both = frame[frame[f"judge_{v}"].notna() & frame[f"panel_{v}"].notna()]
            flips = both[both[f"judge_{v}"] != both[f"panel_{v}"]]
            pis = both.groupby("item_id").pi.first()
            weighted = sum(1 / pis[i] for i in set(flips.item_id)) / (1 / pis).sum()
            metrics[name][v] = dict(n_units=len(pis), units_flipped=flips.item_id.nunique(),
                                    weighted_flip=float(weighted), n_occurrences=len(both),
                                    occurrences_flipped=len(flips))
    metrics["identity"] = dict(n=len(idn), false_alarms=int(idn.constraint_preserving.eq(False).sum()))
    metrics["scoped_mutation"] = dict(n=len(mut), detected=int(mut.violation.eq(True).sum()))
    metrics["new_challenge"] = dict(mutants_detected=int(det), controls_false_alarm=int(fa), n_each=24)
    (OUT / "refreshed_summary.json").write_text(json.dumps(metrics, indent=2) + "\n")
    # Historical intro is retained in evidence_prev; regenerate its verdict row
    # from this exact primary table rather than repeating the older 1.3% figure.
    summary = "; ".join(f"{v}: {m['units_flipped']}/{m['n_units']} units ({100*m['weighted_flip']:.2f}% weighted)"
                        for v, m in metrics["primary"].items())
    intro = "\n".join(("| Contract verdicts recomputed from panel labels (primary, excluding quarantine) | "
                        + summary + " | machine agreement only; human gate pending |")
                       if line.startswith("| Contract verdicts recomputed") else line
                       for line in intro.splitlines())
    intro = intro.replace("the arbiter rule and src/attribute.py are unchanged.",
                          "the extraction calls are historical. ACTION 2 refresh uses shared arbiter > agreement > unknown "
                          "resolution and primary quarantine exclusions; no new judge calls were made.")
    outro = (OUT / "report_outro.md").read_text() if (OUT / "report_outro.md").exists() else ""
    quar = quarantine()
    (OUT / "report.md").write_text("\n".join([intro] + inj + chl + pl + vl + quar + [outro]) + "\n")
    from evidence_status import annotate_report
    annotate_report(OUT / 'report.md')
    print("\n".join(inj + chl + pl + vl + quar))


def quarantine():
    t = pd.read_csv(ROOT / "analysis/main1/sensitivity_quarantine_refusal_acceptance.csv")
    raw = pd.read_parquet(ROOT / "runs/main1/scored_raw_oracle.parquet")
    out = ["## 6. Refusal/acceptance quarantine\n",
           "src/attribute.py now writes `quarantine_refusal_acceptance` (True for every row of a speech-act family "
           "with a refusal or acceptance variant: act-10, act-16 in main1). runs/main1/scored.parquet was regenerated; "
           "critical labels use annotation/label_resolution.jsonl across all refreshed runs. Old tables are "
           "preserved as scored_prev.parquet; analysis/reconciliation.md lists changed endpoints. "
           "src/analyze.py writes analysis/main1/sensitivity_quarantine_refusal_acceptance.csv; headline analyses "
           "now exclude quarantine throughout (58 families, including 8 speech-act families). "
           "The full 60-family analysis is retained in analysis/main1_quarantine_inclusive.\n",
           "P0 speech-act critical match / constraint_preserving (pooled over 4 models; mean of model estimates):\n"]
    q = t[(t.prompt_id == "P0")]
    rows = []
    for ch in ["bare", "noncrit", "chip1", "chipall", "full"]:
        r = {"channel": ch}
        for sub in ["all_speech_act_families", "primary_excl_quarantine", "quarantined_only"]:
            for met in ["critical_match", "constraint_preserving"]:
                x = q[(q.channel == ch) & (q.subset == sub) & (q.metric == met)].estimate
                if x.notna().any():
                    r[f"{sub} {met}"] = f"{x.mean():.3f}"
        rows.append(r)
    cols = ["channel"] + [c for c in rows[-1] if c != "channel"]
    out.append("| " + " | ".join(cols) + " |")
    out.append("|" + "---|" * len(cols))
    for r in rows:
        out.append("| " + " | ".join(r.get(c, "") for c in cols) + " |")
    rq = raw[raw.family_id.isin(["act-10", "act-16"]) & (raw.prompt_id == "P0") & raw.channel.isin(["full"])]
    pq = pd.read_parquet(ROOT / "runs/main1/scored.parquet")
    pq = pq[pq.family_id.isin(["act-10", "act-16"]) & (pq.prompt_id == "P0") & pq.channel.isin(["full"])]
    out.append("")
    out.append(f"Quarantined families, P0 full channel, critical match: production (relaxed) "
               f"{int(pq.critical_match.sum())}/{len(pq)}, raw oracle {int(rq.critical_match.sum())}/{len(rq)}. "
               "These numbers are sensitivity-only and cannot carry a headline.\n")
    return out


if __name__ == "__main__":
    main()

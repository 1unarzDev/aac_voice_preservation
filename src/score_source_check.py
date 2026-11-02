"""Score Part 21 returns: human vs detector labels of the source messages, and the human-corrected T2 posterior.

usage: python src/score_source_check.py [CSV ...]   (default: annotation/returns_source_check/labels_part21_*.csv)
          [--key annotation/source_check_key.csv] [--out analysis/source_check] [--no-t2]
       python src/score_source_check.py --self-check    (simulated returns on the real key; writes nothing)

Input: the CSVs source_check.html exports (columns item_id, annotator, practice, negated, polite, act). Practice rows are
dropped. "unsure" and blank are missing, never a disagreement. A coding by someone who is not a coder of that message, or who
is on its blocked list (typed its keywords in Part 9), is reported as a problem and dropped.

Human label per message (fixed in COORDINATOR_STEPS section 4, "Part 21", before any return):
  primary      both coders gave a label and they are equal (negated / polite: yes or no; act: statement, question or request).
               For the binary "question or request vs statement" label, question and request count as the same answer.
  split        the coders differ: no consensus for the agreement statistics (counted and listed). For the T2 correction a
               yes/no split is a coin flip, p = 0.5 (sensitivity: the stratum rate instead).
  single       one coder labelled and the other was unsure: that label for the T2 correction, excluded from the agreement
               statistics (sensitivity: included).
Detector labels come from the key (the rule-based detector behind the T2 analysis).

Reports (report.md, summary.json, items.csv, human_labels_t2.csv):
  * per label (negated, polite, question-or-request, 3-way act): human-vs-detector agreement, Cohen kappa (item bootstrap CI),
    sensitivity, specificity and PPV of the detector with Wilson CIs, unweighted and re-weighted by w_total (the Horvitz-
    Thompson weight of the key: stratum size / drawn, over the elicitation inclusion probability; Kish-effective-n Wilson CIs);
    human-human agreement; the human rate per detector stratum.
  * corrected T2 estimate. P(negated | no negation word in the keywords) is re-estimated with human labels by the T2 code path
    (src/robust_t2_posterior.py --human-labels): the 600 messages of the elicitation sample get p_neg = the human label where
    one exists (both coders agree: 1 or 0; split: .5; single: that label) and otherwise the human-negated rate of the
    message's detector stratum among labelled messages (stratified sample, so the stratum mean is unbiased for the stratum).
    The estimate is printed next to the detector-based one, for human keywords and for POS-cap4, with the T2 message bootstrap
    CIs (the bootstrap does not include the sampling uncertainty of the Part 21 labels, which is shown through the stratum
    rates and the two sensitivity runs: split -> stratum rate; labelled messages only for the agreement table).
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import glob
import io
import json
import random
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agree_stats import cohen_kappa  # noqa: E402
from score_gold import kappa_boot, n_eff, wilson  # noqa: E402

STRATA = ["negated", "polite", "question_request", "plain_other"]
YN = {"yes", "no"}
ACTS = {"statement", "question", "request"}
T2 = ROOT / "src" / "robust_t2_posterior.py"


def read_csv(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_returns(paths, key):
    codings, problems = {}, []
    for p in paths:
        for r in read_csv(p):
            iid = r["item_id"]
            if str(r.get("practice", "0")) == "1" or iid.startswith("prac"):
                continue
            if iid not in key:
                problems.append(f"{Path(p).name}: unknown item {iid}"); continue
            k = key[iid]
            who = r["annotator"].strip()
            if who not in k["coders"].split("|"):
                problems.append(f"{Path(p).name}: {who} is not a coder of {iid}; dropped"); continue
            if who in k["blocked_people"].split("|"):
                problems.append(f"{Path(p).name}: {who} is blocked for {iid}; dropped"); continue
            lab = {}
            for f, ok in (("negated", YN), ("polite", YN), ("act", ACTS)):
                v = (r.get(f) or "").strip().lower() or None
                if v is not None and v != "unsure" and v not in ok:
                    problems.append(f"{Path(p).name}: {who} {iid} {f} {v!r} out of schema; treated as missing"); v = None
                lab[f] = None if v == "unsure" else v
            if (who, iid) in codings:
                problems.append(f"{Path(p).name}: duplicate coding {who}/{iid}; keeping the later row")
            codings[(who, iid)] = lab
    return codings, problems


def binar(f, v):
    """The binary label scored for field f from a coder's answer."""
    if v is None:
        return None
    return (v in ("question", "request")) if f == "act" else (v == "yes")


def human_label(votes: list, rule: str):
    """votes: labels (None removed). strict: two equal; single: one label allowed (sensitivity)."""
    if len(votes) == 2 and votes[0] == votes[1]:
        return votes[0]
    if rule == "plurality" and len(votes) == 1:
        return votes[0]
    return None


def wstat(det: list, hum: list, w: list | None):
    """Agreement of a binary detector with a binary human reference (weights optional)."""
    n = len(det)
    if not n:
        return {"n": 0}
    W = w or [1.0] * n
    tot = sum(W)

    def part(c):
        return sum(wi for d, h, wi in zip(det, hum, W) if c(d, h))
    tp, fp, fn, tn = part(lambda d, h: d and h), part(lambda d, h: d and not h), part(lambda d, h: not d and h), part(lambda d, h: not d and not h)
    ne = n_eff(W) if w else n

    def r(a, b):
        return None if not b else round(a / b, 3)

    def ci(a, b, nb):          # Wilson on the (effective) size of the denominator
        return None if not b else wilson(a / b * nb, nb)
    npos, nneg = sum(hum), n - sum(hum)
    nd = sum(det)
    k = sum(d == h for d, h in zip(det, hum))
    out = {"n": n, "human_positive": int(npos), "detector_positive": int(nd), "agree": k, "acc": round(k / n, 3), "acc_ci": wilson(k, n),
           "kappa": cohen_kappa(list(det), list(hum)), "kappa_ci": kappa_boot(list(det), list(hum), seed=20261102),
           "sensitivity": r(tp, tp + fn), "sensitivity_ci": ci(tp, tp + fn, npos if not w else n_eff([wi for h, wi in zip(hum, W) if h]) if npos else 0),
           "specificity": r(tn, tn + fp), "specificity_ci": ci(tn, tn + fp, nneg if not w else n_eff([wi for h, wi in zip(hum, W) if not h]) if nneg else 0),
           "ppv": r(tp, tp + fp), "ppv_ci": ci(tp, tp + fp, nd if not w else n_eff([wi for d, wi in zip(det, W) if d]) if nd else 0),
           "human_prevalence": round((tp + fn) / tot, 3), "detector_prevalence": round((tp + fp) / tot, 3)}
    if w:
        out["acc"] = round((tp + tn) / tot, 3); out["acc_ci"] = wilson((tp + tn) / tot * ne, ne)
        out["n_eff"] = round(ne, 1)
    return out


def fmt(x):
    if x is None:
        return "n/a"
    return f"{100 * x:.0f}%"


def fmt_ci(m, k, ck):
    if not m.get("n") or m.get(k) is None:
        return "n/a"
    ci = m.get(ck)
    return f"{100 * m[k]:.0f}%" + (f" [{100 * ci[0]:.0f}, {100 * ci[1]:.0f}]" if ci else "")


def run_t2(labels_path: Path, out_dir: Path, boot: int):
    cmd = [sys.executable, str(T2), "--human-labels", str(labels_path), "--out-dir", str(out_dir), "--boot", str(boot)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode:
        raise RuntimeError("robust_t2_posterior.py failed:\n" + r.stderr[-2000:])
    return json.loads((out_dir / "summary.json").read_text())


def t2_row(summ, dim="polarity", chan="human"):
    return next(x for x in summ["table"] if x["dimension"] == dim and x["channel"] == chan)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "source_check_key.csv"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "source_check"))
    ap.add_argument("--no-t2", action="store_true", help="skip the corrected T2 run (about 1.5 min)")
    ap.add_argument("--t2-boot", type=int, default=1000)
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    key = {r["item_id"]: r for r in read_csv(a.key)}
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / "returns_source_check" / "labels_part21_*.csv")))
    if not paths:
        print("no return CSVs found (annotation/returns_source_check/labels_part21_*.csv)", file=sys.stderr)
        return 1
    codings, problems = load_returns(paths, key)
    by_item = defaultdict(list)
    for (who, iid), lab in codings.items():
        by_item[iid].append((who, lab))
    S = {"returns": [Path(p).name for p in paths], "annotators": sorted({w for w, _ in codings}), "problems": problems,
         "n_items_key": len(key), "codings_expected": 2 * len(key), "codings_received": len(codings)}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    DET = {"negated": lambda k: bool(int(k["detector_negated"])), "polite": lambda k: bool(int(k["detector_polite"])),
           "act": lambda k: k["detector_qr"] in ("question", "request")}
    LABELS = {"negated": "negated", "polite": "polite", "act": "question or request (vs statement)"}

    def votes(iid, f):
        return [l[f] for _, l in by_item.get(iid, []) if l[f] is not None]

    # ---- per label agreement
    S["labels"] = {}
    for f in ("negated", "polite", "act"):
        res = {}
        for rule in ("strict", "plurality"):
            ids = []
            for iid, k in key.items():
                vs = [binar(f, v) for v in votes(iid, f)]
                hl = human_label(vs, rule)
                if hl is not None:
                    ids.append((iid, hl))
            det = [DET[f](key[i]) for i, _ in ids]; hum = [h for _, h in ids]
            w = [float(key[i]["w_total"]) for i, _ in ids]
            res[rule] = {"unweighted": wstat(det, hum, None), "reweighted": wstat(det, hum, w),
                         "by_stratum": {s: wstat([DET[f](key[i]) for i, _ in ids if key[i]["stratum"] == s],
                                                 [h for i, h in ids if key[i]["stratum"] == s], None) for s in STRATA}}
        # coders: both coded, how many split / unsure
        two = [iid for iid in key if len(by_item.get(iid, [])) == 2]
        pr = [(binar(f, a_[1][f]), binar(f, b_[1][f])) for iid in two for a_, b_ in [sorted(by_item[iid], key=lambda x: x[0])]
              if a_[1][f] is not None and b_[1][f] is not None]
        res["human_human"] = {"n": len(pr), "agree": round(sum(x == y for x, y in pr) / len(pr), 3) if pr else None,
                              "agree_ci": wilson(sum(x == y for x, y in pr), len(pr)),
                              "kappa": cohen_kappa([x for x, _ in pr], [y for _, y in pr])}
        res["items_split"] = sum(1 for iid in key if len({binar(f, v) for v in votes(iid, f)}) > 1)
        res["items_unsure_or_missing"] = sum(1 for iid in key if len(votes(iid, f)) < 2)
        S["labels"][f] = res
    # 3-way act
    pairs3 = []
    for iid in key:
        v = votes(iid, "act")
        if len(v) == 2 and v[0] == v[1]:
            d = key[iid]["detector_qr"]
            pairs3.append((v[0], "statement" if d == "statement_or_other" else d))
    S["act_three_way"] = {"n": len(pairs3), "agree": sum(x == y for x, y in pairs3),
                          "kappa": cohen_kappa([y for _, y in pairs3], [x for x, _ in pairs3]),
                          "confusion_rows_human_cols_detector": {h_: dict(Counter(d for x, d in pairs3 if x == h_))
                                                                 for h_ in sorted({x for x, _ in pairs3})}}
    # human negated rate per detector stratum (strict + single), for imputation
    rates = {}
    for s in STRATA:
        vals = []
        for iid, k in key.items():
            if k["stratum"] != s:
                continue
            vs = [v == "yes" for v in votes(iid, "negated")]
            if len(vs) == 2 and vs[0] == vs[1]:
                vals.append(float(vs[0]))
            elif len(vs) == 1:
                vals.append(float(vs[0]))
        rates[s] = {"n_labelled": len(vals), "human_negated_rate": round(sum(vals) / len(vals), 4) if vals else None}
    S["human_negated_rate_by_detector_stratum"] = rates
    # ---- labels file for the T2 code path (all 600 messages of the elicitation sample)
    frame = [json.loads(l) for l in open(ROOT / "annotation" / "elicitation_key.jsonl")]
    def stratum_of(x):
        d = x["detector_labels"]
        return ("negated" if d["polarity"] == "negated" else "polite" if d["politeness"] != "none" else
                "question_request" if d["speech_act"] in ("question", "request/command") else "plain_other")
    by_src = {k["source_item_id"]: (iid, k) for iid, k in key.items()}
    rows_t2 = {"primary": [], "split_to_stratum_rate": []}
    srcc = Counter()
    for x in frame:
        s = stratum_of(x)
        base = rates[s]["human_negated_rate"]
        hit = by_src.get(x["item_id"])
        p1 = p2 = base; src = "imputed_stratum_rate"
        if hit:
            vs = [v == "yes" for v in votes(hit[0], "negated")]
            if len(vs) == 2 and vs[0] == vs[1]:
                p1 = p2 = float(vs[0]); src = "human_agree"
            elif len(vs) == 2:
                p1, p2, src = 0.5, base, "human_split"
            elif len(vs) == 1:
                p1 = p2 = float(vs[0]); src = "human_single"
        srcc[src] += 1
        if base is None and p1 is None:
            continue
        rows_t2["primary"].append({"item_id": x["item_id"], "p_neg": p1, "source": src, "stratum": s})
        rows_t2["split_to_stratum_rate"].append({"item_id": x["item_id"], "p_neg": p2, "source": src, "stratum": s})
    S["t2_label_sources"] = dict(srcc)
    for name, rr in rows_t2.items():
        fn = out / ("human_labels_t2.csv" if name == "primary" else "human_labels_t2_split_to_rate.csv")
        with open(fn, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["item_id", "p_neg", "source", "stratum"]); w.writeheader(); w.writerows(rr)
    S["t2"] = None
    if not a.no_t2:
        base = json.loads((ROOT / "analysis" / "robust" / "t2_posterior" / "summary.json").read_text())
        S["t2"] = {"detector_based_committed": {c: {k: t2_row(base, "polarity", c)[k] for k in ("posterior_empirical", "posterior_empirical_lo",
                                                  "posterior_empirical_hi", "pi_frame", "d_loss", "silent_reversal_per_1000")} for c in ("human", "pos_cap4")}}
        for name, fn in (("human_corrected", "human_labels_t2.csv"), ("human_corrected_split_to_rate", "human_labels_t2_split_to_rate.csv")):
            sm = run_t2(out / fn, out / f"t2_{name}", a.t2_boot)
            S["t2"][name] = {c: {k: t2_row(sm, "polarity", c)[k] for k in ("posterior_empirical", "posterior_empirical_lo", "posterior_empirical_hi",
                                                                          "pi_frame", "d_loss", "silent_reversal_per_1000", "model_share_cue_given_nocue")}
                             for c in ("human", "pos_cap4")}
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")

    rows = []
    for iid, k in key.items():
        row = {c: k[c] for c in ("item_id", "source_item_id", "stratum", "w_total", "text")}
        for f in ("negated", "polite", "act"):
            row[f"coders_{f}"] = "|".join(f"{w}:{l[f] or ''}" for w, l in sorted(by_item.get(iid, [])))
        row |= {"detector_negated": k["detector_negated"], "detector_polite": k["detector_polite"], "detector_qr": k["detector_qr"]}
        rows.append(row)
    with open(out / "items.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    L = ["# Part 21: human check of the source-message labels (T2)\n",
         f"Generated by `src/score_source_check.py`. Returns: {len(paths)} file(s), {len(S['annotators'])} annotators; {S['codings_received']} of "
         f"{S['codings_expected']} expected codings. Key: `annotation/source_check_key.csv` ({len(key)} messages from the 600-message "
         "elicitation sample, oversampled on what the detector calls negated, polite or question/request).\n",
         "Human label = both coders agree (primary). The detector is scored against it: Cohen kappa (item-bootstrap CI), sensitivity, specificity and PPV "
         "(Wilson 95% CIs). \"Reweighted\" uses the key's Horvitz-Thompson weight (stratum size / drawn, over the elicitation inclusion probability) so the "
         "oversampled strata count as in the frame; its CIs use the Kish effective n.\n"]
    for f in ("negated", "polite", "act"):
        R = S["labels"][f]
        L += [f"## {LABELS[f]}\n", "| | n | human positive | detector positive | agree | kappa | sensitivity | specificity | PPV |", "|---|---|---|---|---|---|---|---|---|"]
        for nm, m in (("unweighted", R["strict"]["unweighted"]), ("reweighted", R["strict"]["reweighted"]),
                      ("unweighted, single coders included", R["plurality"]["unweighted"])):
            if not m.get("n"):
                L.append(f"| {nm} | 0 | | | | | | | |"); continue
            kap = f"{m['kappa']}" + (f" [{m['kappa_ci'][0]}, {m['kappa_ci'][1]}]" if m.get("kappa_ci") else "")
            L.append(f"| {nm} | {m['n']} | {m['human_positive']} | {m['detector_positive']} | {fmt_ci(m, 'acc', 'acc_ci')} | {kap} | "
                     f"{fmt_ci(m, 'sensitivity', 'sensitivity_ci')} | {fmt_ci(m, 'specificity', 'specificity_ci')} | {fmt_ci(m, 'ppv', 'ppv_ci')} |")
        hh = R["human_human"]
        L += ["", f"Coders: {R['items_split']} messages split, {R['items_unsure_or_missing']} with fewer than two labels. Human-human on the {hh['n']} "
                  f"messages both labelled: {fmt(hh['agree'])} agree, kappa {hh['kappa']}.", "",
              "By detector stratum (unweighted): | stratum | n | human positive | detector positive | agree |", "|---|---|---|---|---|"]
        for s in STRATA:
            m = R["strict"]["by_stratum"][s]
            if m.get("n"):
                L.append(f"| {s} | {m['n']} | {m['human_positive']} | {m['detector_positive']} | {fmt_ci(m, 'acc', 'acc_ci')} |")
        L.append("")
    t3 = S["act_three_way"]
    L += [f"3-way act (statement / question / request) where both coders agree: {t3['agree']}/{t3['n']} match the detector's question/request/statement, "
          f"kappa {t3['kappa']}. Rows = human, columns = detector: {t3['confusion_rows_human_cols_detector']}.\n",
          "## Human negated rate per detector stratum (used to impute the messages nobody labelled)\n", "| detector stratum | labelled | human negated rate |", "|---|---|---|"]
    for s, r in rates.items():
        L.append(f"| {s} | {r['n_labelled']} | {fmt(r['human_negated_rate'])} |")
    L += ["", f"T2 label sources over the 600 messages: {S['t2_label_sources']}.\n"]
    if S["t2"]:
        L += ["## Corrected T2: P(source message negated | no negation word in the keywords)\n",
              "Same code path as `analysis/robust/t2_posterior` (`src/robust_t2_posterior.py --human-labels`): Horvitz-Thompson over the elicitation frame, "
              "message bootstrap CIs. Only the polarity of the source message changes. Detector-based = the committed T2 numbers.\n",
              "| keyword channel | detector-based | human-corrected | human-corrected, splits -> stratum rate | silent reversals per 1,000 (detector -> corrected) |", "|---|---|---|---|---|"]
        T = S["t2"]
        for c in ("human", "pos_cap4"):
            def p(x):
                return f"{100 * x['posterior_empirical']:.1f}% [{100 * x['posterior_empirical_lo']:.1f}, {100 * x['posterior_empirical_hi']:.1f}]"
            L.append(f"| {c} | {p(T['detector_based_committed'][c])} | {p(T['human_corrected'][c])} | {p(T['human_corrected_split_to_rate'][c])} | "
                     f"{T['detector_based_committed'][c]['silent_reversal_per_1000']:.1f} -> {T['human_corrected'][c]['silent_reversal_per_1000']:.1f} |")
        L.append("")
    L += ["## Messages where the humans' negation label differs from the detector (both coders agree)\n", "| item | stratum | detector | humans | message |", "|---|---|---|---|---|"]
    for iid, k in key.items():
        v = [binar("negated", x) for x in votes(iid, "negated")]
        if len(v) == 2 and v[0] == v[1] and v[0] != DET["negated"](k):
            L.append(f"| {iid} | {k['stratum']} | {'negated' if DET['negated'](k) else 'not negated'} | {'negated' if v[0] else 'not negated'} | {k['text']} |")
    if problems:
        L += ["\n## Problems in returns\n"] + [f"- {p}" for p in problems]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


def self_check() -> int:
    """Simulated coders on the real key: they mostly follow the detector, but 25% of detector-negated messages are
    'not negated' for them and 8% of the others are negated. Checks loading, the blocked-coder rule, the agreement
    statistics and the corrected T2 run (small bootstrap) in a temporary directory."""
    keyp = ROOT / "annotation" / "source_check_key.csv"
    key = read_csv(keyp)
    rng = random.Random(3)
    ids = sorted({c for k in key for c in k["coders"].split("|")})
    assert len(key) == 200 and len(ids) == 20
    assert all(len(k["coders"].split("|")) == 2 and not set(k["coders"].split("|")) & set(filter(None, k["blocked_people"].split("|"))) for k in key)

    def make(neg_if_det, neg_if_not):
        rows = {x: [] for x in ids}
        for k in key:
            truth_neg = rng.random() < (neg_if_det if k["detector_negated"] == "1" else neg_if_not)
            for x in k["coders"].split("|"):
                neg = truth_neg if rng.random() < 0.95 else not truth_neg
                pol = (k["detector_polite"] == "1") if rng.random() < 0.9 else rng.random() < 0.5
                act = {"question": "question", "request": "request"}.get(k["detector_qr"], "statement") if rng.random() < 0.9 else "statement"
                un = rng.random() < 0.03
                rows[x].append({"item_id": k["item_id"], "annotator": x, "check_id": "part21", "practice": 0, "order": 1,
                                "negated": "unsure" if un else ("yes" if neg else "no"), "polite": "yes" if pol else "no", "act": act,
                                "note": "", "time_ms": 3000, "started_at": "x", "tool": "source_check_v1", "exported_at": "x"})
        for x in ids:
            rows[x].insert(0, {"item_id": "prac-1", "annotator": x, "check_id": "part21", "practice": 1, "order": 1, "negated": "no",
                               "polite": "yes", "act": "request", "note": "", "time_ms": 1, "started_at": "x", "tool": "source_check_v1",
                               "exported_at": "x"})
        return rows

    def write(rows, td):
        paths = []
        for x, rs in rows.items():
            p = Path(td) / f"labels_part21_{x}.csv"
            with open(p, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rs[0])); w.writeheader(); w.writerows(rs)
            paths.append(str(p))
        return paths
    with tempfile.TemporaryDirectory() as td:
        rows = make(0.75, 0.08)
        bad = key[0]; stranger = next(x for x in ids if x not in bad["coders"].split("|"))
        rows[stranger].append({**rows[stranger][1], "item_id": bad["item_id"], "annotator": stranger})
        paths = write(rows, td)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main([*paths, "--key", str(keyp), "--out", str(Path(td) / "out"), "--t2-boot", "20"])
        S = json.loads((Path(td) / "out" / "summary.json").read_text())
        hl = read_csv(Path(td) / "out" / "human_labels_t2.csv")
        assert (Path(td) / "out" / "report.md").exists() and (Path(td) / "out" / "items.csv").exists()
        # all-"not negated" humans: corrected posterior must collapse to 0
        rows0 = make(0.0, 0.0)
        for rs in rows0.values():
            for r in rs:
                if r["negated"] == "yes":
                    r["negated"] = "no"
        (Path(td) / "z").mkdir()
        p0 = write(rows0, Path(td) / "z")
        with contextlib.redirect_stdout(io.StringIO()):
            main([*p0, "--key", str(keyp), "--out", str(Path(td) / "out0"), "--t2-boot", "20"])
        S0 = json.loads((Path(td) / "out0" / "summary.json").read_text())
    assert rc == 0 and len(S["problems"]) == 1 and "not a coder" in S["problems"][0], S["problems"]
    assert S["codings_received"] == 400
    neg = S["labels"]["negated"]["strict"]["unweighted"]
    assert neg["n"] > 150 and 0.6 < neg["acc"] < 0.98 and neg["sensitivity"] is not None and neg["specificity"] is not None, neg
    assert S["labels"]["negated"]["strict"]["reweighted"]["n_eff"] < neg["n"], "reweighting must lower the effective n"
    assert S["labels"]["polite"]["strict"]["unweighted"]["n"] > 150 and S["labels"]["act"]["strict"]["unweighted"]["n"] > 150
    assert len(hl) == 600 and {r["source"] for r in hl} >= {"human_agree", "imputed_stratum_rate"}, Counter(r["source"] for r in hl)
    assert all(0 <= float(r["p_neg"]) <= 1 for r in hl)
    pc = S["t2"]["human_corrected"]["human"]["posterior_empirical"]; pd_ = S["t2"]["detector_based_committed"]["human"]["posterior_empirical"]
    assert 0 <= pc <= 1 and pd_ > 0, (pc, pd_)
    assert S0["t2"]["human_corrected"]["human"]["posterior_empirical"] == 0.0 and S0["t2"]["human_corrected"]["pos_cap4"]["posterior_empirical"] == 0.0, S0["t2"]
    print(f"self-check OK: detector negated kappa {neg['kappa']}, sens {neg['sensitivity']}, spec {neg['specificity']}; corrected T2 posterior "
          f"{100 * pc:.1f}% vs detector-based {100 * pd_:.1f}% (all-human-'no' check -> 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

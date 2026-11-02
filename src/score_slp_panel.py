"""Score the SLP expert panel (pure standard library; plan: expert_package/slp/ANALYSIS_PLAN.md).

    python3 src/score_slp_panel.py --self-check
    python3 src/score_slp_panel.py --returns expert_package/returns_slp [--part17 annotation/returns_repair_v2] [--out report.md]

Inputs
  returns   slp_rating_<ID>.csv from the HTML tool (rater_id, task, item_id, severity, block_flag, says_selected, acceptable, note, ...)
  key       expert_package/slp_key.csv (private)           item_id, arm, pair_id, judge_fail_types, judge_meaning_fail, part17_item_id
  counts    expert_package/judge_failure_counts.csv         existing judge failure patterns per arm (no new model calls)
  part17    optional directory of classmate repair_audit_v2_<ID>.csv files

With two raters this is an expert review, not a population estimate. Nothing here is a test of significance.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import math
import random
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TYPES = ["NEG", "ACT", "AGT", "CRT", "POL", "TIM", "ADD"]
TYPE_NAME = {"NEG": "negation dropped/added", "ACT": "question/statement/command changed", "AGT": "actor switched",
             "CRT": "certainty added/removed", "POL": "politeness added/removed", "TIM": "time changed", "ADD": "added content"}
A_LEVELS = ["yes", "partly", "no"]
B_LEVELS = ["yes", "edit", "no"]
CAVEAT = ("Two raters: this is an expert review of a fixed set of outputs, not a population estimate. Agreement statistics from "
          "n = 2 raters describe these two raters on these items and have no sampling distribution over raters; any interval shown "
          "resamples items only.")


# ------------------------------------------------------------------ io
def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_returns(d: Path):
    rows = []
    for p in sorted(Path(d).glob("slp_rating_*.csv")):
        rows += read_csv(p)
    by = defaultdict(lambda: defaultdict(dict))   # rater -> item -> fields
    for r in rows:
        by[r["rater_id"]][r["item_id"]] = r
    return by


# ------------------------------------------------------------------ statistics
def pct(a, b):
    return float("nan") if b == 0 else 100.0 * a / b


def cohen_kappa(x, y, levels, weights="none"):
    """Cohen's kappa for two label lists (None pairs dropped). weights 'linear' for ordinal scales."""
    pairs = [(a, b) for a, b in zip(x, y) if a in levels and b in levels]
    n = len(pairs)
    if n == 0:
        return float("nan"), 0
    k = len(levels); idx = {l: i for i, l in enumerate(levels)}
    def w(i, j):
        return 0.0 if i == j else (1.0 if weights == "none" else abs(i - j) / (k - 1))
    po = sum(1 - w(idx[a], idx[b]) for a, b in pairs) / n
    px = Counter(a for a, _ in pairs); py = Counter(b for _, b in pairs)
    pe = sum((px[l1] / n) * (py[l2] / n) * (1 - w(idx[l1], idx[l2])) for l1 in levels for l2 in levels)
    if abs(1 - pe) < 1e-12:
        return float("nan"), n   # no variation: kappa undefined
    return (po - pe) / (1 - pe), n


def raw_agree(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a and b]
    return pct(sum(a == b for a, b in pairs), len(pairs)), len(pairs)


def boot_ci(x, y, levels, weights="none", B=2000, seed=20261101):
    """Percentile CI for kappa, resampling ITEMS only (raters fixed)."""
    pairs = [(a, b) for a, b in zip(x, y) if a in levels and b in levels]
    if len(pairs) < 5:
        return (float("nan"), float("nan"))
    rng = random.Random(seed); vals = []
    for _ in range(B):
        s = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        k, _ = cohen_kappa([a for a, _ in s], [b for _, b in s], levels, weights)
        if not math.isnan(k): vals.append(k)
    if len(vals) < B // 2:
        return (float("nan"), float("nan"))
    vals.sort(); return (vals[int(.025 * len(vals))], vals[int(.975 * len(vals)) - 1])


def f(v, d=2):
    return "n/a" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{d}f}"


# ------------------------------------------------------------------ task 1
def task1(by):
    sev = {t: {} for t in TYPES}; flag = {t: {} for t in TYPES}
    for rater, items in by.items():
        for t in TYPES:
            r = items.get(t)
            if not r: continue
            if r.get("severity", "").strip().isdigit(): sev[t][rater] = int(r["severity"])
            if r.get("block_flag"): flag[t][rater] = r["block_flag"]
    out = {}
    for t in TYPES:
        v = list(sev[t].values()); fl = list(flag[t].values())
        out[t] = dict(mean=(sum(v) / len(v) if v else float("nan")), n=len(v), by_rater=dict(sev[t]),
                      block_or_flag=(pct(sum(x in ("block", "flag") for x in fl), len(fl)) if fl else float("nan")),
                      block=(pct(sum(x == "block" for x in fl), len(fl)) if fl else float("nan")), n_flag=len(fl))
    return out


def weights_from(t1, rater=None):
    """w_t = mean severity / 5 (or one rater's severity / 5). Missing -> NaN (type excluded from the rate and reported)."""
    w = {}
    for t in TYPES:
        if rater is None:
            m = t1[t]["mean"]
        else:
            m = t1[t]["by_rater"].get(rater, float("nan"))
        w[t] = m / 5.0
    return w


# ------------------------------------------------------------------ weighted failure rates
def load_counts(p):
    pop = defaultdict(lambda: defaultdict(Counter)); n = {}
    for r in read_csv(p):
        pop[r["population"]][r["arm"]][r["pattern"]] += int(r["count"]); n[(r["population"], r["arm"])] = int(r["n"])
    return pop, n


def weighted_rate(patterns: Counter, n: int, w: dict, drop=()):
    """Mean over outputs of the largest weight among the failure types the judge flagged (0 if none)."""
    tot = 0.0; missing = False
    for pat, c in patterns.items():
        ts = [t for t in (pat.split("|") if pat else []) if t not in drop]
        if not ts: continue
        ws = [w[t] for t in ts]
        if any(math.isnan(x) for x in ws): missing = True; continue
        tot += c * max(ws)
    return (100.0 * tot / n if n else float("nan")), missing


def unweighted(patterns: Counter, n: int, drop=()):
    k = sum(c for pat, c in patterns.items() if [t for t in (pat.split("|") if pat else []) if t not in drop])
    return pct(k, n)


def failure_table(t1, pop, nn, raters):
    rows = []
    wmean = weights_from(t1)
    wr = {r: weights_from(t1, r) for r in raters}
    for popname, arms in pop.items():
        for arm, pats in arms.items():
            n = nn[(popname, arm)]
            wr_all, miss = weighted_rate(pats, n, wmean)
            wr_six, _ = weighted_rate(pats, n, wmean, drop=("ADD",))
            per = [weighted_rate(pats, n, wr[r])[0] for r in raters]
            per = [x for x in per if not math.isnan(x)]
            rows.append(dict(population=popname, arm=arm, n=n, unweighted=unweighted(pats, n), unweighted_six=unweighted(pats, n, ("ADD",)),
                             weighted=wr_all, weighted_six=wr_six, lo=(min(per) if per else float("nan")),
                             hi=(max(per) if per else float("nan")), missing=miss))
    return rows


# ------------------------------------------------------------------ task 2
def task2(by, key):
    raters = sorted(by)
    rows = []
    for r in raters:
        for k in key:
            x = by[r].get(k["item_id"])
            if x and (x.get("says_selected") or x.get("acceptable")):
                rows.append(dict(rater=r, item=k["item_id"], arm=k["arm"], pair=k["pair_id"], a=x.get("says_selected", ""),
                                 b=x.get("acceptable", ""), jfail=int(k["judge_meaning_fail"]), jadd=int(k["judge_added_content"]),
                                 p17=k.get("part17_item_id", "")))
    return rows


def acceptability(rows, arms):
    out = {}
    for arm in arms:
        sub = [r for r in rows if r["arm"] == arm]
        a = Counter(r["a"] for r in sub if r["a"]); b = Counter(r["b"] for r in sub if r["b"])
        out[arm] = dict(n=len(sub), a=a, b=b,
                        a_yes=pct(a["yes"], sum(a.values())), b_yes=pct(b["yes"], sum(b.values())),
                        b_yes_or_edit=pct(b["yes"] + b["edit"], sum(b.values())))
    return out


def paired(rows, arm1, arm2, field, good):
    """Per-pair counts, pooled over raters: both good / only arm1 good / only arm2 good / neither."""
    idx = {(r["rater"], r["pair"], r["arm"]): r[field] for r in rows}
    c = Counter()
    for (rater, pair, arm), v in idx.items():
        if arm != arm1: continue
        o = idx.get((rater, pair, arm2))
        if o is None or not v or not o: continue
        g1, g2 = v in good, o in good
        c["both" if g1 and g2 else (f"only_{arm1}" if g1 else (f"only_{arm2}" if g2 else "neither"))] += 1
    return c


def agreement(rows, raters):
    if len(raters) != 2:
        return None
    r1, r2 = raters
    items = sorted({r["item"] for r in rows})
    m = {(r["rater"], r["item"]): r for r in rows}
    out = {}
    for field, levels in (("a", A_LEVELS), ("b", B_LEVELS)):
        x = [m.get((r1, i), {}).get(field) for i in items]; y = [m.get((r2, i), {}).get(field) for i in items]
        ra, n = raw_agree(x, y)
        k, _ = cohen_kappa(x, y, levels); kw, _ = cohen_kappa(x, y, levels, "linear")
        lo, hi = boot_ci(x, y, levels)
        out[field] = dict(n=n, raw=ra, kappa=k, kappa_w=kw, lo=lo, hi=hi)
    # binary collapses: a yes vs not-yes; b yes vs not-yes
    for field in ("a", "b"):
        x = [(m.get((r1, i), {}).get(field) or None) for i in items]; y = [(m.get((r2, i), {}).get(field) or None) for i in items]
        bx = ["y" if v == "yes" else ("n" if v else None) for v in x]; by_ = ["y" if v == "yes" else ("n" if v else None) for v in y]
        k, n = cohen_kappa(bx, by_, ["y", "n"])
        out[field]["kappa_bin"] = k
    return out


def vs_judge(rows, raters):
    out = {}
    for r in raters + ["both agree"]:
        pairs = []
        if r == "both agree":
            by_item = defaultdict(dict)
            for x in rows: by_item[x["item"]][x["rater"]] = x
            for it, d in by_item.items():
                if len(d) == len(raters) and len({v["a"] for v in d.values()}) == 1 and next(iter(d.values()))["a"]:
                    v = next(iter(d.values())); pairs.append(("yes" if v["a"] == "yes" else "notyes", "pass" if v["jfail"] == 0 else "fail"))
        else:
            for x in rows:
                if x["rater"] == r and x["a"]:
                    pairs.append(("yes" if x["a"] == "yes" else "notyes", "pass" if x["jfail"] == 0 else "fail"))
        n = len(pairs); ag = sum((a == "yes") == (b == "pass") for a, b in pairs)
        k, _ = cohen_kappa([("p" if a == "yes" else "n") for a, _ in pairs], [("p" if b == "pass" else "n") for _, b in pairs], ["p", "n"])
        tab = Counter(pairs)
        out[r] = dict(n=n, raw=pct(ag, n), kappa=k, table=tab)
    return out


def load_part17(d: Path):
    by = defaultdict(lambda: defaultdict(list))   # item -> field -> list
    for p in sorted(Path(d).glob("repair_audit_v2_*.csv")):
        for r in read_csv(p):
            if r.get("practice") == "1": continue
            for fld, col in (("quality", "a_quality"), ("contract", "b_contract")):
                if r.get(col): by[r["item_id"]][fld].append(r[col])
    return by


def majority(vals):
    c = Counter(vals).most_common()
    return c[0][0] if c and (len(c) == 1 or c[0][1] > c[1][1]) else None


def vs_part17(rows, p17):
    out = {}
    pairs_a, pairs_b = [], []
    for x in rows:
        if not x["p17"] or x["p17"] not in p17: continue
        c = p17[x["p17"]]
        mc = majority(c["contract"]); mq = majority(c["quality"])
        if mc and x["a"]: pairs_a.append((x["a"], mc))
        if mq and x["b"]: pairs_b.append((x["b"], {"yes": "yes", "minor": "edit", "no": "no"}.get(mq)))
    for name, pr, lv in (("says-what-selected vs classmate contract", pairs_a, A_LEVELS), ("acceptable vs classmate usable", pairs_b, B_LEVELS)):
        k, n = cohen_kappa([a for a, _ in pr], [b for _, b in pr], lv)
        out[name] = dict(n=len(pr), raw=pct(sum(a == b for a, b in pr), len(pr)), kappa=k)
    return out


# ------------------------------------------------------------------ report
def report(returns, key, counts, part17=None):
    by = load_returns(returns); raters = sorted(by)
    L = ["# SLP expert panel: scored report", "", CAVEAT, "", f"Raters with returns: {', '.join(raters) or 'none'}.", ""]
    if not raters:
        return "\n".join(L + ["No returns found."])
    t1 = task1(by)
    L += ["## Task 1: severity by type (mean of raters; 1 trivial to 5 critical)", "",
          "| type | mean severity | by rater | weight w = mean/5 | % block or flag | % block |", "|---|---|---|---|---|---|"]
    for t in TYPES:
        r = t1[t]
        L.append(f"| {TYPE_NAME[t]} | {f(r['mean'])} (n={r['n']}) | {', '.join(f'{k}: {v}' for k, v in sorted(r['by_rater'].items()))} | "
                 f"{f(r['mean'] / 5)} | {f(r['block_or_flag'], 0)} | {f(r['block'], 0)} |")
    rows = task2(by, key)
    pop, nn = load_counts(counts)
    L += ["", "## Clinically weighted failure rate (existing judge failures x SLP weights)", "",
          "Per output: the largest weight among the judge-flagged failure types (0 if none). 'range' is the weighted rate under each "
          "rater's own severities (min to max); it is a sensitivity range, not a confidence interval. Two populations; compare arms "
          "only within a population.", "",
          "| population | arm | n | unweighted any-failure % | clinically weighted % | range over raters | weighted % without added content | unweighted % without added content |",
          "|---|---|---|---|---|---|---|---|"]
    for r in failure_table(t1, pop, nn, raters):
        L.append(f"| {r['population']} | {r['arm']} | {r['n']} | {f(r['unweighted'], 1)} | {f(r['weighted'], 1)}{' (some weights missing)' if r['missing'] else ''} | "
                 f"{f(r['lo'], 1)} to {f(r['hi'], 1)} | {f(r['weighted_six'], 1)} | {f(r['unweighted_six'], 1)} |")
    arms = ["guard_repair", "guard_original", "chip", "word"]
    acc = acceptability(rows, arms)
    L += ["", "## Task 2: SLP acceptability by arm (both raters pooled; counts are rater-judgments)", "",
          "| arm | rated | (a) yes / partly / no | (b) yes / edit / no | % (a) yes | % (b) yes | % (b) yes or edit |", "|---|---|---|---|---|---|---|"]
    for a in arms:
        r = acc[a]
        L.append(f"| {a} | {r['n']} | {r['a']['yes']} / {r['a']['partly']} / {r['a']['no']} | {r['b']['yes']} / {r['b']['edit']} / {r['b']['no']} | "
                 f"{f(r['a_yes'], 0)} | {f(r['b_yes'], 0)} | {f(r['b_yes_or_edit'], 0)} |")
    L += ["", "Per rater, % (b) yes:", ""]
    for r in raters:
        sub = acceptability([x for x in rows if x["rater"] == r], arms)
        L.append(f"- {r}: " + "; ".join(f"{a} {f(sub[a]['b_yes'], 0)}% (n={sum(sub[a]['b'].values())})" for a in arms))
    L += ["", "### Paired comparisons on the same inputs (descriptive counts of rater-judgments; (b) good = yes)", ""]
    for a1, a2 in (("guard_repair", "guard_original"), ("chip", "word")):
        c = paired(rows, a1, a2, "b", {"yes"})
        L.append(f"- {a1} vs {a2}: both good {c['both']}; only {a1} {c['only_' + a1]}; only {a2} {c['only_' + a2]}; neither {c['neither']}")
    ag = agreement(rows, raters)
    L += ["", "## SLP to SLP agreement", ""]
    if ag is None:
        L.append(f"Agreement needs exactly two raters; found {len(raters)}.")
    else:
        L += ["| question | items | raw agreement % | Cohen kappa | linear-weighted kappa | kappa (yes vs not yes) | item-bootstrap 95% interval for kappa |", "|---|---|---|---|---|---|---|"]
        for fld, nm in (("a", "(a) says what selected"), ("b", "(b) acceptable to speak")):
            r = ag[fld]
            L.append(f"| {nm} | {r['n']} | {f(r['raw'], 0)} | {f(r['kappa'])} | {f(r['kappa_w'])} | {f(r['kappa_bin'])} | {f(r['lo'])} to {f(r['hi'])} |")
        s = {t: t1[t]["by_rater"] for t in TYPES}
        both = [t for t in TYPES if len(s[t]) == 2]
        if both:
            ex = sum(len(set(s[t].values())) == 1 for t in both); w1 = sum(abs(list(s[t].values())[0] - list(s[t].values())[1]) <= 1 for t in both)
            L.append(f"\nTask 1 severity: identical on {ex} of {len(both)} types; within one point on {w1} of {len(both)}.")
        L.append("\n" + CAVEAT)
    vj = vs_judge(rows, raters)
    L += ["", "## SLP vs the stored LLM judge", "",
          "Judge meaning-pass = no judge-flagged failure other than added content. SLP pass = (a) yes. Raw agreement and kappa, 2x2.", "",
          "| SLP | items | raw agreement % | kappa | SLP yes & judge pass | SLP yes & judge fail | SLP not-yes & judge pass | SLP not-yes & judge fail |", "|---|---|---|---|---|---|---|---|"]
    for r, d in vj.items():
        t = d["table"]
        L.append(f"| {r} | {d['n']} | {f(d['raw'], 0)} | {f(d['kappa'])} | {t[('yes', 'pass')]} | {t[('yes', 'fail')]} | {t[('notyes', 'pass')]} | {t[('notyes', 'fail')]} |")
    L += ["", "## SLP vs classmate Part 17 (overlapping items only)", ""]
    if part17 and Path(part17).exists() and any(Path(part17).glob("repair_audit_v2_*.csv")):
        for nm, d in vs_part17(rows, load_part17(Path(part17))).items():
            L.append(f"- {nm}: {d['n']} item-judgments, raw agreement {f(d['raw'], 0)}%, kappa {f(d['kappa'])}")
    else:
        L.append("Part 17 returns not found; skipped.")
    L += ["", "No significance tests are reported. " + CAVEAT]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ self-check
def self_check():
    # kappa: textbook 2x2 (a=20 yes/yes, 5 yes/no, 10 no/yes, 15 no/no) -> po .7, pe .5, kappa .4
    x = ["y"] * 25 + ["n"] * 25; y = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    k, n = cohen_kappa(x, y, ["y", "n"]); assert n == 50 and abs(k - 0.4) < 1e-9, k
    assert cohen_kappa(["yes"] * 4, ["yes"] * 4, A_LEVELS)[0] != cohen_kappa(["yes"] * 4, ["yes"] * 4, A_LEVELS)[0]   # NaN: no variation
    kp, _ = cohen_kappa(["yes", "partly", "no", "yes"], ["yes", "partly", "no", "yes"], A_LEVELS); assert abs(kp - 1) < 1e-9
    kw, _ = cohen_kappa(["yes", "no"], ["no", "yes"], A_LEVELS, "linear"); assert kw < 0
    # weighted rate: patterns '' (6), 'NEG' (2), 'NEG|ADD' (1), 'ADD' (1), n=10; w NEG=.8, ADD=.4
    w = {t: 0.2 for t in TYPES}; w["NEG"] = 0.8; w["ADD"] = 0.4
    wr, miss = weighted_rate(Counter({"": 6, "NEG": 2, "NEG|ADD": 1, "ADD": 1}), 10, w)
    assert not miss and abs(wr - 100 * (2 * .8 + .8 + .4) / 10) < 1e-9, wr          # 28.0
    wr6, _ = weighted_rate(Counter({"": 6, "NEG": 2, "NEG|ADD": 1, "ADD": 1}), 10, w, drop=("ADD",))
    assert abs(wr6 - 24.0) < 1e-9, wr6
    assert abs(unweighted(Counter({"": 6, "NEG": 2, "NEG|ADD": 1, "ADD": 1}), 10) - 40.0) < 1e-9
    assert majority(["yes", "yes", "no"]) == "yes" and majority(["yes", "no"]) is None
    # end to end on synthetic files
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); (td / "ret").mkdir()
        key = [dict(item_id=f"S{i:02d}", arm=a, pair_id=f"p{i % 5}", judge_fail_types="", judge_meaning_fail="0" if i % 2 else "1",
                    judge_added_content="0", part17_item_id=(f"rv-{i}" if i < 4 else "")) for i, a in
               zip(range(1, 9), ["guard_repair", "guard_original", "chip", "word"] * 2)]
        with open(td / "key.csv", "w", newline="") as fh:
            wcsv = csv.DictWriter(fh, fieldnames=list(key[0])); wcsv.writeheader(); wcsv.writerows(key)
        head = ["rater_id", "task", "item_id", "severity", "block_flag", "says_selected", "acceptable", "note", "saved_at", "tool"]
        sev1 = {"NEG": 5, "ACT": 4, "AGT": 4, "CRT": 3, "POL": 2, "TIM": 4, "ADD": 2}
        for rid, shift in (("SLP1", 0), ("SLP2", 1)):
            with open(td / "ret" / f"slp_rating_{rid}.csv", "w", newline="") as fh:
                wcsv = csv.writer(fh); wcsv.writerow(head)
                for t in TYPES:
                    wcsv.writerow([rid, 1, t, max(1, sev1[t] - (shift if t in ("CRT", "POL") else 0)), "block" if sev1[t] >= 4 else "flag", "", "", "", "", ""])
                for i, k_ in enumerate(key):
                    a = A_LEVELS[(i + (shift if i == 3 else 0)) % 3]
                    wcsv.writerow([rid, 2, k_["item_id"], "", "", a, B_LEVELS[(i) % 3], "note, x", "", ""])
        with open(td / "counts.csv", "w", newline="") as fh:
            wcsv = csv.writer(fh); wcsv.writerow(["arm", "population", "pattern", "count", "n"])
            for arm, pats in (("baseline", {"": 6, "NEG": 2, "ADD": 2}), ("guard", {"": 8, "ACT": 1, "ADD": 1})):
                for p_, c in pats.items(): wcsv.writerow([arm, "toy", p_, c, 10])
        (td / "p17").mkdir()
        with open(td / "p17" / "repair_audit_v2_P02.csv", "w", newline="") as fh:
            wcsv = csv.writer(fh); wcsv.writerow(["item_id", "annotator", "practice", "a_quality", "b_contract"])
            for i in range(1, 4): wcsv.writerow([f"rv-{i}", "P02", 0, "yes", "yes"])
        rep = report(td / "ret", read_csv(td / "key.csv"), td / "counts.csv", td / "p17")
        by = load_returns(td / "ret"); t1 = task1(by)
        assert abs(t1["NEG"]["mean"] - 5) < 1e-9 and abs(t1["CRT"]["mean"] - 2.5) < 1e-9
        pop, nn = load_counts(td / "counts.csv")
        ft = {r["arm"]: r for r in failure_table(t1, pop, nn, ["SLP1", "SLP2"])}
        assert abs(ft["baseline"]["weighted"] - 100 * (2 * 1.0 + 2 * (2.0 / 5)) / 10) < 1e-9, ft["baseline"]
        assert ft["baseline"]["lo"] <= ft["baseline"]["weighted"] <= ft["baseline"]["hi"] + 1e-9
        rows = task2(by, read_csv(td / "key.csv")); assert len(rows) == 16
        ag = agreement(rows, ["SLP1", "SLP2"]); assert ag["b"]["raw"] == 100.0 and abs(ag["b"]["kappa"] - 1) < 1e-9
        assert 0 < ag["a"]["raw"] < 100
        assert "SLP vs classmate Part 17" in rep and "Part 17 returns not found" not in rep
        assert "not a population estimate" in rep
    print("self-check passed")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--returns", default=str(ROOT / "expert_package/returns_slp"))
    ap.add_argument("--key", default=str(ROOT / "expert_package/slp_key.csv"))
    ap.add_argument("--counts", default=str(ROOT / "expert_package/judge_failure_counts.csv"))
    ap.add_argument("--part17", default=str(ROOT / "annotation/returns_repair_v2"))
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    txt = report(a.returns, read_csv(a.key), a.counts, a.part17)
    if a.out: Path(a.out).write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())

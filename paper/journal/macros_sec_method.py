"""Macros for the Method section (sections/s2.tex). Loaded by make_macros.py (register(ctx) -> functions).

Every value is read from a stored analysis/annotation file; the source path is recorded in macro_sources.json.
Keys here use the prefixes hw*, arb*, nd*, t9*, or*, orr*, nat*, hg*, p19*, p18* (new keys only; no existing key is redefined).
Part 10 strict-rule values come from paper/journal/part10_gate.json (written by part10_gate.py from stored labels).
"""
from __future__ import annotations
import json, re
from collections import defaultdict
import numpy as np
import pandas as pd


def register(ctx):
    put, ci, J, ROOT, macros, sources = ctx["put"], ctx["ci"], ctx["J"], ctx["ROOT"], ctx["macros"], ctx["sources"]

    def wilson(k, n, z=1.959964):
        if not n:
            return np.nan, np.nan
        ph = k / n; den = 1 + z * z / n
        c = (ph + z * z / (2 * n)) / den
        h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
        return max(0.0, c - h), min(1.0, c + h)

    def frac(key, k, n, src, wil=True):
        put(key + "K", k, src, "int"); put(key + "N", n, src, "int")
        if n:
            put(key, k / n, src)
            if wil:
                lo, hi = wilson(k, n); put(key + "Lo", lo, src + " (Wilson 95%)"); put(key + "Hi", hi, src + " (Wilson 95%)")

    # ------------------------------------------------------------ hw1 construction and judging
    def hw_build():
        p = "analysis/hw1/summary.json"; d = J(p)
        put("hwCand", d["n_candidates"], p, "int"); put("hwKept", d["n_kept"], p, "int")
        put("hwBootN", d["n_boot"], p, "int"); put("hwSeed", d["seed"], p, "s")
        wr = {json.loads(l)["writer_id"] for l in open(ROOT / "data/items/hw.jsonl")}
        put("hwWritersKept", len(wr), "data/items/hw.jsonl (distinct writer_id among kept families)", "int")
        c = J("runs/hw1/config.json"); put("hwRequests", c["n_requests"], "runs/hw1/config.json", "int")
        r = J("runs/hw1/judge_report.json"); q = "runs/hw1/judge_report.json"
        put("hwUnits", r["n_units"], q, "int")
        put("hwJJCrit", r["J1_vs_J2"]["critical"]["agree"], q); put("hwJJCritKappa", r["J1_vs_J2"]["critical"]["kappa"], q, "f3")
        put("hwJJAddedKappa", r["J1_vs_J2"]["added_content"]["kappa"], q, "f2")
        put("hwNeedArb", r["needs_arbiter"], q, "int")
        put("hwNeedArbShare", r["needs_arbiter"] / r["n_units"], q)

    def breadth_fams():
        mb = J("analysis/model_breadth/summary.json")
        fams = {re.match(r"[a-z]+", m).group(0) for m in mb["models"]}
        put("breadthFamilies", len(fams), "analysis/model_breadth/summary.json (distinct leading name of model ids)", "int")

    def wc_arbiter():
        h = J("analysis/r2c/headline.json"); put("wcArbRows", h["arbiter_resolved_rows"], "analysis/r2c/headline.json", "int")
        a = J("analysis/r2c/arbitration/agreement.json"); s = "analysis/r2c/arbitration/agreement.json"
        put("wcArbUnits", a["n_units"], s, "int")
        put("wcArbSidedJOne", a["arbiter_equals"]["J1"], s, "int"); put("wcArbSidedJTwo", a["arbiter_equals"]["J2"], s, "int")

    def nondeterminism():
        agree = defaultdict(lambda: [0, 0])
        for run in ["expB1", "expC1"]:
            gp = ROOT / f"runs/{run}/generations.jsonl"
            if not gp.exists():
                continue
            by = defaultdict(dict)
            for line in open(gp):
                r = json.loads(line)
                by[(run, r["model"], r["prompt_id"], r["input_text"], r["sample_idx"])][r.get("namespace")] = r["raw_text"].strip()
            for k, v in by.items():
                if "d1" in v and "d2" in v:
                    agree[(run, k[1])][0] += v["d1"] == v["d2"]; agree[(run, k[1])][1] += 1
        rates = {k: a / n for k, (a, n) in agree.items() if n}
        s = "runs/expB1,expC1 generations.jsonl d1 vs d2 (same request reissued)"
        api = [v for (run, m), v in rates.items() if m == "gpt-6.1-terra"]; loc = [v for (run, m), v in rates.items() if m != "gpt-6.1-terra"]
        put("ndApiMin", min(api), s); put("ndApiMax", max(api), s); put("ndLocalMin", min(loc), s); put("ndLocalMax", max(loc), s)

    def t9():
        p = "analysis/robust/t9_validator_replay/summary.json"; s = J(p)
        c = [s["raw"][k] for k in ("W-C r2c1", "hw1", "W-D r2d1")]
        put("t9Inputs", sum(x["cue_inputs"] for x in c), p, "int")
        put("t9Compat", sum(x["verdicts"].get("compatible", 0) for x in c), p, "int")
        put("t9Unknown", sum(x["verdicts"].get("unknown", 0) for x in c), p, "int")
        put("t9Conflicts", sum(len(x["conflicts"]) for x in c), p, "int")
        put("t9GenCalls", s["generation_calls"], p, "int")

    # ------------------------------------------------------------ oracle tests
    def oracle_authored():
        p = "analysis/oracle/injection_results.csv"; inj = pd.read_csv(ROOT / p)
        ide, mut = inj[inj.model == "identity"], inj[inj.model == "mutant"]
        frac("orIdFa", int((~ide.constraint_preserving.astype(bool)).sum()), len(ide), p + " identity (contract false alarm)")
        frac("orMut", int(mut.violation.astype(bool).sum()), len(mut), p + " scoped mutants detected as Violation")
        p = "analysis/oracle/challenge_results.csv"; chl = pd.read_csv(ROOT / p)
        new = chl[chl.role.isin(["control", "mutant"])]; mu, co = new[new.role == "mutant"], new[new.role == "control"]
        frac("orKeyMut", int((~mu.match_prod.astype(bool)).sum()), len(mu), p + " production rule")
        frac("orKeyCtl", int((~co.match_prod.astype(bool)).sum()), len(co), p + " production rule (false alarms)")
        frac("orKeyMutStrict", int((~mu.match_raw.astype(bool)).sum()), len(mu), p + " strict rule (no acceptance relaxation)")
        am = mu[mu.group == "acceptance"]
        frac("orKeyAccProd", int((~am.match_prod.astype(bool)).sum()), len(am), p + " acceptance group, production rule")
        put("orKeyGroups", new.group.nunique(), p, "int"); put("orKeyPerGroup", len(mu) / new.group.nunique(), p + " (mutants / groups)", "int")

    def oracle_real():
        p = "analysis/oracle_real/summary.json"; o = J(p); h = o["headline"]
        for k, n in (("judge", "J"), ("surface", "S"), ("overlap", "O")):
            frac(f"orr{n}Mut", h[k + "_mut"]["k"], h[k + "_mut"]["n"], p); frac(f"orr{n}Fa", h[k + "_fa"]["k"], h[k + "_fa"]["n"], p)
        put("orrSeed", o["seed"], p, "s"); put("orrNAll", o["n_mutants"], p, "int"); put("orrNBooster", o["booster_only"]["n_mut"], p, "int")
        put("orrUnresolved", o["n_unresolved_judge"], p, "int")

    def oracle_natural():
        p = "analysis/oracle_natural/summary.json"; n = J(p)
        for vn, tag in (("violation", "Viol"), ("preservation_failure", "Pres")):
            for scope, pre in (("pooled_heldout_sets", "natHo"), ("pooled_failure_sets", "natAll")):
                x = n[scope][vn]
                for m, mk in (("precision", "P"), ("recall", "R")):
                    ci(f"{pre}{tag}{mk}", x[m], x[m + "_ci"][0], x[m + "_ci"][1], p + f" {scope}")
                put(f"{pre}{tag}Pos", x["n_ref_pos"], p, "int")
        put("natHoUnitsViol", sum(n["sets"][k]["violation"]["n_units"] for k in ("new", "hw")), p, "int")

    # ------------------------------------------------------------ human gates (Parts 10, 12, 13; H7)
    def gates():
        p7 = "analysis/robust/t7_human_gate/summary.json"; t7 = J(p7)
        p10 = "paper/journal/part10_gate.json"; t10 = J(p10)
        stored = {"HSeven": ("main1", t7["main1_H7_A1A2"], p7), "PTen": ("new", t10, p10), "PTwelve": ("elic", t7["part12_elic"], p7),
                  "PThirteen": ("hw", t7["part13_hw"], p7)}
        tot = 0
        for tag, (run, g, src) in stored.items():
            sj = f"annotation/judge_validation_{run}.json"; sv = J(sj)["human"]
            put(f"hg{tag}Coders", len(sv["members"]), sj, "int")
            put(f"hg{tag}Sampled", g["items"], src, "int"); tot += g["items"]
            put(f"hg{tag}Test", g["test_items"], src, "int")
            cs = sv["judge"]["critical"]["sampled_test/final"]
            put(f"hg{tag}CritRZero", cs["kappa"], sj + " sampled_test/final (stored rule)", "f2")
            for dim, nm in (("critical", "Crit"), ("speech_act", "Act"), ("agent", "Agent"), ("added_content", "Added")):
                e = g["dims"][dim]["test/R1"]
                ci(f"hg{tag}{nm}", e["kappa"], e["ci"][0], e["ci"][1], src + f" {dim} test/R1", "f2")
            hh = g["dims"]["critical"].get("human_human_vs_judge_human")
            if hh and hh.get("human_human_kappa") is not None:
                put(f"hg{tag}HH", hh["human_human_kappa"], src + " critical human_human_vs_judge_human", "f2")
                put(f"hg{tag}JH", hh["judge_human_kappa"], src + " critical human_human_vs_judge_human", "f2")
        put("hgTotalSampled", tot, p7 + " + " + p10 + " (sum of sampled items)", "int")
        put("hgCritMin", min(g["dims"]["critical"]["test/R1"]["kappa"] for _, g, _ in stored.values()), p7 + " + " + p10 + " (lowest strict critical kappa)", "f2")
        put("hgCritLoMin", min(g["dims"]["critical"]["test/R1"]["ci"][0] for _, g, _ in stored.values()), p7 + " + " + p10 + " (lowest lower bound)", "f2")
        put("hgGate", 0.6, "analysis/oracle/report.md: PREREG kappa>=0.6 gate for human gold (DESIGN constant)", "f1")
        put("p17PerItem", 3, "annotation/COORDINATOR_STEPS.md 4b: --per-item 3 (DESIGN constant)", "int")

    # ------------------------------------------------------------ Part 19 and Part 18 design
    def part19():
        p = "analysis/arbiter_check/summary.json"; d = J(p)
        put("p19Items", d["n_items_key"], p, "int"); put("p19ArbItems", d["arbiter_items"], p, "int")
        put("p19CanYouItems", d["can_you"]["items"], p, "int"); put("p19People", len(d["annotators"]), p, "int")
        put("p19CodingsReceived", d["codings_received"], p, "int"); put("p19CodingsLabelled", d["codings_with_label"], p, "int")
        n_arb = d["human_vs_arbiter"]["per_coding"]["n"]; exp = d["arbiter_items"] * 2
        put("p19ArbLabelledN", n_arb, p, "int"); put("p19ArbExpected", exp, p + " (2 coders per unit by design)", "int")
        put("p19ArbUnlabelledShare", 1 - n_arb / exp, p + " (expected minus labelled; unsure or blank)")
        s = d["arbiter_sided_with"]
        put("p19SidedJOne", s["J1"], p, "int"); put("p19SidedJTwo", s["J2"], p, "int"); put("p19SidedNeither", s["neither"], p, "int")
        m = d["human_match_by_arbiter_side"]
        ci("p19MatchJOneSide", m["J1"]["arbiter_label"]["p"], *m["J1"]["arbiter_label"]["ci"], p)
        ci("p19MatchJTwoSide", m["J2"]["arbiter_label"]["p"], *m["J2"]["arbiter_label"]["ci"], p)
        hh = d["human_human"]["arbiter"]
        ci("p19HHAgree", hh["agree"]["p"], *hh["agree"]["ci"], p); put("p19HHKappa", hh["kappa"], p, "f2")
        put("p19HHItems", hh["items"], p, "int"); put("p19Split", d["human_vs_arbiter"]["items_with_split_coders"], p, "int")
        put("p19CanYouLabelled", d["can_you"]["codings_with_label"], p, "int")

    def part18_design():
        p = "analysis/intent_check/summary.json"; d = J(p)
        put("p18PerWriter", d["acceptability"]["all"]["yes"]["n"] / len(d["writers"]), p + " (items / writers)", "int")


    def example_pol():
        p = "analysis/hw1/examples.md"; t = (ROOT / p).read_text()
        sec = t.split("## polarity")[1].split("## ")[0]
        m = re.search(r"first of (\d+) qualifying families by hash", sec)
        if m: put("exPolQual", int(m.group(1)), p, "int")
        m = re.search(r"occur at ([\d.]+) \[([\d.]+), ([\d.]+)\]% of bare rows \(n=(\d+), (\d+) writers\).*?matches the target ([\d.]+) \[([\d.]+), ([\d.]+)\]% of the time \(n=(\d+)\)", sec, re.S)
        if m:
            g = m.groups()
            put("exPolWrong", float(g[0]) / 100, p); put("exPolWrongLo", float(g[1]) / 100, p); put("exPolWrongHi", float(g[2]) / 100, p)
            put("exPolBareN", int(g[3]), p, "int"); put("exPolWriters", int(g[4]), p, "int")
            put("exPolChip", float(g[5]) / 100, p); put("exPolChipLo", float(g[6]) / 100, p); put("exPolChipHi", float(g[7]) / 100, p)
            put("exPolChipN", int(g[8]), p, "int")

    def writers_range():
        p = "analysis/hw1/summary.json"; d = J(p)
        put("hwWrMin", min(d["writers_by_dim"].values()), p, "int"); put("hwWrMax", max(d["writers_by_dim"].values()), p, "int")

    def terra_kappa():
        p = "analysis/robust/t7_human_gate/summary.json"; g = J(p)["main1_H7_A1A2"]["dims"]["critical"]["by_model_R1"]["gpt-6.1-terra"]
        put("hgHSevenTerra", g["kappa"], p + " main1_H7 critical by_model_R1 gpt-6.1-terra", "f2"); put("hgHSevenTerraN", g["n"], p, "int")
        lo = min(v["kappa"] for v in J(p)["main1_H7_A1A2"]["dims"]["critical"]["by_model_R1"].values())
        put("hgHSevenModelMin", lo, p + " main1_H7 critical by_model_R1 (lowest model)", "f2")

    return [example_pol, writers_range, terra_kappa, hw_build, breadth_fams, wc_arbiter, nondeterminism, t9, oracle_authored, oracle_real, oracle_natural, gates, part19, part18_design]

"""Draw the items for the two expert-input packages and write the private keys.

    .venv/bin/python src/build_expert_package.py

Reads stored outputs only (0 generation calls, 0 judge calls). Deterministic: every draw ranks units by
sha256(SEED | stratum | unit id) and takes the first that qualifies, so re-running reproduces the draw.

Writes
  expert_package/slp_key.csv                  PRIVATE key: neutral id -> arm, source ids, judge labels, Part 17 id
  expert_package/slp_draw.json                PRIVATE draw record (rule, pool sizes, counts, task-1 picks)
  expert_package/judge_failure_counts.csv     existing judge failure patterns per arm (input to score_slp_panel.py)
  expert_package/_build/slp_items.json               items embedded in slp_rating.html (arm labels hidden)
  expert_package/_build/consultant_items.json        examples embedded in the consultant packet
  expert_package/consultant_key.csv           PRIVATE key for the consultant examples
Then run src/build_slp_tool.py and src/build_consultant_packet.py to render the HTML.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "expert_package"
SEED = "expert-panel-2026-11-01"
TYPES = ["NEG", "ACT", "AGT", "CRT", "POL", "TIM", "ADD"]   # failure / change types (shared with the scorer)


def rank(stratum: str, uid: str) -> str:
    return hashlib.sha256(f"{SEED}|{stratum}|{uid}".encode()).hexdigest()


def norm(s) -> str:
    return re.sub(r"\W+", " ", str(s).lower()).strip()


def truthy(v) -> bool:
    if v is None or (isinstance(v, float) and v != v): return False
    return bool(v is True or (not isinstance(v, str) and v == 1) or v == "yes" or v == "True")


# ---------------------------------------------------------------- failure types (declared in ANALYSIS_PLAN.md)
def fail_types(r) -> list[str]:
    """Change types the stored judge labels flag for one output."""
    dim = r["dimension"]
    miss = r["critical_match"] is False or r["critical_match"] == False  # noqa: E712 (numpy bool)
    t = set()
    if miss:
        t.add({"polarity": "NEG", "speech_act": "ACT", "agent": "AGT", "certainty": "CRT",
               "politeness": "POL", "time_quantity": "TIM"}[dim])
    if truthy(r.get("contra_polarity")): t.add("NEG")
    if truthy(r.get("contra_speech_act")): t.add("ACT")
    if truthy(r.get("contra_agent")): t.add("AGT")
    # an emphatic/hedge word counts as an addition only when the input did not carry a certainty cue (a [SURE] or
    # [MAYBE] chip echoed in the output is the supplied cue, not an addition)
    stance_added = (truthy(r.get("emphatic_added")) or truthy(r.get("hedge_added"))) and not truthy(r.get("in_input_certainty"))
    if truthy(r.get("contra_certainty")) or stance_added: t.add("CRT")
    if truthy(r.get("contra_politeness")) or truthy(r.get("politeness_added")): t.add("POL")
    if truthy(r.get("added_content")): t.add("ADD")
    return sorted(t, key=TYPES.index)


# ---------------------------------------------------------------- display helpers
GLOSS = {
    "[NOT]": "not (negative)", "[YES]": "yes (positive)", "[?]": "this is a question", "[TELL]": "this is a statement",
    "[ASK]": "this is a request", "[I]": "I (the speaker does it)", "[YOU]": "you (the listener does it)",
    "[THEY]": "someone else does it", "[WE]": "we do it together", "[MAYBE]": "unsure (maybe)",
    "[SURE]": "very sure", "[PLEASE]": "polite (please)", "[PLAIN]": "plain, no polite words",
    "[PAST]": "it already happened", "[NOW]": "it is happening now", "[LATER]": "it will happen later",
    "[WANT]": "want", "[MUST]": "must", "[REFUSE]": "refuse",
}
PLAIN_VALUE = {
    "negated": "a negative message (with 'not' or 'no')", "affirmative": "a positive message (no 'not')",
    "question": "a question", "statement": "a statement", "request/command": "a request or command",
    "offer/suggestion": "an offer or suggestion", "unclear/mixed": "unclear", "speaker": "the speaker (I)",
    "addressee": "the listener (you)", "third party": "someone else (they, he, she, it)", "we/joint": "we",
    "unspecified": "nobody in particular", "hedged/uncertain": "unsure ('maybe', 'I think')",
    "plain assertion": "plain, with no hedge", "strongly certain/emphatic": "very sure ('definitely', 'really')",
    "plain": "plain, with no polite words", "polite": "polite ('please', 'could you')",
    "past": "in the past", "now": "now", "later": "later",
}


def split_input(input_text: str) -> dict:
    s = str(input_text)
    if s.startswith("The user typed:"):
        return {"mode": "typed", "text": s[len("The user typed:"):].strip(), "chips": []}
    body = s[len("Keywords:"):].strip() if s.startswith("Keywords:") else s
    chips = re.findall(r"\[[A-Z?]+\]", body)
    return {"mode": "keywords", "text": body, "chips": [{"chip": c, "meaning": GLOSS.get(c, "")} for c in chips]}


# ---------------------------------------------------------------- load
def load():
    hw = pd.read_parquet(ROOT / "runs/hw1/scored.parquet")
    ct = pd.read_parquet(ROOT / "runs/hwctl1/scored.parquet")
    gw = pd.read_parquet(ROOT / "analysis/guard_wc/scored.parquet")
    m1 = pd.concat([pd.read_parquet(ROOT / f"runs/{r}/scored.parquet").assign(run=r) for r in ("main1", "r2c1", "pilot1")], ignore_index=True)
    ex = set(json.loads((ROOT / "analysis/chip_controls/summary.json").read_text())["excluded_families"])
    kept_fams = set(ct.family_id) - ex      # the 546 analysed families of analysis/chip_controls
    hw = hw[(hw.prompt_id == "P0") & hw.valid.astype(bool) & hw.family_id.isin(kept_fams)].copy()
    ct = ct[(ct.prompt_id == "P0") & ct.valid.astype(bool) & ct.family_id.isin(kept_fams)].copy()
    m1 = m1[(m1.prompt_id == "P0") & m1.valid.astype(bool)].copy()
    gw = gw.copy()
    gw["critical"] = gw["crit"]; gw["variant_value"] = gw["cv"]
    return hw, ct, gw, m1


def j_labels(df):
    """J1 added-content evidence by text_id (for the task-1 'added content' note)."""
    ev = {}
    for run in ("hw1", "hwctl1", "main1", "r2c1", "pilot1"):
        p = ROOT / f"runs/{run}/judgments.jsonl"
        if not p.exists(): continue
        for line in open(p):
            r = json.loads(line)
            if r.get("J1_added_evidence"): ev[r["text_id"]] = r["J1_added_evidence"]
    return ev


def part17_index():
    k = pd.read_csv(ROOT / "annotation/repair_audit_v2_key.csv")
    return {(norm(r.input_text), norm(r.text)): (r.item_id, r.arm) for r in k.itertuples()}


# ---------------------------------------------------------------- Task 2 draw
def draw_task2(hw, ct, gw):
    rec = {"seed": SEED}
    p17 = part17_index()
    # --- guard: strict failure at P0 repaired by G1 (changed, strict pass)
    key = ["model", "family_id", "variant", "channel"]
    P0 = gw[gw.prompt_id == "P0"].set_index(key); G1 = gw[gw.prompt_id == "G1"].set_index(key)
    j = P0.join(G1, lsuffix="_p", rsuffix="_g")
    rep = j[(j.strict_p == 0) & (j.strict_g == 1) & j.changed_g.astype(bool)].reset_index()
    rec["guard_pool_repairs"] = len(rep)
    rep["rk_ov"] = ""
    rep["p17_rep"] = [p17.get((norm(a), norm(b)), (None, None)) for a, b in zip(rep.input_text_g, rep.text_g)]
    rep["p17_orig"] = [p17.get((norm(a), norm(b)), (None, None)) for a, b in zip(rep.input_text_p, rep.text_p)]
    rep["ov"] = [x[0] is not None and x[1] == "repaired" for x in rep.p17_rep]
    rep["ov_orig"] = [x[0] is not None and x[1] == "original_failed" for x in rep.p17_orig]
    rep["uid"] = rep.model + "|" + rep.family_id + "|" + rep.variant + "|" + rep.channel
    rec["guard_pool_overlap_part17_repaired"] = int(rep.ov.sum())
    picked, fams = [], set()
    for stratum, sub in (("guard_overlap", rep[rep.ov]), ("guard_other", rep[~rep.ov])):
        sub = sub.assign(rk=[rank(stratum, u) for u in sub.uid]).sort_values("rk")
        n = 0
        for r in sub.itertuples():
            if r.family_id in fams: continue
            fams.add(r.family_id); picked.append((stratum, r)); n += 1
            if n == 10: break
        rec[f"{stratum}_drawn"] = n
    guard = pd.DataFrame([r._asdict() for _, r in picked]); guard["stratum"] = [s for s, _ in picked]
    # originals: 10 of the 20 inputs; those whose original also sits in Part 17 first, then hash rank
    guard["_o"] = [(0 if o else 1, rank("guard_orig", u)) for o, u in zip(guard.ov_orig, guard.uid)]
    orig_uids = set(guard.assign(_k=guard._o).sort_values("_k").uid.head(10))
    rec["guard_originals_with_part17_overlap"] = int(guard[guard.uid.isin(orig_uids)].ov_orig.sum())
    # --- chip vs plain word on the same (family, variant, model)
    k3 = ["family_id", "variant", "model"]
    chip = hw[hw.channel == "chip1"].set_index(k3); nl = ct[ct.channel == "nlcue"].set_index(k3)
    pj = chip.join(nl, lsuffix="_c", rsuffix="_n", how="inner").reset_index()
    pj = pj[pj.critical_c.notna() & pj.critical_n.notna()]
    rec["chip_word_pool_pairs"] = len(pj)
    pj["uid"] = pj.family_id + "|" + pj.variant + "|" + pj.model
    dims = sorted(pj.dimension_c.unique(), key=lambda d: rank("chipdim", d))
    alloc = {d: (2 if i < 4 else 1) for i, d in enumerate(dims)}
    rec["chip_word_dimension_allocation"] = alloc
    cw, fams2 = [], set()
    for d in dims:
        sub = pj[pj.dimension_c == d]; sub = sub.assign(rk=[rank("chipword|" + d, u) for u in sub.uid]).sort_values("rk")
        n = 0
        for r in sub.itertuples():
            if r.family_id in fams2: continue
            fams2.add(r.family_id); cw.append(r); n += 1
            if n == alloc[d]: break
    chipword = pd.DataFrame([r._asdict() for r in cw])
    items = []

    def add(arm, src_ids, input_text, text, labels_row, pair_id, extra=None):
        items.append(dict(arm=arm, input_text=input_text, text=text, pair_id=pair_id, src=src_ids,
                          types=fail_types(labels_row), **(extra or {})))
    for _, r in guard.iterrows():
        pid = r.uid
        rowp = {c[:-2]: r[c] for c in guard.columns if c.endswith("_p") and c[:-2] in
                ("dimension", "critical_match", "contra_polarity", "contra_speech_act", "contra_agent", "contra_certainty",
                 "contra_politeness", "emphatic_added", "hedge_added", "politeness_added", "added_content", "in_input_certainty")}
        rowg = {c[:-2]: r[c] for c in guard.columns if c.endswith("_g") and c[:-2] in rowp}
        add("guard_repair", f"guard_wc G1 {r.output_id_g}", r.input_text_g, r.text_g, rowg, pid,
            dict(p17=(r.p17_rep[0] if r.ov else "")))
        if pid in orig_uids:
            add("guard_original", f"guard_wc P0 {r.output_id_p}", r.input_text_p, r.text_p, rowp, pid,
                dict(p17=(r.p17_orig[0] if r.ov_orig else "")))
    for _, r in chipword.iterrows():
        cols = ("dimension", "critical_match", "contra_polarity", "contra_speech_act", "contra_agent", "contra_certainty",
                "contra_politeness", "emphatic_added", "hedge_added", "politeness_added", "added_content", "in_input_certainty")
        rc = {c: r[c + "_c"] for c in cols}; rn = {c: r[c + "_n"] for c in cols}
        pid = r.uid
        add("chip", f"hw1 chip1 {r.output_id_c}", r.input_text_c, r.text_c, rc, pid, dict(p17=""))
        add("word", f"hwctl1 nlcue {r.output_id_n}", r.input_text_n, r.text_n, rn, pid, dict(p17=""))
    # neutral ids: seeded permutation
    items.sort(key=lambda it: rank("neutral", it["arm"] + it["src"]))
    for i, it in enumerate(items, 1):
        it["id"] = f"S{i:02d}"
    rec["n_items"] = len(items); rec["by_arm"] = dict(Counter(it["arm"] for it in items))
    return items, rec


# ---------------------------------------------------------------- Task 1 draw
def draw_task1(hw, ct, m1, used_outputs, used_fams, ev):
    d = pd.concat([hw.assign(run="hw1"), ct.assign(run="hwctl1"), m1], ignore_index=True)
    d = d[d.cue_in_input.fillna(False).astype(bool) & d.channel.isin(["chip1", "chipall", "full", "nlcue"])]
    d = d[(d.critical_source == "agree") & ~d.output_id.isin(used_outputs) & ~d.family_id.isin(used_fams)]
    pol = d.dimension == "politeness"
    M = d.critical_match == False  # noqa: E712
    strata = {
        "NEG": [("negation dropped", d[(d.dimension == "polarity") & M & (d.variant_value == "negated") & (d.critical == "affirmative")]),
                ("negation added", d[(d.dimension == "polarity") & M & (d.variant_value == "affirmative") & (d.critical == "negated")])],
        "ACT": [("question became a statement", d[(d.dimension == "speech_act") & M & (d.variant_value == "question") & (d.critical == "statement")]),
                ("statement became a command", d[(d.dimension == "speech_act") & M & (d.variant_value == "statement") & (d.critical == "request/command")])],
        "AGT": [("actor switched", d[(d.dimension == "agent") & M & d.critical.isin(["speaker", "addressee", "third party", "we/joint"])])],
        "CRT": [("certainty added", d[(d.emphatic_added.fillna(False).astype(bool) | d.hedge_added.fillna(False).astype(bool))
                                      & ~d.in_input_certainty.fillna(False).astype(bool) & ~d.text.str.contains(r"\[")]),
                ("certainty removed", d[(d.dimension == "certainty") & M & (d.variant_value == "hedged/uncertain") & (d.critical == "plain assertion")])],
        "POL": [("politeness added", d[pol & M & (d.variant_value == "plain") & (d.critical == "polite")]),
                ("politeness removed", d[pol & M & (d.variant_value == "polite") & (d.critical == "plain")])],
        "TIM": [("time changed", d[(d.dimension == "time_quantity") & M & d.critical.isin(["past", "now", "later"])])],
        "ADD": [("content added", d[(d.added_content == "yes") & (d.critical_match == True) & ~d.politeness_added.fillna(False).astype(bool)  # noqa: E712
                                    & ~d.emphatic_added.fillna(False).astype(bool)
                                    & d.text_id.map(lambda t: len(ev.get(t, "").split()) >= 2)])],
    }
    picks, rec = [], {}
    for t in TYPES:
        chosen, fams = [], set()
        subs = strata[t]
        if len(subs) == 2:
            order = [(subs[0], 1), (subs[1], 1)]
        else:
            order = [(subs[0], 2)]
        for (label, pool), n in order:
            pool = pool.assign(rk=[rank(f"t1|{t}|{label}", o) for o in pool.output_id]).sort_values("rk")
            rec[f"{t}/{label}"] = len(pool)
            got = 0; dirs = set()
            for r in pool.itertuples():
                dkey = (r.variant_value, r.critical)
                if r.family_id in fams or (n > 1 and dkey in dirs and len(pool.groupby(["variant_value", "critical"])) > 1 and got == 1):
                    continue
                fams.add(r.family_id); dirs.add(dkey); got += 1
                chosen.append((label, r))
                if got == n: break
            if got < n:   # pool too small: fill from the other direction of the same type if any
                rec[f"{t}/{label}/short"] = n - got
        for label, r in chosen:
            parts = split_input(r.input_text)
            if t == "ADD":
                note = ("The sentence adds something the selection does not contain"
                        + (f" (for example: '{ev[r.text_id]}')." if r.text_id in ev else "."))
            elif t == "CRT" and label == "certainty added":
                note = "The selection did not say how sure the person is. The sentence adds a sure or unsure word."
            elif t == "POL" and label == "politeness added":
                note = "The selection used no polite words. The sentence adds polite words."
            else:
                note = (f"The selection means: {PLAIN_VALUE.get(r.variant_value, r.variant_value)}. "
                        f"The sentence says: {PLAIN_VALUE.get(r.critical, r.critical)}.")
            picks.append(dict(type=t, change=label, input=parts, text=r.text, note=note,
                              src=f"{r.run} {r.prompt_id} {r.output_id}", family=r.family_id))
    return picks, rec


# ---------------------------------------------------------------- judge failure counts (all arms)
def counts(hw, ct, gw):
    rows = []

    def tally(name, pop, df):
        df = df[df.critical.notna()] if "critical" in df else df
        pat = Counter(); n = 0
        for r in df.to_dict("records"):
            pat["|".join(fail_types(r))] += 1; n += 1
        for p, c in pat.items():
            rows.append(dict(arm=name, population=pop, pattern=p, count=c, n=n))
    for arm, prompt in (("baseline_P0", "P0"), ("guard_G1", "G1"), ("guard_G1s", "G1s")):
        tally(arm, "W-C speech-act (1,872 targets)", gw[gw.prompt_id == prompt])
    for arm, df, ch in (("baseline_noncrit", hw, "noncrit"), ("baseline_bare", hw, "bare"), ("chip", hw, "chip1"),
                        ("word", ct, "nlcue"), ("irrelevant_chip", ct, "irrel")):
        tally(arm, "hw1 human-written pairs, six dimensions", df[df.channel == ch])
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- consultant examples
HEALTH = re.compile(r"\b(pain|painkiller|doctor|nurse|medic\w*|pill|hospital|sick|ill|fever|surgery|clinic|pharmacy|therap\w*|"
                    r"accident|hurt\w*|cancer|diagnos\w*|symptom\w*|injur\w*|allerg\w*|disab\w*|speech|talk|voice|communicat\w*|type)\b", re.I)


def draw_consultant(hw, ct, gw, m1, ev, used):
    bank = pd.concat([hw.assign(run="hw1"), ct.assign(run="hwctl1")], ignore_index=True)
    bank = bank[~bank.text.map(lambda s: bool(HEALTH.search(s))) & ~bank.input_text.map(lambda s: bool(HEALTH.search(s)))]
    bank = bank[(bank.critical_source == "agree") & bank.critical.notna()]
    bank = bank.assign(ftypes=[fail_types(r) for r in bank.to_dict("records")])
    cue = bank.cue_in_input.fillna(False).astype(bool)

    def first(df, stratum, k=1, excl=()):
        df = df[~df.family_id.isin(excl)]
        df = df.assign(rk=[rank("cons|" + stratum, o) for o in df.output_id]).sort_values("rk")
        out, fams = [], set()
        for r in df.itertuples():
            if r.family_id in fams: continue
            fams.add(r.family_id); out.append(r)
            if len(out) == k: break
        return out

    def card(r, **kw):
        return dict(input=split_input(r.input_text), text=r.text, src=f"{r.run} P0 {r.output_id}", family=r.family_id,
                    types=list(r.ftypes), **kw)
    ex = {}
    ok = bank[cue & bank.ftypes.map(lambda t: t == []) & bank.channel.isin(["chip1", "chipall"]) & bank.dimension.isin(["polarity", "speech_act", "agent", "time_quantity"])]
    R = {}
    R["R1_good"] = first(ok[ok.dimension.isin(["polarity", "speech_act"])], "R1good")
    R["R1_bad"] = first(bank[cue & bank.channel.eq("chip1") & bank.dimension.eq("polarity") & bank.ftypes.map(lambda t: "NEG" in t)], "R1bad")
    full = bank[bank.channel.eq("full")]
    R["R2_good"] = first(full[full.ftypes.map(lambda t: t == [])], "R2good")
    R["R2_bad"] = first(bank[bank.channel.isin(["chip1", "chipall"]) & cue & bank.politeness_added.fillna(False).astype(bool)
                             & bank.dimension.eq("politeness")], "R2bad")
    bare = bank[bank.channel.eq("bare") & bank.dimension.isin(["polarity", "speech_act"]) & ~cue]
    R["R3_a"] = first(bare[bare.dimension.eq("polarity")], "R3a")
    R["R3_b"] = first(bare[bare.dimension.eq("speech_act")], "R3b")
    # R4: same words, chip1 kept the value, chipall (more chips) broke it
    k = ["family_id", "variant", "model"]
    c1 = bank[bank.channel == "chip1"].set_index(k); ca = bank[bank.channel == "chipall"].set_index(k)
    jj = c1.join(ca, lsuffix="_1", rsuffix="_a", how="inner").reset_index()
    jj = jj[jj.ftypes_1.map(lambda t: t == []) & jj.ftypes_a.map(lambda t: len(t) > 0)]
    jj = jj.assign(oid=jj.output_id_1)
    R["R4"] = first(jj.rename(columns={"output_id_1": "output_id"}), "R4")
    chosen = {n: v for n, v in R.items()}
    # R5 examples from the frozen builder-defect audit
    wb = pd.read_csv(ROOT / "analysis/wb/contract_audit_diff.csv")
    wb = wb[wb.audit_status == "definite_conflict"].drop_duplicates("input_text")
    src = {}
    for line in open(ROOT / "data/items/wb.jsonl"):
        r = json.loads(line); src[r["family_id"]] = r["variants"]["A"]["source"]
    r5 = []
    for fam in ("wb-aactext-test-00113", "wb-aactext-train-01930"):
        r = wb[wb.family_id == fam].iloc[0]
        r5.append(dict(source=src[fam], input=split_input(r.input_text), text=r.text, src=f"wb1 {r.output_id}", family=fam))
    return chosen, r5, first, bank, cue, card


def main():
    OUT.mkdir(exist_ok=True); (OUT / "slp").mkdir(exist_ok=True); (OUT / "consultant").mkdir(exist_ok=True)
    hw, ct, gw, m1 = load()
    ev = j_labels(None)
    items, rec = draw_task2(hw, ct, gw)
    used_out = {it["src"].split()[-1] for it in items}
    used_fam = set()
    for it in items:
        pass
    # families of task-2 items (so task-1 examples are never the same items or the same families)
    fam_lookup = {}
    for df in (hw, ct, gw):
        for o, f in zip(df.output_id, df.family_id): fam_lookup[o] = f
    used_fam = {fam_lookup[o] for o in used_out if o in fam_lookup}
    t1, rec1 = draw_task1(hw, ct, m1, used_out, used_fam, ev)
    rec["task1_pool_sizes"] = rec1; rec["task1_n"] = len(t1)
    # ---- write keys
    import csv
    with open(OUT / "slp_key.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "arm", "pair_id", "source", "input_text", "text", "judge_fail_types", "judge_meaning_fail",
                    "judge_added_content", "part17_item_id"])
        for it in sorted(items, key=lambda x: x["id"]):
            w.writerow([it["id"], it["arm"], it["pair_id"], it["src"], it["input_text"], it["text"], "|".join(it["types"]),
                        int(any(t != "ADD" for t in it["types"])), int("ADD" in it["types"]), it.get("p17", "")])
    pub = [dict(id=it["id"], input=split_input(it["input_text"]), text=it["text"]) for it in sorted(items, key=lambda x: x["id"])]
    (OUT / "_build" / "slp_items.json").write_text(json.dumps(dict(task1=t1, task2=pub), indent=1, ensure_ascii=False))
    rec["task1_picks"] = [dict(type=p["type"], change=p["change"], src=p["src"], family=p["family"]) for p in t1]
    counts(hw, ct, gw).to_csv(OUT / "judge_failure_counts.csv", index=False)
    # ---- consultant
    chosen, r5, first, bank, cue, card = draw_consultant(hw, ct, gw, m1, ev, used_out)
    cons = {"requirements": {}, "r5": r5}
    for name, v in chosen.items():
        if name == "R4":
            cons["requirements"][name] = [dict(one_chip=dict(input=split_input(r.input_text_1), text=r.text_1),
                                               more_chips=dict(input=split_input(r.input_text_a), text=r.text_a),
                                               src=f"hw1 P0 {r.output_id} / {r.output_id_a}", family=r.family_id,
                                               types=list(r.ftypes_a)) for r in v]
        else:
            cons["requirements"][name] = [card(r) for r in v]
    # 10 example outputs: 3 good, 4 bad (distinct types), 3 repaired (first try + repair)
    excl_fam = {c["family"] for v in cons["requirements"].values() for c in v} | {x["family"] for x in r5}
    good_pool = bank[cue & bank.ftypes.map(lambda t: t == []) & bank.channel.isin(["chip1", "chipall", "nlcue"])]
    goods = first(good_pool, "ex_good", 3, excl_fam)
    bads = []
    for t, dim in (("NEG", "polarity"), ("ACT", "speech_act"), ("POL", "politeness"), ("ADD", None)):
        pool = bank[cue & bank.ftypes.map(lambda x, t=t: t in x) & (bank.dimension.eq(dim) if dim else True)]
        if t == "ADD": pool = pool[pool.ftypes.map(lambda x: x == ["ADD"])]
        bads += first(pool, "ex_bad_" + t, 1, excl_fam | {b.family_id for b in bads})
    # repaired: guard repairs, the first try and the repaired sentence both shown
    key = ["model", "family_id", "variant", "channel"]
    P0 = gw[gw.prompt_id == "P0"].set_index(key); G1 = gw[gw.prompt_id == "G1"].set_index(key)
    j = P0.join(G1, lsuffix="_p", rsuffix="_g")
    rep = j[(j.strict_p == 0) & (j.strict_g == 1) & j.changed_g.astype(bool)].reset_index()
    rep = rep[~rep.text_g.map(lambda s: bool(HEALTH.search(s))) & ~rep.text_p.map(lambda s: bool(HEALTH.search(s)))]
    rep = rep.assign(rk=[rank("cons_rep", "|".join(map(str, r))) for r in rep[key].values.tolist()]).sort_values("rk")
    reps, fams = [], set(excl_fam)
    for r in rep.itertuples():
        if r.family_id in fams: continue
        fams.add(r.family_id); reps.append(r)
        if len(reps) == 3: break
    cards = []
    for r in goods: cards.append(card(r, kind="good"))
    for r in bads: cards.append(card(r, kind="bad"))
    for r in reps:
        cards.append(dict(input=split_input(r.input_text_g), text=r.text_g, first_try=r.text_p, kind="repaired",
                          src=f"guard_wc P0 {r.output_id_p} -> G1 {r.output_id_g}", family=r.family_id, types=[]))
    cards.sort(key=lambda c: rank("cons_order", c["src"]))
    for i, c in enumerate(cards, 1): c["id"] = f"E{i:02d}"
    cons["examples"] = cards
    (OUT / "_build" / "consultant_items.json").write_text(json.dumps(cons, indent=1, ensure_ascii=False))
    with open(OUT / "consultant_key.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "kind", "source", "family", "judge_fail_types"])
        for c in sorted(cards, key=lambda c: c["id"]):
            w.writerow([c["id"], c["kind"], c["src"], c["family"], "|".join(c["types"])])
        for name, v in cons["requirements"].items():
            for c in v: w.writerow([name, "requirement example", c["src"], c["family"], "|".join(c["types"])])
        for x in r5: w.writerow(["R5", "requirement example", x["src"], x["family"], "builder defect"])
    rec["consultant_examples"] = Counter(c["kind"] for c in cards)
    (OUT / "slp_draw.json").write_text(json.dumps(rec, indent=1, default=lambda o: dict(o) if isinstance(o, Counter) else str(o)))
    print(json.dumps(rec, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())

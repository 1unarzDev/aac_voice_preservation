"""Part 17: repair audit v2 (60 repaired + 60 unrepaired controls, NEW texts only, 3 raters per item).

0 generation, 0 judge calls. Built from the frozen eligible pools of Parts 4 and 11 (no new scoring).

Pools (30 repaired + 30 control from each):
  discovery  annotation/repair_audit_eligible.csv  (Part 4 pool, guard1). The Part 4 selection
             algorithm is re-run unchanged (hash order sha1(text_id + "repair-audit-2026"), per-model
             quota, family-distinct first pass, controls matched to the repaired picks' per-model
             cue/ambiguous mix) with quotas scaled to 30 per arm (8 per model; later passes relax).
  transfer   annotation/repair_audit_transfer_eligible.csv  (Part 11 pool, W-C guard). The frozen
             FREEZE.md rule: ascending SHA256 of the normalised text, distinct texts, first N. No model
             balancing, no design weights.
EXCLUDED before the draw: every normalised text that appeared in Part 4 or Part 11 (the 80 selected
items of the two keys); a text drawn once is never drawn again (across arms and pools). If a pool
cannot supply 30, the draw takes what exists and the shortfall is written to the summary.

Raters: P02 P07 P09 P10 P11 P14, 3 per item. Balanced incomplete block design: the 20 triples of
raters are each used once per stratum (arm x pool, 30 items) plus the 10 blocks of the 2-(6,3,2)
design, so every rater gets 15 items per stratum (60 in all) and every pair of raters shares the same
number of items (24 when the pools are full). Which item gets which triple is a seeded shuffle.

Added 2026-11-01 before any return (D-064): two comparison arms for the confound "controls never failed, so
repaired hard cases are compared with easy ones". 20 items per arm, 10 per pool, in the SAME frozen hash order.
  original_failed  the pre-repair P0 output of a repaired item (the guard flagged it and then repaired it).
                   Drawn from the already-drawn v2 repaired sources in hash_rank order, so every item is
                   paired with its repaired item (paired_source_id = that repaired item's source_id).
  strip_only       the G1s output (deterministic removal of an unsupplied "please", no model call) for the
                   same input. G1s equals the first pass unless a "please" was stripped, and often equals the
                   repair itself; a sentence cannot be shown twice, so this arm uses only inputs where the strip
                   changed the first pass AND differs from the guard's repair. Drawn paired-first (v2 repaired
                   sources in hash_rank order), then, to reach 10, the other eligible repaired units of the
                   pool in their frozen hash order (unpaired; paired_source_id blank).
  Excluded as for v2: any text of Parts 4/11, of the 120 v2 items, or already drawn here; a source whose
  candidate equals another arm's sentence (normalised) is skipped. Raters: the same 6, 3 per item,
  chosen by a seeded search (balanced load per arm and pool; overlap with the repaired item's raters
  penalised, so a source's original-failed item goes to the three raters who did not rate its repair
  where possible). The 120 existing rows, their ids and raters are not touched (the draw is re-run
  deterministically and asserted equal to the committed key when it exists).

Writes:
  annotation/repair_audit_v2_key.csv      private key (arm, pool, model, source ids, raters)
  annotation/repair_audit_v2_sample.json  counts, exclusions, shortfalls, load matrix
  annotation_package/stage4/repair_audit_v2_<ID>.html   one self-contained tool per rater (Part 4 tool,
                                           relabelled "Part 17"; items embedded; refuses another ID)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_repair_audit as mra  # noqa: E402
from explode import normalise  # noqa: E402

DISC_SALT = "repair-audit-2026"
ID_SALT = "repair-audit-v2-item-2026"
DESIGN_SEED = 20261102
OUT_DIR = ROOT / "annotation_package" / "stage4"
KEY = ROOT / "annotation" / "repair_audit_v2_key.csv"
SUMMARY = ROOT / "annotation" / "repair_audit_v2_sample.json"
STRATA = [(arm, pool) for pool in ("discovery", "transfer") for arm in ("repaired", "control")]


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()


def excluded_texts() -> dict[str, str]:
    """normalised text -> where it appeared (Part 4 and Part 11 selected items)."""
    ex = {}
    for part, f in (("Part 4", "repair_audit_key.csv"), ("Part 11", "repair_audit_transfer_key.csv")):
        for r in read_csv(ROOT / "annotation" / f):
            ex[normalise(r["text"])] = part
    return ex


# ------------------------------------------------------------------ discovery pool
def discovery_units(arm: str, ex: dict) -> dict:
    units, dropped = {}, 0
    for r in read_csv(ROOT / "annotation" / "repair_audit_eligible.csv"):
        if r["arm"] != arm:
            continue
        assert r["hash"] == sha1(r["text_id"] + DISC_SALT), "hash order differs from the Part 4 rule"
        if normalise(r["text"]) in ex:
            dropped += 1
            continue
        units[r["text_id"]] = {
            "text_id": r["text_id"], "text": r["text"], "input_text": r["input_text"],
            "models": set(r["models"].split("|")), "families": set(r["families"].split("|")),
            "dimensions": set(r["dimensions"].split("|")), "channels": set(r["channels"].split("|")),
            "group": r["channel_group"], "output_ids": r["output_ids"], "hash": r["hash"],
            "hash_rank": int(r["hash_rank"]), "n_occ": r["n_occurrences"]}
    return units, dropped


def draw_discovery(ex, n, per_model):
    rep, d1 = discovery_units("repaired", ex)
    ctl, d2 = discovery_units("control", ex)
    # a text may be repaired in one request and a control elsewhere: keep it only as repaired
    rep_norm = {normalise(u["text"]) for u in rep.values()}
    ctl = {k: u for k, u in ctl.items() if normalise(u["text"]) not in rep_norm}
    old = mra.PER_ARM, mra.PER_MODEL
    mra.PER_ARM, mra.PER_MODEL = n, per_model
    try:
        r_sel = mra.select(rep, DISC_SALT, distinct_text=True)
        gq = Counter((m, rep[t]["group"]) for t, m in r_sel)
        c_sel = mra.select(ctl, DISC_SALT, group_quota=dict(gq), distinct_text=True)
    finally:
        mra.PER_ARM, mra.PER_MODEL = old
    rows = {"repaired": [], "control": []}
    for arm, units, sel in (("repaired", rep, r_sel), ("control", ctl, c_sel)):
        for t, m in sel:
            u = units[t]
            rows[arm].append({
                "arm": arm, "pool": "discovery", "assigned_model": m, "source_id": t, "output_ids": u["output_ids"],
                "families": "|".join(sorted(u["families"])), "dimensions": "|".join(sorted(u["dimensions"])),
                "channels": "|".join(sorted(u["channels"])), "channel_group": u["group"],
                "hash_rank": u["hash_rank"], "hash": u["hash"], "input_text": u["input_text"], "text": u["text"],
                "eligible_after_exclusion": len(units)})
    return rows, {"repaired": len(rep), "control": len(ctl), "dropped_as_prior": {"repaired": d1, "control": d2}}


# ------------------------------------------------------------------ transfer pool
def draw_transfer(ex, n):
    rows = {}
    info = {"dropped_as_prior": {}}
    for arm in ("repaired", "control"):
        elig = [r for r in read_csv(ROOT / "annotation" / "repair_audit_transfer_eligible.csv") if r["arm"] == arm]
        elig.sort(key=lambda r: int(r["hash_rank"]))
        for a, b in zip(elig, elig[1:]):
            assert a["selection_hash"] <= b["selection_hash"], "frozen SHA256 order broken"
        keep = [r for r in elig if normalise(r["text"]) not in ex]
        info["dropped_as_prior"][arm] = len(elig) - len(keep)
        info[arm] = len(keep)
        rows[arm] = keep
    return rows, info


def transfer_rows(arm, cand, n, taken):
    out = []
    for r in cand:
        nt = normalise(r["text"])
        if nt in taken:
            continue
        taken.add(nt)
        out.append({
            "arm": arm, "pool": "transfer", "assigned_model": r["assigned_model"], "source_id": r["output_id"],
            "output_ids": r["output_id"], "families": r["family_id"] + "/" + r["variant"],
            "dimensions": r["dimensions"], "channels": r["channels"], "channel_group": "cue",
            "hash_rank": int(r["hash_rank"]), "hash": r["selection_hash"], "input_text": r["input_text"],
            "text": r["text"], "eligible_after_exclusion": len(cand)})
        if len(out) >= n:
            break
    return out


# ------------------------------------------------------------------ rater design
def design(raters):
    """Triples per stratum: all C(k,3) triples + a 2-(k,3,2)-style block set when k == 6."""
    triples = list(itertools.combinations(range(len(raters)), 3))
    assert len(raters) == 6 and len(triples) == 20
    best = None
    comp = {t: tuple(sorted(set(range(6)) - set(t))) for t in triples}
    pairs_ = []
    seen = set()
    for t in triples:
        if t not in seen:
            seen |= {t, comp[t]}; pairs_.append((t, comp[t]))
    for bits in range(2 ** len(pairs_)):
        blocks = [p[(bits >> i) & 1] for i, p in enumerate(pairs_)]
        pc = Counter(frozenset(x) for b in blocks for x in itertools.combinations(b, 2))
        load = Counter(i for b in blocks for i in b)
        score = (max(pc.values()) - min(pc.values()) if len(pc) == 15 else 99, max(load.values()) - min(load.values()))
        if best is None or score < best[0]:
            best = (score, blocks)
    assert best[0] == (0, 0), best[0]
    return triples, best[1]


def assign(items_by_stratum, raters):
    triples, extra = design(raters)
    rng = random.Random(DESIGN_SEED)
    for stratum, items in items_by_stratum.items():
        blocks = triples + extra
        order = list(range(len(blocks)))
        rng.shuffle(order)
        # items in frozen hash order; the k-th item takes the k-th shuffled block (cycled if the pool is short or long)
        for k, it in enumerate(items):
            it["raters"] = "|".join(raters[i] for i in blocks[order[k % len(blocks)]])


# ------------------------------------------------------------------ comparison arms (added before any return)
NEW_ARMS = ("original_failed", "strip_only")
ARM_PER_POOL = 10
ARM_SEED = 20261101
MAX_PER_RATER = 85
CUE = {"chip1", "chipall", "full"}


class Triads:
    """Original (P0), guard (G1) and strip-only (G1s) output for the same request, per pool."""

    def __init__(self):
        import pandas as pd
        import interventions as iv
        sc, pairs = iv.guard_frame(ROOT / "runs" / "guard1")
        k = ["base_key", "family_id", "variant", "channel"]
        m = pairs["G1"].merge(pairs["G1s"][k + ["text_G1s", "output_id_G1s", "valid_G1s", "strict_fail_G1s"]],
                              on=k, how="left")
        self.disc = m[m.valid & m.valid_G1 & m.valid_G1s.fillna(False).astype(bool) & m.changed_G1.astype(bool)]
        w = pd.read_parquet(ROOT / "analysis" / "guard_wc" / "scored.parquet")
        self.wc = w
        KEYC = ["model", "family_id", "variant", "channel"]
        self.p0 = w[w.prompt_id.eq("P0")].set_index(KEYC)
        self.g1s = w[w.prompt_id.eq("G1s")].set_index(KEYC)
        self.g1 = w[w.prompt_id.eq("G1")].set_index(KEYC)

    def occurrences(self, pool, source_id, model=None, loc=None):
        """List of dicts (p0/g1/g1s texts and ids) for a repaired source, preferred model first."""
        out = []
        if pool == "discovery":
            occ = self.disc[self.disc.text_id_G1 == source_id]
            for r in occ.itertuples(index=False):
                out.append({"model": r.model, "family": r.family_id, "dimension": r.dimension, "channel": r.channel,
                            "input_text": r.input_text, "g1": r.text_G1, "p0": r.text, "g1s": r.text_G1s,
                            "p0_id": r.output_id, "g1s_id": r.output_id_G1s,
                            "p0_fail": r.strict_fail, "g1s_fail": r.strict_fail_G1s})
            out.sort(key=lambda o: (o["model"] != model, o["p0_id"]))
        else:
            # output ids repeat across prompts, so the request is located by (model, family, variant, channel)
            kk = tuple(loc)
            g = self.g1.loc[kk]
            a, b = self.p0.loc[kk], self.g1s.loc[kk]
            assert g.output_id == source_id and a.input_text == b.input_text == g.input_text and bool(g.changed)
            out.append({"model": kk[0], "family": kk[1], "dimension": g.dimension, "channel": kk[3],
                        "input_text": g.input_text, "g1": g.text, "p0": a.text, "g1s": b.text,
                        "p0_id": a.output_id, "g1s_id": b.output_id,
                        "p0_fail": None if a.strict != a.strict else int(a.strict) == 0,
                        "g1s_fail": None if b.strict != b.strict else int(b.strict) == 0})
        return out


def _arm_row(arm, pool, o, which, rep, rank, hash_, n_elig):
    return {"arm": arm, "pool": pool, "assigned_model": o["model"], "source_id": o[which + "_id"],
            "output_ids": o[which + "_id"], "families": o["family"], "dimensions": o["dimension"],
            "channels": o["channel"], "channel_group": "cue" if o["channel"] in CUE else "ambiguous",
            "hash_rank": rank, "hash": hash_, "input_text": o["input_text"], "text": o[which],
            "paired_source_id": rep["source_id"] if rep else "", "paired_item_id": "",
            "p0_judge_strict_fail": o["p0_fail"], "g1s_judge_strict_fail": o["g1s_fail"],
            "eligible_after_exclusion": n_elig}


def draw_arms(by_stratum, ex, existing_norm, tri):
    """Return (rows, info). Walk orders are frozen; see the module docstring."""
    taken = set(existing_norm)
    rows, info = [], {}
    for pool in ("discovery", "transfer"):
        rep = sorted(by_stratum[("repaired", pool)], key=lambda r: r["hash_rank"])
        if pool == "transfer":
            for r in rep:       # families = "<family>/<variant>", channels = the one channel of the row
                fam, var = r["families"].split("/")
                r["loc"] = (r["assigned_model"], fam, var, r["channels"])
        rep_by_src = {r["source_id"]: r for r in rep}
        # ---- original_failed: paired, hash order of the already-drawn repaired items
        got, skipped = [], []
        for r in rep:
            if len(got) >= ARM_PER_POOL:
                break
            ok = None
            for o in tri.occurrences(pool, r["source_id"], r["assigned_model"], r.get("loc")):
                n0 = normalise(o["p0"])
                if n0 in ex or n0 in taken or n0 == normalise(r["text"]):
                    continue
                ok = o; break
            if ok is None:
                skipped.append(r["source_id"]); continue
            taken.add(normalise(ok["p0"]))
            got.append(_arm_row("original_failed", pool, ok, "p0", r, r["hash_rank"], r["hash"], len(rep)))
        rows += got
        info[f"{pool}/original_failed"] = {"drawn": len(got), "paired": len(got), "skipped_sources": skipped}
        # ---- strip_only: strip changed the first pass and differs from the repair; paired first
        if pool == "discovery":
            allrep = sorted(read_csv(ROOT / "annotation" / "repair_audit_eligible.csv"), key=lambda r: int(r["hash_rank"]))
            allrep = [{"source_id": r["text_id"], "hash_rank": int(r["hash_rank"]), "hash": r["hash"],
                       "assigned_model": r["assigned_model"]} for r in allrep if r["arm"] == "repaired"]
        else:
            allrep = sorted(read_csv(ROOT / "annotation" / "repair_audit_transfer_eligible.csv"),
                            key=lambda r: int(r["hash_rank"]))
            allrep = [{"source_id": r["output_id"], "hash_rank": int(r["hash_rank"]), "hash": r["selection_hash"],
                       "assigned_model": r["assigned_model"],
                       "loc": (r["assigned_model"], r["family_id"], r["variant"], r["channels"])}
                      for r in allrep if r["arm"] == "repaired"]
        order = rep + [r for r in allrep if r["source_id"] not in rep_by_src]
        got2, nopair_reason = [], Counter()
        for r in order:
            if len(got2) >= ARM_PER_POOL:
                break
            ok = None
            for o in tri.occurrences(pool, r["source_id"], r.get("assigned_model"), r.get("loc")):
                ng, n0 = normalise(o["g1s"]), normalise(o["p0"])
                if ng == n0:
                    nopair_reason["strip left the first pass unchanged"] += 1; continue
                if ng == normalise(o["g1"]):
                    nopair_reason["strip equals the repair (same sentence)"] += 1; continue
                if ng in ex or ng in taken:
                    nopair_reason["text already used"] += 1; continue
                ok = o; break
            if ok is None:
                continue
            taken.add(normalise(ok["g1s"]))
            rp = rep_by_src.get(r["source_id"])
            got2.append(_arm_row("strip_only", pool, ok, "g1s", rp, r["hash_rank"], r["hash"], len(order)))
        rows += got2
        info[f"{pool}/strip_only"] = {
            "drawn": len(got2), "paired_with_a_repaired_v2_item": sum(bool(x["paired_source_id"]) for x in got2),
            "candidates_walked": len(order), "rejected_during_walk": dict(nopair_reason)}
        # descriptive: how many of the pool's 30 repaired v2 items have a strip-only output that is the same sentence
        same = unch = 0
        for r in rep:
            o = tri.occurrences(pool, r["source_id"], r["assigned_model"], r.get("loc"))[0]
            same += normalise(o["g1s"]) == normalise(o["g1"]); unch += normalise(o["g1s"]) == normalise(o["p0"])
        info[f"{pool}/repaired_v2_items_vs_strip"] = {
            "n": len(rep), "strip_output_identical_to_repair": same, "strip_left_first_pass_unchanged": unch}
    return rows, info


def assign_arms(new_rows, key_rows, raters):
    """Seeded hill-climb over triples of raters for the new rows (see module docstring)."""
    triples = [tuple(t) for t in itertools.combinations(range(len(raters)), 3)]
    ridx = {r: i for i, r in enumerate(raters)}
    base = Counter(ridx[x] for r in key_rows for x in r["raters"].split("|"))
    T = {r["source_id"]: {ridx[x] for x in r["raters"].split("|")} for r in key_rows if r["arm"] == "repaired"}
    rng = random.Random(ARM_SEED)
    # start: complement of the repaired triple when paired, else random
    cur = []
    for r in new_rows:
        t = T.get(r["paired_source_id"])
        cur.append(tuple(sorted(set(range(6)) - t)) if t else rng.choice(triples))

    def cost(asg):
        c = 0
        strata = defaultdict(Counter)
        tot = Counter(base)
        for r, t in zip(new_rows, asg):
            for x in t:
                strata[(r["arm"], r["pool"])][x] += 1; strata[(r["arm"], "all")][x] += 1; tot[x] += 1
            pt = T.get(r["paired_source_id"])
            if pt:
                c += 10 * len(set(t) & pt)
        for s in strata.values():
            vals = [s[i] for i in range(6)]
            c += 100 * (max(vals) - min(vals))
        c += 200 * (max(tot.values()) - min(tot.values()))
        pc = Counter(frozenset(p) for t in asg for p in itertools.combinations(t, 2))
        vals = [pc[frozenset(p)] for p in itertools.combinations(range(6), 2)]
        c += max(vals) - min(vals)
        # the same source's original and strip items: avoid sharing raters
        byp = defaultdict(list)
        for r, t in zip(new_rows, asg):
            if r["paired_source_id"]:
                byp[r["paired_source_id"]].append(set(t))
        for ts in byp.values():
            if len(ts) == 2:
                c += 2 * len(ts[0] & ts[1])
        return c

    best = cost(cur)
    for _ in range(40000):
        i = rng.randrange(len(cur)); old = cur[i]
        cur[i] = rng.choice(triples)
        c = cost(cur)
        if c <= best:
            best = c
        else:
            cur[i] = old
    for r, t in zip(new_rows, cur):
        r["raters"] = "|".join(raters[i] for i in t)
    return best


# ------------------------------------------------------------------ html
GUARD_OLD = "function startFor(id) {\n  if (!id) { S = null; return; }\n"
GUARD_NEW = ("function startFor(id) {\n  if (!id) { S = null; return; }\n"
             "  if (id.trim().toUpperCase() !== ASSIGNED) {\n"
             "    S = null; renderProgress();\n"
             "    say(\"This file is for annotator \" + ASSIGNED + \". Ask the study coordinator for your own file.\");\n"
             "    return;\n  }\n  id = ASSIGNED;\n")


def render_rater_html(rid: str, items: list[dict]) -> str:
    html = (ROOT / "annotation_package" / "repair_audit.html").read_text()
    blob = json.dumps(items, ensure_ascii=False, indent=0).replace("</", "<\\/")
    new, n = re.subn(r"(/\*AUDIT_ITEMS_BEGIN\*/).*?(/\*AUDIT_ITEMS_END\*/)",
                     lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
    assert n == 1
    for old, rep, cnt in (("(Part 4)", "(Part 17)", 2),
                          ('const RUN = "repair_audit_v1";', f'const RUN = "repair_audit_v2_{rid}";\nconst ASSIGNED = "{rid}";', 1),
                          ('return "repairaudit:v1:" + id;', 'return "repairaudit:v2:" + id;', 1),
                          ('a.download = "repair_audit_" + S.annot', 'a.download = "repair_audit_v2_" + S.annot', 1),
                          (GUARD_OLD, GUARD_NEW, 1)):
        assert new.count(old) == cnt, (old, new.count(old))
        new = new.replace(old, rep)
    return new


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=60, help="items per arm (half from each pool)")
    ap.add_argument("--raters", default="P02,P07,P09,P10,P11,P14")
    ap.add_argument("--per-item", type=int, default=3)
    ap.add_argument("--no-arms", dest="arms", action="store_false",
                    help="draw only the original 120 items (the two comparison arms are added by default)")
    a = ap.parse_args()
    raters = a.raters.split(",")
    assert a.per_item == 3 and len(raters) == 6, "the balanced design is built for 6 raters x 3 per item"
    half = a.n // 2
    ex = excluded_texts()
    assert len(ex) == 80, len(ex)
    prior_key = list(read_csv(KEY)) if KEY.exists() else []

    disc, dinfo = draw_discovery(ex, half, per_model=-(-half // 4) + 0)   # 30 -> 8 per model
    # texts already drawn in the discovery pool must not appear again
    taken = {normalise(r["text"]) for arm in disc for r in disc[arm]}
    cand, tinfo = draw_transfer(ex, half)
    trans = {arm: transfer_rows(arm, cand[arm], half, taken) for arm in ("repaired", "control")}
    by_stratum = {(arm, pool): (disc if pool == "discovery" else trans)[arm] for arm, pool in STRATA}

    shortfalls = {f"{pool}/{arm}": half - len(rows) for (arm, pool), rows in by_stratum.items() if len(rows) < half}
    for rows in by_stratum.values():
        rows.sort(key=lambda r: r["hash_rank"])
    assign({f"{p}/{a_}": rows for (a_, p), rows in by_stratum.items()}, raters)

    key_rows = [r for rows in by_stratum.values() for r in rows]
    for r in key_rows:
        r["item_id"] = "rv-" + sha1(ID_SALT + r["pool"] + r["source_id"])[:6]
    ids = [r["item_id"] for r in key_rows]
    assert len(set(ids)) == len(ids)
    norm = [normalise(r["text"]) for r in key_rows]
    assert len(set(norm)) == len(norm), "duplicate sentence in v2"
    assert not set(norm) & set(ex), "v2 overlaps Parts 4/11"
    for r in key_rows:
        assert len(set(r["raters"].split("|"))) == 3

    cols = ["item_id", "arm", "pool", "assigned_model", "source_id", "output_ids", "families", "dimensions",
            "channels", "channel_group", "hash_rank", "hash", "raters", "input_text", "text", "eligible_after_exclusion",
            "paired_source_id", "paired_item_id", "p0_judge_strict_fail", "g1s_judge_strict_fail"]
    key_rows.sort(key=lambda r: (r["pool"], r["arm"], r["hash_rank"]))
    base_rows = list(key_rows)
    arms_info = None
    if a.arms:
        # ---- comparison arms (added before any return): appended after the 120 base rows
        new_rows, arms_info = draw_arms(by_stratum, set(ex), set(norm), Triads())
        arms_info["assignment_cost"] = assign_arms(new_rows, base_rows, raters)
        for r in new_rows:
            r["item_id"] = "rv-" + sha1(ID_SALT + r["arm"] + r["pool"] + r["source_id"])[:6]
        rep_item = {r["source_id"]: r["item_id"] for r in base_rows if r["arm"] == "repaired"}
        for r in new_rows:
            r["paired_item_id"] = rep_item.get(r["paired_source_id"], "")
        ids2 = [r["item_id"] for r in base_rows + new_rows]
        assert len(set(ids2)) == len(ids2), "item id collision"
        norm2 = [normalise(r["text"]) for r in base_rows + new_rows]
        assert len(set(norm2)) == len(norm2), "duplicate sentence after adding arms"
        assert not set(norm2) & set(ex)
        for r in new_rows:
            assert len(set(r["raters"].split("|"))) == 3
        for arm in NEW_ARMS:
            for pool in ("discovery", "transfer"):
                n_ = sum(r["arm"] == arm and r["pool"] == pool for r in new_rows)
                assert n_ == ARM_PER_POOL, (arm, pool, n_)
        new_rows.sort(key=lambda r: (r["arm"], r["pool"], r["hash_rank"]))
        key_rows = base_rows + new_rows
    if prior_key:
        old120 = [r for r in prior_key if r["arm"] in ("repaired", "control")]
        assert len(old120) == 120 and [{c: r[c] for c in cols[:16]} for r in old120] == \
            [{c: str(r[c]) for c in cols[:16]} for r in base_rows], "the 120 base items or their raters changed"
    with open(KEY, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, restval="", extrasaction="ignore"); w.writeheader(); w.writerows(key_rows)

    all_strata = STRATA + ([(ar, p) for ar in NEW_ARMS for p in ("discovery", "transfer")] if a.arms else [])
    load = {rid: {"items": 0, **{f"{p}/{ar}": 0 for ar, p in all_strata}} for rid in raters}
    pair = Counter()
    for r in key_rows:
        rs = r["raters"].split("|")
        for x in rs:
            load[x]["items"] += 1; load[x][f"{r['pool']}/{r['arm']}"] += 1
        for x, y in itertools.combinations(sorted(rs), 2):
            pair[f"{x}-{y}"] += 1
    summ = {
        "design": "see make_repair_audit_v2.py docstring", "n_per_arm_requested": a.n, "per_item": a.per_item,
        "raters": raters, "exclusion": {"normalised_texts_in_parts_4_11": len(ex)},
        "pool_sizes_after_exclusion": {"discovery": {k: dinfo[k] for k in ("repaired", "control")},
                                       "transfer": {k: tinfo[k] for k in ("repaired", "control")}},
        "dropped_as_prior": {"discovery": dinfo["dropped_as_prior"], "transfer": tinfo["dropped_as_prior"]},
        "selected": {f"{p}/{ar}": len(by_stratum[(ar, p)]) for ar, p in STRATA},
        "shortfalls": shortfalls or "none",
        "selected_by_model": {f"{p}/{ar}": dict(sorted(Counter(r["assigned_model"] for r in by_stratum[(ar, p)]).items()))
                              for ar, p in STRATA},
        "selected_by_channel_group": {f"{p}/{ar}": dict(Counter(r["channel_group"] for r in by_stratum[(ar, p)]))
                                      for ar, p in STRATA},
        "comparison_arms": arms_info if arms_info else "not drawn (--no-arms)",
        "ratings_total": sum(v["items"] for v in load.values()), "per_rater_load": load,
        "shared_items_per_rater_pair": dict(sorted(pair.items())),
    }
    assert max(v["items"] for v in load.values()) <= MAX_PER_RATER, "more than 85 items for a rater"
    SUMMARY.write_text(json.dumps(summ, indent=2) + "\n")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for rid in raters:
        mine = sorted((r for r in key_rows if rid in r["raters"].split("|")), key=lambda r: r["item_id"])
        items = [{"item_id": r["item_id"], "text": r["text"], "input": mra.visible_input(r["input_text"])} for r in mine]
        (OUT_DIR / f"repair_audit_v2_{rid}.html").write_text(render_rater_html(rid, items))
    print(json.dumps(summ, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

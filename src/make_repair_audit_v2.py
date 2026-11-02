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
    a = ap.parse_args()
    raters = a.raters.split(",")
    assert a.per_item == 3 and len(raters) == 6, "the balanced design is built for 6 raters x 3 per item"
    half = a.n // 2
    ex = excluded_texts()
    assert len(ex) == 80, len(ex)

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
            "channels", "channel_group", "hash_rank", "hash", "raters", "input_text", "text", "eligible_after_exclusion"]
    key_rows.sort(key=lambda r: (r["pool"], r["arm"], r["hash_rank"]))
    with open(KEY, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(key_rows)

    load = {rid: {"items": 0, **{f"{p}/{ar}": 0 for ar, p in STRATA}} for rid in raters}
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
        "ratings_total": sum(v["items"] for v in load.values()), "per_rater_load": load,
        "shared_items_per_rater_pair": dict(sorted(pair.items())),
    }
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

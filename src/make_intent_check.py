"""Part 18: writer intent check ("did it say what you meant?"). 0 generation, 0 judge calls.

Each writer P01-P20 sees 10 model outputs that were generated from their OWN kept pairs (run hw1,
prompt P0) and says which of their two versions (A or B) each output says, and whether they would
accept it as their message. This is writer-intent agreement. It is NOT validation by AAC users.

Pool: kept pairs in data/items/hw.jsonl (547) joined to runs/hw1/scored.parquet, prompt P0,
suggestion 0, valid output with text. P06: only P06's kept TIME pairs (P06's one speech-act pair,
hw-act-043, is excluded, D-058). Channels: `bare` (keywords only, the critical dimension is not
given) and `chip1` (keywords plus the one critical chip: the critical-cue channel; `chipall` and
`full` add the other chips and are not used).

Draw rule (declared; seed 20261102, one random.Random per writer seeded from seed + writer id):
  * 10 slots per writer: 5 bare + 5 chip1, 10 different pairs (no pair twice), no repeated sentence
    where avoidable.
  * Models: the writer's model order is a seeded shuffle of the 4 models, cycled over the 10 slots,
    so each model gets 2-3 slots and bare/chip1 get different extra models.
  * Variants (the pair side the output was generated from): bare slots A,B,A,B,A and chip1 slots
    B,A,B,A,B for even writers; reversed for odd writers. So every writer gets 5 from A and 5 from B.
    NOTE: in `bare` the input does not say which version it came from (A and B give identical
    keywords), so the "intended variant" of a bare item is only the drawn side; scoring reports
    bare separately.
  * Slots are filled in a seeded random order; each takes a candidate whose dimension has been used
    least so far for that writer, ties broken by the seeded rng. If a slot has no candidate, the
    variant constraint is relaxed, then the model constraint (recorded in the key as `relaxed`).

Writes:
  annotation_package/stage4/<ID>_intent.json   blind: the writer's own A and B sentences, the
                                               keywords + chips the model got, the output sentence
  annotation/intent_check_key.csv              private: intended variant, channel, model, judge verdict
  annotation/intent_check_sample.json          counts and the declared rule
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from make_repair_audit import visible_input  # noqa: E402

OUT_DIR = ROOT / "annotation_package" / "stage4"
KEY = ROOT / "annotation" / "intent_check_key.csv"
SUMMARY = ROOT / "annotation" / "intent_check_sample.json"
CHANNELS = ("bare", "chip1")
P06_EXCLUDED_FAMILIES = {"hw-act-043"}
TOOL = "intent_check_v1"


def fnv(s: str) -> int:
    """Same hash as the page's seedOf (FNV-1a over UTF-16 code units; IDs are ASCII)."""
    h = 2166136261
    for c in s:
        h ^= ord(c)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def owner_hash(wid: str) -> str:
    return format(fnv(wid.strip().upper() + "|intent"), "08x")


def kept_pairs() -> dict[str, dict]:
    items = {}
    for line in (ROOT / "data" / "items" / "hw.jsonl").read_text().splitlines():
        it = json.loads(line)
        items[it["family_id"]] = it
    assert len(items) == 547, len(items)
    return items


def writer_families(items: dict, wid: str) -> list[str]:
    fams = sorted(f for f, it in items.items() if it["writer_id"] == wid)
    if wid == "P06":
        fams = [f for f in fams if items[f]["dimension"] == "time_quantity" and f not in P06_EXCLUDED_FAMILIES]
    return fams


def draw_writer(wi: int, wid: str, fams: list[str], pool: pd.DataFrame, models: list[str], seed: int, n_per: int):
    rng = random.Random(f"{seed}|{wid}")
    perm = models[:]
    rng.shuffle(perm)
    seq = [perm[i % len(perm)] for i in range(2 * n_per)]
    flip = wi % 2
    slots = []
    for ci, ch in enumerate(CHANNELS):
        for i in range(n_per):
            slots.append({"channel": ch, "model": seq[ci * n_per + i],
                          "variant": "AB"[(i + ci + flip) % 2]})
    rng.shuffle(slots)
    own = pool[pool.family_id.isin(fams)]
    used_f, used_t, dim_n, picked = set(), set(), Counter(), []
    for s in slots:
        relaxed = []
        for stage in ("exact", "variant", "model"):
            c = own[(own.channel == s["channel"]) & ~own.family_id.isin(used_f)]
            if stage in ("exact", "variant"):
                c = c[c.model == s["model"]]
            if stage == "exact":
                c = c[c.variant == s["variant"]]
            if len(c) and stage != "exact":
                relaxed.append(stage)
            if len(c):
                break
        assert len(c), (wid, s)
        fresh = c[~c.text.isin(used_t)]
        c = fresh if len(fresh) else c
        low = min(dim_n[d] for d in c.dimension.unique())
        c = c[c.dimension.map(lambda d: dim_n[d] == low)].sort_values(["family_id", "variant", "model"])
        r = c.iloc[rng.randrange(len(c))]
        used_f.add(r.family_id); used_t.add(r.text); dim_n[r.dimension] += 1
        picked.append((r, "+".join(relaxed)))
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="hw1")
    ap.add_argument("--per-writer", type=int, default=10)
    ap.add_argument("--seed", type=int, default=20261102)
    ap.add_argument("--writers", default=",".join(f"P{i:02d}" for i in range(1, 21)))
    a = ap.parse_args()
    assert a.per_writer % 2 == 0
    n_per = a.per_writer // 2
    items = kept_pairs()
    s = pd.read_parquet(ROOT / "runs" / a.run / "scored.parquet")
    s = s[s.prompt_id.eq("P0") & s.suggestion_idx.eq(0) & s.channel.isin(CHANNELS) & s.family_id.isin(items)
          & s.valid.astype(bool) & s.parse_ok.astype(bool) & s.text.fillna("").str.strip().ne("")].copy()
    models = sorted(s.model.unique())
    key_rows, summ_w = [], {}
    for wi, wid in enumerate(a.writers.split(",")):
        fams = writer_families(items, wid)
        picked = draw_writer(wi, wid, fams, s, models, a.seed, n_per)
        rows = []
        for r, relaxed in picked:
            it = items[r.family_id]
            assert it["writer_id"] == wid
            iid = "ic-" + hashlib.sha1(f"intent-check-2026|{wid}|{r.output_id}|{r.family_id}|{r.variant}|{r.channel}".encode()).hexdigest()[:6]
            rows.append({
                "item_id": iid, "writer_id": wid, "family_id": r.family_id, "dimension": r.dimension,
                "intended_variant": r.variant, "channel": r.channel, "model": r.model, "prompt_id": r.prompt_id,
                "output_id": r.output_id, "text": r.text, "input_text": r.input_text,
                "version_A": it["variants"]["A"]["source"], "version_B": it["variants"]["B"]["source"],
                "intended_value": it["variants"][r.variant]["critical_value"],
                "other_value": it["variants"]["AB".replace(r.variant, "")]["critical_value"],
                "bare_input_identical_AB": int(r.channel == "bare"),
                "judge_chose": r.chose, "judge_critical": r.critical, "judge_critical_match": r.critical_match,
                "judge_critical_source": r.critical_source, "judge_committed": r.committed,
                "relaxed": relaxed})
        assert len({x["family_id"] for x in rows}) == len(rows) == a.per_writer
        assert len({x["item_id"] for x in rows}) == len(rows)
        key_rows += rows
        blind = [{"item_id": x["item_id"], "A": x["version_A"], "B": x["version_B"],
                  "input": visible_input(x["input_text"]), "text": x["text"]}
                 for x in sorted(rows, key=lambda x: x["item_id"])]
        doc = {"check_id": f"intent_{wid}", "tool": TOOL, "version": 1, "n_items": len(blind),
               "owner": owner_hash(wid), "items": blind}
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{wid}_intent.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        summ_w[wid] = {"pairs_available": len(fams), "by_channel": dict(Counter(x["channel"] for x in rows)),
                       "by_variant": dict(Counter(x["intended_variant"] for x in rows)),
                       "by_model": dict(sorted(Counter(x["model"] for x in rows).items())),
                       "by_dimension": dict(Counter(x["dimension"] for x in rows)),
                       "relaxed": sum(bool(x["relaxed"]) for x in rows)}
    assert len({k["item_id"] for k in key_rows}) == len(key_rows)
    with open(KEY, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(key_rows[0])); w.writeheader(); w.writerows(key_rows)
    tot = lambda f: dict(sorted(Counter(k[f] for k in key_rows).items()))  # noqa: E731
    summ = {"run": a.run, "seed": a.seed, "per_writer": a.per_writer, "n_items": len(key_rows),
            "rule": __doc__.split("Draw rule")[1].split("Writes:")[0].strip(),
            "totals": {f: tot(f) for f in ("channel", "intended_variant", "model", "dimension", "judge_chose")},
            "p06": "only P06's kept time pairs; hw-act-043 (speech act) excluded (D-058)",
            "per_writer": summ_w}
    SUMMARY.write_text(json.dumps(summ, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summ.items() if k not in ("rule", "per_writer")}, indent=1))
    print("slots relaxed:", sum(v["relaxed"] for v in summ_w.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

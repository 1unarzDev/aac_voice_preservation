"""Part 4 repair audit: freeze the hash-ordered sample and embed it in the offline tool.

0 generation, 0 judge calls.

Units (one per distinct text, text_id = explode.py's sha1 of the normalised text; each
text_id in guard1 belongs to exactly one visible input):
  repaired  G1 output text that differs from the P0 first pass of the same request
            (changed=True), primary families (act-10/act-16 quarantine excluded), any
            channel. Awkward or failed repairs are kept: no filtering on judge outcome.
  control   P0 first-pass text that the guard left unchanged in every occurrence and that
            the judge scored as a strict pass in every occurrence (cue channels:
            constraint-preserving and no politeness addition; bare/noncrit: no
            politeness addition, the only rule that applies there).

Selection (frozen): sort each arm's units by sha1(text_id + "repair-audit-2026") and walk
the order, accepting a unit while its model's quota is open (5 per model, 20 per arm) and,
in a first pass, while none of its families is already used in that arm. Controls also
match the repaired picks' per-model cue/ambiguous channel mix. Passes then relax the family
constraint, the channel mix, and finally the model quota, only if needed to reach 20.
Inclusion probabilities are estimated by re-running the identical algorithm under 4000
random salts (Monte Carlo; the realised sample uses the fixed salt).

Writes (private, never in the package):
  annotation/repair_audit_key.csv        selected 40 items, arm, provenance, pi, eligible counts
  annotation/repair_audit_eligible.csv   all eligible units with pi
  annotation/repair_audit_sample.json    summary counts
and embeds the blind items (item_id, sentence, visible input) in
annotation_package/repair_audit.html between the AUDIT_ITEMS markers.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SALT = "repair-audit-2026"
ID_SALT = "repair-audit-2026-item"
PER_MODEL, PER_ARM = 5, 20
MC_REPS = 4000
CUE = {"chip1", "chipall", "full"}
CHIP_MEANING = {
    "[NOT]": "negation", "[YES]": "affirmative (not negated)", "[?]": "a question",
    "[ASK]": "a request to the listener", "[REFUSE]": "declining", "[TELL]": "a plain statement",
    "[MAYBE]": "uncertain", "[SURE]": "certain", "[MUST]": "obligation", "[WANT]": "desire",
    "[I]": "I do it", "[YOU]": "the listener does it", "[WE]": "we do it",
    "[THEY]": "someone else does it", "[PAST]": "past time", "[NOW]": "present time",
    "[LATER]": "future time", "[PLEASE]": "polite", "[PLAIN]": "no added politeness",
}
HTML = ROOT / "annotation_package" / "repair_audit.html"
KEY = ROOT / "annotation" / "repair_audit_key.csv"
ELIG = ROOT / "annotation" / "repair_audit_eligible.csv"
SUMMARY = ROOT / "annotation" / "repair_audit_sample.json"


def h(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def visible_input(input_text: str) -> dict:
    if input_text.startswith("The user typed:"):
        return {"kind": "typed", "typed": input_text.split(":", 1)[1].strip()}
    assert input_text.startswith("Keywords:"), input_text
    body = input_text.split(":", 1)[1]
    chips = re.findall(r"\[[^\]]+\]", body)
    words = re.sub(r"\[[^\]]+\]", " ", body).split()
    out = []
    for c in chips:
        m = CHIP_MEANING.get(c) or (f"exactly {c[1:-1]}" if re.fullmatch(r"\[\d+\]", c) else None)
        assert m, c
        out.append({"chip": c, "meaning": m})
    return {"kind": "keywords", "words": " ".join(words), "chips": out}


def build_pools():
    import interventions as iv
    sc, pairs = iv.guard_frame(ROOT / "runs" / "guard1")      # primary: quarantine excluded
    j = pairs["G1"]
    j = j[j.valid & j.valid_G1].copy()
    assert not j.family_id.isin(["act-10", "act-16"]).any()

    def agg(rows, tcol, scol_p0, scol_g1):
        units = {}
        for _, r in rows.iterrows():
            u = units.setdefault(r[tcol], {
                "text_id": r[tcol], "text": r["text_G1"] if tcol == "text_id_G1" else r["text"],
                "input_text": r["input_text"], "models": set(), "families": set(), "dimensions": set(),
                "channels": set(), "p0_texts": set(), "output_ids": set(), "n_occ": 0,
                "p0_strict_fail": set(), "g1_strict_fail": set()})
            assert u["input_text"] == r["input_text"]
            u["models"].add(r.model); u["families"].add(r.family_id); u["dimensions"].add(r.dimension)
            u["channels"].add(r.channel); u["p0_texts"].add(r.text); u["n_occ"] += 1
            u["output_ids"].add(r["output_id_G1"] if tcol == "text_id_G1" else r["output_id"])
            u["p0_strict_fail"].add(str(r[scol_p0])); u["g1_strict_fail"].add(str(r[scol_g1]))
        for u in units.values():
            u["group"] = "cue" if u["channels"] & CUE else "ambiguous"
            assert not (u["channels"] & CUE and u["channels"] - CUE), u  # one input -> one channel group
        return units

    rep = agg(j[j.changed_G1.astype(bool)], "text_id_G1", "strict_fail", "strict_fail_G1")
    # control: all occurrences unchanged and strict pass
    occ = j.groupby("text_id").agg(any_changed=("changed_G1", lambda s: bool(s.astype(bool).any())),
                                   all_pass=("strict_fail", lambda s: bool(s.notna().all() and
                                                                           (~s.astype(bool)).all())))
    ok_ids = set(occ.index[~occ.any_changed & occ.all_pass]) - set(rep)
    rep_texts = {u["text"] for u in rep.values()}
    ctl = agg(j[j.text_id.isin(ok_ids)], "text_id", "strict_fail", "strict_fail_G1")
    ctl = {k: u for k, u in ctl.items() if u["text"] not in rep_texts}
    return rep, ctl


def select(units: dict, salt: str, group_quota: dict | None = None) -> list[tuple[str, str]]:
    """Return [(text_id, assigned_model)] in acceptance order."""
    order = sorted(units, key=lambda t: h(t + salt))
    models = sorted({m for u in units.values() for m in u["models"]})
    quota = {m: PER_MODEL for m in models}
    gq = {k: v for k, v in (group_quota or {}).items()}
    picked, used_fam, taken = [], set(), set()
    # passes: (family-distinct, channel-mix, model-quota)
    for fam_c, grp_c, mod_c in [(True, True, True), (False, True, True), (False, False, True),
                                (False, False, False)]:
        if not group_quota:
            grp_c = False
        for t in order:
            if len(picked) >= PER_ARM:
                break
            if t in taken:
                continue
            u = units[t]
            if fam_c and u["families"] & used_fam:
                continue
            cands = sorted(u["models"], key=lambda m: (-quota[m], m))
            if mod_c:
                cands = [m for m in cands if quota[m] > 0]
            if grp_c:
                cands = [m for m in cands if gq.get((m, u["group"]), 0) > 0]
            if not cands:
                continue
            m = cands[0]
            quota[m] -= 1
            if (m, u["group"]) in gq:
                gq[(m, u["group"])] -= 1
            picked.append((t, m)); taken.add(t); used_fam |= u["families"]
    return picked


def draw(rep, ctl, salt):
    r = select(rep, salt)
    gq = Counter((m, rep[t]["group"]) for t, m in r)
    c = select(ctl, salt, group_quota=dict(gq))
    return r, c


def main() -> int:
    import pandas as pd
    rep, ctl = build_pools()
    r_sel, c_sel = draw(rep, ctl, SALT)
    assert len(r_sel) == PER_ARM and len(c_sel) == PER_ARM, (len(r_sel), len(c_sel))

    # Monte Carlo inclusion probabilities under the identical algorithm
    rng = random.Random(20261031)
    inc = Counter()
    for _ in range(MC_REPS):
        s = "mc-%016x" % rng.getrandbits(64)
        a, b = draw(rep, ctl, s)
        inc.update(("repaired", t) for t, _ in a)
        inc.update(("control", t) for t, _ in b)
    pi = {k: v / MC_REPS for k, v in inc.items()}

    def elig_counts(units):
        by_m = Counter(m for u in units.values() for m in u["models"])
        by_g = Counter(u["group"] for u in units.values())
        return by_m, by_g

    summ = {"salt": SALT, "per_model": PER_MODEL, "per_arm": PER_ARM, "mc_reps": MC_REPS,
            "source": "runs/guard1/scored.parquet (+generations.jsonl), primary families", "arms": {}}
    elig_rows, key_rows = [], []
    for arm, units, sel in (("repaired", rep, r_sel), ("control", ctl, c_sel)):
        by_m, by_g = elig_counts(units)
        selm = dict(sel)
        summ["arms"][arm] = {
            "eligible_units": len(units), "eligible_by_model_any": dict(sorted(by_m.items())),
            "eligible_by_channel_group": dict(by_g),
            "eligible_multi_model_units": sum(len(u["models"]) > 1 for u in units.values()),
            "selected_by_model": dict(sorted(Counter(selm.values()).items())),
            "selected_by_channel_group": dict(Counter(units[t]["group"] for t in selm)),
            "selected_by_channel": dict(Counter(c for t in selm for c in sorted(units[t]["channels"]))),
            "selected_by_dimension": dict(Counter(d for t in selm for d in sorted(units[t]["dimensions"]))),
            "selected_distinct_families": len({f for t in selm for f in units[t]["families"]}),
        }
        for rank, t in enumerate(sorted(units, key=lambda t: h(t + SALT))):
            u = units[t]
            row = {"arm": arm, "text_id": t, "hash_rank": rank, "hash": h(t + SALT),
                   "selected": t in selm, "assigned_model": selm.get(t, ""),
                   "models": "|".join(sorted(u["models"])), "families": "|".join(sorted(u["families"])),
                   "dimensions": "|".join(sorted(u["dimensions"])), "channels": "|".join(sorted(u["channels"])),
                   "channel_group": u["group"], "n_occurrences": u["n_occ"],
                   "input_text": u["input_text"], "text": u["text"],
                   "p0_texts": " || ".join(sorted(u["p0_texts"])),
                   "output_ids": "|".join(sorted(u["output_ids"])),
                   "p0_strict_fail": "|".join(sorted(u["p0_strict_fail"])),
                   "g1_strict_fail": "|".join(sorted(u["g1_strict_fail"])),
                   "pi_mc": round(pi.get((arm, t), 0.0), 4),
                   "eligible_arm": len(units),
                   "eligible_model_any": "|".join(f"{m}:{by_m[m]}" for m in sorted(u["models"]))}
            elig_rows.append(row)
            if t in selm:
                key_rows.append(row)
    for row in key_rows:
        row["item_id"] = "ra-" + h(ID_SALT + row["text_id"])[:6]
    ids = [r["item_id"] for r in key_rows]
    assert len(set(ids)) == len(ids) == 2 * PER_ARM
    texts = [r["text"] for r in key_rows]
    assert len(set(texts)) == len(texts), "duplicate sentence across arms"
    summ["selected_pi_range"] = {arm: [min(r["pi_mc"] for r in key_rows if r["arm"] == arm),
                                       max(r["pi_mc"] for r in key_rows if r["arm"] == arm)]
                                 for arm in ("repaired", "control")}

    cols = ["item_id"] + [c for c in key_rows[0] if c != "item_id"]
    pd.DataFrame(key_rows)[cols].sort_values(["arm", "hash_rank"]).to_csv(KEY, index=False)
    pd.DataFrame(elig_rows).to_csv(ELIG, index=False)
    SUMMARY.write_text(json.dumps(summ, indent=2) + "\n")

    # blind embedded items: id, sentence, visible input only; ordered by item_id (arm-mixed)
    items = [{"item_id": r["item_id"], "text": r["text"], "input": visible_input(r["input_text"])}
             for r in sorted(key_rows, key=lambda r: r["item_id"])]
    blob = json.dumps(items, ensure_ascii=False, indent=0).replace("</", "<\\/")
    html = HTML.read_text()
    new, n = re.subn(r"(/\*AUDIT_ITEMS_BEGIN\*/).*?(/\*AUDIT_ITEMS_END\*/)",
                     lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
    assert n == 1
    HTML.write_text(new)
    print(json.dumps(summ, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

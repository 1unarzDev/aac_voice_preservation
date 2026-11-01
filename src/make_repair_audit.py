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

--source guard_wc (B4, Part 11: the W-C confirmation transfer). PRESPECIFIED selection,
  exactly as analysis/guard_wc/FREEZE.md: the first 20 distinct normalised texts per arm
  (G1 changed; G1 unchanged with a strict-correct first pass) by ascending SHA256 of the
  normalised text, ties by model/family/variant/channel. The list is the frozen
  analysis/guard_wc/audit_sample.csv (sha256 checked against audit_manifest.json) and is
  re-derived here from analysis/guard_wc/scored.parquet with the same rule; the two must
  match. No model balancing; inclusion is deterministic, so there are NO design weights
  (pi_mc is blank); counts by model are descriptive. Pass B shows each row's frozen input.
  Private outputs annotation/repair_audit_transfer_{key,eligible}.csv and
  annotation/repair_audit_transfer_sample.json. The tool
  annotation_package/repair_audit_transfer.html is generated from repair_audit.html (the
  template is not modified) with its own title, RUN tag, localStorage namespace
  ("repairaudit:transfer:v1:") and CSV name (repair_audit_transfer_<ID>.csv).
--source guard_wc_balanced: the model-balanced alternative with Monte Carlo pi (Part 4
  design on guard_wc). NOT USED; local only (annotation/*_balanced_unused*), uncommitted.
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

SOURCES = {
    "guard1": {"run": "guard1", "salt": "repair-audit-2026", "id_salt": "repair-audit-2026-item",
               "prefix": "ra-", "html": "repair_audit.html", "stem": "repair_audit", "template": None},
    # Part 11 as packaged: the FREEZE.md prespecified list, no design weights (main_frozen)
    "guard_wc": {"run": "guard_wc", "frozen": True, "id_salt": "repair-audit-transfer-frozen-item",
                 "prefix": "rx-", "html": "repair_audit_transfer.html", "stem": "repair_audit_transfer",
                 "template": {"part": "Part 11", "run": "repair_audit_transfer_v1",
                              "store": "repairaudit:transfer:v1:", "csv": "repair_audit_transfer_"},
                 "frozen_list": "analysis/guard_wc/audit_sample.csv",
                 "frozen_manifest": "analysis/guard_wc/audit_manifest.json"},
    # NOT USED (coordinator decision: prespecification wins). Model-balanced alternative,
    # local only: written to annotation/, never to the package, never committed.
    "guard_wc_balanced": {"run": "guard_wc", "salt": "repair-audit-transfer-2026",
                          "id_salt": "repair-audit-transfer-2026-item", "prefix": "rb-",
                          "html": "repair_audit_transfer_balanced_unused.html", "html_dir": "annotation",
                          "stem": "repair_audit_transfer_balanced_unused",
                          "template": {"part": "Part 11, unused alternative",
                                       "run": "repair_audit_transfer_balanced_unused_v1",
                                       "store": "repairaudit:transfer-balanced-unused:v1:",
                                       "csv": "repair_audit_transfer_balanced_unused_"},
                          "frozen_list": "analysis/guard_wc/audit_sample.csv", "by_input": True},
}
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


def build_pools(run: str = "guard1", by_input: bool = False):
    """by_input: unit = (text, visible input) (guard_wc text ids are per text only, and a
    sentence can occur under two inputs); the unit id is then '<text_id>|<sha1(input)[:8]>'."""
    import interventions as iv
    sc, pairs = iv.guard_frame(ROOT / "runs" / run)      # primary: quarantine excluded
    j = pairs["G1"]
    j = j[j.valid & j.valid_G1].copy()
    assert not j.family_id.isin(["act-10", "act-16"]).any()
    assert not j.quarantine_refusal_acceptance.fillna(False).astype(bool).any()

    def agg(rows, tcol, scol_p0, scol_g1):
        units = {}
        for _, r in rows.iterrows():
            uid = f"{r[tcol]}|{h(r['input_text'])[:8]}" if by_input else r[tcol]
            u = units.setdefault(uid, {
                "text_id": uid, "text": r["text_G1"] if tcol == "text_id_G1" else r["text"],
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
    ok_ids = set(occ.index[~occ.any_changed & occ.all_pass]) - {u.split("|")[0] for u in rep}
    rep_texts = {u["text"] for u in rep.values()}
    ctl = agg(j[j.text_id.isin(ok_ids)], "text_id", "strict_fail", "strict_fail_G1")
    ctl = {k: u for k, u in ctl.items() if u["text"] not in rep_texts}
    return rep, ctl


def select(units: dict, salt: str, group_quota: dict | None = None,
           distinct_text: bool = False) -> list[tuple[str, str]]:
    """Return [(text_id, assigned_model)] in acceptance order. distinct_text: never accept a
    second unit with an already accepted sentence (by_input units)."""
    order = sorted(units, key=lambda t: h(t + salt))
    models = sorted({m for u in units.values() for m in u["models"]})
    quota = {m: PER_MODEL for m in models}
    gq = {k: v for k, v in (group_quota or {}).items()}
    picked, used_fam, taken, used_text = [], set(), set(), set()
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
            if distinct_text and u["text"] in used_text:
                continue
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
            picked.append((t, m)); taken.add(t); used_fam |= u["families"]; used_text.add(u["text"])
    return picked


def draw(rep, ctl, salt, distinct_text=False):
    r = select(rep, salt, distinct_text=distinct_text)
    gq = Counter((m, rep[t]["group"]) for t, m in r)
    c = select(ctl, salt, group_quota=dict(gq), distinct_text=distinct_text)
    return r, c


def render_html(cfg: dict, blob: str) -> str:
    """Embed the items; for a derived tool, re-label the template (Part 4 file untouched)."""
    src = ROOT / "annotation_package" / ("repair_audit.html" if cfg["template"] else cfg["html"])
    html = src.read_text()
    new, n = re.subn(r"(/\*AUDIT_ITEMS_BEGIN\*/).*?(/\*AUDIT_ITEMS_END\*/)",
                     lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
    assert n == 1
    t = cfg["template"]
    if t:
        for old, rep_, cnt in (("(Part 4)", f"({t['part']})", 2),
                               ('const RUN = "repair_audit_v1";', f'const RUN = "{t["run"]}";', 1),
                               ('return "repairaudit:v1:" + id;', f'return "{t["store"]}" + id;', 1),
                               ('a.download = "repair_audit_" + S.annot', f'a.download = "{t["csv"]}" + S.annot', 1)):
            assert new.count(old) == cnt, (old, new.count(old))
            new = new.replace(old, rep_)
    return new


def main_frozen(cfg: dict) -> int:
    """Part 11: the FREEZE.md list (see module docstring). No sampling, no weights."""
    import pandas as pd
    from explode import normalise
    fl, man = ROOT / cfg["frozen_list"], json.loads((ROOT / cfg["frozen_manifest"]).read_text())
    assert hashlib.sha256(fl.read_bytes()).hexdigest() == man["sample_sha256"], "frozen list changed"
    frozen = pd.read_csv(fl)
    # re-derive with the frozen rule (analysis/guard_wc/analyze.py audit())
    KEYC = ["model", "family_id", "variant", "channel"]
    fr = pd.read_parquet(ROOT / "analysis/guard_wc/scored.parquet")
    b = fr[fr.prompt_id.eq("P0")].set_index(KEYC)
    g = fr[fr.prompt_id.eq("G1")].set_index(KEYC)
    arm_of = {"changed": "repaired", "unchanged_correct": "control"}
    key_rows, elig_rows, summ_arms = [], [], {}
    for group, cand in (("changed", g[g.changed]), ("unchanged_correct", g[(~g.changed) & b.strict.eq(1)])):
        cand = cand.reset_index().sort_values(KEYC)
        cand["norm"] = cand.text.map(normalise)
        cand["selection_hash"] = cand.norm.map(lambda x: hashlib.sha256(x.encode()).hexdigest())
        distinct = cand.drop_duplicates("norm").sort_values(["selection_hash"] + KEYC).reset_index(drop=True)
        fz = frozen[frozen.group == group].reset_index(drop=True)
        mine = distinct.head(20)
        assert list(mine.selection_hash) == list(fz.selection_hash) and list(mine.output_id) == list(fz.output_id), \
            f"re-derived {group} list differs from {cfg['frozen_list']}"
        arm = arm_of[group]
        mem = cand.groupby("norm")
        for rank, r in distinct.iterrows():
            m = mem.get_group(r["norm"])
            row = {"arm": arm, "frozen_group": group, "hash_rank": rank, "selection_hash": r["selection_hash"],
                   "selected": rank < 20, "assigned_model": r["model"],
                   "models": "|".join(sorted(set(m.model))), "families": "|".join(sorted(set(m.family_id))),
                   "dimensions": "|".join(sorted(set(m.dimension))), "channels": r["channel"],
                   "member_channels": "|".join(sorted(set(m.channel))), "channel_group": "cue",
                   "family_id": r["family_id"], "variant": r["variant"], "n_memberships": len(m),
                   "member_inputs": " || ".join(sorted(set(m.input_text))),
                   "input_text": r["input_text"], "text": r["text"], "output_id": r["output_id"],
                   "inclusion": "frozen rule (FREEZE.md): first 20 distinct normalised texts per arm by "
                                "ascending SHA256; deterministic, not probability sampling; no design weights",
                   "pi_mc": "", "design_weight": ""}
            elig_rows.append(row)
            if rank < 20:
                key_rows.append(row)
        sel = [r for r in key_rows if r["arm"] == arm]
        summ_arms[arm] = {
            "eligible_occurrences": len(cand), "eligible_distinct": len(distinct),
            "manifest_eligible_distinct": man[group]["eligible_distinct"],
            "selected_by_model_descriptive": dict(sorted(Counter(r["assigned_model"] for r in sel).items())),
            "eligible_distinct_by_model_descriptive": dict(sorted(Counter(distinct.model).items())),
            "selected_by_channel": dict(sorted(Counter(r["channels"] for r in sel).items())),
            "selected_distinct_families": len({r["family_id"] for r in sel}),
            "selected_multi_membership": sum(r["n_memberships"] > 1 for r in sel)}
        assert len(distinct) == man[group]["eligible_distinct"]
    for row in key_rows:
        row["item_id"] = cfg["prefix"] + h(cfg["id_salt"] + row["selection_hash"])[:6]
    assert len({r["item_id"] for r in key_rows}) == len(key_rows) == 40
    assert len({normalise(r["text"]) for r in key_rows}) == 40, "duplicate sentence across arms"
    summ = {"design": "PRESPECIFIED (analysis/guard_wc/FREEZE.md, Audit and examples): first 20 distinct "
                      "normalised texts per arm by ascending SHA256(normalised text), ties by model, family, "
                      "variant, channel. Deterministic; no model balancing; no inclusion probabilities or "
                      "design weights. Counts by model are descriptive only.",
            "frozen_list": cfg["frozen_list"], "frozen_list_sha256": man["sample_sha256"],
            "rederived_from": "analysis/guard_wc/scored.parquet (matches the frozen list)",
            "arms": summ_arms}
    cols = ["item_id"] + [c for c in key_rows[0] if c != "item_id"]
    pd.DataFrame(key_rows)[cols].sort_values(["arm", "hash_rank"]).to_csv(KEY, index=False)
    pd.DataFrame(elig_rows).to_csv(ELIG, index=False)
    SUMMARY.write_text(json.dumps(summ, indent=2) + "\n")
    items = [{"item_id": r["item_id"], "text": r["text"], "input": visible_input(r["input_text"])}
             for r in sorted(key_rows, key=lambda r: r["item_id"])]
    blob = json.dumps(items, ensure_ascii=False, indent=0).replace("</", "<\\/")
    HTML.write_text(render_html(cfg, blob))
    print(json.dumps(summ, indent=1))
    return 0


def main() -> int:
    import argparse
    import pandas as pd
    global SALT, ID_SALT, KEY, ELIG, SUMMARY, HTML
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", choices=sorted(SOURCES), default="guard1")
    a = ap.parse_args()
    cfg = SOURCES[a.source]
    KEY = ROOT / "annotation" / f"{cfg['stem']}_key.csv"
    ELIG = ROOT / "annotation" / f"{cfg['stem']}_eligible.csv"
    SUMMARY = ROOT / "annotation" / f"{cfg['stem']}_sample.json"
    HTML = ROOT / cfg.get("html_dir", "annotation_package") / cfg["html"]
    if cfg.get("frozen"):
        return main_frozen(cfg)
    SALT, ID_SALT = cfg["salt"], cfg["id_salt"]
    bi = bool(cfg.get("by_input"))
    rep, ctl = build_pools(cfg["run"], by_input=bi)
    r_sel, c_sel = draw(rep, ctl, SALT, distinct_text=bi)
    assert len(r_sel) == PER_ARM and len(c_sel) == PER_ARM, (len(r_sel), len(c_sel))

    # Monte Carlo inclusion probabilities under the identical algorithm
    rng = random.Random(20261031)
    inc = Counter()
    for _ in range(MC_REPS):
        s = "mc-%016x" % rng.getrandbits(64)
        a, b = draw(rep, ctl, s, distinct_text=bi)
        inc.update(("repaired", t) for t, _ in a)
        inc.update(("control", t) for t, _ in b)
    pi = {k: v / MC_REPS for k, v in inc.items()}

    def elig_counts(units):
        by_m = Counter(m for u in units.values() for m in u["models"])
        by_g = Counter(u["group"] for u in units.values())
        return by_m, by_g

    summ = {"salt": SALT, "per_model": PER_MODEL, "per_arm": PER_ARM, "mc_reps": MC_REPS,
            "source": f"runs/{cfg['run']}/scored.parquet (+generations.jsonl), primary families", "arms": {}}
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
        row["item_id"] = cfg["prefix"] + h(ID_SALT + row["text_id"])[:6]
    ids = [r["item_id"] for r in key_rows]
    assert len(set(ids)) == len(ids) == 2 * PER_ARM
    texts = [r["text"] for r in key_rows]
    assert len(set(texts)) == len(texts), "duplicate sentence across arms"
    summ["selected_pi_range"] = {arm: [min(r["pi_mc"] for r in key_rows if r["arm"] == arm),
                                       max(r["pi_mc"] for r in key_rows if r["arm"] == arm)]
                                 for arm in ("repaired", "control")}
    if cfg.get("frozen_list") and (ROOT / cfg["frozen_list"]).exists():
        fz = pd.read_csv(ROOT / cfg["frozen_list"])
        grp = {"changed": "repaired", "unchanged_correct": "control"}
        fz_texts = {(grp.get(g, g), t) for g, t in zip(fz["group"], fz["text"])}
        summ["overlap_with_frozen_sha256_list"] = {
            "file": cfg["frozen_list"], "rule": "FREEZE.md: first 20 per arm by ascending SHA256(normalised "
                                                "text); deterministic, no inclusion probabilities",
            "frozen_list_by_arm": dict(Counter(grp.get(g, g) for g in fz["group"])),
            **{arm: sum((arm, r["text"]) in fz_texts for r in key_rows if r["arm"] == arm)
               for arm in ("repaired", "control")}}

    cols = ["item_id"] + [c for c in key_rows[0] if c != "item_id"]
    pd.DataFrame(key_rows)[cols].sort_values(["arm", "hash_rank"]).to_csv(KEY, index=False)
    pd.DataFrame(elig_rows).to_csv(ELIG, index=False)
    SUMMARY.write_text(json.dumps(summ, indent=2) + "\n")

    # blind embedded items: id, sentence, visible input only; ordered by item_id (arm-mixed)
    items = [{"item_id": r["item_id"], "text": r["text"], "input": visible_input(r["input_text"])}
             for r in sorted(key_rows, key=lambda r: r["item_id"])]
    blob = json.dumps(items, ensure_ascii=False, indent=0).replace("</", "<\\/")
    HTML.write_text(render_html(cfg, blob))
    print(json.dumps(summ, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

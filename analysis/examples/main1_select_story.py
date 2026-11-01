"""Read stored runs only; reproduce the exploratory story gallery and its denominators.

Run from any directory with the project's .venv/bin/python. No model calls.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from interventions import guard_frame, sha1, span_sets

MODEL_ORDER = {m: n for n, m in enumerate(
    ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"])}
items = {x["family_id"]: x for x in map(json.loads, (ROOT / "data/items/test.jsonl").open())}
main = pd.read_parquet(ROOT / "runs/main1/scored.parquet")
p0 = main[main.prompt_id.eq("P0")].copy()
p0["model_order"] = p0.model.map(MODEL_ORDER)
p0 = p0.sort_values(["family_id", "variant", "model_order", "sample_idx", "suggestion_idx", "output_id"])
raw = pd.read_parquet(ROOT / "runs/main1/scored_raw_oracle.parquet")
_, gp = guard_frame(ROOT / "runs/guard1")
j = gp["G1"]
j = j[j.channel.isin(["chip1", "chipall", "full"]) & ~j.family_id.isin(["act-10", "act-16"])].copy()
assert j.strict_fail.notna().all() and j.strict_fail_G1.notna().all()
j["h"] = [sha1(*t) for t in zip(j.base_key, j.family_id, j.variant, j.channel)]
j = j.sort_values(["h", "output_id"])
fixed = j[j.strict_fail & ~j.strict_fail_G1]
unfixed = j[j.strict_fail & j.strict_fail_G1]
_, sets = span_sets(ROOT / "runs/span1")
w = sets.pivot_table(index=["model", "family_id", "dimension"], columns="prompt_id", values="coverage").reset_index()
w["h"] = [sha1(m, f) for m, f in zip(w.model, w.family_id)]
w = w.sort_values(["h", "model", "family_id"])
target_sets = w[w.dimension.isin(["polarity", "certainty"])]
gains = target_sets[(target_sets.I2 == 1) & (target_sets.P2 == 0)]
polite_sets = w[w.dimension.eq("politeness")]
losses = polite_sets[(polite_sets.I2 == 0) & (polite_sets.P2 == 1)]

example_rows = []
examples = []


def stored(run, row, arm=None):
    suffix = "_" + arm if arm else ""
    rec = {k: row[k + suffix] for k in ["output_id", "request_key", "text", "critical"]}
    rec.update(run=run, model=row.model, family_id=row.family_id,
               variant=row.variant, channel=row.channel,
               prompt_id=arm or row.prompt_id, input_text=row.input_text)
    example_rows.append(rec)
    return rec


def add_pair(eid, pool, channels):
    chosen = pool.iloc[0]
    r = p0[(p0.family_id == chosen.family_id) & (p0.variant == chosen.variant) & (p0.model == chosen.model)]
    examples.append(dict(id=eid, source=items[chosen.family_id]["variants"][chosen.variant]["source"],
                         outputs=[stored("main1", r[r.channel.eq(c)].iloc[0]) for c in channels]))


add_pair("E1", p0[(p0.dimension == "polarity") & (p0.channel == "bare") & (p0.variant_value == "negated")],
         ["bare", "noncrit", "chip1"])
add_pair("E2", p0[(p0.dimension == "certainty") & (p0.channel == "bare") & (p0.variant_value == "hedged/uncertain")],
         ["bare", "chip1", "full"])
for eid, pool in [
    ("E3", p0[(p0.dimension == "politeness") & (p0.channel == "full") & (p0.variant_value == "plain") & (p0.critical == "polite")]),
    ("E4", p0[(p0.dimension == "speech_act") & (p0.channel == "chip1") & ~p0.quarantine_refusal_acceptance & (p0.variant_value == "question") & (p0.critical == "request/command")]),
]:
    r = pool.iloc[0]
    examples.append(dict(id=eid, source=items[r.family_id]["variants"][r.variant]["source"], outputs=[stored("main1", r)]))
for eid, r in [("E5", fixed.iloc[0]), ("E6", unfixed.iloc[0]), ("E7", fixed.iloc[1])]:
    examples.append(dict(id=eid, source=items[r.family_id]["variants"][r.variant]["source"],
                         hash=r.h, outputs=[stored("guard1", r), stored("guard1", r, "G1")]))
span = pd.read_parquet(ROOT / "runs/span1/scored.parquet")
for eid, r in [("E8", gains.iloc[0]), ("E9", losses.iloc[0])]:
    outputs = []
    for arm in ["P2", "I2"]:
        rows = span[(span.model == r.model) & (span.family_id == r.family_id) & (span.variant == "A") & (span.channel == "bare") & (span.prompt_id == arm)].sort_values(["sample_idx", "suggestion_idx"])
        assert len(rows) == 3
        outputs.extend(stored("span1", row) for _, row in rows.iterrows())
    examples.append(dict(id=eid, hash=r.h, sources=items[r.family_id]["variants"], outputs=outputs))


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower().replace("’", "'").replace("'", "")).strip()


identity = raw[raw.channel.eq("full")].copy()
identity["source"] = [items[f]["variants"][v]["source"] for f, v in zip(identity.family_id, identity.variant)]
identity = identity[[norm(a) == norm(b) for a, b in zip(identity.text, identity.source)]]
identity_bad = identity[~identity.critical_match.astype(bool)].copy()
identity_bad["mo"] = identity_bad.model.map(MODEL_ORDER)
r = identity_bad[identity_bad.prompt_id.eq("P0")].sort_values(["family_id", "variant", "mo", "output_id"]).iloc[0]
current = main[(main.output_id == r.output_id) & (main.variant == r.variant) & (main.channel == r.channel)].iloc[0]
examples.append(dict(id="E10", source=r.source, quarantine=True,
                     scoring_table="runs/main1/scored_raw_oracle.parquet",
                     raw_critical_match=bool(r.critical_match),
                     relaxed_critical_match=bool(current.critical_match),
                     outputs=[stored("main1", r)]))

bare_pol = p0[(p0.dimension == "polarity") & (p0.channel == "bare")].drop_duplicates("output_id")
bare_cer = p0[(p0.dimension == "certainty") & (p0.channel == "bare")].drop_duplicates("output_id")
plain_full = p0[(p0.dimension == "politeness") & (p0.channel == "full") & (p0.variant_value == "plain")]
polite_full = p0[(p0.dimension == "politeness") & (p0.channel == "full") & (p0.variant_value == "polite")]
all_full = p0[p0.channel.eq("full")]
plain_full_all = all_full[["[PLEASE]" not in items[f]["variants"][v]["all_chips"]
                           for f, v in zip(all_full.family_id, all_full.variant)]]
hedged_full = all_full[(all_full.dimension == "certainty") & (all_full.variant_value == "hedged/uncertain")]
questions = p0[(p0.dimension == "speech_act") & (p0.channel == "chip1") & ~p0.quarantine_refusal_acceptance & (p0.variant_value == "question")]
acts = p0[(p0.dimension == "speech_act") & (p0.channel == "chip1") & ~p0.quarantine_refusal_acceptance]
hedge_chip = p0[(p0.dimension == "certainty") & (p0.channel == "chip1") & (p0.variant_value == "hedged/uncertain")]
pol_chip = p0[(p0.dimension == "polarity") & (p0.channel == "chip1")]
plain_chip = p0[(p0.dimension == "politeness") & (p0.channel == "chip1") & (p0.variant_value == "plain")]
correct = j[~j.strict_fail]


def count(n, d):
    return dict(n=int(n), denominator=int(d), percent=round(100 * n / d, 3))


rates = dict(
    bare_polarity_affirmative=count((bare_pol.critical == "affirmative").sum(), len(bare_pol)),
    polarity_chip_match=count(pol_chip.critical_match.sum(), len(pol_chip)),
    bare_certainty_plain=count((bare_cer.critical == "plain assertion").sum(), len(bare_cer)),
    bare_certainty_hedged=count((bare_cer.critical == "hedged/uncertain").sum(), len(bare_cer)),
    hedged_chip_match=count(hedge_chip.critical_match.sum(), len(hedge_chip)),
    full_plain_to_polite=count((plain_full.critical == "polite").sum(), len(plain_full)),
    full_polite_to_plain=count((polite_full.critical == "plain").sum(), len(polite_full)),
    full_plain_to_polite_all_families=count(plain_full_all.politeness_added.sum(), len(plain_full_all)),
    full_hedges_removed=count((hedged_full.critical != "hedged/uncertain").sum(), len(hedged_full)),
    question_chip_to_request=count((questions.critical == "request/command").sum(), len(questions)),
    question_chip_nonquestion=count((questions.critical != "question").sum(), len(questions)),
    speech_chip_match_excl_quarantine=count(acts.critical_match.sum(), len(acts)),
    plain_chip_to_polite=count((plain_chip.critical == "polite").sum(), len(plain_chip)),
    guard_fixed_excl_quarantine=count(len(fixed), j.strict_fail.sum()),
    guard_unfixed_excl_quarantine=count(len(unfixed), j.strict_fail.sum()),
    guard_baseline_strict_pass_excl_quarantine=count((~j.strict_fail).sum(), len(j)),
    guard_final_strict_pass_excl_quarantine=count((~j.strict_fail_G1).sum(), len(j)),
    guard_changed_correct_cue_excl_quarantine=count(correct.changed_G1.sum(), len(correct)),
    guard_broke_correct_cue_excl_quarantine=count(correct.strict_fail_G1.sum(), len(correct)),
    literal_ask_you_prefix_among_fixed=count(fixed.text_G1.str.startswith("Ask you ").sum(), len(fixed)),
    I2_target_P2_coverage=count(target_sets.P2.sum(), len(target_sets)),
    I2_target_final_coverage=count(target_sets.I2.sum(), len(target_sets)),
    I2_target_gained=count(len(gains), (target_sets.P2 == 0).sum()),
    I2_politeness_P2_coverage=count(polite_sets.P2.sum(), len(polite_sets)),
    I2_politeness_final_coverage=count(polite_sets.I2.sum(), len(polite_sets)),
    I2_politeness_coverage_lost=count(len(losses), len(polite_sets)),
    I2_politeness_loss_conditional=count(len(losses), (polite_sets.P2 == 1).sum()),
    oracle_normalized_identity_false_failures=count(len(identity_bad), len(identity)),
)

# Verify quoted strings against the original JSONL records, independently of the parquet.
for run in {r["run"] for r in example_rows}:
    outputs = [json.loads(line) for line in (ROOT / f"runs/{run}/outputs.jsonl").open()]
    for row in [r for r in example_rows if r["run"] == run]:
        matches = [(n, x) for n, x in enumerate(outputs, 1)
                   if x["output_id"] == row["output_id"] and x["request_key"] == row["request_key"]
                   and x["family_id"] == row["family_id"] and x["variant"] == row["variant"]
                   and x["channel"] == row["channel"] and x["prompt_id"] == row["prompt_id"]]
        assert len(matches) == 1, (run, row)
        line, match = matches[0]
        assert match["text"] == row["text"]
        assert match["input_text"] == row["input_text"]
        row["jsonl_line"] = line

paths = ["data/items/test.jsonl", "src/interventions.py"] + [
    f"runs/{r}/{f}" for r in ["main1", "guard1", "span1"] for f in ["scored.parquet", "outputs.jsonl"]
] + ["runs/main1/scored_raw_oracle.parquet"]
result = dict(date="2026-10-31", scope="Exploratory gallery; machine-scored rates; human gate pending",
              sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
              rates=rates, examples=examples)
out = Path(__file__).with_name("story_evidence.json")
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(rates, indent=2))
print(f"Verified {len(example_rows)} stored output occurrences for {len(examples)} examples; wrote {out}")

"""Cheap regression tests for fault classes that no stored-data replay reaches (found by the seeded-fault sweep):
non-completion on a cue channel (attribute.score), oracle verdict(), layer0 tie rules, runio occurrence validity.
Self-contained synthetic cases with hand-derived expectations."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attribute  # noqa: E402
import layer0  # noqa: E402
import oracle_wa  # noqa: E402
import runio  # noqa: E402

ITEM = {"family_id": "t-1", "dimension": "polarity", "split": "hw", "context": None,
        "variants": {"A": {"source": "I want to go.", "critical_value": "affirmative", "chips": [], "all_chips": ["[I]"]},
                     "B": {"source": "I do not want to go.", "critical_value": "negated", "chips": ["[NOT]"], "all_chips": ["[NOT]", "[I]"]}},
        "bare": "go", "noncritical": "now", "critical_options": ["affirmative", "negated", "mixed/unclear"]}
GEN = ("polarity", "agent", "certainty", "speech_act", "politeness")
GENERAL = {"polarity": "negated", "agent": "speaker", "certainty": "plain assertion", "speech_act": "statement", "politeness": "none"}


def _write(p, rows):
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _run(tmp_path, occ_rows, gen_rows, crit=None):
    items = tmp_path / "items.jsonl"
    _write(items, [ITEM])
    _write(tmp_path / "outputs.jsonl", occ_rows)
    _write(tmp_path / "generations.jsonl", gen_rows)
    if crit is not None:
        tid = runio.text_key(occ_rows[0]["text"])
        _write(tmp_path / "judgments.jsonl", [dict(
            text_id=tid, family_id="t-1", input_text=occ_rows[0]["input_text"], J1_critical=crit, J2_critical=crit,
            needs_arbiter=False, critical=crit, added_content=None, **GENERAL)])
    df = attribute.score(tmp_path, items)
    return df


def _occ(channel, text="I do not want to go.", variant="B"):
    return {"output_id": "o1", "text": text, "request_key": "rk1", "model": "m", "prompt_id": "P0", "temperature": 0.0,
            "sample_idx": 0, "suggestion_idx": 0, "family_id": "t-1", "variant": variant, "channel": channel,
            "input_text": f"in-{channel}", "valid": True, "dimension": "polarity", "split": "hw"}


def _gen_fail(channel, variant="B"):
    return {"request_key": "rk2", "model": "m", "prompt_id": "P0", "temperature": 0.0, "sample_idx": 0, "error": "boom",
            "suggestions": [], "input_text": f"in-{channel}", "dimension": "polarity", "split": "hw",
            "targets": [{"family_id": "t-1", "variant": variant, "channel": channel}]}


def test_non_completion_on_cue_channel_is_not_constraint_preserving(tmp_path):
    df = _run(tmp_path, [_occ("bare")], [_gen_fail("chip1"), _gen_fail("bare")], crit="negated")
    nc = df[~df["valid"].astype(bool) & df["text"].eq("")]
    cue = nc[nc.channel == "chip1"].iloc[0]
    amb = nc[nc.channel == "bare"].iloc[0]
    assert cue["cue_in_input"] and cue["constraint_preserving"] == False and cue["constraint_preserving"] is not None   # failed to produce: constraint not preserved
    assert cue["violation"] is None or cue["violation"] != cue["violation"]  # no label: violation not scored
    assert not amb["cue_in_input"] and (amb["constraint_preserving"] is None or amb["constraint_preserving"] != amb["constraint_preserving"])


def test_valid_cue_output_scored_by_critical_match(tmp_path):
    df = _run(tmp_path, [_occ("chip1")], [], crit="negated")
    r = df.iloc[0]
    assert bool(r["critical_match"]) and not r["violation"] and r["constraint_preserving"]
    df = _run(tmp_path, [_occ("chip1")], [], crit="affirmative")
    r = df.iloc[0]
    assert not bool(r["critical_match"]) and r["violation"] and not r["constraint_preserving"]


def test_oracle_verdict_rules():
    var = ITEM["variants"]["B"]
    ok = oracle_wa.verdict("polarity", var, "chip1", {"critical": "negated", **{d: v for d, v in GENERAL.items() if d != "polarity"}})
    assert ok["critical_match"] is True and ok["violation"] is False and ok["constraint_preserving"] is True
    bad = oracle_wa.verdict("polarity", var, "chip1", {"critical": "affirmative"})
    assert bad["critical_match"] is False and bad["violation"] is True and bad["constraint_preserving"] is False
    amb = oracle_wa.verdict("polarity", var, "bare", {"critical": "negated"})
    assert amb["violation"] is None and amb["assumption"] is True and amb["constraint_preserving"] is None
    # contradiction: channel gives agent ([I] -> speaker, via chipall); an output with another agent contradicts it
    c = oracle_wa.verdict("polarity", var, "chipall", {"critical": "negated", "agent": "addressee"})
    assert c["critical_match"] is True and c["constraint_preserving"] is False
    c2 = oracle_wa.verdict("polarity", var, "chipall", {"critical": "negated", "agent": "speaker"})
    assert c2["constraint_preserving"] is True


def test_layer0_booster_does_not_outrank_hedge():
    assert layer0.label_many(["I think it is definitely fine."])[0]["certainty"] == "hedged/uncertain"


def test_layer0_polarity_needs_every_main_clause_negated():
    lab = lambda s: layer0.label_many([s])[0]["polarity"]  # noqa: E731
    assert lab("I do not like it but I will go.") == "mixed/unclear"
    assert lab("I do not like it.") == "negated"


def test_occurrence_validity_requires_flag_and_text():
    assert runio._norm({"text": "hi", "valid": False})["valid"] is False     # flag says invalid: stays invalid
    assert runio._norm({"text": "  ", "valid": True})["valid"] is False      # blank text: invalid
    assert runio._norm({"text": "hi", "valid": True})["valid"] is True
    assert runio._norm({"text": "hi"})["valid"] is True

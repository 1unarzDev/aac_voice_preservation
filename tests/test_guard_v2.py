"""Unit tests for guard v2 acceptance check A (src/guard_v2.py). CPU only, no model calls."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import guard_v2 as G  # noqa: E402

FF = ["politeness:added"]


def test_clean_accepts():
    assert G.acceptance("Bring slippers to me.", "Please bring slippers to me.", {}, FF) == []


def test_collateral_polarity_speechact_number_time():
    assert "collateral:polarity" in G.acceptance("I do not want tea.", "I want tea, thank you.", {}, FF)
    assert "collateral:speech_act" in G.acceptance("Do you want tea?", "I want tea, thank you.", {}, FF)
    assert "collateral:number" in G.acceptance("I want tea.", "I want 2 teas, thank you.", {}, FF)
    assert "collateral:time" in G.acceptance("Yesterday I called the clinic.", "I will call the clinic, thank you.", {}, FF)


def test_flagged_dim_exempt():
    assert not any(r.startswith("collateral:polarity")
                   for r in G.acceptance("I do not want tea.", "I want tea.", {}, ["polarity:negated"]))


def test_fragments():
    for t in ["I want the", "Go", "I want tea and", "I want tea. I want tea.", "Rewritten: I want tea.",
              "[ASK] bring tea.", "I want tea", "\"I want tea."]:
        assert "incomplete" in G.complete_reasons(t, "I want tea please."), t
    assert G.complete_reasons("Dr. Lee is at the clinic.", "Dr Lee clinic") == []
    assert G.complete_reasons("It costs 3.5 dollars.", "costs 3.5 dollars") == []


def test_echo():
    for t in ["Ask you to bring tea.", "Tell you that it is open.", "The polarity is negated.", "Command them to leave."]:
        assert "echo" in G.echo_reasons(t, "Keywords: [ASK] [YOU] tea"), t
    assert G.echo_reasons("Bring tea to me.", "Keywords: [ASK] [YOU] tea") == []


def test_retry_message_shared_with_g1():
    import interventions as I
    assert G.retry_message(FF, []) == I.feedback(FF)
    assert G.retry_message(FF, ["echo"]).startswith(I.feedback(FF))
    assert "complete sentence" in G.retry_message([], ["incomplete"])


def test_preuse():
    assert G.preuse() == 0

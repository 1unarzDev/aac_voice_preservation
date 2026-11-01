"""Unit tests for src/layer0.py.  Run: python -m pytest tests/test_layer0.py -q
(or plain `python tests/test_layer0.py`)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import layer0  # noqa: E402

CASES = [
    # text, {dim: expected}
    ("I don't want to go to the party tonight.",
     {"polarity": "negated", "speech_act": "statement", "agent": "speaker",
      "certainty": "plain assertion", "politeness": "none"}),
    ("I want to go to the party tonight.", {"polarity": "affirmative", "agent": "speaker"}),
    ("Could you please help me with my coat?",
     {"speech_act": "request/command", "agent": "addressee",
      "certainty": "n/a (question/request)", "politeness": "please"}),
    ("Would you mind opening the window?",
     {"speech_act": "request/command",
      "politeness": "softened request (could you/would you mind)"}),
    ("Can I leave the meeting early today?", {"speech_act": "question", "agent": "speaker"}),
    ("Can you pick me up after work?", {"speech_act": "request/command", "politeness": "none"}),
    ("Are you going to the store?", {"speech_act": "question", "agent": "addressee"}),
    ("No thanks, I already ate.", {"speech_act": "refusal", "politeness": "thanks/apology",
                                   "polarity": "negated"}),
    ("Let's watch a movie tonight.", {"speech_act": "offer/suggestion", "agent": "we/joint"}),
    ("Maybe I will come tomorrow.", {"certainty": "hedged/uncertain", "agent": "speaker"}),
    ("I'm definitely coming tomorrow.", {"certainty": "strongly certain/emphatic"}),
    ("My mom is picking me up at five.", {"agent": "third party",
                                          "certainty": "plain assertion"}),
    ("Pass me the water.", {"speech_act": "request/command", "agent": "addressee",
                            "politeness": "none"}),
    ("I want you to call my sister.", {"agent": "addressee"}),
    ("You need to call grandma.", {"speech_act": "statement", "agent": "addressee"}),   # CB-1
    ("My cut is infected again.", {"agent": "speaker"}),                                 # CB-4
    ("I think the lift is broken.", {"agent": "third party"}),                           # CB-3/4
    ("No, you can't borrow my car.", {"agent": "addressee"}),                            # CB-5
    ("I think he's coming.", {"certainty": "hedged/uncertain", "agent": "third party"}),
    ("Thank you so much!", {"speech_act": "other", "politeness": "thanks/apology"}),
    ("I can help you later.", {"certainty": "plain assertion"}),   # 'can' not a hedge
    ("I'm not sure if I can come.", {"certainty": "hedged/uncertain"}),
]


def test_cases():
    bad = []
    for text, exp in CASES:
        got = layer0.label(text)
        for d, v in exp.items():
            if got[d] != v:
                bad.append(f"{text!r}: {d} expected {v!r} got {got[d]!r}")
    assert not bad, "\n".join(bad)


def test_dont_tokenization_and_longest_match():
    doc = layer0.nlp()("If you don't mind, I think we can't go.")
    words = layer0.surface_words(doc)
    assert "don't" in words and "can't" in words and "n't" not in words
    hits = layer0.match_phrases(words)
    phrases = [h[2] for h in hits]
    assert "if you don't mind" in phrases          # multiword softener survives the split
    assert "i think" in phrases and "think" not in phrases   # no double count
    spans = [(h[0], h[1]) for h in hits]
    assert all(a[1] <= b[0] for a, b in zip(spans, spans[1:]))  # non-overlapping


if __name__ == "__main__":
    test_cases(); test_dont_tokenization_and_longest_match(); print("ok")

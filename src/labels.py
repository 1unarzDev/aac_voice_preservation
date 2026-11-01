"""Label schema shared by layer0, judge, attribute, make_gold and annotate.html (SPEC v0.1).

Option strings are copied verbatim from SPEC "Label schema"; do not paraphrase them,
every downstream join compares strings.
"""
from __future__ import annotations

GENERAL_OPTIONS: dict[str, list[str]] = {
    "polarity": ["affirmative", "negated", "mixed/unclear"],
    "speech_act": ["statement", "question", "request/command", "refusal",
                   "offer/suggestion", "other"],
    "agent": ["speaker", "addressee", "we/joint", "third party", "unspecified"],
    "certainty": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic",
                  "n/a (question/request)"],
    "politeness": ["none", "please", "softened request (could you/would you mind)",
                   "thanks/apology"],
}
GENERAL_DIMS = list(GENERAL_OPTIONS)
ADDED_CONTENT_OPTIONS = ["yes", "no"]

# One-line definitions shown to judges and humans (kept identical on purpose).
DEFINITIONS: dict[str, str] = {
    "polarity": "Is the main statement or request negated (not/never/no/don't)? "
                "'mixed/unclear' if both or you cannot tell.",
    "speech_act": "What the sentence does: tells (statement), asks for information (question), "
                  "asks someone to do something (request/command), declines (refusal), "
                  "proposes or offers (offer/suggestion).",
    "agent": "Who does the main action: the speaker (I), the listener (you), both (we/let's), "
             "someone else (third party), or no doer is stated (unspecified).",
    "certainty": "How sure the sentence sounds: plain, hedged (maybe/I think/probably), "
                 "strongly certain (definitely/really/for sure). Questions and requests: n/a.",
    "politeness": "Explicit politeness words only: 'please'; a softened request "
                  "(could you / would you mind / if possible); thanks or apology. Else none.",
    "added_content": "Does the sentence state a fact, reason, person, place or time that is "
                     "NOT in the input words? Grammar words and chips' meanings do not count.",
}

UNCLEAR = {"unclear/mixed", "mixed/unclear", "unclear", "mixed"}

SOFT = "softened request (could you/would you mind)"
EMPH = "strongly certain/emphatic"
PLAIN_A = "plain assertion"
POLITE_VALUES = {"please", SOFT, "thanks/apology"}

# Chip -> (general dimension, set of output values that honour it). Chips without a
# general dimension (MUST, WANT, PAST/NOW/LATER, numbers) only matter as critical cues.
# D-007: [SURE] is honoured by plain OR emphatic (emphatic is logged separately as a
# stance addition); [PLEASE] by any explicit polite marker.
CHIP_TO_GENERAL: dict[str, tuple[str, frozenset]] = {
    "[NOT]": ("polarity", frozenset({"negated"})),
    "[YES]": ("polarity", frozenset({"affirmative"})),
    "[?]": ("speech_act", frozenset({"question"})),
    "[ASK]": ("speech_act", frozenset({"request/command"})),
    "[REFUSE]": ("speech_act", frozenset({"refusal"})),
    "[TELL]": ("speech_act", frozenset({"statement"})),
    "[MAYBE]": ("certainty", frozenset({"hedged/uncertain"})),
    "[SURE]": ("certainty", frozenset({PLAIN_A, EMPH})),
    "[I]": ("agent", frozenset({"speaker"})),
    "[YOU]": ("agent", frozenset({"addressee"})),
    "[WE]": ("agent", frozenset({"we/joint"})),
    "[THEY]": ("agent", frozenset({"third party"})),
    "[PLEASE]": ("politeness", frozenset(POLITE_VALUES)),
    "[PLAIN]": ("politeness", frozenset({"none"})),
}

# Spec of a general dimension when all_chips is silent on it. agent has no default:
# a variant without a role chip makes no explicit role commitment (None = not scored).
GENERAL_DEFAULTS = {"polarity": frozenset({"affirmative"}),
                    "speech_act": frozenset({"statement"}),
                    "certainty": frozenset({PLAIN_A}),
                    "politeness": frozenset({"none"})}

NA_CERTAINTY = "n/a (question/request)"


def general_spec(all_chips: list[str], override: dict | None = None) -> dict[str, frozenset | None]:
    """Variant's general-dimension commitments from all_chips: dim -> set of output
    values that honour it (None = no commitment). A per-variant `general_spec` dict in
    the item file ({dim: value or [values]}) overrides."""
    spec: dict[str, frozenset | None] = {d: GENERAL_DEFAULTS.get(d) for d in GENERAL_DIMS}
    for c in all_chips:
        if c in CHIP_TO_GENERAL:
            d, v = CHIP_TO_GENERAL[c]
            spec[d] = v
    acts = spec["speech_act"] or frozenset()
    if acts & {"question", "request/command"} and not any(c in all_chips for c in ("[MAYBE]", "[SURE]")):
        spec["certainty"] = frozenset({NA_CERTAINTY})
    for d, v in (override or {}).items():
        spec[d] = frozenset([v] if isinstance(v, str) else v)
    return spec


def dims_in_chips(chips: list[str]) -> set[str]:
    return {CHIP_TO_GENERAL[c][0] for c in chips if c in CHIP_TO_GENERAL}


def critical_match(dimension: str, variant_value: str, label: str | None) -> bool | None:
    """Does an extracted critical label honour the variant's critical value?
    D-007: on certainty, 'plain assertion' is honoured by plain OR emphatic."""
    if label is None:
        return None
    if dimension == "certainty" and variant_value == PLAIN_A:
        return label in (PLAIN_A, EMPH)
    return label == variant_value


def is_unclear(label: str | None) -> bool:
    return label is not None and label in UNCLEAR

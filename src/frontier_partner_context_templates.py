"""Frozen templates + instruction text for partner_context Stage 0 (written before any turn was authored).
sha256 of this file's TEMPLATES/INSTRUCTION/CHECKER strings is recorded in analysis/frontier/partner_context/turns_meta.json."""
import hashlib, json

SEED = 20261102
NEG_TOKENS = ["not", "no", "never", "n't", "none", "nothing", "without", "neither", "nor", "cannot"]
TEMPLATES = {
    "polarity": {
        "N": "What happened with {topic}?",
        "D": "I guess {topic} worked out as planned.",
        "X": "I heard {topic} did not work out.",
        "Q": "Did {topic} happen?",
    },
}
INSTRUCTION = (
    "You write ONE short remark that a conversation partner says to an AAC user just before the user composes a reply.\n"
    "Keywords (the only information you have about the topic): {bare}; {noncritical}\n"
    "Template for the remark type {type}: {template}\n"
    "Fill the {{topic}} slot with a natural short noun phrase made from the keywords only, and lightly adapt the surface form so it is fluent "
    "English, keeping the template's meaning and move. Do not add facts beyond the keywords. At most 14 words. "
    "For types N, D and Q do not use any negation word (not, no, never, n't, nothing, without, neither, nor, cannot). "
    "Type Q must be a polar yes/no question with no negation. "
    "Reply with only the remark, no quotes."
)
RETRY_SUFFIX = "\nRephrase differently from the plain template."
CHECKER = (
    "A conversation partner says something to a person who is about to reply. Topic keywords: {kw}.\n"
    "Partner's remark: \"{turn}\"\n"
    "Two possible replies the person might give:\n"
    "Reading 1: {r1}\nReading 2: {r2}\n"
    "Which reply does the partner's remark make more likely? Answer with exactly one of: 1, 2, neither."
)
READINGS = {"aff": "about \"{kw}\": the thing happened / is so (affirmative)",
            "neg": "about \"{kw}\": the thing did not happen / is not so (negated)"}

def sha():
    return hashlib.sha256(json.dumps([TEMPLATES, INSTRUCTION, RETRY_SUFFIX, CHECKER, READINGS, NEG_TOKENS], sort_keys=True).encode()).hexdigest()

"""Round-2 frozen authoring/checker text for partner_context (amendments A3-A5, written before any turn was authored)."""
import hashlib, json
SEED = 20261103
NEG_TOKENS = ["not", "no", "never", "n't", "none", "nothing", "nobody", "without", "neither", "nor", "cannot"]
XC_TOKENS = ["no", "nobody", "nothing", "none", "never", "no one"]
SPEC = {
    "D": "the partner says, in their own natural words, that this thing happened or is the case. Use NO negation word (not, no, never, n't, nothing, none, nobody, without, neither, nor, cannot).",
    "Xa": "the partner says that this thing did not happen or is not the case, using an explicit negation word (not, n't, never or no) in whatever sentence structure is natural.",
    "Xb": "the partner says that this thing did not happen or is not the case WITHOUT any negation word: express it with a negative-meaning verb or phrase (such as failed, fell through, was cancelled, was dropped, was called off); choose naturally for the topic.",
    "Xc": "the partner says that this thing did not happen or is not the case using a quantifier or existential negation (nobody, nothing, none, no sign of, no one, never).",
    "Q": "the partner asks a plain yes/no question about this thing. Use NO negation word. Use only words from the keywords (any inflection) plus function words; introduce no other topic words, people, places or things.",
}
INSTRUCTION = (
    "You write ONE short remark that a conversation partner says to an AAC user just before the user composes a reply.\n"
    "Keywords (the only information you have about the topic): {bare}; {noncritical}\n"
    "Remark type: {spec}\n"
    "Use only the topic implied by the keywords: no new people, places, objects or facts. Natural everyday English, one sentence, at most 14 words. "
    "Do not use the words 'work out' or 'worked out'. Reply with only the remark, no quotes."
)
RETRY_SUFFIX = "\nRephrase it in a different way from the obvious phrasing."
CHECKER = (  # same wording as A2
    "A conversation partner says something to a person who is about to reply. Topic keywords: {kw}.\n"
    "Partner's remark: \"{turn}\"\n"
    "Two possible replies the person might give:\n"
    "Reading 1: {r1}\nReading 2: {r2}\n"
    "Which reply does the partner's remark make more likely? Answer with exactly one of: 1, 2, neither."
)
READINGS = {"aff": "the user's sentence will say that \"{kw}\" is so / happened (an affirmative sentence)",
            "neg": "the user's sentence will say that \"{kw}\" is not so / did not happen (a negated sentence)"}
LOCK = ("Topic keywords: {kw}.\nA partner's question: \"{turn}\"\n"
        "Does the question mention any entity, place, person, object or topic that is NOT in the keyword list (ignoring function words and word inflections)? Answer exactly yes or no.")
# echo / reply judge prompts (A3.1); EJ2 reverses option order. Judge sees ONLY turn + output.
EJ = ("A conversation partner said: \"{turn}\"\nAn AAC user then produced this sentence: \"{out}\"\n"
      "Question A (echo): Does the sentence re-use the partner's own value-bearing wording (the same negation-bearing or outcome-bearing phrase, verbatim or a near-verbatim paraphrase of the partner's remark), instead of the user's own fresh statement about the topic?\n"
      "Question B (reply): Is the sentence phrased as a reply that answers or acknowledges the partner (e.g. starts with yes, yeah, oh, right, I heard, I know, or reports what the partner said), rather than the user's own message?\n"
      "Answer in exactly this format: A=<{o1}|{o2}> B=<{o1}|{o2}>")
def sha():
    return hashlib.sha256(json.dumps([SEED, NEG_TOKENS, SPEC, INSTRUCTION, RETRY_SUFFIX, CHECKER, READINGS, LOCK, EJ], sort_keys=True).encode()).hexdigest()

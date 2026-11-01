"""Prompt templates (SPEC v0.1). Template text lives in prompts/*.txt; this module
renders it and fingerprints it.

  P0  generic (old prompts/expand.txt wording) + chip legend   greedy  T=0    k=1  1 sentence
  S3  identical template to P0 (prompts/P0.txt), sampled          T=0.7  k=3  1 sentence each
  P1  preservation instructions                                    greedy  T=0    k=1  1 sentence
  P2  spanning: JSON list of 3 different meanings                  greedy  T=0    k=1  3 sentences

Placeholders: {legend} (prompts/chip_legend.txt, in EVERY prompt), {context}
("Situation: ...\\n" or empty) and {input} (channel-specific input_text). Rendering
uses plain str.replace, so JSON braces in templates are safe.
"""
from __future__ import annotations

import hashlib
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
LEGEND_FILE = PROMPT_DIR / "chip_legend.txt"

# Chip vocabulary in legend order; chips are always rendered in this fixed order.
CHIP_ORDER = ["[NOT]", "[YES]", "[?]", "[ASK]", "[REFUSE]", "[TELL]", "[MAYBE]", "[SURE]",
              "[MUST]", "[WANT]", "[I]", "[YOU]", "[WE]", "[THEY]", "[PAST]", "[NOW]",
              "[LATER]", "[PLEASE]", "[PLAIN]"]


@dataclass(frozen=True)
class PromptSpec:
    prompt_id: str
    template_file: str
    temperature: float
    k: int               # number of independent samples (requests) per input
    n_suggestions: int   # suggestions expected in ONE response
    max_tokens: int
    legend_file: str = "chip_legend.txt"   # P0x: extended legend; default keeps P0..P2 shas


PROMPTS: dict[str, PromptSpec] = {p.prompt_id: p for p in [
    PromptSpec("P0", "P0.txt", 0.0, 1, 1, 96),
    PromptSpec("S3", "P0.txt", 0.7, 3, 1, 96),
    PromptSpec("P1", "P1.txt", 0.0, 1, 1, 96),
    PromptSpec("P2", "P2.txt", 0.0, 1, 3, 256),
    # P0 template + extended legend (alias chips, [·] padding = ignore, "Meaning:" line).
    # Separate id so P0's sha / request_keys / cache stay valid. Not in DEFAULT_PROMPTS.
    PromptSpec("P0x", "P0.txt", 0.0, 1, 1, 96, "chip_legend_x.txt"),
]}
DEFAULT_PROMPTS = ["P0", "S3", "P1", "P2"]   # what build_requests uses when --prompts is omitted


_NUM_CHIP = re.compile(r"^\[\d+\]$")
_warned: set[str] = set()


def _chip_rank(c: str) -> tuple[int, int]:
    if c in CHIP_ORDER:
        return (CHIP_ORDER.index(c), 0)
    # Numeric quantity chips ([2], [5]) are used by pilot items but are NOT in the SPEC v0.1
    # vocabulary/legend; accepted provisionally, placed after the time chips.
    return (CHIP_ORDER.index("[LATER]"), int(c[1:-1]) + 1)


def sort_chips(chips: list[str]) -> list[str]:
    unknown = [c for c in chips if c not in CHIP_ORDER and not _NUM_CHIP.match(c)]
    if unknown:
        raise ValueError(f"unknown chips {unknown}")
    for c in chips:
        if _NUM_CHIP.match(c) and c not in _warned:
            _warned.add(c)
            print(f"warning: numeric chip {c} is not in the SPEC legend", file=sys.stderr)
    return sorted(dict.fromkeys(chips), key=_chip_rank)


@lru_cache(maxsize=None)
def _read(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8").strip()


def template_sha(prompt_id: str) -> str:
    """sha256 over template + legend text: changes if either file changes."""
    spec = PROMPTS[prompt_id]
    blob = _read(spec.template_file) + "\n---legend---\n" + _read(spec.legend_file)
    return hashlib.sha256(blob.encode()).hexdigest()


def render(prompt_id: str, input_text: str, context: str | None = None) -> str:
    spec = PROMPTS[prompt_id]
    ctx = f"Situation: {context.strip()}\n" if context else ""
    return (_read(spec.template_file)
            .replace("{legend}", _read(spec.legend_file))
            .replace("{context}", ctx)
            .replace("{input}", input_text))


def all_shas() -> dict[str, str]:
    return {pid: template_sha(pid) for pid in PROMPTS}


if __name__ == "__main__":
    print(render("P2", "Keywords: [NOT] want go party", "At home after school."))
    print(all_shas())


# Encodings for follow-up Exp B (aliases are defined in prompts/chip_legend_x.txt, i.e. P0x).
ALIAS = {"[NOT]": "[NEGATIVE]", "[YES]": "[AFFIRMATIVE]", "[?]": "[QUESTION]", "[ASK]": "[REQUEST]",
         "[REFUSE]": "[DECLINE]", "[TELL]": "[STATEMENT]", "[I]": "[I-DO-IT]", "[YOU]": "[YOU-DO-IT]",
         "[THEY]": "[THEY-DO-IT]", "[PLEASE]": "[POLITE]", "[PLAIN]": "[NO-PLEASE]"}
PAD = "[·]"   # P0x legend: "a spacer chip with no meaning: ignore it"
NL_PHRASE = {"[NOT]": "negative (not)", "[YES]": "affirmative", "[?]": "a question",
             "[ASK]": "a request to the listener", "[REFUSE]": "declining",
             "[TELL]": "a plain statement", "[I]": "I am the one doing it",
             "[YOU]": "the listener is the one doing it", "[THEY]": "someone else is the one doing it",
             "[PLEASE]": "polite", "[PLAIN]": "no added politeness"}


def nl_meaning(chips: list[str]) -> str:
    """Natural-language commitment field carrying exactly `chips` (legend order)."""
    return "Meaning: " + ", ".join(NL_PHRASE[c] for c in sort_chips(chips)) + "."

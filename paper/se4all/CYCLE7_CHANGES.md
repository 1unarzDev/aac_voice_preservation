# SE4All cycle 7 changes (2026-11-02)

Build: docker latexmk, 8 pages including references, all pages viewed. Not committed. No model calls.

- **Macros**: new `cc_*` block in `make_macros.py` reading `analysis/chip_controls/summary.json` (irrelevant-chip gain range, plain-word difference on speech act, count of dimensions within 5 pp, with asserts). No typed numbers.
- **Lever reworded**: Sec. II says the tested lever is the missing cue, the chip being one encoding and the probe; the abstract says "supplying the missing speech-act cue, as a one-tap chip or a plain word" (one clause added); the "manipulation check" sentence and the Conclusion now say "supplied cue".
- **Controls paragraph** (Sec. III-A, "Controls: the cue, not the chip"): irrelevant chip rules out "any added chip helps" (chip beats it by 30.0 to 80.9 pp); plain word within 2.1 pp of the chip on 5 of 6 dimensions and 8.2 pp better on speech act; framed as any AAC system being able to surface the cue as an ordinary word, with no new interface vocabulary.
- **Harness tie** (extension-cost paragraph): a new input encoding is one more channel, as with the plain-word control, re-scored with the same critical-match metric and no change to the verdict code. Wording is limited to what the scripts show (`src/build_chip_controls.py`, `src/analyze_chip_controls.py`).
- Abstract stays about 170 words.

# CALE-AI cycle 6 changes (2026-11-01 night)

Build: docker latexmk, body ends on page 8 (references begin on page 8 and run to page 10), all pages viewed. Not committed. No new numbers; all via existing macros.

- **Title**: "Gains Hide Failures: A Ledger Evaluation of a Commitment Guard for AAC Sentence Expansion" (no author or project wording). Conclusion opener "The guard works as intended" replaced by the measured statement (+pass points, repair rate, strict-check pass-to-fail, feedback beats resampling at matched temperature).
- **Raters**: audit "designed for 3 independent raters per text"; body adds that the pilot's raters were effectively about 1.1 independent.
- **Usable rate**: "resolved items" in abstract and Sec. 6.2.
- **Baseline**: abstract keeps G1-G1r and states "guard at temperature 0, resampling at 0.7"; body calls the matched G1t-G1r (+6.94 confirmation) "the clean feedback effect"; contributions give both. "Same budget" changed to "same retry cap".
- **Pass metrics**: joint-pass repair rate removed from the body (not in the glossary).
- **API model**: "one commercial API model (gpt-6.1-terra)".
- **Timestamps**: "git-timestamped" replaced by "pre-specified in version control; a hash of the protocol was deposited publicly after the confirmation freeze, so it does not certify the freeze, and repository timestamps are not independently verifiable" (no URL).
- **Concurrent paper**: now says it shares data (confirmation items, human-written pairs, scorer) and that this paper's results are reported in full here.
- **Fig. 1**: caption defines chips ([NOT], [?], [ASK], [YOU], [I], [PLAIN]); column "Fix returned" renamed "Guard output".
- **Abstract**: about 200 words, says "speech-act", leads with results, ends on predictions and the design.
- **References**: dropped gorenshtein2026intentdrift, williamsceci2026biased, wang2025toxirewrite (citations removed; not in lit/, non-essential). `% VERIFY` added in refs.bib for wang2026politemisaligned, ziegenbein2026editing, elgaar2025lingconv, zhao2025politeness (not in lit/). Lacosse, Frisch, Choudhury, Pauli are in lit/.
- Not done: prior-work table, best-of-n baseline, joint-primary restructure of Table 3, glossary move to page 1 (needs new analysis or space).

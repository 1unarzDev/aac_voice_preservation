# SE4All cycle 1 changes (2026-11-01)

Build: docker latexmk, 7 pages including references (limit 8). Not committed.

## What changed
- **Restructured around the SE thesis** ("testing the test oracle"). New title; abstract leads with the hw1 results, then the two oracle defects, then the human kappa.
- **Harness figure** (TikZ, Fig. 2): family spec, channel renderer, R5 validator, generator, extractor J1/J2 + arbiter, verdict code, and a dashed box for the oracle tests.
- **Traceability table (Table I):** R1-R5 with source, executable test, and what the test found. The text says plainly that all five are the authors' proposal.
- **Worked defect-to-regression-test trace** (Table III, Sec. IV): the relaxed acceptance oracle that hid substitutions (A) and the W-B input-builder defect found by the R5 audit (B).
- **hw1 is the primary replication.** Table II puts hw1 beside W-C. Caveats stated: 6-7 writers per contrast, exploratory, not preregistered, direction and consistency rather than interval width.
- **Judge validation** from the two judge_validation JSONs (kappa .97 / .94, verdict agreement, verdict kappa range). The first gate is labelled as being on discovery items.
- **Elicitation** is two sentences (20.8% vs 100% negation loss), framed as anchoring the Assumption channel, with the compressor flagged as not a user model.
- **Cut:** W-D (one table cell), the guard (figure, table and Table IV), P2/S3 prompts, the checker figure, the discovery human-gate table, and the Part 4 audit numbers.
- **Claim discipline:**
  - "pre-specified and git-timestamped", with the hash-deposit caveat (it post-dates the W-C freeze);
  - the Figure 1 "owner" labels are declared a design choice;
  - one naming scheme: Act-gain, Politeness, Default (P1-P3 are mentioned once as the pre-specified names);
  - Positionality rewritten per `aac_domain_review.md`; authorship limitation and an intended-use sentence added.
- **AAC wording:**
  - "crowd-written AACText";
  - the chip is a probe, with its access-method cost;
  - symbol AAC is out of scope;
  - no "spoken as the user's own".
- **Ethics:** author-confirmed facts folded in (adult classmates, consent, payment and food). The AUTHOR-CONFIRM comment is removed.
- **Related work:** test-oracle problem (Weyuker 1982, Barr 2015), metamorphic testing (Chen 2018), mutation analysis (Jia & Harman 2011) and RE for ML (Vogelsang & Borg 2019).
- **Fig. 1:** three hw1 cards chosen by the declared SHA rule (polarity, speech act, politeness), each with its stratum rate. Strings are re-verified against `runs/hw1/outputs.jsonl` by `make_macros.py`.
- **Macros:** `make_macros.py` gained a cycle-1 block (hw_*, hwp*, hwe_*, jve_*, jvh_*, el_*, hash_release) and writes `hw_gallery_table.tex`. A diff of the prose shows no hand-typed result numbers; the typed numbers that remain are design constants.

## Could not do, and why
- Part 4 repair audit and Part 17 are not reported. Part 17 has not returned, and Part 4 is a pilot, so the paper has one qualitative sentence in Threats and no numbers.
- Vogelsang & Borg page range is from memory (`% VERIFY` in `refs.bib`). The other new classics were entered from memory of the published records, and the bib header says so.
- The deposit-hash release tag is named from the brief and is not verified from the repo (no local git tag). Confirm it before submission.
- No AAC user or clinician input, and no AI-disclosure text (lab supplies it).
- hw1 per-model politeness numbers are macros read from `primary_by_model.csv`, but there is no Part 15 (10-writer speech-act) update yet.

## Remaining weaknesses
- The oracle is still an LLM, and the arbiter ran after outcomes were known. The human kappas use plurality references and taught coders.
- hw1 rests on 6-7 writers per contrast, and the Act-gain and Default contrasts are near manipulation checks.
- Four small or quantized models, one prompt, English only; the T1 legend confound and T2 Bayes-rational default framing are not addressed here.
- The R4 composition requirement has only a pointer to the omitted W-D study.
- No stakeholder derivation of R1-R5.
- The abstract is dense.

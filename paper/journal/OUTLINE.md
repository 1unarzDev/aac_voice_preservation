# TACCESS journal manuscript: outline (2026-11-04)

Target: ACM Transactions on Accessible Computing, submit about Dec 10-15 (free through the authors' university ACM Open agreement). Template: `acmart` `manuscript,review` (builds; see Build). Thesis (from `ideas/frontier/CRITIC_SYNTHESIS.md`): critical-commitment preservation is a hard filter, not the objective. The objective is covering the writer's whole intended message with approval-gated drafts at the lowest tap and reading cost, validated against writers and SLPs, with attribution (loss / violation / assumption) explaining uncovered intent.

Files in this folder: `main.tex` (compiling skeleton, section stubs call real macros), `make_macros.py` (reads analysis files, writes `results_macros.tex` and `macro_sources.json`, 245 macros), `refs.bib` (13 entries copied from the CALE-AI bib plus two concurrent-work placeholders, all `VERIFY`), this file.

Macro convention: `\jm` + camelCase key with digits spelled out and separators dropped (`p17` -> `pOneSeven`, `f1` -> `fOne`). Example: `\jmpOneSevenDiffUsable` (Part 17 repaired-minus-control usable), `\jmfOneRevPolChip` (polarity reversals per 1,000, chip). Lo/Hi suffixes carry the interval. `macro_sources.json` maps every macro to its analysis file. A slot that is not yet filled has `\jmslotSFiveReady` / `\jmslotCovReady` = 0.

## 1. Title and abstract draft

**Title (working).** Necessary but Not Sufficient: Preserving the Writer's Commitments and Covering Their Intended Message in LLM Keyword Expansion for AAC

Alternative: Say What They Meant: Commitment Preservation, Intent Coverage and Writer-Grounded Validity for LLM-Mediated AAC.

**Abstract (macro-backed; every number below is a macro, written here as the macro name).**
Keyword-to-sentence expansion lets a person who types a few words speak a full sentence, but a model that drops a negation, swaps who does what, or turns a request into a question can say something the writer did not mean. We build a measurement harness around seven kinds of silent meaning change and apply it to six models from five families on sentence pairs written by 20 human writers. Models default to the affirmative reading in `\jmbreadthMinAff`% or more of bare inputs, and that default is not a prompt-legend artifact (`\jmlegendNoLegendAff`% without the legend). A one-token cue restores the commitment: negation reversals fall from `\jmfOneRevPolBare` to `\jmfOneRevPolChip` per 1,000 messages and politeness reversals from `\jmfOneRevPoliteBare` to `\jmfOneRevPoliteChip`; an irrelevant control cue does nothing. A guard raises speech-act preservation on fresh families from `\jmgtJointP`% to `\jmgtJointG`%; weighting failures by what two speech-language pathologists judged serious cuts the failure rate from `\jmslpWCueBare`% to `\jmslpWCueChip`% with a chip. In a blind audit by three classmate raters per item, repairs showed no detectable usability cost under the frozen rule (`\jmpOneSevenDiffUsable` points, interval `\jmpOneSevenDiffUsableLo` to `\jmpOneSevenDiffUsableHi`). Preserving the critical commitment is nevertheless necessary and far from sufficient: writers accepted `\jmpOneEightAcceptYesK` of `\jmpOneEightAcceptN` drafts as written, and judge-correct drafts still failed the writer in `\jmwmRightR1`% of cases, because the draft lost detail the keywords could not carry and misresolved who did what, not because it added content. The cue lifts the writer's intended-version match by `\jmpOneEightCueGain` points; automatic judges agree with a human arbiter in only `\jmpOneNineAgreeJOne`% (judge 1) and `\jmpOneNineAgreeJTwo`% (judge 2) of codings against `\jmpOneNineAgreeArb`% for humans, so we propose approval-gated draft sets scored on coverage of the writer's whole intent per tap, and report the pilot of that measure. [slot: one clause with the intent-coverage pilot result, or drop.]

Rules applied (LOOP_BRIEF tone rule): leads with what works; the limitation is the final-section material, not the abstract's last sentence; no AAC-user-benefit, IRB or "pre-registered" claim. The sentence "ends on the proposal" must be rechecked once the coverage pilot lands.

## 2. Contribution list (what the cover letter and introduction commit to)

1. A commitment-preservation harness for LLM keyword expansion: seven-dimension commitment vector, minimal-pair design with writer-written pairs (hw1), controlled channels (bare, chip, plain word, irrelevant chip, natural-language cue), judge plus human arbiter, family/writer-cluster bootstrap. Evidence: hw1, chip_controls, legend_test, model_breadth.
2. A per-dimension default-elicitation profile, priced per 1,000 messages, with the cue as the intervention (same-items measurement on 332 units, three local models plus terra). Not a claim that the affirmative default is new (cite Chen et al., ACL 2023).
3. Cue restoration is replicated across six models and five families, controlled by an irrelevant cue and a natural-language cue, and survives a no-legend arm.
4. A guard and a repair-usability audit with a frozen decision rule (Part 17): guard transfer to fresh speech-act families, plus a blind three-rater audit showing no detectable usability cost (interval includes 0) and large gains over each original failure in meaning preserved and invented stance.
5. SLP-weighted failure: the first severity weights for AAC meaning errors we know of (n=2, expert review), and a clinically weighted failure rate per arm.
6. Necessary-not-sufficient result: writer-grounded whole-message analysis (Part 18, 200 outputs, 20 writers). Rejection is compression loss and event/role misresolution, not added content. Consultants independently asked for the same relations.
7. Instrument validity as a result: judge-writer kappa `\jmpOneEightKappa`, SLP-judge kappa about `\jmslpJudgeKappaOne`/`\jmslpJudgeKappaTwo`, human-arbiter agreement `\jmpOneNineAgreeArb`% (Part 19), "Can you...?" coded as a request by `\jmpOneNineCanYouRequest`% of coders.
8. Ask-policy null: model-confidence and CLAM-style ask rules do not beat gated-random at matched taps; cue-on-everything is the efficient policy on the measured dimensions (frontier figure).
9. Requirements from two paid AAC-user design consultants: R6 (drafts never spoken without approval), a NOT-scope list, exact-copy default, differing drafts shown. Reported as requirement changes, not as experience data.
10. (Slot) Stage 5 human checks of treated outputs and source labels (Parts 20-25), and (slot, not yet run) intent coverage of approval-gated draft sets per tap.

## 3. Section plan with exact claims, evidence paths and macro sources

Convention: "claim" is the sentence the section must be able to support. "Macros" are keys in `results_macros.tex` (prefix `\jm` omitted). "ADD" marks a macro that `make_macros.py` still has to produce (the data exist).

### S1 Introduction
- Claim: accuracy-style metrics hide silent reversals; a gain-only evaluation of commitment preservation is necessary-not-sufficient; what works is a one-token cue and an approval-gated design.
- Evidence: `analysis/EVIDENCE_MAP.md`; macros of abstract.
- Contributions list from section 2. End with a roadmap, no limitation stacking.

### S2 Related work
- AAC prediction and expansion (KWickChat, SpeakFaster, Cai 2022 abbreviation expansion, Valencia 2023, Valencia 2020 agency, Arnold 2020), `refs.bib`.
- Affirmative bias: Chen et al. ACL 2023 (`chen2023say`) is the prior result; we cite it and do not claim the default as new. We add the human base rate and per-dimension price. Also Braun (EMNLP Findings 2025, direction is task-dependent), from `CRITIC_SYNTHESIS.md` C2; add to bib after verification.
- Ask/assume/show-two: Conf-Gen, INTENT-SIM, AskBench (all `VERIFY` before citing; C1 section of the critic synthesis lists their status [O]/[S]).
- Validity of judges: Zheng 2023, PPI (Angelopoulos 2023), Frisch 2026 (calls for measuring intent alignment).
- Concurrent work: the SE4All archival paper and the CALE-AI workshop paper (`concurrent_se4all`, `concurrent_caleai`, placeholders). State which results they contain (section 9).

### S3 Requirements and commitment model
- Claim: R1-R5 were rated important by both consultants; R6 (drafts never spoken without approval), NOT-scope, exact-copy default and differing drafts are consultant-driven changes. Commitment vector has seven dimensions; the whole-message finding proposes an eighth, event/role structure (who does what).
- Evidence: `annotation/returns_consultant/{C01,C02}/design_review_answers.txt`, `expert_package/consultant/`, `expert_package/PAPER_WORDING.md` (status words: expert annotators, paid design consultants, expert review, not a population estimate).
- Macros: none (qualitative). Report requirement changes only (a table: suggestion, change made or not, why) from the closed feedback log.

### S4 Study design and materials
- Claim: designs, populations and estimators are stated once; every endpoint has a denominator.
- Content: hw1 (20 writers, `\jmhwFamilies` analysed families, 6-7 writers per contrast), channels, 6 models / 5 families (`\jmbreadthModels`), judges J1/J2 and human arbiter, W-C discovery vs confirmation populations, cluster bootstrap seeds (SEED 20261031), Part 17 frozen rule (`annotation/COORDINATOR_STEPS.md` section 4), SLP panel design, consultant package. Ethics paragraph: canonical text in `main.tex` (annotators adult non-author classmates, consented, paid; no IRB claim).
- Evidence: `analysis/hw1/report.md`, `analysis/EVIDENCE_MAP.md`, `analysis/model_breadth/report.md`.

### S5 Results I: default and cue (Figure 3 heat table feeds from here)
- Claim 5a: with bare input, models choose the affirmative reading in at least `\jmbreadthMinAff`% across six models, and `\jmlegendNoLegendAff`% [`Lo`, `Hi`] with no legend (so the default is not a legend artifact).
  Evidence: `analysis/legend_test/summary.json`, `arm_share.csv`; `analysis/model_breadth/summary.json`. Macros: breadthMinAff, legendNoLegendAff(+Lo/Hi), legendAff.
- Claim 5b: hw1 chip gain over a non-critical cue is `\jmhwChipGain` pp [`\jmhwChipGainLo`, `\jmhwChipGainHi`] (6 writers, 67 families; claim direction and consistency, not interval width). Politeness-removal and affirmative-share contrasts are `\jmhwPolGain`, `\jmhwAffShare`.
  Evidence: `analysis/hw1/primary_contrasts.csv`, `summary.json`. Macros: hwChipGain, hwPolGain, hwAffShare.
- Claim 5c: the effect is cue content, not extra tokens: an irrelevant chip adds about nothing (agent `\jmctlIrrelAgent`, certainty `\jmctlIrrelCert`, polarity `\jmctlIrrelPol` pp); a natural-language cue equals a chip within 5 pp on most dimensions.
  Evidence: `analysis/chip_controls/summary.json` (`decision_by_dimension`). Macros: ctlIrrelAgent/Cert/Pol. ADD: remaining dimensions and the nl-cue equivalence rows.
- Claim 5d: same-items reversals per 1,000 (332 units): polarity `\jmfOneRevPolBare` to `\jmfOneRevPolChip` (chip) / `\jmfOneRevPolWord` (word); politeness `\jmfOneRevPoliteBare` to `\jmfOneRevPoliteChip` / `\jmfOneRevPoliteWord`; speech-act restoration `\jmfOneActRestoreChip`% (chip) to `\jmfOneActRestoreChipG`% (chip plus guard). Chip and word are not distinguishable on polarity and politeness.
  Evidence: `analysis/frontier/default_profiles/followup/{f1_price.csv,f1_restoration.csv,f1_decisions.csv}`. Macros: fOneRev*, fOneActRestore*, fOneUnits.
- Claim 5e: replication on all six models; per-model rows go in a supplement table (ADD: per-model cells from `analysis/model_breadth/*.csv`; Gemini lite as a seventh row from `gemini_*` files, flagged as machine API replication).

### S6 Results II: guard and repair cost
- Claim 6a: the guard transfers to fresh speech-act families: joint pass `\jmgtJointP`% to `\jmgtJointG`% (CIs `Lo`/`Hi`), `\jmgtTargets` targets, `\jmgtFamilies` families. Deletion-only (strip) earns part of that gain (ADD from `guard_wc/headline.json`: `G1s`, strict repairs 251/478).
  Evidence: `analysis/guard_wc/headline.json`, `ACCEPTANCE.md`, `analysis/guard_baseline/summary.json`. Macros: gtJointP, gtJointG.
- Claim 6b (Part 17): repaired usable `\jmpOneSevenRepUsable`% vs control `\jmpOneSevenCtlUsable`%, difference `\jmpOneSevenDiffUsable` [`Lo`,`Hi`]: no detectable usability cost under the frozen rule (interval includes 0). Preserving `\jmpOneSevenDiffPres`, usable-and-preserving `\jmpOneSevenDiffUsPres` (control items are easier: the gap is an item-difficulty effect, state once). Paired with each own failed original: meaning preserved `\jmpOneSevenOrigPres` [`Lo`,`Hi`] p=`\jmpOneSevenOrigPresP`, invented stance `\jmpOneSevenOrigStance` p=`\jmpOneSevenOrigStanceP`, usable `\jmpOneSevenOrigUsable` (ns). Gemma repairs are `\jmpOneSevenGemmaUsable`% usable (K/N `\jmpOneSevenGemmaUsableK`/`N`).
  Evidence: `analysis/repair_audit_v2/{summary.json,report.md}`. Do not write "usable repairs are as good as controls"; write what the rule says.
- Claim 6c (SLP, n=2 expert review): negation severity `\jmslpNegSeverity`/5, block `\jmslpNegBlock`%; clinically weighted failure: guard `\jmslpWGuardBase`% to `\jmslpWGuardG`%; cue `\jmslpWCueBare`% to `\jmslpWCueChip`% (chip) / `\jmslpWCueWord`% (word); repairs acceptable `\jmslpAccRepair`% vs originals `\jmslpAccOrig`%.
  Evidence: `src/score_slp_panel.py` run on `expert_package/returns_slp` (make_macros runs it into tmp and parses). Macros: slpNegSeverity, slpW*, slpU*, slpAcc*.

### S7 Results III: necessary but not sufficient (Figure 2 waterfall)
- Claim 7a: waterfall over 200 writer-rated outputs: judge says critical right (`\jmwmRightN` of 200) -> writer says it is the intended version (49 of 126 judged; ADD `wmRightIntendedK` = N - `\jmwmRightR1K`) -> accepted as written (`\jmpOneEightAcceptYesK` of `\jmpOneEightAcceptN`). The cue lifts match from `\jmpOneEightMatchBare`% to `\jmpOneEightMatchChip`% (+`\jmpOneEightCueGain` [Lo, Hi], cluster over 20 writers).
  Evidence: `analysis/intent_check/summary.json`, `analysis/whole_message/summary.json`. Macros: pOneEightMatch*, pOneEightCueGain, wmRight*, pOneEightAccept*.
- Claim 7b: among judge-correct outputs the writer did not accept, the primary reasons are substitution (event/role misresolution) `\jmwmRightSubst`% and dropped writer detail `\jmwmRightDropped`%; added content is `\jmwmAdded`%. `\jmwmDroppedUnrecShare`% of non-accepted writer sentences contain words absent from the keywords (compression loss, the model could not have known them). Classifier validated against a 40-item hand check (kappa `\jmwmHandKappa`; hand coder is an LLM, state once).
  Evidence: `analysis/whole_message/{summary.json,report.md}`, `analysis/frontier/whole_message/REPORT.md` and Follow-up (LOWO parity result). Do NOT claim that expansions add unrequested content.
- Claim 7c (slot): human checks of treated outputs and source labels from Stage 5 Parts 20-25 enter as Section 7.4 (see section 6 below).
- Claim 7d (slot, not yet run): intent coverage of approval-gated draft sets per tap (see section 6 below).

### S8 Results IV: validity of the measuring instrument
- Claim: automatic judges do not track writers or clinicians well enough to be the final metric; the arbiter does.
  - Writer vs judge kappa `\jmpOneEightKappa`; SLP vs judge kappa `\jmslpJudgeKappaOne` / `\jmslpJudgeKappaTwo`.
  - Humans vs arbiter `\jmpOneNineAgreeArb`% (kappa `\jmpOneNineKappaArb`) vs J1 `\jmpOneNineAgreeJOne`% (kappa `\jmpOneNineKappaJOne`) vs J2 `\jmpOneNineAgreeJTwo`% (kappa `\jmpOneNineKappaJTwo`) over `\jmpOneNineCodings` codings.
  - "Can you...?" coded as request/command by `\jmpOneNineCanYouRequest`% (`\jmpOneNineCanYouK`/`\jmpOneNineCanYouN`), so the alternative coding is not what humans do.
- Evidence: `analysis/arbiter_check/summary.json`, `intent_check/summary.json`, `whole_message/summary.json`. Consequence: no J1 fallback in primary estimates; PPI-style correction is a methods paragraph, not a headline.

### S9 Cost, frontier and ask policies (Figure 3)
- Claim: reversals per 1,000 vs taps: always-commit `\jmdpAlwaysCommitPol` [Lo, Hi] (0 taps); ask policies ranked by prior at 10% taps `\jmdpAskPriorPol`; gated-random at 10% taps `\jmdpAskRandPol`; CLAM-style gated `\jmclamPol`. Intervals overlap: ask policies do not beat gated-random. Cue on every message (1,000 taps/1,000) reaches `\jmfOneRevPolChip` (chip) / `\jmfOneRevPolWord` (word). SLP weights: polarity `\jmwPol`, politeness `\jmwPolite`, speech act `\jmwAct`; weighted share of total failure `\jmwSharePol`/`Polite`/`Act`.
- Evidence: `analysis/frontier/default_profiles/{intervention_same_items_r3.csv,policy_budgets_r3.csv,slp_weighted_price_h2.csv,followup/clam_contrasts.csv}`; figure source `fig_reversals_vs_asks_r3.pdf`. State the arithmetic assumption (asked user supplies the cue, rho = 1) and that r3 "transported rho" was superseded by F1 measured rows (D-091).

### S10 Discussion, limitations, ethics, conclusion
- Limitations, stated once: hw1 is exploratory with 6-7 writers per contrast; SLP and consultants n=2 each (expert review, not population estimates; consultants not a sample of AAC users); machine judges are validated only through the human checks above; no AAC-user benefit or deployment claim; no IRB or exemption claim ("did not seek an institutional review determination").
- Conclusion: lead with what works (cue, guard, no detectable usability cost) and the new target (coverage of whole intent per tap, with attribution), one sentence on the open coverage problem.

## 4. Figure plan

1. **Pipeline figure** (S4). Elements: keywords + optional cue -> model -> draft(s) -> judge / human arbiter -> commitment vector (7 dimensions) -> writer approval gate (R6) -> speak. Mark where hw1, Part 17, Part 18, SLP, consultants plug in. Reuse style of `paper/figs/fig_pipeline.pdf` (do not reuse content verbatim from SE4All; redraw to show approval gate and coverage). Source: static, no numbers.
2. **Necessary-not-sufficient waterfall** (S7). Bars: 200 outputs -> judge critical right (`wmRightN`) -> writer says intended version -> accepted as written, with chip and bare split. Source: `analysis/intent_check/summary.json`, `analysis/whole_message/summary.json`. Callout: reasons for loss between bars (substitution / dropped / fluency). Script to write: `paper/journal/figs/make_waterfall.py` reading the same files as the macros.
3. **Reversals-per-1,000 vs taps frontier with baselines** (S9). X: taps per 1,000 messages; Y: reversals per 1,000 (log or broken axis). Lines per dimension (polarity, politeness, speech act). Baselines: always-commit, ask-prior-ranked, ask-gated-random, CLAM-style, cue-everywhere (chip, word), chip + guard. SLP-weighted overlay. Source: `intervention_same_items_r3.csv`, `followup/f1_price.csv`. Reuse and restyle `fig_reversals_vs_asks_r3.pdf`.
4. **Dimension x intervention heat table** (S5). Rows: seven dimensions (agent, certainty, polarity, politeness, speech act, time/quantity; event/role proposed, no data yet). Columns: bare default rate, chip gain, word gain, irrelevant control, guard, SLP severity. Cell value and denominator printed. Source: `analysis/hw1/six_dim_rates.csv`, `chip_gain.csv`, `chip_controls/chip_controls.csv`, `model_breadth/*`, SLP severity from scorer. Table form with shading, no color-only encoding.
5. (Slot) **Coverage-per-tap curve** from the intent-coverage pilot (S7 7d).
6. (Supplement) per-model forest plot and the consultant change log table.

## 5. Hard rules carried into every section (from LOOP_BRIEF and HANDOFF 7)
- Every number is a macro from `make_macros.py`; no hand-typed numbers; examples are real stored outputs chosen by a declared rule, printed with their rate (`analysis/hw1/examples.md`, `analysis/examples/`).
- Never claim IRB approval or exemption, AAC-user benefit, adviser participation, or that machine-panel agreement validates anything. Say "pre-specified and git-timestamped", never "pre-registered" (the hash deposits post-date the W-C freeze: protocol-hash-2026-11-01 and later deposits; do not claim they certify W-C).
- Annotators: adult non-author university classmates, consented, paid (payment and food). SLPs: two anonymous expert raters (n=2, expert review not population estimate). Consultants: two paid AAC-user design consultants; report requirement changes, not their experiences.
- Do not call the affirmative default new; cite Chen et al. ACL 2023.
- Part 17 stays as "no detectable usability cost under the frozen rule", with the interval printed. Gemma repairs 32% usable stays in the paper.
- Abstract and conclusion follow the Tone rule (lead with what works; limitations once in the body).
- Keep the part-4 pilot and SE4All discovery numbers out unless relabelled as pilot; use Part 17 as primary.

## 6. Slots for pending work

### Slot A: Stage 5 (Parts 20-25, due Thu Nov 5 23:59)
Parts: 20 treated-output labels (120 outputs x2), 21 source labels (200 messages x2, weighted; behind the T2 posterior), 22-25 four frontier label checks (value_of_cue 73 items, knows_not_says, partner_context, multilingual/default_profiles; see `annotation/frontier_*_items.json`). Plug-in plan:
- Inputs expected: returns in `annotation/returns_stage5/` (path per COORDINATOR_STEPS), scored into `analysis/stage5/summary.json` (create the scorer first; `make_macros.py` sets `slotSFiveReady` from that file's existence).
- S6 gains a human-checked row for treated outputs (are judge-passed chip/word/guard outputs also judged preserving by humans?), reported next to the machine rate. If humans and judges disagree, the human rate replaces the machine rate in the abstract and the discrepancy goes to S8.
- S8 gains source-label accuracy from Part 21 (it underwrites the T2 posterior and every "default per 1,000" price). If label accuracy is low, reweight prices and say so.
- Parts 22-25: each frontier item becomes a one-line row in a "frontier checks" table in the supplement, with the human-checked result. A confirmation of the terra verbalised-uncertainty lead (+.098, CI touches 0) is the only one that may enter the main text.
- Macros to ADD: `s5TreatedK/N/Rate(+CI)` per arm, `s5SourceAcc`, `s5SourceWeighted`, and per-check rows. Until then these render as `\pending{}`.

### Slot B: intent-coverage pilot (not yet run)
Question: does an approval-gated set of up to k drafts (differing in one named commitment dimension; consultants' R6 and differing-drafts request) cover the writer's intended message more often than the single best draft, at what tap and reading cost?
- Design to freeze before running (git-timestamped, hash deposit): writers = existing Part 18 writers (20) or a new batch; items = their own keywords + own intended sentence; arms = single best draft, k=2 and k=3 minimal-pair sets, set with cue; measure coverage (writer marks any draft as the intended message, or intended-plus-small-edit), taps (cue taps + selection), reading cost (number of drafts read), attribution of uncovered intent to loss / violation / assumption using the classifier validated in S7 (whole_message).
- Endpoints: coverage per set, coverage per tap, attribution shares. Baseline from existing data: single-draft intended-version match is `\jmpOneEightMatchChip`% (chip) and `\jmpOneEightMatchBare`% (bare); accepted as-is is `\jmpOneEightAcceptYesK` of `\jmpOneEightAcceptN`.
- Generation cost: plain generation via `research submit aac-llm`; judge concurrency <=3, generation <=4, no Gemini. Human portion needs the annotators again (consent and payment as in earlier parts; no new IRB claim). If time does not allow, S7 7d becomes "design and baseline" and the abstract's last clause is dropped.
- Macro slot: `cov*` keys read from `analysis/intent_coverage/summary.json`. `slotCovReady` flips automatically.

## 7. Differences from prior publication (cover-letter paragraph, draft)

This manuscript is substantially new relative to our SE4All archival paper (cited as concurrent work) and our CALE-AI workshop paper (non-archival; cited). Those papers establish, on discovery and confirmation families, that a deletion-based guard raises pass rates, that a chip cue restores a missing commitment, and (in a short form) that humans write keywords with a low negation rate. They report no result from the studies that make up this paper's core. New here: (i) the human-written pair replication across 20 writers and six models with controlled cue channels (irrelevant, natural-language, legend); (ii) the blind three-rater repair-usability audit under a frozen rule; (iii) writer-intent validation (Part 18: intended-version match, acceptance as written, whole-message reasons) and the resulting argument that commitment preservation is necessary but not sufficient; (iv) human arbiter agreement and the demonstration that machine judges do not track writers or clinicians; (v) the SLP severity weights and clinically weighted failure rates; (vi) the consultants' requirement changes (R6, NOT-scope, differing drafts); (vii) the same-items dimension-by-intervention profile with a tap-priced frontier and the ask-policy null; (viii) [slots] human checks of treated outputs and source labels, and an intent-coverage pilot of approval-gated draft sets. Overlapping material (the guard on W-C families, the discovery-set cue result) is shortened to one table cited to the earlier papers. No figure or table is reused without redrawing, and text overlap is limited to the shared methods description. We will provide both papers to the editor on request.

## 8. Risks and what to verify before drafting
- Prior-work: Chen et al. 2023 (affirmative bias in keyword-to-sentence) must appear in the introduction; Braun 2025 and the Conf-Gen / INTENT-SIM / AskBench items in the critic synthesis are marked [S] (snippet only) and need opened abstracts before citing.
- Part 17 reading: lower bound of the difference is -27.6 pp. Write "no detectable usability cost", never "no cost".
- hw1: direction and consistency across 6-7 writers; the interval width is not the claim.
- Reversals frontier: ask-policy rows assume the asked user supplies the cue (rho = 1); the measured F1 rows supersede the earlier transported rho. Print this in the caption.
- Consultant and SLP material: n=2 each. Apply `expert_package/PAPER_WORDING.md` status words verbatim in methods and limitations.
- Gemini lite rows: available in `analysis/model_breadth/gemini_*`; user rule "no Gemini" applies to new calls, not to existing results; label as an additional machine replication.
- `make_macros.py` runs `src/score_slp_panel.py` into `tmp/` and deletes the output; the SLP macros come from parsing its markdown tables (fragile if the report format changes; consider adding a `--json` flag).
- Macros still to ADD: per-model breadth table, per-dimension control rows, guard G1s / strict-repair counts, waterfall intended count, Stage 5 and coverage keys, consultant log counts.

## 9. Build
```
. .venv/bin/activate && python paper/journal/make_macros.py
docker run --rm -v ~/aac-voice-preservation:/w -w /w/paper/journal texlive/texlive:latest-full latexmk -pdf main.tex
```
(Clean `main.aux/.bbl/.blg` before rebuilding if latexmk reports a stale bibtex state. The skeleton compiles to 2 pages, 0 undefined references. Template check on the target journal's current author instructions is still open: acmart `manuscript,review` is used; confirm the TACCESS submission format and whether single-anonymous review requires removing author text.)

# Frontier plan: whole-message fidelity and unrequested content (id whole_message)

Written 2026-11-02, BEFORE any outcome of the experiments below was generated or inspected. Author: specialist director.
Nothing here has been run. Status of every number in this file: none (no result exists). The aggregate Part 18 / SLP summaries
that were already public in the repo (writers accept 1/200 as-is; writer-judge kappa .24 on the four-label question; SLP-judge
kappa about .19) are the motivation and were read; no item-level AUROC, no per-strategy output and no metric score was computed
before this plan was frozen.

Coordination note: `src/analyze_whole_message.py` (untracked, written by another session at 16:32; `analysis/whole_message/` is
an empty directory) is a lexical reason-class analysis of Part 18 and the SLP panel. It is NOT run, edited or overwritten here.
Its lexical features (content-lemma Jaccard / token F1) are reused only as the pre-declared lexical baseline M2 below; if that
session produces `analysis/whole_message/summary.json` first, read it and cite it, do not duplicate.

## 0. Why this frontier, and the novelty check

Finding: preserving the critical commitment is necessary but not sufficient. In Part 18 writers accepted 1 of 200 outputs as-is,
and only 25% of outputs were said to match the intended variant (39% with the chip, 11% without). The critical-dimension judge
agrees with the writer at kappa .24 because it labels one dimension and the writer judges the whole message.

Literature check (WebSearch, 2026-11-02; items marked [S] are search-snippet level only, not opened; all must be opened and
re-verified before citation in a paper):
- Faithfulness taxonomy: intrinsic (contradicts source) versus extrinsic (cannot be verified from source) hallucination; Ji et al.
  "Survey of Hallucination in NLG", ACM Computing Surveys 2023, doi 10.1145/3571730 [S]. Unrequested content in AAC expansion is
  extrinsic hallucination, but with a stricter standard: the source is three keywords, so almost any detail is unsupported, and
  the user can only veto, not verify.
- Detectors we can implement as baselines: AlignScore (Zha et al., ACL 2023, arXiv 2305.16739; reports AUC-ROC on TRUE and
  SummaC) [S]; SummaC (Laban et al., TACL 2022) [S]; SelfCheckGPT (Manakul et al., EMNLP 2023, aclanthology 2023.emnlp-main.557;
  consistency across samples) [S]; FActScore (Min et al., 2023; share of atomic claims supported) [S].
- Meaning-preservation metrics and their known failures: BERTScore (Zhang et al., ICLR 2020, arXiv 1904.09675), BLEURT, MeaningBERT
  (Beauchemin et al., Frontiers in AI 2023, doi 10.3389/frai.2023.1223924): general metrics fail trivial sanity checks and
  correlate weakly with human meaning judgments [S]. We adopt MeaningBERT-style sanity tests (identical sentence must score
  top, unrelated sentence must score bottom) as pre-declared validity gates.
- Closest to our generation side: SHARS (arXiv 2606.03628, detect-and-reject segments then resample; claims-to-sentence rewrite)
  [S]; Factcheck-Bench / Factcheck-GPT minimal-edit correction rule (arXiv 2311.09000, Findings of EMNLP 2024) [S]; FACTWASH
  (arXiv 2608.03372; typed change report DROPPED/STRENGTHENED/REVERSED/ADDED) [S]. These are generic text, not AAC, with
  no motor cost and no writer-intent labels.
- AAC: KWickChat (Shen et al., IUI 2022, doi 10.1145/3490099.3511145; evaluated with BLEU/WER and two human judges, keyword-only
  baseline) [S]; SpeakFaster (Nature Communications 2024, doi 10.1038/s41467-024-53873-3; saves motor actions, no fidelity axis)
  [S]; Choudhury et al., arXiv 2503.11881 (Human-LLM representation alignment for affective sentence generation in AAC; closest
  "intent alignment" evaluation, emotion-focused) [S]; Valencia et al., CHI 2023 doi 10.1145/3544548.3581560 (qualitative: loss of
  voice and intent) [S]; Frisch et al., arXiv 2606.24854 (intent measurement is an open challenge) [S].
- Search did not surface any paper that (a) validates an unrequested-content metric for AAC keyword expansion against the
  expanding writer's own judgments and against SLP ratings, or (b) benchmarks minimal-expansion / exact-copy / contrastive-draft
  / constrained-rewrite strategies on writer-authored minimal pairs with a critical-commitment judge. Novelty confidence:
  MEDIUM. The metric ingredients are known (NLI/claim support); the contribution is the validated AAC-specific target (writer
  intent), the two-sided evaluation (commitments kept AND unrequested content reduced), and the cost accounting. Risk: reviewers
  may call (b) "applied prompt engineering"; the guard against that is the benchmark against detect-resample and G1.

## 1. Definitions (frozen)

- Input x: keyword string (with or without chip). Output y: one sentence. Intended sentence r: the writer's version A or B text
  for the family, only available for hw1/hw2 items (never at deployment).
- Critical commitment kept (CK): existing judge `critical_match` after the blind arbiter, no J1 fallback (as in analysis/hw1).
- Unrequested content (UC): material in y that neither x nor the function-word / inflection minimum needed for grammaticality
  supports: new entities, places, times, reasons, people, politeness, certainty words, quantities, or a changed sentence frame
  (e.g. "I want to ...", "Tell you to ...", "I must ... now").
- Whole-message fidelity (WMF): y says what r says and nothing else: no UC, no dropped target content, same critical value.
- Edit effort E: word-level Levenshtein distance from y to r (proxy for repair taps; writer-free, judge-free).

## 2. Hypotheses

- H1 (metric validity). A whole-message metric predicts writer rejection of an output better than the critical-only judge does.
- H2 (insufficiency, descriptive). Among outputs with CK = true, the share with UC or dropped content is large in every
  model; report the rate per 1,000 messages. No test, no threshold.
- H3 (minimal-expansion prompting). A prompt that forbids adding content reduces UC without lowering CK, relative to P0 and
  relative to the existing preservation prompt P1 (the strong prompt-only baseline).
- H4 (exact-copy default). A deterministic copy-with-minimal-grammar default has the lowest UC but pays in fluency/intelligibility;
  it is a Pareto point, not a winner. Expected: reduces UC, raises fragment rate and E on some dimensions.
- H5 (contrastive drafts). Showing k=3 drafts that differ in the critical dimension, built from a minimal-expansion base, covers
  the intended message more often than k=3 independent samples from P0 (equal budget), at a tap cost of 1 to 2.
- H6 (commitment-constrained rewriting). A detect-then-rewrite loop whose detector is the UC metric reduces UC beyond
  resampling alone (D-068 style, no feedback) and beyond P1, with CK non-inferior.
- H7 (does not help). Gains are smaller or absent on bare input (the cue is missing, so intent is unrecoverable), on
  speech_act and time_quantity items, and for the small local model; these are pre-registered subgroup reports, not tests.

## 3. Metric candidates (frozen before any scoring)

All score (x, y) reference-free, and (x, y, r) reference-based; a score in [0,1] where 1 is perfect; UC and "dropped" flags are
also returned.
- M0 critical-only baseline: existing judge `critical_match` (1 = kept). The thing we must beat.
- M2 lexical: content-lemma F1 between y and r (spaCy en_core_web_sm lemmas, stop words and chip realisations removed) and
  reference-free novelty = share of y content lemmas absent from x. Reuses the declared rules of src/analyze_whole_message.py.
- M3 NLI/alignment: bidirectional entailment (x-paraphrased-as-r vs y) with AlignScore-base if it installs offline in .venv;
  otherwise a local cross-encoder NLI model; if neither is obtainable, M3 is dropped and said so. No new accounts.
- M4 local-LLM logprob: Qwen2.5-14B (GPU lock) yes/no logprob for "does y contain anything not in x / r?" and "does y say what r
  says?"; P(yes) is the score. Cheap enough for in-loop use (H6 detector).
- M1 PRIMARY (rubric LLM judge, gpt-6.1-sol effort low, judge.py, concurrency <=3): one call per unique output returns JSON
  {unrequested: [phrases], dropped: [phrases], frame_changed: bool, score_1to5}. Prompt text and schema are saved to
  `analysis/frontier/whole_message/m1_prompt_v1.txt` and its sha256 appended to this file before first use. Score = score_1to5/5;
  binary WMF-fail = unrequested nonempty OR dropped nonempty OR frame_changed OR critical differs from r.
  Two variants: M1-ref (sees r) and M1-free (sees only x and y; the deployable one).
- Sanity gates (MeaningBERT-style, run on 100 families before anything else): y = r must score WMF-pass for >= 95% under M1-ref;
  y = r of a different family must be WMF-fail for >= 95%; y = x keywords copied verbatim must have UC = none for >= 90%. A metric
  that fails a gate is not used for any claim.

## 4. Experiments (staged; each <= ~1 day compute)

### Stage 0. Freeze (hours; no GPU, no generation)
Build the Part 18 + SLP feature table (script `src/frontier_whole_message_features.py`; joins analysis/intent_check/items.csv,
expert_package/slp_key.csv, expert_package/returns_slp/). Freeze M1 prompt, sanity-gate set, strategy prompts S1 to S5 (texts saved
and hashed here), family subsets and seeds. Append hashes to this file.
Declared splits: Part 18 development half = writers P01 to P10; holdout half = writers P11 to P20 (by writer ID, fixed now).
M1 prompt may be revised ONCE after looking at the development half only; a revision is called v2 and reported next to v1.
The holdout half is scored once, with the frozen prompt.

### Stage 1. Metric pilot and validation (about 3 h; ~700 judge calls, no GPU generation)
Score the 200 Part 18 outputs and 50 SLP cards with M0, M1-ref, M1-free, M2, M3 (if available), M4 (GPU lock, about 10 min), plus
sanity gates. Labels:
- L1 (primary): writer says the output is NOT the intended variant (something else or the other version), 195 usable items.
- L2: writer would not accept even with a small edit ("no"; 120 of 200 are "no").
- L3 (descriptive only; floor effect, 1/200 yes): accept-as-is.
- L4: SLP "acceptable to speak" not-yes on the 50 cards (descriptive, n=50, two raters, no test).
Statistic: AUROC with 95% CI from a writer-cluster bootstrap (B = 5,000, seed 20261102); item bootstrap as sensitivity. Paired
delta AUROC versus M0 from the same bootstrap draws.
Decision rule (pre-declared):
- M1 (ref or free) is "validated" for L1 iff holdout-half AUROC >= 0.75 AND the full-200 paired delta versus M0 has a CI excluding
  0 AND it passes the sanity gates. If M1-ref validates but M1-free does not, generation experiments use M1-ref and the paper says
  the reference-free detector is not good enough to deploy.
- If no candidate is validated: STOP the metric claim. Report the negative result (writer intent is not recoverable from
  output text alone) and run Stage 2/3 only with M2 + E + the existing critical judge, labelled "unvalidated proxies".
- Label noise: writers rate 10 items each; report the ceiling implied by writer-to-writer inconsistency using the bare/chip
  structure (bare cannot match by construction, so L1 on bare is excluded from the primary AUROC; reported separately).
- Ensemble (ridge logistic, 5-fold CV over writer groups) is secondary and cannot be the headline.

### Stage 2. Strategy pilot (about 6 to 8 h wall; local GPU ~1 h, API ~3 h)
Data: 60 hw1 families (10 per dimension, seeded draw rule `sha256("wm-pilot|family_id")` ascending, one family per near-duplicate
component), both variants, channel chip1 (cue supplied) and bare, = 240 inputs per model. Models: qwen2.5-7b, llama3.1-8b, gemma3-4b
(local, sequential under `flock /tmp/aacv_gpu.lock`, one llama-server at a time) and gpt-6.1-terra (concurrency <= 4).
Arms (all greedy T=0 unless stated; each uses P0's legend and framing):
- A0 P0 (existing stored outputs reused).
- A1 P1 (existing preservation prompt, stored outputs reused: the prompt-only strong baseline).
- A2 minimal-expansion prompt (new): "Use only the given words; add only the small grammatical words needed (articles, auxiliaries,
  prepositions, pronoun for the speaker). Do not add people, places, times, reasons, politeness or certainty. If unsure, stay
  close to the keywords."
- A3 exact-copy default: deterministic template. Content words and cue words in input order, chip realised by a fixed phrase
  table, minimal auto grammar (no LLM). A3+ is a variant that asks the LLM to repair grammar only under a lexical constraint
  (output content lemmas must be a subset of input lemmas plus function words; violation falls back to A3). Naive baselines:
  A3 is itself the "do nothing" floor; always-commit = A0.
- A4 contrastive drafts: A2 base plus k=3 drafts that differ only on the critical dimension (prompt instructs three drafts, each
  fixing the dimension differently, otherwise identical wording). Compared with B4 = 3 independent samples from P0 at T=0.7 (S3
  style, equal draft budget) and B4' = P2 spanning prompt (existing).
- A5 constrained rewriting: draft from A2; M4 detector (Qwen2.5-14B logprob; for local arms the 14B is served separately under the
  lock after the generation pass) flags UC; if flagged, ONE rewrite with the flagged phrases quoted ("remove these; keep these
  commitments"), then re-check; max 1 rewrite. Baselines: B5 resample-only (T=0.7, up to 2 resamples, detector-selected,
  no feedback; the D-068 design) and G1 (frozen commitment guard, as implemented in src/guard_baseline.py / interventions.py,
  CK-targeted, not UC-targeted).
- Closest published approach implemented: SHARS-style detect-then-resample (B5) and the Factcheck minimal-edit rule (A5 prompt
  states "no additional insertions or deletions beyond the flagged phrases"). SelfCheckGPT-style consistency (disagreement
  among the 3 samples of B4 as a UC predictor) is scored as an M-candidate on the same items (reference-free, no new calls).
Outcome measurement per unique output: M1 (Stage-1 validated variant) + existing judge for CK (7 dims, blind arbiter via
src/arbiter_tool.py when J1/J2 disagree, output text only, no J1 fallback) + M2 + E. About 240 x 4 models x ~8 arms, deduplicated
(A3 has no model dependence; A0/A1 outputs already stored): about 6k unique outputs, 12k judge calls at concurrency 3 is too
many for a pilot, so the pilot scores M1 and CK on a 120-input-per-model subsample (chip1 only; = 480 x 8 = 3.8k outputs;
7.7k calls, ~6 to 8 h). Budget guard: if codex-lb returns a usage-limit error, pause and resume; cached in `runs/cache/`.
Pilot go/no-go (declared): proceed to Stage 3 for an arm only if, pooled over the 4 models, paired UC rate versus A0 drops by
>= 5 pp (point estimate) and CK drops by no more than 3 pp (point estimate). Otherwise the arm is dropped from Stage 3 and reported
as "pilot negative" with its numbers. Arms are not tuned after the pilot except for one pre-declared change: prompt wording
may be revised once if the model refuses format (parse failure > 5%), and the revised wording is logged here with its hash.

### Stage 3. Full test on hw1 (about 1 day; run only for surviving arms)
Data: 240 families (40 per dimension; the 60 pilot families included; same seeded rule), both variants, chip1 and bare, 4 models.
= 1,920 inputs per arm in total across models. Outcomes as in Stage 2. Estimated unique outputs ~11k, 22k judge calls: at the earlier
observed ~35 calls/min at concurrency 8, concurrency 3 is ~13/min, so full scoring of all outputs would be ~28 h; to stay within
one day the CK judge is run for all outputs, and M1 is run on all outputs of chip1 and on a 50% seeded subsample of bare
(declared now; subsample key `sha256("wm-bare|output_id")` ascending). If throughput is better, the subsample is extended
(never reduced). M4 and M2 run on everything (GPU or CPU, cheap).
Primary estimand per arm: paired difference (arm minus A0) in the share of outputs with WMF-fail (M1), over model-pooled items,
with a family-cluster bootstrap CI (B = 10,000, seed 20261102), chip1 channel, restricted to the 4 primary models, equal weight per
model. Co-primary: CK rate difference (non-inferiority margin -2 pp: lower CI bound must exceed -2 pp). Secondary: UC rate alone,
dropped-content rate, fragment/fluency fail (judge field), E (mean word edit distance to r), per dimension, per model, bare channel.
Multiplicity: Holm across the surviving arms for the primary contrast.
Success criterion (arm is "a real improvement" iff ALL hold):
1. WMF-fail reduction versus A0 >= 10 pp with the CI excluding 0 and Holm p < .05;
2. reduction versus A1 (the strong prompt baseline) >= 5 pp with CI excluding 0 (otherwise the arm is only "as good as the prompt we
   already had");
3. CK non-inferiority versus A0 (margin -2 pp);
4. fragment rate not worse than A0 by more than 3 pp;
5. direction holds in >= 3 of the 4 models (descriptive sign count).
For A4 the outcome is coverage: at least one of the 3 drafts is WMF-pass and CK; compared with B4 and B4'; criterion 1 reads +10 pp
over B4, criterion 2 over B4'; tap cost reported (1 tap to choose when drafts differ, +1 tap if reading both is counted: report
both). For A5 criteria 2 additionally requires beating B5 (resample-only) by >= 3 pp.
Failure reporting: any arm that fails is reported with its numbers; "where it does not help" tables by dimension, model, channel.

### Stage 4. Confirmation on hw2 (about 3 h; new writers, never used for any choice)
After Stage 3, choose at most ONE winning arm (rule: highest WMF-fail reduction among arms meeting criteria 1 to 5; ties go to the
cheaper arm) plus A0 and A1 and A3. Run on the hw2 accepted pairs (Part 15/16; dropped pairs removed; chip1 and bare;
4 models), score identically. Pre-declared claim: replicate iff the hw2 point estimate of the primary contrast has the same
sign and >= 50% of the Stage-3 magnitude, and the CK non-inferiority point estimate holds; CI reported (it will be wide). No
rescue analyses.

### Stage 5. AAC-terms translation (no new generation; 1 h)
For each arm, per 1,000 messages: (a) unrequested-content outputs; (b) outputs failing a critical commitment (silent reversals,
existing definition); (c) clinically weighted failure rate with SLP weights from expert_package/slp/ANALYSIS_PLAN.md (largest
flagged weight; primary includes ADD; weights read from the scored SLP panel only after its own plan produces them; if weights
are not yet scored, report unweighted and mark the weighted column pending); (d) expected taps (A3: 0 extra; A0, A1, A2, A5: 0
extra when accepted, E word-level edits otherwise; A4: +1 tap to choose, +E on the chosen draft); (e) draft acceptability by the
human check below. Include the tap-versus-WMF-fail frontier with always-commit, always-ask and random-ask on the same items
(ask = display 3 drafts or a cue prompt; costs from the existing cost model in analysis/derived and interaction_agency ideas).
Figures to build later: (1) CK versus WMF-fail scatter per model and arm showing that preserving the commitment is not
sufficient; (2) AUROC panel per metric with cluster CIs; (3) tap-versus-UC frontier; (4) a worked-example strip: real stored
outputs for one item per dimension under A0/A1/A2/A4/A5, chosen by declared rule (first item by hash rank per dimension where
A0 has CK true and WMF-fail true, and the arm output shown regardless of whether it improves).

## 5. Human annotation requests (not sent; orchestrator batches)

See `ANNOTATION_REQUEST.md` in this folder (request R-WM-1: treated-output check, about 20 annotators, 10 to 12 minutes; items built
only after Stage 3 because they sample stored arm outputs). Machine-only Stages 1 to 4 proceed meanwhile and every result is labelled
PROVISIONAL until R-WM-1 returns. An optional R-WM-2 asks the same 2 anonymous SLPs to rate 30 unrequested-content cards for expert
acceptability (expert annotation of materials, no AAC users).

## 6. Compute and data summary

| Stage | Data | Models/API | Wall time | Gate |
|---|---|---|---|---|
| 0 | Part 18, SLP cards, hashes | none | 2 h | none |
| 1 | 200 + 50 outputs, 100 sanity families | gpt-sol (~700 calls), Qwen2.5-14B logprobs (10 min GPU) | 3 h | metric validated or STOP |
| 2 | 60 families, 8 arms, 4 models | local GPU about 1 h under lock; gpt-terra gen; ~7.7k judge calls | 6 to 8 h | per-arm go/no-go |
| 3 | 240 families, surviving arms | as above; ~22k judge calls (subsampled bare) | ~24 h | success criteria 1 to 5 |
| 4 | hw2 pairs | same | 3 h | replication rule |
| 5 | stored | none | 1 h | none |

GPU etiquette: every local server launch under blocking flock; hw2 owns the lock at times (wait); one llama-server at a time; Qwen2.5-14B
detector and generation servers are never up together. API: gpt generation <= 4, judge.py --concurrency <= 3. No Gemini.

## 7. Integrity rules in force

- Pre-declared metric, predictor (M1 variants), splits, margins, success criteria above; deviations are appended below with date, reason
  and what had been seen.
- No J1 fallback; blind arbiter through src/arbiter_tool.py on output text only; refusal/acceptance quarantine unchanged.
- Goodhart guard: A5 uses M4 (local logprob detector) in the loop; evaluation uses M1 (different model, rubric) and E (judge-free).
  If M4 and M1 diverge on the arm effect, the claim rests on the smaller one and the divergence is reported.
- Examples are real stored outputs selected by the declared rule. Machine-panel agreement is never called human validation. Writer
  and SLP judgments are the validation targets; no AAC users as participants; no IRB claims.
- The writers' own acceptance data remain a floor-effect measure (1/200); a strategy is never claimed to make messages
  "acceptable as-is" unless R-WM-1 shows it.
- Only files written under analysis/frontier/whole_message/, src/frontier_whole_message_*.py and runs/frontier_whole_message_*.

## 8. Deviation log
(empty)

### Freeze record (appended 2026-11-02 before any M1 call; engineer round 1)
- m1_prompt_v1.txt sha256 = fe9af5fdb506a36f757f7600343dec77994da60c8f39714ddee7d3ebac906b9c. Script src/frontier_whole_message_m1.py (judge gpt-6.1-sol, effort low, json_schema).
- Sanity-gate set (declared): 100 Part 18 items drawn by sha256("wm-gate|item_id") ascending. Gate a: y = intended sentence r under M1-ref must be WMF-pass (>=95%). Gate b: y = intended sentence of the next item in the cyclic order of the gate set (a different family) under M1-ref must be WMF-fail (>=95%). Gate c: y = the input keywords copied verbatim (chips and "Keywords:" stripped) under M1-free must have empty `unrequested` (>=90%).
- Round-1 scope (engineer): Stage 0 + Stage 1 on the metric side (M0, M1-ref, M1-free, M2 lexical, length-ratio baseline). M3 and M4 only if feasible (see round1.md). Splits as declared (dev P01-P10, holdout P11-P20).
- Pre-declared labels L1/L2/L4, AUROC with writer-cluster bootstrap B=5000 seed 20261102, validation rule as in Stage 1.

### Deviation / scope log, round 1 (appended 2026-11-02; Stage 1 outcomes already seen, Stage 2 outcomes NOT yet seen when this was written)
- Stage 1 primary-contrast interpretation: the plan says "full-200 paired delta" AND "bare excluded from primary AUROC". Both readings are reported; headline is the conservative one (see round1.md). M1-ref binary WMF-fail turned out degenerate (dropped list non-empty for 100% of CK-true outputs because writers' sentences carry details the keywords never contain), so the graded 1-5 score is the metric used for AUROC; the binary variant is reported only as such.
- Stage 2 pilot was run as an API-only slice: model gpt-6.1-terra only (no local GPU use; avoids the hw2-held lock); chip1 channel only; 54 families = 9 per dimension x 6 dimensions (time and quantity are one dimension "time_quantity" in hw1), selection key sha256("wm-pilot|family_id") ascending, near-duplicate components NOT enforced (not available in a quick form); both variants = 108 inputs. Arms run: A0 (stored hw1 P0), A1 (P1, generated now: no stored P1 outputs exist for hw1), A2 minimal-expansion (prompts text analysis/frontier/whole_message/prompt_A2_minimal.txt, sha256 973b49bf824115422f8f600b05f5124e97242f99067df09107805273d12ced07), A3 deterministic exact-copy template (src/frontier_whole_message_s2_gen.py, no LLM). NOT run: A3+, A4, A5, B4, B5, G1, M3, M4, Stages 3-5.
- Stage 2 outcome measures, declared before looking: CK = critical_match from judge.py J1/J2 with blind arbiter (no J1 fallback; 5 units arbitrated blind on output text; first draft of the arbiter file was rewritten before any analysis because the view printed one dimension header over items of two dimensions); WMF = M1-free binary fail and unrequested-content (UC) flag (the deployable variant, validated for chip1 only in Stage 1) plus M1-ref graded score as secondary; E = word-level Levenshtein distance to the writer's sentence for the variant. Fragment proxy = no finite verb by spaCy. Go/no-go as in plan (UC drop >= 5 pp vs A0 with CK drop <= 3 pp, point estimates), applied to this single-model slice, so it can only say "pilot go/no-go on one model".
- Paired contrasts use a family-cluster bootstrap (B=10,000, seed 20261102), both variants of a family resampled together.

## Decisions

### Director decision after round 1 (appended 2026-11-02; POST-PILOT, labelled as such): CONTINUE to round 2

Decision: continue, with a narrowed claim and a fix-first order. Stage 1 and Stage 2 outcomes were seen before this was written; everything below is a post-pilot amendment and is not pre-registered.

Why continue: the critic's fatal issues are about what the evidence can claim, not about whether the question is worth answering. Writers reject 59% of outputs that keep the critical commitment, so a gap in the current metric is real and is AAC-relevant. But right now we have a judge-defined flag with no writer outcome that moves, and baselines that are missing.

Narrowed claim (use in all drafts until round 2 changes it): "Under the plain prompt, about 26% of chip1 outputs carry judge-flagged unrequested content, versus about 4% under P1 or minimal-expansion. One model, one draw, judge-defined. Writer-intent match does not improve. Critical retention alone does not predict writer rejection." Do not claim that UC removal helps writers.

ROUND 2 INSTRUCTIONS (fix critic issues in this order; write each rule into PLAN.md before looking at outcomes)

1. Metric validity (fatal 2, major 1). Freeze before scoring:
   a. Add trivial baselines on the same 195 items with writer-cluster bootstrap CIs: output word count, length ratio, lexical F1, edit distance to the keyword string, and a length+lexical logistic model (cross-validated by writer). M1-free must beat the best trivial baseline by a paired delta whose CI excludes 0. If not, report M1-free as NOT validated beyond length.
   b. Replace the binary M0 strawman with a graded critical-only comparator (critical-commitment confidence or logprob-based), so the ceiling artifact is removed.
   c. Report M1-ref as an upper bound only (it sees the writer sentence). Make the deployable claim on M1-free alone. State that the holdout lower bound (.71) is under the declared .75 threshold and report it as a miss. Do not re-declare the threshold.
   d. Label the graded-score primary as post hoc, with the reason (binary degeneracy).
   e. Run an independent-family judge (local qwen2.5-14b or mistral-nemo-12b under flock) on the same items for M1-free, and report agreement with the gpt judge and AUROC. This is the Goodhart/self-preference guard (M4). If it fails, the metric is gpt-family-specific and must be said so.
   f. Fix the verbatim-copy false-positive problem (39% of keyword copies flagged): report the false-flag rate on a "verbatim copy" stratum as a limitation, or exclude and state the effect on AUROC.

2. Intervention noise and baselines (major 3, 6). 
   a. Regenerate A0 fresh alongside A1/A2 (same date, same endpoint), with at least 3 independent draws per arm per input. Report the noise floor as draw-to-draw UC variation within an arm. Stored A0 stays as a secondary check.
   b. Report per-1,000 rates with CIs (input-cluster bootstrap); drop point estimates from counts below about 10 events or flag them as "n events of N".
   c. Net the A1 fragment cost into one composite: silent reversals + UC + fragments, with SLP-weighted harm and taps per 1,000. A1 vs A2 is then a fluency trade, so prefer A2.
   d. Add the declared baselines that can be run without human labels: G1 guard, always-commit, always-ask, random-ask at the matched ask rate, and the closest published approach implementable (SelfCheckGPT-style sampling-consistency for unrequested content, using the 3 draws from 2a). State which one is closest and how it was adapted.

3. Generality (major 5). Extend Stage 2 to at least 3 generators (gpt-6.1-terra, one more API family if available through codex-lb, and local llama3.1-8b or qwen2.5-14b) and both chip1 and bare channels. Apply the near-duplicate family control. Use more writers where available in the hw1 pool and report the per-writer L1 spread. Do not run Stage 4 (hw2) until the metric passes 1a.

4. Mechanism of the flat intent match (fatal 1). Instead of more UC counts, test why match does not move: (i) how many of the 59% rejections are explained by event/role misresolution vs added content, using the existing whole_message labels; (ii) test a two-candidate output (A2 plus a second distinct reading) on match-to-intent with the same judge. This is the only route by which removing UC could help writers, and it is the natural AAC contribution (offer alternatives rather than one rewrite). Report where it does NOT help.

5. Human annotation (no sending; orchestrator batches). Update ANNOTATION_REQUEST.md to cover: writer-intent acceptability on about 120 A0/A1/A2 outputs (about 20 adult non-author annotators, 10 min each) to check whether UC removal changes judged acceptability, and the verbatim-copy false-flag check. Label every machine-only result provisional until those return.

6. Novelty (major 7). Open and read the cited prior work (faithfulness and minimal-expansion prompting, SelfCheckGPT, keyword-to-sentence generation, Chen et al. ACL 2023) before any novelty claim. Position the contribution as (a) the finding that critical-commitment retention does not predict writer rejection, (b) a validated-or-not deployable whole-message flag, and (c) the AAC-terms translation. Do not claim minimal-expansion prompting as new.

Stop rules for round 3: stop after round 2 if M1-free fails to beat the trivial length/lexical baselines or the independent judge. In that case report the negative result and the critical-retention-vs-rejection finding only. Continue to round 3 only if the metric passes and the two-candidate arm shows a match-to-intent gain whose CI excludes 0.

## ROUND 2 (engineer) FREEZE RECORD (appended 2026-11-02, BEFORE any round-2 generation, local-judge score or trivial-baseline AUROC was computed; Stage 1/2 round-1 numbers HAD been seen)
All of this follows the Director's post-round-1 instructions. Nothing below is a new pre-registration of round-1 results; round-1 results are fixed.
Everything in round 2 is machine-only and PROVISIONAL until R-WM-1 / R-WM-2 (ANNOTATION_REQUEST.md, not sent) return.

### R2-A. Metric validity (items: the same 195 Part 18 L1-usable items, writer-cluster bootstrap B=5000 seed 20261102)
- Trivial baselines (scores oriented so higher = predicts rejection): T1 output word count; T2 length ratio (output words / keyword count); T3 lexical F1 to the writer sentence (1 - F1; reference-using, kept as the conservative comparator); T4 content-lemma novelty vs the input (round-1 M2_novelty); T5 word-level edit distance to the keyword string (normalised by output length); T6 cross-validated logistic on (T1,T2,T4,T5) with 5-fold CV GROUPED BY WRITER, out-of-fold scores. "Best trivial" = the baseline with the highest point AUROC on the subset being tested (selected on that subset: conservative).
- Graded critical-only comparator M0g: local Qwen2.5-14B (GPU lock), single-token logprob over the lettered options of the production critical question (judge.critical_question, options of the family); score = 1 - P(intended variant's critical value). Replaces binary M0 (kept as a column; ceiling artefact explained in round 1).
- Independent-family judge (Goodhart / self-preference guard): local Qwen2.5-14B and Mistral-Nemo-12B (sequential, each under the lock), reference-free, same rubric as M1-free, answered as single tokens: UC = P(Yes) to "contains unrequested content", SC = expected 1-5 score from digit logprobs (higher score = better; rejection score = 1 - (E[score]-1)/4). Prompt text hashed and logged below before use.
- DEPLOYABLE-METRIC PASS RULE for M1-free (declared now; claims restricted to chip1 as in round 1; bare is reported separately as a miss): ALL of (i) paired delta AUROC of gpt M1-free vs best trivial baseline, chip1, CI lower bound > 0; (ii) paired delta vs M0g, chip1, CI lower bound > 0; (iii) independent-family judge: Spearman with gpt M1-free graded score >= .50 AND own chip1 AUROC >= .65 AND own chip1 AUROC >= best trivial point estimate (tested for each of the two local models; at least one must pass, both are reported); (iv) the holdout (P11-P20) gpt M1-free AUROC lower bound is reported against the original .75 threshold: round 1 saw .71, so this is a recorded MISS and the threshold is NOT re-declared. The metric is therefore called "supplementary-validated, original threshold missed" even if (i)-(iii) pass. If (i) or (iii) fails => STOP rule: report negative result and the critical-vs-rejection finding only; no round 3.
- Graded-score primary is POST HOC (chosen after the binary M1-ref fail flag turned out degenerate: `dropped` non-empty for every CK-true output). M1-ref is an upper bound only (it sees the writer sentence that defines L1) and is not used for any deployable claim.
- Verbatim-copy false flags: round 1 gate c had keyword copies with empty `unrequested` in 100/100, but WMF-fail in 39% (via `dropped` / `frame_changed`). Handling declared: all claim-bearing deployable statements use the UC flag (`unrequested` non-empty) and the graded score, never the binary WMF-fail flag. Reported: UC-flag and WMF-fail rates on the keyword-copy gate stratum (n=100) and on the Part 18 stratum "outputs with zero novel content lemmas" (M2_novelty = 0); AUROC with and without that stratum.

### R2-B. Mechanism of the 59% rejections (item 4i; existing round-1 labels, no new calls)
Among Part 18 L1=1 items, per channel, report shares (overlapping, plus exclusive by the priority order): (a) critical misresolution (judge critical differs from intended, M0=1) or M1-ref frame_changed; (b) unrequested content (M1-free UC or M1-ref UC); (c) dropped detail (M1-ref dropped non-empty) without (a),(b); (d) none of (a)-(c) ("residual / unrecoverable detail"). Also among CK-true: rejection rate by UC flag yes/no (rejection given UC=0 is the key number: if still high, UC removal cannot raise intent match).

### R2-C. Generation experiment (items 2, 3, 4ii)
- Input set: hw1 families, near-duplicate control = one family per analyze_hw1.near_dup_components component (Jaccard >= .75 cross-writer, all other families are singletons), ranked by sha256("wm-r2|family_id") ascending, 6 families per dimension (polarity, speech_act, agent, certainty, politeness, time_quantity) = 36 families; both variants; channels chip1 and bare (input_text as stored in runs/hw1/scored.parquet). 144 (family, variant, channel) inputs. Writers per family are recorded; per-writer counts reported.
- Generators: gpt-6.1-terra (API), gpt-5.6-luna (API; the only second API model; SAME vendor family as the judge, so a self-preference caveat applies), llama3.1-8b (local, flock). Qwen/Nemo are reserved as independent judges, not generators.
- Arms: A0 (P0 prompt, prompts.render), A1 (P1), A2 (prompt_A2_minimal.txt, sha256 973b49bf...). Draws per arm per input: d0 = T=0 (deployed setting; PRIMARY), d1,d2,d3 = T=0.7 (noise floor and SelfCheck-style samples; local seeds 4001..4003). The stored hw1 P0 greedy output (terra, llama) is the secondary check of A0.
- Two-candidate arm A6 (terra only, d0): cand1 = A2 d0; cand2 = a generated "second distinct reading" (prompt saved as prompt_A6_alt.txt): shown cand1, asked for one different plausible sentence that uses only the given words and differs in the main meaning (who/what/statement-vs-question-vs-request), no added content. Equal-budget baseline B4 = cand2' = A2 d1 (an independent T=0.7 sample of the same prompt). Match-to-intent = M1-ref graded score >= 0.8 (declared now; also mean score). Best-of-two = the writer picks the better candidate (idealised writer; upper bound on selection) and costs 1 tap to choose when asked.
- Judging: (1) critical judge judge.py J1/J2 (concurrency 3) on every unique output of d0 (all arms/generators) and of d1-d3 for A0; blind arbiter via arbiter_tool on output text only, no J1 fallback. (2) gpt M1-free (concurrency 3) on every unique d0 output, all generators and arms; gpt M1-ref on terra d0 A0, A1, A2, cand2, B4 only (budget: the shared endpoint does about 8 calls/min). (3) local independent judge UC/SC (Qwen14B and Nemo12B) on all unique outputs d0-d3 (noise floor).
- Failure definitions per output: reversal = critical judge value equals the OTHER variant's critical value (as in round 1); CK = equals own variant's value; UC = gpt M1-free `unrequested` non-empty; fragment = no finite verb (spaCy as in round 1). Composite any-failure = reversal OR UC OR fragment. SLP-weighted harm = largest weight among flagged types, weights from analysis/frontier/multilingual/slp_weights_and_translator.json (the scored SLP panel weights): polarity NEG 1.0, speech_act ACT .8, agent AGT .8, certainty CRT .7, politeness POL .5, time_quantity TIM .8, UC (ADD) .8; fragments are NOT SLP-rated, so the weighted column excludes them and fragments are reported separately. Per 1,000 messages with input-cluster (family) bootstrap CIs (B=5000, seed 20261102); rates from cells with fewer than 10 events are shown as "k/N" without a per-1,000 headline.
- Primary contrasts (d0, paired by input, cluster = family): A2 - A0, A1 - A0, A2 - A1 on UC, reversal, fragment, composite, weighted harm, E (word edits to writer sentence), per generator x channel and pooled with equal generator weight. Noise floor: sd across d1-d3 of each arm's UC rate (local judge) and the share of inputs whose UC flag flips between draws; a contrast smaller than the noise floor is reported as not distinguishable.
- Baselines/policies on the terra d0 data, chip1 and bare: always-commit (cand1 only), always-ask (show cand1+cand2, 1 tap), random-ask at the matched ask rate (average of 1,000 random draws), flag-ask using (a) gpt M1-free UC flag on cand1, (b) SelfCheck-Unigram-style consistency score (closest published detector adapted: mean share of cand1 content tokens absent from each of the 3 T=0.7 samples of the same arm; ask at the matched ask rate by ranking), (c) G1-sim: the guard's role simulated with the critical judge as a perfect monitor (output = first of d0,d1,d2,d3 with CK; it is an UPPER BOUND on what the real G1 monitor can do, applied to A0; the real src/guard_baseline.py was not run). Outcomes: match-to-intent rate (M1-ref >= .8), UC rate, taps per 1,000. SHARS-style detect-then-resample (B5) and A3+, A5 are NOT run (no budget); the "closest published approach" actually run is the SelfCheck-style detector.
- GO/NO-GO for round 3 (declared): metric pass rule R2-A (i)-(iii) holds AND A6 best-of-two match rate minus cand1 match rate has a family-cluster CI excluding 0 AND exceeds B4 (equal-budget) best-of-two minus cand1 with CI-of-difference excluding 0 (both on chip1 and, reported separately, bare).

### Round 2 deviation log (appended 2026-11-02 after the Part 18 validity numbers and the terra/luna d0 generation results HAD been seen; llama3.1-8b generation and the independent-judge scoring of its outputs not yet)
- Budget cuts, forced by an endpoint that returned 524 timeouts and about 8 judge calls/min: gpt-5.6-luna ignores/hangs on a `temperature` argument, so luna was run with default decoding, d0 only (no T=0.7 draws). Terra: d1-d3 only for A0 and A2 (A1 d1-d3 skipped). The noise floor is therefore reported for terra only (and llama if its GPU stage finishes).
- M1-ref graded score never exceeds 3/5 (0.6) on any output (writers' sentences carry details no keywords carry): the DECLARED match threshold (>= 0.8) yields 0 matches in every arm, so the declared go/no-go criterion cannot be met by construction (degenerate, same pathology as the round-1 binary M1-ref flag). Reported as such. Post hoc sensitivity: match = M1-ref >= 0.6 (the best the scale allows) and the mean M1-ref score; files r2_*_posthoc60.csv. These are labelled post hoc.
- R2-B mechanism rule used as declared (frame_changed OR M0=1 for misresolution). M1-ref `frame_changed` is true for 67% of all Part 18 outputs, so the declared category absorbs nearly every rejection (134/146); the declared decomposition is therefore uninformative and the informative numbers are the conditional rejection rates (reject | UC flag, reject | no UC flag and no frame change). Reported without re-declaring.
- Independent-judge Spearman criterion (iii): interpreted strictly on the claim subset (chip1) for the SC graded score; Qwen2.5-14B gets .48 (all-200 .53), Nemo .29. Both readings are given in round2.md.
- Local judge UC threshold (P(Yes) >= .5) is uncalibrated (Qwen14B flags 7%, Nemo 65% where gpt flags 21%); rates from local judges are used only for within-judge contrasts and AUROC, never as UC rates.
- The stored hw1 A0 secondary check (terra) disagrees with the fresh A0 d0 on chip1 CK (98.6% vs 90.3%) and only 69% of texts are identical; that gap is part of the run-to-run noise on this endpoint.

### Round 2 director decision (2026-11-02, post-round-2; labelled POST-PILOT)
DECISION: STOP. No round 3. The declared stop rule fires: criterion (i) fails (M1-free vs output word count, paired delta AUROC +.04 [-.07,+.16], CI includes 0) and criterion (iii) is missed under the declared strict reading (Qwen14B Spearman .48 on chip1, Nemo .29). The go/no-go match criterion is also degenerate by construction (M1-ref never exceeds 0.6). All results remain machine-judged and PROVISIONAL.

What is reportable (negative/limited result only):
1. Graded critical-only retention does not predict writer rejection (AUROC .45-.55); 59% of CK-kept chip1 outputs are rejected (82% with UC flag, 43% without, 15% with no UC and no frame change).
2. M1-free (.77) is not distinguishable from word count (.72); holdout .82 [.71,.91] is a recorded miss against the .75 threshold.
3. A2-vs-A0 UC reduction is a gpt-judged, same-vendor-family result; it is exploratory, not a deployable-metric or AAC-benefit claim.

Zero-compute fixes to the write-up (post-hoc amendments, none re-declares a threshold; no new generation):
- Report Nemo12B and Qwen14B A2-A0 contrasts beside the gpt UC contrast; label the -287/1,000 figure "gpt-judged, same family as terra/luna generators".
- Reversal claim (-37/1,000, about 11 events): report against both stored and fresh A0 (terra fresh A0 CK .903 vs stored .986; the gain vanishes against stored A0), or drop it.
- State both readings of criterion (iii): strict chip1 SC Spearman (Qwen .48, Nemo .29, fail) and the post hoc UC reading (Qwen .54, pass). Stop rule stands because (i) fails.
- Add leave-one-writer-out AUROCs for M1-free and word count (analysis of stored scores only; 10 writer clusters per half).
- Note A6 UC is NaN for 126/144 rows and filled with 0 in the composite; do not headline composite for A6. The +.031 M1-ref match gain is post hoc, capped at .6, under 0.15 rating point: not an AAC improvement.
- Novelty: no novelty claim for minimal-expansion prompting or two-candidate arms. Open and read Cai 2022, KWickChat, Chen 2023/2024, arXiv 2503.11881 before any positioning paragraph; until verified, cite none as established.
- Human annotation: R-WM-1 (acceptability of A0/A1/A2 outputs) and the verbatim-copy false-flag check stay in ANNOTATION_REQUEST.md, not sent; no benefit-to-people claim before it returns.

### Follow-up F1 pre-declared rule (2026-11-03, written BEFORE running; CPU only, stored scores only, no new model calls)
Source: SYNTHESIS.md section 5 item 5. Data: r2_validity_features.csv, chip1 (n=97, 20 writers) as primary, all200 as secondary.
- Analyses: (a) leave-one-writer-out (LOWO): drop each writer, recompute AUROC of M1free_gpt and T1_wordcount for writer rejection (L1) and the paired delta (M1free - wordcount); (b) writer-jackknife SE and 95% CI (normal, delete-one) of the delta; (c) writer-stratified (within-writer pairs only) AUROC for both scores, to remove between-writer base-rate confounding.
- Verdict rule: "M1-free beats word count" is SUPPORTED only if the jackknife CI of the delta excludes 0 AND the minimum LOWO delta is > 0. "Parity with word count" is reported if the jackknife CI includes 0 and |delta| < .10 in all LOWO fits. The frontier verdict (null metric) FLIPS only under SUPPORTED. Anything else leaves the verdict unchanged. M1-free vs the .75 threshold: report the LOWO min AUROC; the threshold is met only if min >= .75.
- Script: src/frontier_whole_message_followup_lowo.py; outputs followup_lowo.csv, followup_summary.json, followup.md.

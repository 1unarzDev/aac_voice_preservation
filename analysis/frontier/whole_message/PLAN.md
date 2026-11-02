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

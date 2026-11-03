# knows_not_says Follow-up F2 (2026-11-03): continuous negation-mass, K = 256 sampling, verbalised-confidence baseline

Label: POST-PILOT follow-up. Rule pre-declared in PLAN.md ("Follow-up F2" and "F2 implementation notes") before any F2 score was computed. Everything stays detector-relative and PROVISIONAL (the detector-validity annotation has not returned). Source: SYNTHESIS.md section 5 item 7.
Scripts: `src/frontier_knows_not_says_f2_negmass.py` (S1, CPU), `src/frontier_knows_not_says_f2_k256.py` + `frontier_knows_not_says_f2_gpu.sh` (S2 and S3 generation, one blocking flock hold), `src/frontier_knows_not_says_f2_analyze.py` (analysis). Outputs: `followup/` (`r2_retest.csv`, `policy10.csv`, `negmass_*.csv`, `k256_units.csv`), `followup_summary.json`. Raw generations: `runs/frontier_knows_not_says_f2/`.
Note on provenance: the generation stage had been run by an earlier session before this one; its outputs were checked (66,560 K = 256 requests per model, 0 errors; 512 verbal requests per model, 100% parsed) and reused unchanged. This session wrote the analysis.

## Design (as declared)
E-cap4 only (540 units, 107 source-negated, no negation word in the keywords). Models qwen2.5-7b and llama3.1-8b, prompt P0n.
- S1 negation mass: along the stored greedy path, first 12 positions, 1 - prod(1 - m_t) with m_t the top-20 probability on negation tokens.
- S2: K = 256 samples at T = 1 (no truncation), max 40 tokens, same layer0 detector. Units: all 107 positives plus 160 random negatives (HT-rescaled). Lexical comparator read out on the same subset.
- S3: verbalised probability (0 to 100) that the intended message contains a negation, greedy; qwen2.5-7b, llama3.1-8b, plus gpt-6.1-terra as an informational extra.
- R2 passes for a score only if (a) pooled AUROC lower 95% CI > .55 AND (b) pooled AUROC minus lexical >= .03 with the Bonferroni(3) 98.33% paired CI excluding 0. The verdict flips only if a score passes in the pooled row AND each model's point AUROC exceeds the lexical point AUROC. Item bootstrap, B = 10,000, seed 20261102.

## Results (weighted AUROC for source-negated vs not, among no-cue units)
| score | pooled [95% CI] | qwen2.5-7b | llama3.1-8b | lexical | pooled - lexical [98.33% CI] | (a) | (b) | each model above lexical |
|---|---|---|---|---|---|---|---|---|
| S1 negation mass | .669 [.607, .732] | .649 | .690 | .643 | +.026 [-.078, +.124] | pass | fail | yes |
| S2 K = 256 share (267-unit subset) | .617 [.572, .663] | .560 | .674 | .632 | -.015 [-.110, +.078] | pass | fail | no |
| S3 verbalised (local pair) | .597 [.545, .650] | .613 | .581 | .643 | -.047 [-.152, +.057] | fail | fail | no |
| S3 verbalised, gpt-6.1-terra (informational) | .741 [.672, .809] | | | .643 | +.098 [-.010, +.201] | | | |
Stage 1 reference (K = 16 sampled share): qwen .531, llama .590, lexical .643.
S1max (max over positions) is indistinguishable from S1 (pooled .669).

Ties at exactly 0 among positives (resolution check): S1 qwen 46%, llama 11%; S2 (K = 256) qwen 83%, llama 36% (among all subset units 92% and 56%); S3 qwen 0%, llama 62%. Parse rate for S3 100% for all three models.

Secondary policy check, ask the top 10% (caught minus random-ask at the same rate, per 1,000 messages; about 108 positives per 1,000 exist):
| score | qwen | llama |
|---|---|---|
| S1 negation mass | +24.3 [13.5, 36.3] | +22.7 [12.0, 34.5] |
| S2 K = 256 | +10.7 [4.3, 18.7] | +22.4 [11.4, 35.0] |
| S3 verbalised | +8.8 [3.5, 15.2] | +6.1 [0.9, 12.3] |
Lexical logistic: +13.2 [3.9, 23.8] (+9.7 [0.3, 20.4] on the S2 subset). The S1 and lexical policy rows were not contrasted with each other (not declared); their intervals overlap.

## Verdict under the declared rule
- No score passes R2. S1 and S2 clear (a) (they carry a per-input signal above chance, lower CI .61 and .57), but neither beats the lexical keyword classifier by .03 with the CI excluding 0. S3 (local models) does not clear (a).
- The frontier verdict does NOT flip. Reading: "informative but not better than a keyword classifier".
- Resolution caveat: partly lifted. With continuous scores the AUROC rises from Stage 1's .53 / .59 to .65 / .69 (S1), and llama's S2 positives are tied at 0 in 36% of cases (below the 50% bar). It is kept for qwen: 83% of qwen positives still never produce a negation in 256 samples at T = 1, so for that model the signal is absent, not merely unresolved.
- What changed in substance: R2 in its Stage 1 form ("the model has no per-input signal") is too strong. A logprob-derived negation mass is above chance, pooled lower CI .607, and its point estimate is above lexical for both models. What cannot be claimed is superiority; the paired CI against lexical spans -.08 to +.12.
- Lead, not a finding: gpt-6.1-terra's verbalised score (.741, +.098 over lexical, paired CI -.010 to +.201) came close. It cannot flip the verdict under the rule and was not part of the declared pass set; if a frontier-model verbal baseline matters, it is the one thing worth a pre-declared confirmatory run with more units.
- Detector-relative and provisional as before. Two models on the same items are consistency, not replication.

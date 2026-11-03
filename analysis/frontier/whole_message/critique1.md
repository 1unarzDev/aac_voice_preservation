# Critique, round 1 (adversarial: methods/statistics + novelty) - whole_message

Verdict: valid = false (2 fatal issues). Re-checks run on stage1_features.csv (200 Part 18 items, L1 usable n=195, chip1 n=97).

## Fatal
1. Headline "UC removal helps AAC" is not supported by the pilot's own data. The Stage 1 validation target is writer rejection, yet Stage 2 shows UC falling 22 pp (A0 to A1/A2) while M1-ref (match to the writer's meaning) is flat (.489 to .496/.500, CI includes 0) and repair edits are unchanged (~5 words). So the metric validated on writers does not move with the intervention it is used to score, or the UC it measures is not the thing writers reject. The AAC translation ("removes ~222 messages per 1,000") counts a judge flag, not an outcome. The repo's own whole-message analysis (compression loss and misresolution, not added content, drives rejection) points the same way. Either drop the claim or show writers/annotators prefer the treated outputs (R-WM-1, not run).
2. The M1-free vs M0 "validation" is a straw-man comparison. M0 is binary with 96% positives on chip1 (AUROC .53 is a ceiling artifact), versus a graded 1-5 LLM score. The correct benchmark is a trivial graded baseline. My re-check on chip1: output word count alone gives AUROC ~.72 (1 - .276, direction flipped), length/keyword ratio .68, M1-free UC flag alone .71, M1-free graded .77. The M1-free advantage over length is small, untested (no paired delta, CIs overlap hugely given 10 writers per half), and the pre-declared ">= .75 holdout" rule is passed by .82 with CI [.71,.91] whose lower bound is under .75. The "validated" label is overclaimed; "not distinguishable from output length" is the honest reading. Length is also a confound for UC (longer = more added words) and for the arms, since A1 and A3 shorten outputs.

## Major
- Circularity: M1-ref sees the writer sentence that defines L1 (the writer's comparison). AUROC .88-.92 measures LLM reproduction of the writer's contrast, not independent validity. Report as upper bound only. Also M1-ref binary is degenerate (dropped non-empty for 100%), so H2 "406 per 1,000" rests solely on M1-free flags whose precision against humans is unknown; gate c shows 39% of verbatim keyword copies are WMF-fail under M1-free.
- Same LLM family (gpt-6.1) generates (terra), judges M1 (sol) and the critical judge; validation instrument and outcome instrument are the same, so Stage 2 is not independent. The planned Goodhart guard (M4, local logprob) was not run and no non-LLM check was substituted.
- Stage 2 A0 is stored data from an earlier run, A1/A2 fresh; A0-vs-A1 contrast mixes prompt, time and sampling (API ignores seeds). A1 = A2 on UC (37/1000) and WMF (74/1000) exactly; no replicate runs to give a sampling-noise floor, so -22 pp is a one-draw estimate. A1 also raises fragments 0.9% to 10.2%, a cost that offsets part of the UC gain and is only mentioned, not netted into an AAC cost.
- Counts are tiny: 9 reversals per 1,000 is 1 of 108; "46 per 1,000" is 5 of 108. Per-1,000 extrapolation without CIs is misleading. Family near-duplicates not controlled (plan required it), single model, chip1 only; the go/no-go on one model cannot license Stage 3 as planned.
- Writer-cluster bootstrap has 10 clusters per half; the holdout CIs are far too narrow in effect if writers differ (L1 rate ranges .5 to 1.0 by writer). No random-effects or leave-one-writer-out check. The "all 200" AUROCs are inflated by the channel mix (bare is nearly all positive); pooled AUROC partly measures chip-vs-bare.
- Deviation log was appended after Stage 1 outcomes were seen (disclosed), and the switch from binary to graded score for AUROC was decided after seeing the binary degeneracy; the plan's decision rule referenced the binary WMF-fail. Graded score is a post hoc primary.
- Missing declared baselines: G1, always/random-ask, B4/B5 (SHARS-style resample), SelfCheckGPT, M3/M4, Stage 3-5. So the "benchmarked" requirement is unmet; AAC-weighted (SLP) and tap columns are pending.

## Novelty
Prompting "do not add content" and detect-then-resample are standard in faithfulness work (extrinsic hallucination, SelfCheckGPT, SHARS-type); the authors themselves concede A2 is not new over P1. The defensible novelty is the writer-intent label set, not the strategy. Prior-art claim (no paper validates UC against expanding writers' judgments in AAC) rests on search snippets only; sources are unopened [S] and must be verified before any citation.

## Strongest true claims
Under the plain prompt, ~26% of chip1 outputs carry flagged unrequested content versus ~4% under either preservation or minimal-expansion prompts (one model, one draw, judge-defined), while writer-intent match does not improve; and critical-commitment retention alone does not predict writer rejection (59% rejected among CK-kept).

## Next steps
1. Add trivial graded baselines (output length, length ratio, M1 components) to Stage 1 with paired cluster deltas vs M1-free; restate "validated" accordingly.
2. Reframe the AAC claim to compression loss/misresolution; demote UC to a descriptive failure mode, or test UC removal on writer/annotator preference (R-WM-1).
3. Replicate A0/A1/A2 generations (>=3 draws, fresh A0) for a noise floor; report CIs on per-1,000 numbers; net fragments into the cost.
4. Add a non-LLM or different-family judge (M4 local, gemma/qwen) for Stage 2 and a leave-one-writer-out check.
5. Run A4/A5 vs P1, G1, always/random-ask only after the above; add 4 models; open and verify every cited source.

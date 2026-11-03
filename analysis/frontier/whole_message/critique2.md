# Critique, round 2 (adversarial: methods/statistics + novelty) - whole_message

Verdict: valid = true (no fatal issue). The round-2 verdict (metric not beyond length, NO-GO) is conservative and supported. Remaining problems are overclaim risks in the prompt-side and AAC-terms sections. Re-checks were run on r2_outputs.csv (d0 rows, 1,440) and r2_stored_a0_check.csv.

## Major
1. The A2-vs-A0 effect on unrequested content (UC) rests on a single same-vendor judge. gpt-6.1-sol, the same family as the terra and luna generators, defines the UC flag. Nemo12B, the independent judge, shows a far smaller A0-to-A2 gap on chip1: terra .778 to .611, luna .764 to .597, llama .778 to .681. Qwen14B flags only 4 to 8 of 72 outputs per cell. The headline "-287 per 1,000 [-384,-199]" is therefore gpt-judge-defined. The noise section reports only the Qwen sign agreement and does not report the Nemo contrast. Report the A2-A0 contrast on each independent judge's ranking or its calibrated rate before quoting a per-1,000 figure.
2. The silent-reversal gain (-37 per 1,000 [-69,-9]) is about 11 events across 216 chip1 outputs (luna 3 to 0, terra 1 to 0, llama 7 to 3). The fresh terra A0 critical-commitment rate (.903) is 8 pp below the stored A0 run (.986) on the same inputs, which is the size of the claimed A2 gain on CK (+7.4 pp pooled). Against the stored A0, terra A2 (.917) shows no gain. A0 is the baseline here, and its run-to-run noise equals the effect. The A1-A2 reversal difference is -5 per 1,000 [-14,0]. Present reversals as "not distinguishable from endpoint noise" or use both A0 versions.
3. The independent-judge criterion (iii) was read post hoc on the SC score. On chip1, Qwen UC Spearman is .54 (passes the .50 bar) and Qwen SC is .48. Criterion (i) fails regardless, so the stop rule stands. State both readings in the verdict instead of "Qwen misses by .02".
4. Novelty is unsupported. The director's instruction 6 required opening the prior work before any novelty claim; round2.md says no prior work was opened. A quick search shows the closest AAC literature is Cai et al. 2022 (arXiv 2205.03767, which proposes offering several options and requiring user confirmation), the KWickChat and three-candidate systems, and arXiv 2503.11881 (keyword-based generation for AAC). The two-candidate arm is therefore not an AAC contribution, and "critical retention does not predict rejection" is not shown to be unprecedented. I did not open these pages (snippets only), so nothing here is verified for citation. Chen et al. ACL 2023 is cited elsewhere in the repo but not engaged here.
5. The match endpoint is weak. M1-ref is capped at .6, the declared >= .8 criterion is degenerate, and the +.031 gain (terra only) is under 0.15 of a rating point. It is correctly labelled post hoc, but "match +.031 [+.008,+.056]" in the AAC table reads as an improvement. The all-draws and judge-noise floor are not applied to it.
6. Leave-one-writer-out was not run. AUROC CIs come from clusters of 10 writers per half, and L1 rates vary by writer (.5 to 1.0 in round 1). CIs on the chip1 AUROCs (.77 vs .72) are probably too narrow, but the conclusion (no gain over length) is unaffected.

## Minor
- A6 arm: gpt_UC is NaN for 126 of 144 rows, and the composite uses fillna(0), so A6 UC and composite are understated. A6 is used only in the policy tables, but those tables should state this.
- Luna ran with default decoding, d0 only, and terra A1 had no d1-d3. Contrasts on luna are not equivalent in sampling to terra and llama.
- "Pooled equal weight over 3 generators" CIs use n=3 generator-level contrast rows only in the CSV. The CIs come from a family bootstrap, which is fine, but the CSV `n` is misleading.
- Bare channel reversal and harm columns are dominated by the guess rate (CK about .38). They are caveated in round2.md and should not appear in the AAC table.
- Post hoc posthoc60 policy tables are labelled. The always-ask gain (+4 pp chip1) is not above an equal-budget resample, which the report states correctly.

## Strongest true claims
- Whole-message reference-free scoring (M1-free AUROC .77) is not distinguishable from output word count (.72; paired delta +.04 [-.07,+.16]).
- Critical-commitment retention does not predict writer rejection (graded critical AUROC .45 to .55 on chip1; 59% of CK-kept outputs rejected).
- Minimal-expansion and preservation prompts cut gpt-judged UC under every generator, and the gpt-judged direction is stable across draws.
- Detectors do not beat random-ask at matched ask rates.

## Next steps
1. Add the Nemo and Qwen A2-A0 contrasts (ranking-based or calibrated) beside the gpt UC contrast, and downgrade the per-1,000 UC figure to gpt-judged.
2. Report reversals against both A0 runs (stored and fresh) and pool across them, or drop the reversal claim.
3. Open and read Cai 2022, KWickChat, Chen 2023/2024 and the 2503.11881 paper, then rewrite the novelty paragraph.
4. Add leave-one-writer-out AUROCs for M1-free and word count.
5. Send R-WM-1 (acceptability) before any benefit-to-people statement.

Sources (snippets only, unopened): https://arxiv.org/pdf/2205.03767 ; https://arxiv.org/pdf/2503.11881

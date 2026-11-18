# Problem 7: Guard v2 (G2) and item-matched repair audit: frozen plan

Written 2026-11-18, before any G2 generation, before the audit draw is executed, before any rating exists. Not committed.
Nothing below changes after outcomes are seen; later changes go to analysis/guard_v2/DEVIATIONS.md.
Status of what has been seen: Part 17 (analysis/repair_audit_v2) showed repairs cost meaning on stricter endpoints
(repaired vs control usable&preserving -20 pp) and is item-unmatched with n=60/arm. The acceptance rules below were written from the
mechanism (what G1 retries can break), NOT tuned on v2 item texts. The builder must not read v2 repaired texts to adjust any regex or threshold.

## 1. Question and people
Does a post-repair acceptance check make the guard's repairs more usable and meaning-preserving, judged on the SAME inputs?
Humans: about 20 adult non-author classmates annotate study sentences (consented, paid, nothing collected about them). Not AAC users, not
system-user studies. Optional 2 SLPs rate a 40-item subset (secondary, descriptive only).

## 2. G2 definition (frozen; code in src/guard_v2.py, a wrapper that imports interventions.supplied/check/feedback/guard_one unchanged)
G2 = G1 (supplied(), check(), feedback(), temperature 0, 96 tokens, seed 1000 local, tag I1-guard-v2) + acceptance check A(cand, first, spec):
A passes only if ALL hold; otherwise it returns a reason code.
 (i) no collateral change. Label first and cand with layer0.label. For every dimension d in {polarity, speech_act, agent, certainty, politeness}:
     if d was NOT in the first pass's flag list (it was correct or unsupplied), cand label[d] must equal first label[d], except politeness
     may drop to "none" when first had flag politeness:added. Also number set must be a superset of first's numbers_in, and time_class(cand) == time_class(first) when
     time_class(first) is not None and not flagged. Any violation: reason `collateral:<dim>`.
 (ii) complete sentence: parse_ok; exactly one sentence (one terminal .?! at the end, none mid-text except abbreviations Mr/Mrs/Dr/e.g.); ends with . ? or !; starts with a letter
     or digit; >= 3 tokens; last token not in {and, or, but, the, a, an, to, of, for, with, that, if, because, my, your, is, are}; no unbalanced quote/bracket;
     no square-bracket token; no meta lead ("Sure", "Here is", "Rewritten", "Output"); 0.4 <= words(cand)/words(first) <= 2.5. Reason `incomplete`.
 (iii) chip echo: cand must not (a) start with ^(ask|tell|request|command|order)\s+(you|them|him|her|me)\b (case-insens.), (b) contain any chip label string literally
     (labels taken programmatically from interventions.CHIP_TO_GENERAL display tokens, brackets stripped, length >= 2 words only, plus the fixed strings "ask you",
     "tell you", "speech act", "polarity"), (c) contain a 4+ word verbatim n-gram of the chip prompt text. Reason `echo`.
Retry: up to 2 regeneration calls total, same as G1 (same budget). Each retry message appends the acceptance reason in plain words to feedback(flags)
(e.g. "Do not change anything else; write one complete sentence; do not copy the cue words"). Return the FIRST candidate with check()==[] AND A passing.
If none: return the FIRST-PASS text unchanged with flag g2_rejected=<reasons>; (unlike G1, never "fewest flags"). Empty first pass: not eligible.
Log per item: attempts, flags, A reasons, extra_calls, tokens. G2 is deterministic given cache; its first retry equals G1's first retry (cache key reused), so
G2 and G1 are identical whenever G1's repair passes A (concordance by construction, expected 60 to 80 percent; these items contribute 0 discordance to the G2-G1 contrast).
Pre-use check (CPU, no humans): unit tests of A on synthetic fixtures built with src/seeded_faults.py and src/independent_mutants.py (planted collateral, fragment,
echo) must give recall >= 0.9 per fault type and false-reject <= 0.1 on 100 clean model sentences from runs/hw1 P0 (not W-C). If unmet, fix the code once BEFORE the W-C run and log it; no tuning afterwards.

## 3. Stimuli (the item-matched frame)
Frame: every W-C item in runs/guard_wc with prompt_id G1, non-empty flags_initial AND changed == true (G1 repaired). N = 301 (gemma3-4b 147, llama3.1-8b 115,
gpt-6.1-terra 22, qwen2.5-7b 17; 73 families). Reasoning: these are the inputs where a repair was shown to a user.
Excluded: any normalised text that appeared in Parts 4, 11, 17 (the 200 prior audit items).
Draw n = 200 items before G2 is run, using ids only: all 22 terra + 17 qwen items; remaining 161 from gemma (90) and llama (71) by ascending SHA256(output_id + "guardv2-2026").
G2 is then generated for all 301 frame inputs (cost ~ 600 local calls at most); the audit uses the 200 drawn. All 301 are reported descriptively (rate of g2_rejected, changed vs G1, extra calls).
Per drawn item, three sentences (arms): O = original failed (P0 first pass), R1 = G1 repair, R2 = G2 output. Dedup rule: sentences identical after normalisation (lowercase,
collapse whitespace, strip trailing punctuation) are ONE sentence, rated once by 3 raters, credited to every arm that produced it. If R2 == O (G2 rejected, fell back) it is
the O sentence; this is the honest outcome of "returning first pass with a flag" and is retained. Item display: the user's supplied input (typed source sentence or the chip
values, exactly as rate_items.html shows it) and one candidate sentence; arm labels never shown; item order shuffled per rater.

## 4. Raters and assignment
20 raters. Each unique sentence rated by exactly 3 distinct raters; a rater sees at most one sentence per item (so no contrast effect within item). Assignment: Latin-square /
balanced-block routine from src/make_listener_study.py adapted in src/make_guardv2_audit.py (seeded 20261118, explicit sort before every draw). Expected ~450 unique sentences,
~1350 ratings, ~68 per rater plus 8 catch items (4 planted-bad from seeded_faults / independent_mutants with known answer on usable and meaning, 4 known-good plain sentences)
and 3 practice. Exclusion (frozen): rater with < 6/8 catch correct is dropped, their sheets reassigned to a held-out spare rater; if no spare exists, items with < 3 valid ratings are reported
and excluded from the pairing (not imputed). Tools: annotation_package/rate_items.html (questions below), sheets via src/make_assignments.py, returns scored by src/score_repair_audit.py
(new mode --key annotation/guardv2_key.csv; the existing v2 arms mode is extended, existing outputs untouched).
Questions (unchanged wording from Part 17): Pass A usable {yes, minor fix needed, no}; Pass B meaning preserved {yes, partly, no} relative to the supplied input; invented stance {yes, no}
(adds meaning, certainty, politeness or a speaker not given). Can't judge is unknown.

## 5. Endpoints (primary pre-declared)
Item-level consensus = strict majority of known answers among the 3 raters; ties and all-unknown = unknown (reported, excluded from that pair).
 usable = consensus Pass A "yes"; meaning preserved = consensus Pass B "yes"; invented stance = consensus "yes".
PRIMARY 1 (P1): paired difference in MEANING PRESERVED, G2 minus original-failed (R2 - O), over items with consensus on both.
PRIMARY 2 (P2): paired difference in USABLE, G2 minus G1 (R2 - R1), same item.
Secondary (reported, labelled secondary, no inference weight): R1 - O meaning preserved; R2 - R1 meaning preserved; usable and preserving jointly for all three contrasts; invented stance
for all three; usable_or_minor; per model; the rate of g2_rejected; per-rater-rating level analysis; SLP subset agreement with consensus.
Multiplicity: two primaries, Bonferroni, alpha = 0.025 each, two-sided, CIs at 97.5 percent. Secondaries: 95 percent CIs, descriptive.
Decision rules (declared now): P1 is "supported" if the 97.5 percent CI of R2 - O lower bound > 0. P2 is "supported as improvement" if its lower bound > 0, "no worse" if lower bound >= -10 pp
(non-inferiority margin -10 pp), otherwise "G2 not shown to match G1". Any outcome is reported; a null P2 is not re-framed.

## 6. Exact analysis
For each contrast: 2x2 table of paired item consensus (both yes / only first yes / only second yes / neither). Estimate = (b - c)/n. CI = Newcombe method 10 for paired proportions
(score), at 97.5 percent for primaries. Test = exact two-sided McNemar (binomial on b vs c, discordant pairs only), alpha 0.025. Sensitivity 1: cluster bootstrap over family_id
(73 families, 10,000 resamples, seed 20261118) percentile 97.5 percent CI of the paired difference (items from one family share inputs and are not independent). Sensitivity 2: unknown treated as failure
and as success (bounds). Sensitivity 3: rating-level logistic GEE (exchangeable, clustered on item) with arm effect, with rater fixed effect. If cluster bootstrap CI and Newcombe CI disagree on
significance, the cluster bootstrap is the reported primary CI and Newcombe is listed beside it (declared now). Agreement: Krippendorff alpha nominal and pairwise kappa per question; report
if alpha < 0.4 (then consensus is noisy; no recoding).

## 7. Power (frozen)
Target: paired difference of 10 pp in meaning preserved (and usable), exact McNemar / paired-proportion test, alpha 0.025 two-sided (Bonferroni, 2 primaries), power 0.80.
n = (z_{1-a/2} sqrt(p_d) + z_{power} sqrt(p_d - d^2))^2 / d^2, d = 0.10, p_d = discordant proportion.
 p_d 0.15 -> 140 items; 0.20 -> 187; 0.25 -> 235; 0.30 -> 283 (alpha 0.025). (At alpha 0.05: 115, 155, 194, 233.)
Prior information: Part 17 original-failed vs repaired paired: 6 vs 0 discordant of 20 on preserving (p_d 0.30, difference +30 pp), so P1 is powered far above 80 percent
at the expected effect and ~70 percent at a bare 10 pp with p_d 0.30. P2: G2 and G1 coincide on most items, so p_d <= 0.2 is assumed (a changed fraction ~35 percent
and ~half of those discordant on usable); n = 200 gives about 0.82 power at p_d 0.20 and 0.9 at 0.15. The frame has only 301 items, so n = 200 (66 percent of the frame) is the largest
that leaves a draw rule that is not "all": inflating to 250 would add duplicate-family clustering and exceed rater load; design effect from family clustering (~1.1 to 1.2 at 2.7 items per family) is
absorbed by the 0.80 to 0.82 margin and dealt with in the cluster bootstrap. Items with unknown consensus shrink n; expected < 5 percent. If valid pairs < 170 after exclusions, report power achieved, no extension.

## 8. Items and artifacts to build (in order; none run before this plan is hash-deposited)
 1. src/guard_v2.py: G2 wrapper + acceptance check A, unit tests tests/test_guard_v2.py, fixtures via src/seeded_faults.py and src/independent_mutants.py (section 2 pre-use check).
 2. analysis/guard_v2/frame.csv (301 frame ids) and draw.json (200 ids, hash rule above, written before generation; SHA256 of both in FREEZE.md).
 3. G2 generation on the 301 frame inputs: ~/research-cluster/bin/research submit aac-llm (per HANDOFF-AAC.md) for the three local models (gemma3-4b, llama3.1-8b, qwen2.5-7b), API model gpt-6.1-terra via
    codex-lb concurrency <= 4; blocking flock /tmp/aacv_gpu.lock otherwise; Unity priority. Output runs/guard_v2/{generations,outputs}.jsonl, scratch only in ~/aac-voice-preservation/tmp/ (delete after).
 4. Optional automatic arm checks (descriptive): judge src/judge.py (concurrency <= 3) on O/R1/R2 with the blind arbiter src/arbiter_tool.py for disagreements; reported beside, never replacing, the human primary.
 5. src/make_guardv2_audit.py: unique sentence table, dedup map, Latin-square assignment, catch/practice items, key annotation/guardv2_key.csv (item_id, arm map, raters, source ids), sample json, sheets for rate_items.html.
 6. annotation_package sheets x20 + 2 spares; SLP subset of 40 items (the first 40 by the hash order, all three arms) for the 2 SLPs.
 7. src/score_guardv2.py (or the extended score_repair_audit.py mode) implementing section 5 and 6, with --self-check on simulated returns (must reproduce planted known effects and the power numbers in section 7)
    BEFORE real returns are loaded.
 8. analysis/guard_v2/report.md with the pre-declared tables; DEVIATIONS.md; EVIDENCE_MAP entry. Papers are not edited by this task.

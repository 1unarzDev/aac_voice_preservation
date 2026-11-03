# Frontier synthesis (research strategist), 2026-11-03

Inputs: REPORT.md for default_profiles, knows_not_says, multilingual, partner_context, whole_message; value_of_cue summary only (its REPORT.md was not written); ideas/frontier/CRITIC_SYNTHESIS.md; decision_log D-066..D-086. All frontier evidence is machine-only and provisional. Every "not sent" annotation request below is built and waiting for the orchestrator's batch.

## Bottom line
No frontier is journal-ready on its own. None produced a clean positive. Four are nulls or replications of known biases, and the one modest positive (value_of_cue) rests on simulated q and machine labels. The honest asset is a measurement framework plus a set of well-bounded nulls, which together make the "necessary but not sufficient" thesis credible. The strongest TRUE evidence for that thesis is today's human data (D-078), not the frontier runs.

## 1. Ranking (strength of true evidence x novelty x payoff)

| Rank | Frontier | Evidence | Novelty | Payoff | Verdict |
|---|---|---|---|---|---|
| 1 | default_profiles | Medium-high for negation always-commit rate (23.9 [16.0, 32.5] per 1,000); speech act and politeness provisional; ask-policy null (0/4 Holm, MDE 8.5) | Medium (measurement framework: human base rate, SLP-weighted price per 1,000) | Anchors every other frontier; CALE-AI lift; journal section | Keep as the spine |
| 2 | whole_message | Moderate for nulls (M1-free vs word count delta +.04 [-.07, +.16]; critical-only AUROC .45-.55 vs writer rejection; 55/93 commitment-keeping outputs rejected), two judge families agree | Low-medium; the dissociation is the defensible part, and it matches D-082 human data | Directly supports "necessary but not sufficient"; short CALE-AI paragraph | Keep as supporting evidence, drop metric and two-candidate claims |
| 3 | knows_not_says | Medium for reversal scale and qwen overconfidence; low for per-input knowledge (97% / 87% of units tie at 0) | Medium-low; nearest prior arXiv 2511.04869 and 2605.25284 (snippet-checked only) | Negative-result section: "asking beats model uncertainty, and lexical ask matches model ask" | Keep as a section; do not open a new paper unless a continuous score flips R2 |
| 4 | value_of_cue | Moderate for direction, low for size: P-I 13.8% [9.6, 19.3] of SLP-weighted reversals averted at 100 taps, but vs B5-lex only +4.7 [1.1, 9.5], touching 0 at T = 50; q simulated (measured chip restoration .787 vs assumed .9); H2 not met; B6-sup matches P-I | Low-medium | Only candidate "true improvement"; weak and speech-act-only | Lift as honest evaluation framework plus modest result; REPORT.md must still be written |
| 5 | partner_context | Echo effect is real and large (+36.7 pp all negated), propositional part small (+8.7 [6.9, 10.6], author-dependent 4.2 to 9.2); cue removes most | Medium-low (COMPA motivation; Braun contradicts a yes-bias premise) | Bounded subsection; same-tap comparisons only | Subsection, not headline |
| 6 | multilingual | Polarity chip gain replicates in DE/ES/FR (known bias, mechanism check); register default model-dependent on 2 of 6 models; translated stimuli, ES detector failed gate | Low | One paragraph and a small table | Minimal lift; revisit after 4 queued models run |

Cross-cutting reading: the same finding recurs in all frontiers. A silent critical reversal costs about 24 per 1,000 messages for negation. Model uncertainty does not flag it. A cue, whether chip or plain word, removes it at a tap price. Everything beyond that (extra asking policies, whole-message metrics) fails to beat simple baselines. This is a coherent, defensible "limits" story, and it is not a story of a new method that helps.

## 2. What to lift, and what to say

Common caveats for every lift: machine labels, pilot scale, q and rho simulated or transported, SLP weights from n = 2, 20 writers, cluster CIs, no AAC-user data, no J1 fallback.

### SE4All (freeze Nov 10)
Lift almost nothing. SE4All is the societal/access frame; the frontier results are not strong enough to carry a claim there. Allowed, as one sentence in limitations or future work only:
- "Always-commit leaves about 24 silent negation reversals per 1,000 messages at a 2.7% human negation base rate (machine-labelled, provisional); a supplied cue or plain word removes nearly all of them in stored outputs."
Do not lift: any ask-policy claim, any per-1,000 for speech act or politeness, any partner or multilingual claim. Reason: the Nov 10 freeze is too close to get human labels back, and every item here is either already in the study (cue restoration, D-070) or provisional.

### CALE-AI (freeze Nov 16)
Lift as a single "Frontier limits" section with 3 to 4 compact items and 2 figures. Exact claims:
1. **Measurement (default_profiles).** "Always-commit leaves 23.9 [16.0, 32.5] silent negation reversals per 1,000 messages. No tested ask policy beat gated-random at a 10% ask budget (all four Holm p = 1.00; MDE 8.5 per 1,000), so this is a null of limited power, not equivalence." Speech act and politeness (161.9 and 49.4 per 1,000) only in a table tagged "provisional, detector-proxy labels". Keep chip/word reductions out of the abstract (conditional on rho).
2. **Limits of critical-only guarding (whole_message).** "Critical-commitment retention does not predict writer rejection (AUROC .45 to .55; 55 of 93 commitment-keeping outputs rejected). A reference-free whole-message judge does not beat output length (AUROC .77 vs .72, paired delta +.04 [-.07, +.16])." Pair it with D-082 human data (61% rejected; compression loss and event/role misresolution). Unrequested-content reductions only if labelled "gpt-judged"; omit the reversal gain.
3. **Asking beats model uncertainty (knows_not_says).** "Greedy and K = 16 sampling from two 7-8B models almost never restore a dropped negation (sampled negated share 0.49% vs 10.8% target for qwen), the sampled share barely ranks at-risk inputs (AUROC .53 / .59 vs .64 keyword-only), and a model-free lexical ask matches model-based asks." State K = 16 resolution limit and 97% / 87% ties.
4. **Optional, only if space: modest policy result (value_of_cue).** "A learned gate using model internals averts 13.8% [9.6, 19.3] of SLP-weighted speech-act-dominated reversals at 100 taps per 1,000 messages; against a lexicon-gated fixed prompt the gain is +4.7 pp [1.1, 9.5] and its CI touches 0 at T = 50. Quote q = 0.7 (10.7%) beside q = 0.9; use refit CIs; B6-sup matches it." Include the "where it does not help" list. Do not say "calibrated ask-or-assume" or any CRC guarantee. Blocked until value_of_cue/REPORT.md is saved.
5. **Subsection (partner_context).** "A negative partner remark raises negated bare output; +8.7 pp [6.9, 10.6] survives excluding echo and agreement replies (author-dependent: +4.2 to +9.2; conservative +2.8); a supplied cue leaves +1.2 to +7.1 depending on how echoes are counted." Use r3_fig1 and r3_fig3. No per-1,000.
6. **One-line transfer (multilingual).** "Chip restoration holds in DE/ES/FR (pilot, translated, 2 models, machine labels); register defaults are model-dependent." Skip chip-vs-plain equivalence, ctxn, Spanish register.
Citations to add after opening each: Chen et al. ACL 2023 (2305.05976, already in), Cai et al. NAACL 2022, COMPA, Choudhury 2503.11881. Cite 2511.04869 and 2605.25284 only once opened. Never claim an exhaustive AAC search.

Figures to lift: the reversals-vs-asks frontier (default_profiles / value_of_cue), partner r3_fig1 and r3_fig3, whole_message fig1. Each needs a writing-pass redraw to one house style.

## 3. Strongest journal-frontier thesis

**Title.** *Necessary but Not Sufficient: Silent Reversals, Asking, and Writer-Grounded Validity in LLM Keyword Expansion for AAC*

**Thesis.** LLM expansion of AAC keyword strings fails in two separable ways. First, it silently commits to a default reading when a meaning cue is missing from the keywords; for negation this costs about 24 reversals per 1,000 messages, with higher machine-proxy rates for speech act and politeness, and the model's own uncertainty does not flag them. Second, even with every critical cue preserved, writers reject most whole-message drafts (D-078/D-082: 1 of 200 accepted as-is; 61% of judge-correct outputs rejected for event/role misresolution or compression loss), and the LLM judges that the field relies on track writers and SLPs only weakly. Supplying the missing cue (chip or plain word) removes the first failure at a measurable tap price, and a guard repairs it without detectable usability loss, but no tested ask or confidence policy beats cheap lexical and random baselines by a margin we can resolve. We therefore argue for a clinically priced, writer-grounded evaluation: critical commitments are a hard floor, validated against writers rather than judges, and the open problem is intent coverage with approval-gated drafts.

**Contributions.**
1. **A priced default profile.** Per-dimension model default vs human keyword base rate, converted to silent reversals per 1,000 messages and SLP-weighted (default_profiles; D-066 T2 posterior 2.7%), with the always-commit, chip, plain-word and G1 interventions on the same items and the placebo-channel control.
2. **Necessary-not-sufficient, with a decomposition.** Writer rejection split into commitment violation, compression loss, event/role misresolution and added content (whole_message; D-082; D-078 Part 18), showing critical-only guarding explains little of whole-message rejection, plus the validity gap: judge, SLP and writer disagreement, with PPI-corrected intervals.
3. **A calibrated null for asking.** Model-internal, sampled and learned ask policies against always-commit, random, gated-random, lexicon-gated and fixed-prompt baselines on the same items, with MDEs. Result: asking beats model uncertainty, a lexical ask matches model asks, and the only positive (speech act, internals-gated) is modest and q-dependent (knows_not_says, value_of_cue, default_profiles).
4. **Boundary conditions.** Where the finding moves: partner remarks add echo (+8.7 pp propositional), and the chip transfers across DE/ES/FR in a pilot (partner_context, multilingual).

Human data to add before submission: Part 20 and Part 21 (Stage 5), the whole_message R-WM-1 acceptability result, and the default_profiles speech-act and politeness label check. Without these, headline rates for speech act and politeness stay "provisional".

Realistic target: TACCESS or ASSETS-style journal manuscript, early 2027, per the staged plan in CRITIC_SYNTHESIS section 4. It is not a Nov 2026 paper.

## 4. One standalone new-paper idea

**Voice-commitment parity: "Does the synthetic voice say what the text says?"** (CRITIC_SYNTHESIS C9). Render the 547 human minimal pairs (one commitment dimension differs) with 3 TTS systems, neutral and style-prompted. Adult non-author annotators, audio only, recover the contrast; an audio-LLM judge is compared with them. Report per-dimension recoverability and whether style prompts restore lost contrasts (certainty, politeness). It needs no frontier result, reuses the CC BY pair asset, costs about 6 to 8 days and about 20 annotator-hours, and is the only idea that opens a channel the main study never touches. Check speech-venue deadlines (unverified). Caveat: listeners are not AAC users. Runner-up if a speech venue is unwanted: simulated writers (C7), 2 to 3 days. None of the six frontiers earns a standalone paper as it stands.

## 5. What to run next (ordered)

Humans (the orchestrator batches; about 20 adult non-author annotators, no AAC users, no IRB):
1. Send the Nov 16-critical items first: default_profiles (223 items x 2, about 8 min per person), whole_message R-WM-1 (120 items, about 10 min), value_of_cue speech-act stratum A plus stratum B (145-item request, this measures q), partner_context round 3 (258 items x 3, about 15 min). Fold Stage 5 Parts 20 and 21 (about 18 min) into the same packet; total about 50 min per person, so split across two annotator subsets.
2. Second wave if time: knows_not_says (534 items), multilingual (271 items, Spanish annotators first for S items).
3. Nov 3 to 10 CPU-only, no new people: the Stage 0 re-analysis from CRITIC_SYNTHESIS (per-item model of writer acceptance on verdicts, judge labels, embedding similarity, length and dimension; coded "something else" taxonomy; PPI-corrected CIs).

Machine (cheap, within the GPU priority gate D-085/D-086; always under blocking flock):
4. Write value_of_cue/REPORT.md from the saved PLAN, round3 and b5lex files. This is a hard blocker for the CALE-AI item 4.
5. whole_message: leave-one-writer-out for M1-free and word count (quick CPU).
6. default_profiles: same-items chip, plain-word and G1 measurements, plus a CLAM-style comparator; this closes the "benchmark unmet" gap and is the single most valuable engineering item.
7. knows_not_says: continuous negation-mass score, K >= 256 (resolution fix), verbalised-confidence baseline. This is the only run that could flip R2, so run it before deciding to drop the frontier.
8. multilingual: the four queued models (gemma, qwen7b, llama8b, qwen14b); decides whether "model-dependent register default" survives.
9. Open and verify every [S]/[U] citation listed in CRITIC_SYNTHESIS section 7 and each REPORT's novelty paragraph before any novelty sentence.
10. After the Nov 16 freeze, Stage 2 coverage pilot (draft sets, intent coverage per tap) per CRITIC_SYNTHESIS: the one unrun experiment with high surprise potential, and the real core of the journal thesis.

Do not do: probes (C8), constrained decoding (C15), a full tap-priced CRC policy before a Stage 1-style gate shows risk is predictable (the nulls above say it is barely predictable), or new frontier writing beyond the lifts above before human labels return.

## 6. Writing-pass guidance (framing and diagrams)
- Lead with the human, true findings (D-061 to D-082) and present frontier items as "boundary and limits", not as discoveries.
- Always put the baseline beside the method: always-commit, random-ask, gated-random, lexicon-gated, fixed prompt, plain word. Report "where it does not help" as a labelled block.
- Required diagrams: (1) one pipeline figure: keywords, default commitment, silent reversal, cue/ask/guard, tap price; (2) a necessary-not-sufficient waterfall (all drafts, commitments kept, writer-accepted, as-is); (3) one reversals-per-1,000 vs taps frontier with all baselines and CIs; (4) a dimension-by-intervention heat table with SLP-weighted values and a provisional flag.
- Never present simulated q, rho or pi as measured. Never use "calibrated", "equivalent" or "guarantee" for results that are null or heuristic.

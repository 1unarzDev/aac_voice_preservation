# Paper wording for the two expert-input packages

For SE4All and CALE-AI. Not applied to either paper. Numbers in `[brackets]` are placeholders: each must become a macro generated from
`score_slp_panel.py` output or from the closed `FEEDBACK_LOG_TEMPLATE.md` (no hand-typed numbers). Paraphrase freely, but keep the status words:
*expert annotators judging study materials*, *paid design consultants reviewing requirements*, *expert review*, *not a population estimate*,
*not a sample of AAC users*. CALE-AI stays anonymous: no names, no repository URL, no project history.

## 1. Methods

**SLP panel (both papers, methods or evaluation section).**
> Two practising speech-language pathologists acted as expert annotators of study materials. For seven kinds of silent meaning change
> (negation, sentence type, actor, certainty, politeness, time, added content), each rated, on an anchored five-point scale, how serious the change would be if
> spoken as a client's message, and whether a system should block or flag it; the mean of the two ratings gives a severity weight. They then
> rated the same 50 stored outputs, drawn by a seeded rule fixed before rating (20 guard repairs, 10 original outputs for the same inputs, and 10 chip and 10 plain-word-cue outputs for the same inputs, with arm labels hidden), on whether
> each sentence says what the selected words mean and whether it would be acceptable to speak as the client's message.

**Clinically weighted failure rate.**
> We weight each judge-flagged failure by the SLP severity of its type, taking the largest weight among the types flagged on an output, and
> report the mean over outputs next to the unweighted rate.

**AAC-user consultants (both papers, requirements section).**
> The requirements R1 to R5 were reviewed by two paid AAC-user design consultants. They read the requirements in plain language with real
> example outputs and a description of the chip and plain-word designs, and gave design feedback on the requirements and on ten example outputs.
> We logged every suggestion and the change made or not made, and why.

## 2. Ethics (replace the final sentences of the current Ethics paragraph; keep the existing annotator sentences)

> Two speech-language pathologists were paid expert annotators: they judged study materials under a written professional-services agreement, anonymously,
> and the data are about the outputs, not about them. Two AAC-user consultants were paid design consultants who reviewed requirements and examples under a written
> consulting agreement; we did not collect, analyse or report their experiences. Neither package collected demographics, health or disability information, questions about
> the participants' own communication, or recordings; participants are identified only by an ID, and could stop at any time and be paid for time spent.
> The ratings are reported anonymously and in aggregate. As independent researchers we did not seek an institutional review determination.

Use "did not seek an institutional review determination", never "exempt" or "approved" (the existing Ethics wording). Replace the current sentence
"No AAC users, speech-language pathologists or autistic advisers took part in this work" with:
> The requirements were reviewed by two paid AAC-user consultants and rated by two speech-language pathologists as described above; they are still our proposals, and we make no claim about benefit to AAC users.

Do not write "adviser", "co-design", "participatory" or "validated with AAC users".

## 3. Limitations (one place, stated once, briefly)

> The SLP panel is two raters: it is an expert review of a fixed set of outputs, not a population estimate, and its agreement statistics describe these two raters.
> The two consultants are not a sample of AAC users; their feedback shaped the requirements but does not establish what AAC users in general want, and it concerned a text-based design only.

## 4. Sentence patterns for the results

Fill from `score_slp_panel.py` / the closed feedback log. Quote ranges, not intervals, and never "significant".

- Severity: "The two SLPs rated [type with highest mean] as the most serious change (mean [x.x] of 5) and [type with lowest mean] as the least ([x.x]); they would block or flag [k] of seven types."
- Weighted failure: "Weighting each failure by SLP severity, the guard's failure rate falls from [x.x]% (baseline) to [y.y]% (unweighted [a.a]% to [b.b]%)." Or, if it does not: "Weighting by SLP severity leaves the ordering of the arms unchanged / changes it as follows: ..."
- Chip vs plain word: "Weighted failure was [x.x]% for the chip and [y.y]% for the plain-word cue (hw1, six dimensions)."
- Acceptability: "The SLPs judged [k] of [n] guard repairs acceptable to speak as they stand, against [j] of [m] of the original outputs for the same inputs." (Say "rater-judgments" if pooled over the two.)
- Agreement: "The two SLPs agreed on [x]% of the 50 outputs for (a) (Cohen's kappa [x.xx]) and [y]% for (b) ([y.yy]); with two raters these describe this pair, not SLPs in general."
- Against the judge: "On the 50 outputs, SLP (a) = yes matched the judge's meaning-pass on [x]% (SLP1) and [y]% (SLP2); [k] outputs the judge passed were rated no or partly by both SLPs."
- Against classmates: "On the [n] outputs also rated in the classmate audit, SLP and classmate ratings agreed on [x]%."
- Consultants: "Requirements were revised after review by two paid AAC-user consultants: [N] changes to the requirement list ([M] design or wording changes); [K] suggestions were not followed, with reasons in the log." Add examples only from the log, with no identifying detail.
- Examples the consultants judged unacceptable: "Both consultants judged [list of example ids] unacceptable to send; the repaired sentences were [among them / not among them]."

State a null honestly in the same place: "The consultants made no change to R[x]" is a result.

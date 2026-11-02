# T2: is 'affirmative' the Bayes-preferred guess? Posterior of negation given no negation word in the keywords

Stored data only: 0 generation / 0 judge calls. Script `src/robust_t2_posterior.py`; tables `tables.csv`, `polarity_by_model_human_keywords.csv`; numbers in `summary.json`.

## Publishable paragraph (polarity)

Defaulting to *affirmative* when a keyword string contains no negation word is the Bayes-preferred guess on real AAC-style text, so the 99% affirmative share of the models is not by itself an error. In AACText, 8.6% of 6,142 messages are negated (detector, 150/150 against an LLM first pass). A crude content-word compressor (POS-cap4) deletes the negation in 100% of negated messages, and humans typing keywords for the same messages keep it 78.6% of the time (so they drop it 21.4% [15.4, 27.8]). Among keyword strings with no negation word, the share whose source message was negated is therefore 2.7% [1.8, 3.7] for human keywords (Horvitz-Thompson over the elicitation frame; 2.0% by Bayes' rule with the corpus prevalence; 2.2% in the unweighted random half) and 11.4% [9.0, 13.8] for POS-cap4 (8.6% with the corpus prevalence). Guessing affirmative is right 97.3% (human keywords) / 88.6% (POS-cap4) of the time. The models output an affirmative sentence for 99.9% (human keywords) and 99.5% (POS-cap4) of such inputs: the direction of the default is the rational one, but the models are more confident than the evidence (2.5 and 10.9 points fewer negated outputs than the posterior implies), so a frequency argument defends the default but not its certainty. The harm is the asymmetric cost: of every 1,000 messages, about 24 [15, 33] negated messages are silently reversed into an affirmative sentence when the user types the keywords unaided, and 111 [88, 135] with a POS-cap4 compressor, while a spurious negation is introduced in only 0.8 per 1,000. The affirmative guess breaks even with the opposite guess only if a reversed negation costs less than 36 (human keywords) or 8 (POS-cap4) times a spurious one; no sentence-level default can remove that exposure, but a prompt (a [NOT] chip, or a confirmation when no negation word is present) would have to be shown on about 37 (human keywords) / 9 (POS-cap4) inputs per reversal it prevents.

## Estimates by dimension and keyword channel

pi = frame prevalence of the cue in the source message (HT-weighted elicitation sample); d = P(keywords carry no cue | source has cue); post = P(source has cue | keywords carry no cue); model share = share of P0 outputs (4 models) that assert the cue-bearing value given keywords with no cue; reversal/1000 = source has cue, keywords lack it, output lacks it, per 1,000 messages; spurious/1000 = output asserts the cue though the source lacks it. 95% message-bootstrap CIs (stratified by sample type).

| dimension | channel | pi | d (cue dropped) | P(source has cue \| no cue in keywords) | Bayes w/ corpus pi | model share asserting cue \| no cue | silent reversal /1,000 | spurious /1,000 | break-even cost ratio | queries per catch |
|---|---|---|---|---|---|---|---|---|---|---|
| polarity | human | 11.4% [9.2, 13.7] | 21.4% [15.4, 27.8] | 2.7% [1.8, 3.7] | 2.0% | 0.1% [0.1, 0.2] | 23.9 [15.5, 32.5] | 0.8 [0.2, 1.6] | 36.4:1 | 37.4 |
| polarity | pos_cap4 | 11.4% [9.0, 13.8] | 100.0% [100.0, 100.0] | 11.4% [9.0, 13.8] | 8.6% | 0.5% [0.2, 0.7] | 111.0 [88.0, 134.9] | 1.7 [0.1, 3.7] | 7.8:1 | 8.8 |
| politeness | human | 15.4% [12.8, 18.2] | 36.6% [29.5, 43.1] | 6.5% [4.8, 8.2] | 4.6% | 6.7% [5.2, 8.3] | 49.4 [36.4, 63.2] | 75.2 [58.2, 91.7] | 14.4:1 | 15.4 |
| politeness | pos_cap4 | 15.4% [12.7, 18.5] | 21.7% [13.7, 30.3] | 3.9% [2.4, 5.7] | 2.7% | 5.6% [4.1, 7.2] | 33.0 [19.6, 48.4] | 47.4 [34.3, 62.0] | 24.5:1 | 25.5 |
| speech_act | human | 61.7% [57.7, 65.8] | 44.9% [39.5, 50.5] | 47.9% [42.5, 53.3] | 34.8% | 28.2% [24.4, 31.8] | 161.9 [136.4, 188.1] | 62.5 [48.1, 78.0] | 1.1:1 | 2.1 |
| speech_act | pos_cap4 | 61.7% [57.7, 65.9] | 59.6% [53.7, 65.1] | 53.3% [48.3, 58.9] | 39.9% | 19.9% [16.9, 23.1] | 275.0 [240.0, 311.4] | 58.0 [42.3, 75.1] | 0.9:1 | 1.9 |

## Politeness and speech act

**Politeness.** 11.3% of AACText messages carry an explicit polite word (please/could you/thanks/sorry). Given keywords with no polite word, the source was polite in 6.5% [4.8, 8.2] (human) and 3.9% [2.4, 5.7] (POS-cap4, which keeps most 'please'): plain is the Bayes-preferred guess, and for human keywords models assert the cue-bearing value on 6.7% [5.2, 8.3] of such inputs against a posterior of 6.5% [4.8, 8.2] (more than the posterior by 0.2 points); for POS-cap4 models assert the cue-bearing value on 5.6% [4.1, 7.2] of such inputs against a posterior of 3.9% [2.4, 5.7] (more than the posterior by 1.6 points). Politeness the user did type but the keywords dropped is lost for about 49 per 1,000 messages (human keywords); the break-even cost ratio is 14:1, so the asymmetry is far milder than for negation. The opposite error (politeness added that the source lacked; +7.6 pp in hw1 P2 under full input) is a separate false-positive channel: 75 per 1,000 messages here (outputs with any polite marker; the source being plain is the majority case).

**Speech act.** 48.4% of AACText messages are not statements (detector). Given keywords that carry no speech-act cue, the source was a question/request/other in 47.9% [42.5, 53.3] (human) and 53.3% [48.3, 58.9] (POS-cap4), so 'statement' is at best a coin-flip guess; for human keywords models assert the cue-bearing value on 28.2% [24.4, 31.8] of such inputs against a posterior of 47.9% [42.5, 53.3] (fewer than the posterior by 19.7 points); for POS-cap4 models assert the cue-bearing value on 19.9% [16.9, 23.1] of such inputs against a posterior of 53.3% [48.3, 58.9] (fewer than the posterior by 33.4 points). On this dimension the models' statement default is MORE extreme than the posterior supports, with 162 per 1,000 messages having their act reversed or flattened (human keywords). Unlike negation there is no single safe default and the break-even cost ratio is about 1.1:1.

## Per-model silent reversal, polarity, human keywords

| model | silent_reversal_per_1000 | affirmative_share_given_no_neg_word | miss_given_negated_and_dropped |
|---|---|---|---|
| gemma3-4b | 24.157 | 1.000 | 0.991 |
| gpt-6.1-terra | 23.944 | 1.000 | 0.983 |
| llama3.1-8b | 23.455 | 0.996 | 0.962 |
| qwen2.5-7b | 23.944 | 0.999 | 0.983 |

## Checks

* Random half only (unweighted, 300 messages): P(negated | no negation word) = 18/834 = 2.2%.
* hw1 P3 (design-balanced pairs, bare): affirmative 99.76% [99.26, 100.00]; that share is not comparable with the posterior because the pair design makes the true rate 50%; here the real-text posterior is the right benchmark.

## Caveats

* Source polarity, politeness and speech act are detector labels (polarity 150/150 vs LLM first pass; the others less validated), not human gold. Part 9 'lost' flags are the stored lenient ratings.
* The elicitation frame (4,560 texts) excludes messages under 3 words, duplicates and W-B/W-C seeds; short messages ('No.', 'No thanks') are probably more often negated, so frame HT prevalence and the 6,142-message corpus prevalence differ slightly; both are shown.
* The HT frame prevalences (polarity 11.4%, speech act 61.7%) exceed the corpus detector prevalences (8.6%, 48.4%): the enriched-stratum inclusion probabilities are conditional on the random draw and not exact. Treat the HT posterior as the upper and the Bayes-with-corpus-prevalence value as the lower end of the plausible range (they bracket the unweighted random half).
* A negation word in keywords is a lexical test. Humans sometimes encode negation in a content word ('refuse', 'stop'); 'lost' flags (stored ratings) are the lenient human judgement and are used for d; f uses the lexicon.
* Speech-act 'no cue' is the stored lenient 'lost' flag when the source has a cue and a question/request word lexicon otherwise: a proxy.
* Prompt licence (T1: `[NOT]` legend in every prompt) is untested here; this analysis says what the rational default is, not what the model's reason for it is.
* Model outputs are P0 greedy, one draw, 4 models; elic1 arbitrated labels (D-055).

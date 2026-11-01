**Encoding-controlled composition relative to greedy repeat disagreement.**
Each point is the protected-dimension pass→fail proportion on adding the second cue,
minus pass/fail disagreement between d1/d2 on the identical single-cue input.
Left: polarity protected when actor is added; right: agent protected when polarity
is added. Connected dots compare [TELL] and its [STATEMENT] alias under the same
P0x legend. Each model/encoding/panel has 640 aligned cue-addition transitions and
160 unique single-cue repeat pairs. Both draws and all four factorial cells remain
paired. Diamonds pool the four fixed models equally. Bars are pointwise 95%
percentile CIs from 10,000 whole-physical-scenario bootstrap resamples of all 80
scenarios, seed 20261031; expanded A/B records are not independent clusters.

Llama's [STATEMENT] polarity damage is 55/640, exceeding its observed single-cue
repeat floor of 0/160 by 8.59 pp [6.25, 11.09]. Qwen/Gemma agent damage confined
to [TELL] is classified as an encoding defect under the preregistered kill rule.
The selected [TELL] example exposes a CB-7 extraction concern even with judge
agreement; these are stored machine scores, with J1 fallback on disputed focal
labels. Zero-event bootstrap intervals do not establish equivalence. Results
using J2, agreement-only labels, and both-cue repeat floors are in the report.

Source: `analysis/r2d/primary.json` and its input hashes; flat numbers:
`analysis/r2d/headline.json`. Reproduce with
`OPENBLAS_NUM_THREADS=1 .venv/bin/python src/r2d_analyze.py`.

# Pilot1 preliminary signals (DETERMINISTIC layer0 labels only; LLM judge pending) — 2026-10-31
24 families x 2 variants x 5 channels x {P0,P1,P2,S3} x 4 models; 7,680 target rows / 2,949 unique texts.
- H3 (directional defaults under bare): polarity 100% affirmative in EVERY model x prompt incl. P2 spanning sets (negated reading never offered).
  certainty bare: 73% plain, 5% hedged. agent bare: speaker 54%, we 18%, addressee 15%, third 8%.
- H4 (length control): noncrit == bare on every dimension (cue effect not a length artifact).
- H6/H2 (chips): critical match with chip1 0.91-1.00 polarity, 0.95-0.98 agent, 0.69-0.95 certainty, 0.83-0.97 politeness.
  chipall politeness collapses for gemma/qwen (0.55/0.53): extra chips ([ASK]) seem to induce softeners -> politeness Violation. (check with judge)
  speech_act match low even in full (0.66-0.83) -> probably layer0 weakness on refusal/acceptance; needs judge.
- H5 (spanning): coverage@3 under bare, P2 vs sampled S3: politeness 0.75-1.0 vs 0-0.5; agent 0-0.5 vs 0; polarity 0 vs 0.
- Stance additions under bare/noncrit: 'please'/softener added in 4-19% (P0) and 17-38% (P2) of outputs.

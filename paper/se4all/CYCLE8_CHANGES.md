# Cycle 8 (model breadth, C54 + Gemini partial)

- make_macros.py: new block reading analysis/model_breadth/summary.json and gemini_summary.json; macros mb_nmod, mb_nfam, mb_bare_min, mb_leg_min, mb_act_lo/hi, mb_irrel_min, mb_word_max, mb_gem_a/c/n. Asserts the Gemini legend cells have n=184 (a and c) before reporting; Gemini hw/cue tiers are partial and not reported.
- Abstract: one added clause, patterns replicate on six models from five families.
- Method: sentence noting the two larger open models and lite Gemini model were added under unchanged prompts.
- Results: new "Model breadth" paragraph after the controls paragraph (default, legend arms, speech-act chip gain, chip over irrelevant chip, plain word near chip; Gemini legend arms a/c, n=184 each).
- Threats (External): "Four models, three small and quantized" replaced by six models from five families, open <=14B 4-bit, no frontier-size open model, Gemini lite on legend arms only.
- Primary tables still say "four models" (they are the four primary models). Build: 8 pages incl. references, no missing macros.

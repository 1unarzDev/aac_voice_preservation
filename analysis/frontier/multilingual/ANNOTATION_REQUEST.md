# Annotation request: multilingual pilot (draft, not sent)

Purpose: validate (a) translations of minimal pairs and bare keyword strings into German, Spanish, French, and (b) the register and polarity labels on model outputs. Feeds PLAN.md Sec. 4 (label validation) and turns "provisional" into "human-checked".
Who: about 6-9 adult non-author annotators fluent in the language (2-3 per language; ask the orchestrator whether the existing 20 include bilingual people; otherwise paid native checkers). No AAC users, no SLPs, no IRB.
Items (built after Stage 0 as annotation/frontier_multilingual_key.csv and an items JSON for check_pairs.html style tool):
- T: 40 translated pairs per language, drawn by sha256("ml1chk|"+id) order. Q1 "Do A and B differ ONLY in affirmative vs negated?" (yes/no). Q2 "Does the keyword string contain negation or a formal/informal marker?" (yes/no). Q3 "Does the keyword string stand for the same message core as the English?" (yes/partly/no).
- L: 60 model outputs per language (blind to model/arm; 30 polarity, 30 register, drawn by hash). Q4 polarity: affirmative / negated / unclear. Q5 address form: informal (du/tu/tú) / formal (Sie/vous/usted) / none / mixed. Q6 "Sounds natural in this language?" (1-5).
Minutes: about 25 per person (about 100 short judgments). Analysis: kappa against detector/judge, accept translation if >=2 of 3 yes on Q1 and no on Q2; drops reported.

# REFS_VERIFIED: CALE-AI refs.bib (checked 2026-11-04)

Method: each record was opened on 2026-11-04 (ACL Anthology, arXiv, ICLR/NeurIPS proceedings, publisher DOI via the Crossref API, medRxiv); authors, title, venue, year, pages and DOI were compared field by field with refs.bib, and the cited claim was compared with the abstract or text where the page was readable. refs.bib and main.tex were not edited. Entries Crossref-confirmed but whose claim was only checked at abstract level are said so. Not independently reachable: ACM Digital Library pages (Crossref used), Nature page (login redirect; Crossref used), JMIR page (empty; preprint abstract used), PDFs that returned only binary (COMPA, Choudhury; abstract via search/arXiv used).

Counts: corrected: 2, unverifiable: 1, verified: 42, verified record; claim wording needs change: 1; total entries 46.

## Priority actions (CALE-AI)
1. Fix cai2024speakfaster (missing author Sri Jalasutram).
2. Reword: the sentence citing valencia2024compa, mao2025designprobes and xiang2025socializechat for "a one-tap cue such as NOT". None of the three describes a NOT cue. Supported alternatives: COMPA lets AAC users mark conversation segments they intend to address; SocializeChat applies Agree/Disagree/Hesitant/Considerate tags after generation (and notes an initial positive tendency, which is relevant to the paper). Mao et al.'s abstract does not name intent controls. Suggested: "or give the user a control over stance or context~\cite{...}".
3. Chen et al. concerns negative commonsense facts, not AAC messages; say so.
4. lacosse2026cognitivesteering is cited as adding user-side control over intent; the paper's contribution is context-grounded abbreviation expansion with steering (prompt or activation) and bracketed function words incl. "not"; "context control" is more accurate than "intent control".
5. Frisch et al. technical/user-mediated/functional claim is exactly supported.
6. Wang et al. 2026 and Zhao and Hawkins 2025 claims are supported; the VERIFY comments can be removed. ziegenbein2026editing and elgaar2025lingconv exist; elgaar's "collateral change" is the paper's own gloss, not the abstract's.
7. anon2027contracts is unverifiable by design.
8. 13 uncited keys (gorenshtein2026intentdrift, jansevanrensburg2026advisory, vertanen2011imagination, chalfoun2025please, ribeiro2020checklist, angelopoulos2023ppi, donaldson2021everyone, zhang2026politeness, padmakumar2024diversity, williamsceci2026biased, ibrahim2026warmth, zeng2025order, wang2025toxirewrite) exist and are accurate; none prints unless cited.

## Per-entry results

### shen2022kwickchat  [verified]
IUI 2022 pp.853-867, DOI, 4 authors match Crossref (Dudley = John J.; Kristensson = Per Ola).

### cai2024speakfaster  [corrected]
Crossref/Nature record lists 16 authors; bib omits Sri Jalasutram (between Tomanek and Morris). Corrected BibTeX below. Cited for: selection cost / keyword expansion; fine.

Corrected BibTeX / fields:
```bibtex
@article{cai2024speakfaster,
  author = {Cai, Shanqing and Venugopalan, Subhashini and Seaver, Katie and Xiao, Xiang and Tomanek, Katrin and Jalasutram, Sri and Morris, Meredith Ringel and Kane, Shaun and Narayanan, Ajit and MacDonald, Robert L. and Kornman, Emily and Vance, Daniel and Casey, Blair and Gleason, Steve M. and Nelson, Philip Q. and Brenner, Michael P.},
  title = {Using large language models to accelerate communication for eye gaze typing users with {ALS}},
  journal = {Nature Communications}, volume = {15}, number = {1}, pages = {9449}, year = {2024},
  doi = {10.1038/s41467-024-53873-3}
}
```

### valencia2023less  [verified]
CHI 2023, DOI, 6 authors match; pages 1-14 (optional).

### choudhury2025alignment  [verified]
Findings of IJCNLP-AACL 2025, pp.1618-1637, DOI match ACL Anthology. Claim ("test whether affect cues reach the output") supported: keywords + emotion representation (words, VAD, emoji) to sentences, human ratings of how much the sentence conveys the emotion. Preprint arXiv 2503.11881.

### mao2025designprobes  [verified]
DIS 2025 pp.404-422, DOI, 4 authors match. Abstract does not name "intent controls"; see wording note on the intent-controls sentence.

### valencia2024compa  [verified]
CHI 2024, DOI, 9 authors match (pp.1-18). Supports user-marked conversation segments (a context/intent control); does not describe a NOT cue.

### lacosse2026cognitivesteering  [verified]
arXiv 2610.19177 v1, 13 Oct 2026, 3 authors, cs.AI. Claim verified in text: ten high-frequency words, including "not", are given verbatim in square brackets (e.g. "[the] b [is] r h"); "not" is the only negation word kept. Say "keep a short list of bracketed function words, including not" to avoid implying all negation is preserved.

### gorenshtein2026intentdrift  [verified]
medRxiv 10.64898/2026.08.20.26360939, posted 27 Aug 2026, 10 authors match (not peer reviewed; the note says preprint). Uncited.

### xiang2025socializechat  [corrected]
Authors/title/arXiv match. arXiv comment: accepted to IEEE SMC 2025. Add that to note. Supports user stance tags (Agree/Disagree/Hesitant/Considerate applied after generation) but not a NOT cue.

Corrected BibTeX / fields:
```bibtex
  note = {arXiv preprint; accepted to IEEE International Conference on Systems, Man, and Cybernetics (SMC) 2025}
```

### frisch2026complicated  [verified]
arXiv 2606.24854 v1, 23 Jun 2026, 7 authors match; CHI 2026 Speech AI for All workshop. Claim "AI-powered AAC needs technical, user-mediated and functional evaluation together" is exactly supported (Sec 4.1.2). Claim "selection counts omit reading, navigation and fatigue" (SE4All limitations) is implied (mental effort, interface navigation, fatigue, CARE effort score) but the paper never states it about selection counts; write "cf." or "see also" and do not attribute the sentence to them.

### jansevanrensburg2026advisory  [verified]
Crossref: published 10 Sep 2026, 8 authors match; no volume/pages yet (acceptable, online first). Uncited in the active text.

### vertanen2011imagination  [verified]
EMNLP 2011 pp.700-711 (ACL Anthology D11-1065), authors match; no DOI exists. Optionally add url https://aclanthology.org/D11-1065/ in place of the aactext.org page.

### chalfoun2025please  [verified]
Crossref: SPQ 88(1) 66-88, online 2024, issue year 2025. Uncited.

### agarwal2025homogenize  [verified]
arXiv 2409.11360 and Crossref: Dhruv Agarwal, Mor Naaman, Aditya Vashistha, CHI 2025, 1-21. Names no longer from memory.

### ribeiro2020checklist  [verified]
ACL 2020 pp.4902-4912 match. CheckList does define MFT/INV/DIR tests.

### zheng2023judging  [verified]
arXiv 2306.05685: 13 authors match; abstract names position, verbosity and self-enhancement bias (bib text "self-preference" is a fair paraphrase; Panickssery supplies that term). Venue is NeurIPS 2023 Datasets and Benchmarks Track; optionally add to booktitle.

### panickssery2024selfpreference  [verified]
Crossref: NeurIPS 37, pp.68772-68802, DOI match. Optionally add pages = {68772--68802}.

### angelopoulos2023ppi  [verified]
Crossref: Science 382(6671) 669-674. Uncited.

### zisk2019aac  [verified]
Crossref match (Autism in Adulthood 1(2) 93-100).

### donaldson2021everyone  [verified]
Crossref match incl. "endever* corbin" and Jamie McCoy.

### hancock2020aimc  [verified]
Crossref: JCMC 25(1) 89-100 match.

### jakesch2023opinionated  [verified]
Crossref: CHI 2023, 5 authors match.

### arnold2020predictable  [verified]
Crossref: IUI 2020, 3 authors; add pages = {128--138}.

### valencia2020agency  [verified]
Crossref: CHI 2020, 6 authors match (Seunga "Gloria" Yu).

### madaan2023selfrefine  [verified]
NeurIPS 2023 record: 16 authors match. Optionally add doi 10.52202/075280-2019.

### gou2024critic  [verified]
ICLR 2024 page: 7 authors match.

### hohenstein2023communication  [verified]
Crossref: Sci Rep 13, 5487, 9 authors match.

### zhang2026politeness  [verified]
Crossref: PACMHCI 10(6), CSCW094, 23 Sep 2026, pp.1-33, authors match. Uncited in SE4All and CALE-AI.

### padmakumar2024diversity  [verified]
ICLR 2024 page: Padmakumar and He. Uncited.

### klasnja2015mrt  [verified]
Crossref: Health Psychology 34(Suppl) 1220-1228, 7 authors match.

### boruvka2018excursion  [verified]
Crossref confirms JASA 113(523) 1112-1121, DOI, 4 authors. The "CHECK against publisher" comment is resolved.

### anon2027contracts  [unverifiable]
Anonymous concurrent self-citation; cannot be verified by design. Keep as anonymized for review; ensure the camera-ready replaces it with the real record or an arXiv/OSF ID, and that the reviewer-visible text does not rely on unseen claims.

### qu2023conditioning  [verified]
Findings EMNLP 2023 pp.13254-13271, DOI, 3 authors match. Claim: dialog-act conditioning preserves meaning and dialog-act type; "speech-act retention in style transfer" is accurate.

### zhao2025politeness  [verified]  (was marked VERIFY)
EMNLP 2025 main pp.16188-16216, DOI match. Claim supported: models over-use negative politeness; SAC Highlight award. VERIFY comment can be removed.

### wang2026politemisaligned  [verified]  (was marked VERIFY)
Findings EMNLP 2026 pp.26402-26421; DOI as printed by the Anthology (10.18653/2026.findings-emnlp.1248, no /v1/). Claim supported: inter-model agreement exceeds model-human agreement across seven models, plus "neutral compression". VERIFY comment can be removed.

### williamsceci2026biased  [verified]
Crossref: Sci Adv 12(11) eadw5578, 13 Mar 2026, 6 authors match. Uncited.

### ibrahim2026warmth  [verified]
Crossref: Nature 652(8112) 1159-1165, 29 Apr 2026, 3 authors match. Uncited.

### zeng2025order  [verified]
Findings ACL 2025 pp.12479-12492 match. Uncited.

### ziegenbein2026editing  [verified]  (was marked VERIFY)
ACL Anthology: ACL 2026 long, pp.38616-38637, DOI match, 3 authors. Claim supported (meaning-preserving, human-like edits). VERIFY comment can be removed.

### elgaar2025lingconv  [verified]  (was marked VERIFY)
Findings EMNLP 2025 pp.20842-20864 match. Claim "reports a targeted change with collateral change": LingConv controls 40 linguistic attributes while preserving semantics and reports attribute error; plausible but the abstract does not use "collateral change"; keep wording to "controlled paraphrase with semantic preservation".

### wang2025toxirewrite  [verified]
ACL Anthology page: pp.35695-35711, DOI match, 6 authors. Crossref instead lists pp.35683-35699 (disagreement between registries; Anthology kept). Uncited.

### pauli2025stylegap  [verified]
Findings EMNLP 2025 pp.21550-21564 match. Claim supported: metrics correlate with human ratings because test data confound style change and content.

### nicolaidis2019aaspire  [verified]
Crossref match (Autism 23(8) 2007-2019).

### milton2012double  [verified]
Crossref match (Disability & Society 27(6) 883-887).

### cai2022abbrev  [verified]
NAACL 2022 pp.1261-1275, DOI match, 6 authors. Claim (exact-expansion accuracy) fits the abbreviation-expansion evaluation.

### chen2023say  [verified record; claim wording needs change]
Record verified (ACL 2023 pp.9890-9908, Toronto, DOI). The paper shows LLMs write sentences wrongly positive about negative commonsense facts ("lions do not live in the ocean") in keyword-to-sentence constrained generation and attributes it to negation reporting bias. Our wording "positivity bias in keyword-to-sentence generation" is accurate but should say "about negative commonsense facts" so readers do not think it was measured on AAC messages. Not the affirmative default itself being new: correct to cite it as the prior observation.

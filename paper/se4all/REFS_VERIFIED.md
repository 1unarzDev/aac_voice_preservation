# REFS_VERIFIED: SE4All refs.bib (checked 2026-11-04)

Method: each record was opened on 2026-11-04 (ACL Anthology, arXiv, ICLR/NeurIPS proceedings, publisher DOI via the Crossref API, medRxiv); authors, title, venue, year, pages and DOI were compared field by field with refs.bib, and the cited claim was compared with the abstract or text where the page was readable. refs.bib and main.tex were not edited. Entries Crossref-confirmed but whose claim was only checked at abstract level are said so. Not independently reachable: ACM Digital Library pages (Crossref used), Nature page (login redirect; Crossref used), JMIR page (empty; preprint abstract used), PDFs that returned only binary (COMPA, Choudhury; abstract via search/arXiv used).

Counts: corrected: 8, verified: 39, verified record; claim wording needs change: 3; total entries 50.

## Priority actions (SE4All)
1. Fix cai2024speakfaster (missing author Sri Jalasutram; cited and prints). pal2026spica (incomplete author list, pages 218-235) is uncited, so fix it only if it gets cited.
2. Add pages/DOI for cho2025metamorphic; drop "VERIFY" comments that are now resolved (vogelsang2019re4ml, navneet2026voice, zhao2025politeness, wang2026politemisaligned).
3. Reword four claims: R-SPEAK ("scores faithfulness" is unsupported; use co-designed with people with aphasia and compared LLMs on interpreting aphasic speech), Koch et al. ("model-based metrics" rather than "similarity metrics"), Chen et al. (state it concerns negative commonsense facts), and the intent-controls sentence (Mao et al. abstract does not name intent controls; COMPA offers user-marked context, SocializeChat post-hoc stance tags; "expose user-side controls over context or stance" is safer).
4. Frisch et al. as the source for "selection counts omit reading, navigation and fatigue" is an inference; use "see also".
5. Uncited entries do not print (no \nocite), so errors there are harmless; 18 uncited keys could be deleted: weinberg2026irobot, pal2026spica, griffiths2024consultation, griffiths2025authorship, jansevanrensburg2026advisory, varshney-etal-2025-investigating, baradziej2026hedge, chalfoun2025please, agarwal2025homogenize, saparina2026reasoningintent, saravanan2020hierarchical, angelopoulos2023ppi, zhang2026politeness, wang2026politemisaligned, zeng2025order, tang2026throat, wang2025toxirewrite, weinberg2025humor. The 2025-26 entries the paper actually cites (navneet2026voice, zhao2025politeness, altamimi2026rspeak, lacosse2026cognitivesteering, choudhury2025alignment, xiang2025socializechat, frisch2026complicated, mao2025designprobes) all exist.

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

### weinberg2026irobot  [corrected]
Authors/title/DOI match; Crossref gives pp.1-16 and "Tobias M. Weinberg". arXiv 2509.13671 v3 (20 Feb 2026) is the author version. Add pages.

Corrected BibTeX / fields:
```bibtex
@inproceedings{weinberg2026irobot,
  author = {Weinberg, Tobias M. and Gonzalez Penuela, Ricardo E. and Valencia, Stephanie and Roumen, Thijs},
  title = {I, Robot? Exploring Ultra-Personalized {AI}-Powered {AAC}; an Autoethnographic Account},
  booktitle = {Proceedings of the 2026 CHI Conference on Human Factors in Computing Systems},
  year = {2026}, pages = {1--16}, publisher = {ACM},
  doi = {10.1145/3772318.3790310}
}
```

### lacosse2026cognitivesteering  [verified]
arXiv 2610.19177 v1, 13 Oct 2026, 3 authors, cs.AI. Claim verified in text: ten high-frequency words, including "not", are given verbatim in square brackets (e.g. "[the] b [is] r h"); "not" is the only negation word kept. Say "keep a short list of bracketed function words, including not" to avoid implying all negation is preserved.

### pal2026spica  [corrected]  (was marked VERIFY)
Record exists (IUI 2026, pp.218-235, DOI 10.1145/3742413.3789116). Author list "Pal and others" is incomplete: ten authors. Corrected BibTeX below.

Corrected BibTeX / fields:
```bibtex
@inproceedings{pal2026spica,
  author = {Pal, Sayantan and Murali, Nikhil and Jadhav, Atharva Vikas and Bizovi, Jenna and Satchidanand, Antara and Golleru, Manohar and Agarwal, Shalini and Hutchinson, Todd and Higginbotham, Jeff and Srihari, Rohini K.},
  title = {{SPICA}: Scalable and Personalized Conversational Agent Framework for {AAC} Users},
  booktitle = {Proceedings of the 31st International Conference on Intelligent User Interfaces},
  year = {2026}, pages = {218--235}, publisher = {ACM},
  doi = {10.1145/3742413.3789116}
}
```

### xiang2025socializechat  [corrected]
Authors/title/arXiv match. arXiv comment: accepted to IEEE SMC 2025. Add that to note. Supports user stance tags (Agree/Disagree/Hesitant/Considerate applied after generation) but not a NOT cue.

Corrected BibTeX / fields:
```bibtex
  note = {arXiv preprint; accepted to IEEE International Conference on Systems, Man, and Cybernetics (SMC) 2025}
```

### griffiths2024consultation  [corrected]  (was marked VERIFY)
Crossref: Tom Griffiths, Rohan Slaughter, Annalu Waller; JET 18(4) 232-247, DOI match (published 13 Aug 2024). Names now verified, not from memory. Uncited in main.tex.

Corrected BibTeX / fields:
```bibtex
  author = {Griffiths, Tom and Slaughter, Rohan and Waller, Annalu},   % unchanged; names now verified
```

### griffiths2025authorship  [corrected]  (was marked VERIFY)
Crossref: Tom Griffiths, Katherine Broomfield, Laura Hrastelj, Simon Judge, Jonathan Toogood; JET 19(2) 102-112. Title ends "Whose line is it anyway‽" (interrobang), bib has "?!" which is acceptable. Uncited in main.tex.

Corrected BibTeX / fields:
```bibtex
  author = {Griffiths, Tom and Broomfield, Katherine and Hrastelj, Laura and Judge, Simon and Toogood, Jonathan},
  title = {{AI}, communication aids and the challenge of authentic authorship---whose line is it anyway\textinterrobang},
```

### zisk2019aac  [verified]
Crossref match (Autism in Adulthood 1(2) 93-100).

### donaldson2021everyone  [verified]
Crossref match incl. "endever* corbin" and Jamie McCoy.

### frisch2026complicated  [verified]
arXiv 2606.24854 v1, 23 Jun 2026, 7 authors match; CHI 2026 Speech AI for All workshop. Claim "AI-powered AAC needs technical, user-mediated and functional evaluation together" is exactly supported (Sec 4.1.2). Claim "selection counts omit reading, navigation and fatigue" (SE4All limitations) is implied (mental effort, interface navigation, fatigue, CARE effort score) but the paper never states it about selection counts; write "cf." or "see also" and do not attribute the sentence to them.

### jansevanrensburg2026advisory  [verified]
Crossref: published 10 Sep 2026, 8 authors match; no volume/pages yet (acceptable, online first). Uncited in the active text.

### vertanen2011imagination  [verified]
EMNLP 2011 pp.700-711 (ACL Anthology D11-1065), authors match; no DOI exists. Optionally add url https://aclanthology.org/D11-1065/ in place of the aactext.org page.

### varshney-etal-2025-investigating  [verified]
TrustNLP 2025 pp.580-598, DOI, 7 authors match. Uncited.

### baradziej2026hedge  [verified]
Crossref: Frontiers in Language Sciences 5, art. 1953328, 12 Oct 2026, sole author. Uncited.

### chalfoun2025please  [verified]
Crossref: SPQ 88(1) 66-88, online 2024, issue year 2025. Uncited.

### agarwal2025homogenize  [verified]  (was marked VERIFY)
arXiv 2409.11360 and Crossref: Dhruv Agarwal, Mor Naaman, Aditya Vashistha, CHI 2025, 1-21. Names no longer from memory.

### saparina2026reasoningintent  [verified]
arXiv 2511.10453, Saparina and Lapata, v4 8 Aug 2026; comment says "COLM 2026" (listing gives no more). Fine as written. Uncited.

### ribeiro2020checklist  [verified]
ACL 2020 pp.4902-4912 match. CheckList does define MFT/INV/DIR tests.

### yao2024collie  [verified]
ICLR 2024 page: 5 authors match (Austin W. Hanjie). Abstract: grammar-based compositional constraints; claim supported.

### zheng2023judging  [verified]
arXiv 2306.05685: 13 authors match; abstract names position, verbosity and self-enhancement bias (bib text "self-preference" is a fair paraphrase; Panickssery supplies that term). Venue is NeurIPS 2023 Datasets and Benchmarks Track; optionally add to booktitle.

### panickssery2024selfpreference  [verified]
Crossref: NeurIPS 37, pp.68772-68802, DOI match. Optionally add pages = {68772--68802}.

### saravanan2020hierarchical  [corrected]  (was marked VERIFY)
Page opened: Varun Saravanan, Gordon J. Berman, Samuel J. Sober; NBDT vol 3, issue 5, pp.1-25, 21 Jul 2020; arXiv 2007.07797. Bib lacks volume/number/pages. Uncited.

Corrected BibTeX / fields:
```bibtex
@article{saravanan2020hierarchical,
  author = {Saravanan, Varun and Berman, Gordon J. and Sober, Samuel J.},
  title = {Application of the hierarchical bootstrap to multi-level data in neuroscience},
  journal = {Neurons, Behavior, Data Analysis, and Theory}, volume = {3}, number = {5}, pages = {1--25}, year = {2020},
  eprint = {2007.07797}, archivePrefix = {arXiv},
  url = {https://nbdt.scholasticahq.com/article/13927-application-of-the-hierarchical-bootstrap-to-multi-level-data-in-neuroscience}
}
```

### cho2025metamorphic  [corrected]
Real paper; ICSME 2025 pp.174-186, DOI 10.1109/ICSME64153.2025.00025, arXiv 2511.02108. Catalogues metamorphic relations for LLM NLP tasks (claim supported). ICSME page reports 38 MRs/4 LLMs, arXiv version 36 MRs/3 LLMs; do not quote counts. Add pages/DOI.

Corrected BibTeX / fields:
```bibtex
@inproceedings{cho2025metamorphic,
  author = {Cho, Steven and Ruberto, Stefano and Terragni, Valerio},
  title = {Metamorphic Testing of Large Language Models for Natural Language Processing},
  booktitle = {Proceedings of the 41st IEEE International Conference on Software Maintenance and Evolution (ICSME)},
  year = {2025}, pages = {174--186},
  doi = {10.1109/ICSME64153.2025.00025}
}
```

### paiva2021accessibility  [verified]
Crossref: JSS 171, 110819, three authors match. Claim "accessibility engineering spans the life cycle" consistent with an SLR of accessibility across SE processes (title-level check).

### koch2022selfeval  [verified record; claim wording needs change]
Record verified (Insights 2022 pp.180-187, DOI). Abstract: "No metric showed appropriate behaviour for negation" for BERTScore, BLEURT, NUBIA, MoverScore, Mark-Evaluate. Say "model-based evaluation metrics", not "similarity metrics", since BLEURT/NUBIA are learned evaluators.

### angelopoulos2023ppi  [verified]
Crossref: Science 382(6671) 669-674. Uncited.

### altamimi2026rspeak  [verified record; claim wording needs change]
Record verified (JMIR 28, e93518, published 8 Oct 2026; title matches; 10 authors). Co-design is supported: stroke-survivor PPI group (n=5) co-designed with the team. "Scores faithfulness" is NOT supported: eight LLMs were compared for interpretation of AphasiaBank utterances; faithfulness/trust appear as a qualitative theme (misalignment between intended message and output reduced trust). Reword to "was co-designed with people with aphasia and found that mismatch with the intended message reduced trust" or "compared LLMs on interpreting aphasic speech". I could not read the full text (JMIR page returned empty); basis is the JMIR preprint abstract via search.

### zhang2026politeness  [verified]
Crossref: PACMHCI 10(6), CSCW094, 23 Sep 2026, pp.1-33, authors match. Uncited in SE4All and CALE-AI.

### navneet2026voice  [verified]  (was marked VERIFY)
Crossref + arXiv 2602.22145: Navneet, Chandra, Zhang; CHI 2026 Extended Abstracts, pp.1-7 (add). VERIFY note can be removed. Claim verified: semantic preservation stays high (mean SPS 0.748) while cultural/politeness markers are erased (politeness markers lost 71.5% vs lexical 37.1%).

### qu2023conditioning  [verified]
Findings EMNLP 2023 pp.13254-13271, DOI, 3 authors match. Claim: dialog-act conditioning preserves meaning and dialog-act type; "speech-act retention in style transfer" is accurate.

### zhao2025politeness  [verified]
EMNLP 2025 main pp.16188-16216, DOI match. Claim supported: models over-use negative politeness; SAC Highlight award. VERIFY comment can be removed.

### wang2026politemisaligned  [verified]
Findings EMNLP 2026 pp.26402-26421; DOI as printed by the Anthology (10.18653/2026.findings-emnlp.1248, no /v1/). Claim supported: inter-model agreement exceeds model-human agreement across seven models, plus "neutral compression". VERIFY comment can be removed.

### zeng2025order  [verified]
Findings ACL 2025 pp.12479-12492 match. Uncited.

### tang2026throat  [verified]
Crossref: Nat Commun 17, 293, 19 Jan 2026, 23 authors match. Uncited.

### wang2025toxirewrite  [verified]
ACL Anthology page: pp.35695-35711, DOI match, 6 authors. Crossref instead lists pp.35683-35699 (disagreement between registries; Anthology kept). Uncited.

### pauli2025stylegap  [verified]
Findings EMNLP 2025 pp.21550-21564 match. Claim supported: metrics correlate with human ratings because test data confound style change and content.

### weinberg2025humor  [verified]
CHI 2025, DOI, 5 authors match (pp.1-19). Uncited.

### nicolaidis2019aaspire  [verified]
Crossref match (Autism 23(8) 2007-2019).

### milton2012double  [verified]
Crossref match (Disability & Society 27(6) 883-887).

### barr2015oracle  [verified]
Crossref: TSE 41(5) 507-525; add doi 10.1109/TSE.2014.2372785.

### chen2018metamorphic  [verified]
Crossref: CSUR 51(1) art.4, 27 pp.; add doi 10.1145/3143561.

### jia2011mutation  [verified]
Crossref: TSE 37(5) 649-678; add doi 10.1109/TSE.2010.62.

### weyuker1982nontestable  [verified]
Crossref: Computer Journal 25(4) 465-470; add doi 10.1093/comjnl/25.4.465.

### vogelsang2019re4ml  [verified]  (was marked VERIFY)
Crossref: REW 2019 pp.245-251 confirmed; the VERIFY comment can be removed; add doi 10.1109/REW.2019.00050.

### chen2023say  [verified record; claim wording needs change]
Record verified (ACL 2023 pp.9890-9908, Toronto, DOI). The paper shows LLMs write sentences wrongly positive about negative commonsense facts ("lions do not live in the ocean") in keyword-to-sentence constrained generation and attributes it to negation reporting bias. Our wording "positivity bias in keyword-to-sentence generation" is accurate but should say "about negative commonsense facts" so readers do not think it was measured on AAC messages. Not the affirmative default itself being new: correct to cite it as the prior observation.

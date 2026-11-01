# CALE-AI @ AAAI-27: venue facts (verified 2026-10-31)

Full name: **"Evaluating AI Interventions: Causal and Longitudinal Human Effects (CALE-AI)"**.
Sources opened on 2026-10-31:
- Organizer CFP: https://caleai.github.io/
- AAAI-27 workshop listing (CALE-AI entry): https://aaai.org/conference/aaai/aaai-27/aaai-27-workshop-program-list/
- AAAI-27 Author Kit: https://aaai.org/authorkit27/ (redirects to https://aaai.org/wp-content/uploads/2026/10/AuthorKit27.zip,
  zip dated 21 Oct 2026, sha256 `9406a545d5d213757245eb37118fe652b2fccf64f555aff28b49ebe2a780c960`; `TemplateVersion (2027.1)`)
- AAAI-27 main technical track call (parent-conference policy, for context only):
  https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/

Quotes come verbatim from the fetched pages. The organizer page was read through a summarizing fetch tool, so check
each quote against the live page before relying on it for a policy decision.

## Categories and page limits
Organizer CFP:
- "All page limits exclude references."
- "Full Research Papers — up to 8 pages"
- "Short Papers / Work-in-Progress — up to 6 pages"
- "Vision / Position Papers — 4–6 pages"
- "Demo Papers — up to 4 pages"; "Dataset / Benchmark Papers — up to 4 pages"; "Extended Abstracts — up to 2 pages"
- Listed contribution types include "Negative or unexpected results", "Methodological papers" and
  "Reproducibility and evaluation studies".

The AAAI listing is consistent: full 8, short/WIP 6, vision/position 6, demo 4, dataset/benchmark 4, extended
abstract 2. It says to use AAAI format and that references, and appendices "where applicable", are excluded.

**Our choice: Full Research Paper (≤ 8 pages excluding references).** The current draft is 7–8 pages plus
references; see the report in the session log and `main.log`. If the human returns stay at zero, keep the full
category: the paper's claims are about offline evaluation, and every human-dependent claim is already conditional.

## Required content (AAAI listing)
The AAAI listing asks submissions to describe the intervention, the comparison condition, the population and
context, the human outcomes, and the time horizon (paraphrase; its quote limit kept the full sentence out of the
fetch). `main.tex` answers this in Table 1, the evaluation card. Human outcomes and time horizon appear there as
*planned*, not measured.

## Template
- The organizer page names no template. The AAAI listing says "AAAI format".
- We use AAAI-27 Author Kit `aaai2027.sty` / `aaai2027.bst`, copied into this directory, with
  `\usepackage[submission]{aaai2027}` (anonymous submission mode).
- The kit forbids hyperref, geometry, `\vspace{-...}` near floats, `\clearpage`/`\newpage`, `\tiny`, and others
  (see the kit's preamble). `main.tex` follows these rules.

## Anonymity
**Not specified** by either the organizer page or the AAAI listing; the organizer page says only "Each submission
will receive at least two reviews." The AAAI kit has an anonymous-submission template. **Decision: submit
anonymized.** It is the safe default, and the kit supports it. The SE4All sibling is cited as anonymous
concurrent work, and its anonymized PDF can go in the supplement.

## Submission system
EasyChair: https://easychair.org/my/conference?conf=caleai2027. The page's "Submit Paper" button links to "#"
(a placeholder); use the EasyChair URL.

## Dates and timezone
- "Paper submission deadline **November 20, 2026**"; "Author notification **December 2, 2026**";
  "Camera-ready **December 10, 2026**"; "Workshop date **February 22, 23, 2027**".
- Timezone: "Deadlines use the AAAI-relevant timezone if later confirmed." **Not confirmed, so do not assume
  AoE. Plan to submit on Nov 19.**

## In-person requirement
- "CALE-AI is planned as a **one-day, in-person workshop**."
- "Presentations must be delivered in person according to AAAI policy."
- "Registered participants may have access to virtual attendance if provided by AAAI."
- Other AAAI-27 workshop entries repeat that AAAI does not permit virtual presentations. **At least one author
  must present in person in Montréal.** AAAI-27 early registration closes Dec 15, 2026, according to two other
  workshop entries.

## Archival status, prior and concurrent work
- "Accepted contributions will be made available as non-archival workshop papers on the workshop website,
  subject to author permission."
- Extended abstracts only: "Non-archival; prior or concurrently submitted work is welcome."
- **The organizer page states no prior-publication or concurrent-submission policy for full papers.**
- AAAI-27 main track, which is **not** binding on workshops: "AAAI-27 does not permit simultaneous submission of
  papers involving an overlapping set of authors … whether submitted to AAAI-27 or another archival conference or
  journal."
- Our handling:
  - SE4All@ICSE'27 is archival (IEEE), so the CALE-AI paper has to be a distinct contribution. Its focus is
    intervention evaluation: a benefit/harm/cost ledger, kill criteria, and a human-outcome protocol. SE4All's
    focus is requirements, contracts and oracle testing.
  - Shared setup (families, channels, attribution) is summarized in about one paragraph and cited as concurrent.
  - The intervention results (I1/I2 ledgers) appear in SE4All only as a short feasibility note. **The
    orchestrator must check the final SE4All text and keep that note short.**
  - Consider emailing the chairs about concurrent submission. No organizer contact email is listed, so use
    EasyChair or the organizers (Rostami, Oussalah at Oulu; Trattner at Bergen; Veltri at NUS).

## Generative-AI policy
- The organizer page has **no GenAI policy**, and neither does the CALE-AI entry in the AAAI listing.
- AAAI-27 main track (context): "Authors may judiciously use generative AI tools, such as large language models
  and image generators"; "authors remain fully responsible for all submitted material"; "non-existent references,
  or other violations of the Code will be subject to appropriate sanctions".
- Our handling: this draft contains AI-generated text drafted from the project's stored evidence. Every reference
  in `refs.bib` was opened (see `verifiedurl`). A disclosure sentence is drafted (commented out) in `main.tex`;
  the authors decide whether to include it.

## Topics fit (quotes)
- Causal evaluation: "Randomized controlled experiments, A/B tests, micro-randomized trials, sequential
  multiple-assignment randomized trials", "counterfactual evaluation, and off-policy evaluation", and
  "Focus on separating intervention effects from self-selection, context, and system adaptation."
- Longitudinal: "Repeated exposure, cumulative effects, delayed effects, sustained effects, carryover effects,
  habituation, reactance", "preference formation, time-varying confounding, non-stationarity, human–AI
  co-adaptation, and feedback loops."
- RQ2: "How should immediate, sustained, cumulative, delayed, and unintended human effects be measured".

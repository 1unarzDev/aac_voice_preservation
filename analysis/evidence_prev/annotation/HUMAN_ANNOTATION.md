# Human annotation: how to do it (about 60–90 minutes per person)

You will label **what a sentence says**. You never see which model or condition produced it,
or what the original message was. There are no right answers to guess at; label what the words express.

## Setup (2 minutes)
1. Open `annotation/annotate.html` in a browser (double-click it; it needs no internet or server).
2. Type your annotator ID, e.g. `A1` or `A2`. Use the same ID every time.
3. Load the file you were assigned:
   - **Both annotators:** `annotation/gold_core.json` (100 sentences, about 45–60 min). This is the most important part.
   - **If you have more time:** annotator A1 does `gold_extraA.json` (44) and A2 does `gold_extraB.json` (43), about 20–30 min each.
4. Do the 5 practice items first. They show feedback.
5. When finished, click **Download CSV** and put the file in `annotation/returns/` (or send it to the coordinator),
   named like `A1_core.csv`.

## Keys
- `1`–`9`: choose an option for the current question
- `Enter`: next item
- `Backspace`: back
- `S`: unsure/skip this question

Progress saves in the browser automatically, but **download the CSV before closing**.

## What to label
Read `annotation/CODEBOOK.md` once (10 minutes). The short definitions are always shown on screen. In brief:
- **Polarity:** is the main statement negated (not / never / no one) or affirmative?
- **Speech act:** statement, question, request/command, refusal, offer/suggestion, other.
- **Agent:** who does the main action: the speaker (I), the listener (you), we, someone else, or nobody named.
- **Certainty:** plain, hedged (maybe / I think / might), strongly certain (definitely), or n/a for questions and requests.
- **Politeness:** none, please, a softened request (could you / would you mind), thanks/apology.
  "Can you…?" on its own counts as **none**.
- **Added content:** shown last, after you have answered the others. Does the sentence add facts, reasons, people,
  places or times that are not in the typed keywords? Grammar words don't count.

**Work independently.** Don't discuss items with the other annotator until both of you have downloaded your CSVs.

## For autistic reviewers: codebook review (separate, about 45 minutes)
Please read `annotation/CODEBOOK.md`, especially the section "Open questions for reviewers", and tell us, in any format:
- where our definitions of added politeness, certainty or directness don't match what counts as a change to you
- examples that should be treated differently
- anything in the framing that feels wrong

Your comments will be recorded in `orchestration/decision_log.md` with what changed because of them.
Participation and credit are agreed with the study lead. Nothing about you personally is recorded.

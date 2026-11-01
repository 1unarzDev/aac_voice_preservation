# Annotation package: labelling what a sentence says

Thank you for helping. This package contains **everything you need**. Please use **only the files in this folder**.
The project repository holds other files, such as model labels and answer keys, that would bias your judgments,
so please don't open or browse them.

## The task
You will see short English sentences produced by AI writing assistants. For each one you label what the sentence
**says**: whether it is negated, what kind of speech act it is, who does the action, how certain it sounds, whether
it contains politeness markers, and whether it adds content beyond a short keyword list. You will not see which
system produced a sentence or what the "right" answer is meant to be. Label the words on the page.

## Time
- **Part 1, `part1_core.json`** (100 sentences): about 45–60 minutes. **Every annotator does this part.** It is the most important.
- **Part 2, `part2_extraA.json`** (44) and **Part 3, `part3_extraB.json`** (43): optional, about 20–30 minutes each.
  Ideally every annotator does them too; if time is short, split them between annotators.
- **Part 4, `repair_audit.html`** (40 sentences, two short passes): optional, about 15–20 minutes, only after the
  other parts. See the Part 4 section below.
- **Part 5, `wc_source_check.html`** (20 sentence pairs) and **Part 6, `wb_corpus_check.html`** (20 messages, two
  passes): optional, about 15 minutes each, only after Parts 1–4. See the sections at the end.

## Setup (2 minutes)
1. Open `annotate.html` in a desktop browser (double-click it). It works offline and needs no installation.
2. Enter your annotator ID, e.g. `P1`, `P2`. Use the same ID for every part.
3. Click to load a part file. Do the 5 practice items first; they show feedback.
4. Read `CODEBOOK.md` once before starting (about 10 minutes). Short definitions stay on screen while you work. The
   decision rules in `CB_rules.md` are also in the codebook.

## Keys
- `1`–`9` choose an option
- `Enter` next item
- `Backspace` back
- `S` unsure/skip this question

Progress is saved in your browser, but **click "Download CSV" when you finish each part**, and before closing the tab.

## Rules
- **Work independently.** Do not discuss items with other annotators until everyone has submitted.
- Do not use AI tools or search engines to decide labels.
- If two options seem possible, choose the best fit by the codebook and press `S` on that question to mark it unsure.
- "Added content" is asked last, after the typed keywords are shown: does the sentence add facts, reasons, people,
  places or times that are not in the keywords? Grammar words don't count.

## Part 4 (optional, ~15–20 min): sentence check, `repair_audit.html`
Do this only **after Parts 1–3** (or the parts you were asked to do), and only if you have time left. It is a
different, shorter task, and everything it needs is inside the one file. Nothing needs to be loaded.

1. Open `repair_audit.html` in a desktop browser and enter **the same annotator ID** as before. Press `Enter`.
2. **Pass A (40 sentences, about 6–8 min).** Each sentence is shown alone. Answer: *"Is this a complete, natural
   sentence a person could send as-is?"* (`1` yes, `2` minor fix needed, `3` no). If you don't answer yes, a note box
   opens. Type a few words about what is wrong (e.g. "no verb", "wrong pronoun"), then press `Enter`.
3. **Pass B (the same 40 sentences in a new order, about 8–12 min).** Pass B starts after Pass A is finished, and
   **Pass A is then locked**. Now you also see what the user selected (keywords plus chips such as `[NOT]`, whose
   meanings are listed on screen) or the sentence they typed. Answer two questions:
   - *"Does the sentence say everything the input specifies, and nothing that contradicts it?"* (`1` yes, `2` partly, `3` no)
   - *"Does it add meaning, certainty, politeness, or a different speaker that the input did not give?"* (`1` yes, `2` no)
4. Each pass begins with 3 practice items that show feedback. `S` marks a question you can't judge. `Backspace` goes
   back within a pass. Your progress is saved in the browser, and the time spent on each item is recorded automatically.
5. Click **Download CSV** at the end. The file is `repair_audit_<ID>.csv`. Send it along with your other files.

Judge each pass on its own. A sentence can be badly formed and still say what the input specified, and the reverse
can also happen. You will not see which system wrote a sentence or how it was produced. Don't go back to Pass A
after seeing the inputs; the tool prevents this anyway.

## Part 5 (optional, ~15 min): sentence pair check, `wc_source_check.html`
Do this only after Parts 1–4, and only if you have time left. Everything it needs is inside the one file.

1. Open `wc_source_check.html` and enter **the same annotator ID**. Press `Enter`.
2. You see 20 **families**. Each has two sentences, **A** and **B**, that were written to differ in **one** way only:
   negation (*polarity*), what the sentence does (*speech act*: statement, question, request, ...), or *politeness*.
   The dimension is named on screen, with its definitions in the help panel. You also see the **bare keywords** a
   person might select on a communication device, and one extra (noncritical) word shared by both sentences.
3. Answer four questions per family:
   - the value of sentence **A** on that dimension, then the value of sentence **B** (`1`–`7`);
   - *"Could the bare keywords reasonably mean either sentence?"* (`1` yes, `2` only A, `3` only B, `4` neither);
   - *"Do A and B differ ONLY on that dimension?"* (`1` yes, `2` no). If no, a note box opens: type what else
     differs (e.g. "window vs door", "tense changes"), then press `Enter`.
4. Two practice families with feedback come first. `S` marks a question you can't judge; `↑`/`↓` move between
   questions; `Backspace` goes back. Progress is saved in the browser and time per family is recorded.
5. Click **Download CSV** at the end: `wc_source_check_<ID>.csv`.

Label the words on the page, using the same definitions as the codebook. You are not shown what the sentence
writers intended; that is the point of the check.

## Part 6 (optional, ~15 min): message check, `wb_corpus_check.html`
Do this only after Parts 1–4 (before or after Part 5). It uses 20 real messages written for communication
devices, each shortened to a few keywords.

1. Open `wb_corpus_check.html` and enter **the same annotator ID**. Press `Enter`.
2. **Pass 1 (keywords only, about 8 min).** You see only the keywords, never the message. For each of five
   questions (polarity, speech act, agent = who does it, certainty, politeness), **tick every value a person could
   reasonably have meant** with those keywords: natural readings, not far-fetched ones. Tick one value if only one
   makes sense. Keys: `1`–`6` tick or untick a value, `↓`/`↑` move to the next/previous question, `Enter` next message.
3. **Pass 2 (full message, about 6 min).** Pass 2 starts after Pass 1 is finished, and **Pass 1 is then locked**.
   You now see the keywords and the full message the person meant, in a new order. For each question choose the
   **one value the message commits to** (`1`–`6`; the next question is selected automatically).
4. Each pass begins with 2 practice items with feedback. `S` marks a question you can't judge. An optional note box
   is under the questions (`Tab`). Progress is saved in the browser and time per message is recorded.
5. Click **Download CSV** at the end: `wb_corpus_check_<ID>.csv`.

In Pass 1 there is no "right" set: we want to know which readings people find natural. Don't go back to Pass 1
after seeing the messages; the tool prevents this anyway.

## Returning your work
Send the downloaded CSV files, named like `labels_<run>_<ID>.csv` (and `repair_audit_<ID>.csv`,
`wc_source_check_<ID>.csv`, `wb_corpus_check_<ID>.csv` for Parts 4–6), to the study coordinator. Please also send:
- the time you spent;
- a short note on anything confusing in the codebook;
- optionally, whether you have AAC, speech-language or linguistics background. This is used only to describe the annotator pool.

Your labels are used to check how accurately an automatic labelling system reads these sentences. No personal data
beyond your annotator ID and the optional background note is collected.

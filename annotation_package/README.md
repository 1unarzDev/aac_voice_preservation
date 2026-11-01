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
- **Part 7, `write_pairs.html`** (write 15 sentence pairs): about 35 minutes, only if assigned as a writer. See the
  Part 7 section below; it includes the release of your sentences under CC BY 4.0.
- **Part 8, `check_pairs.html`** with a check file from the coordinator (30 sentence pairs written by other people):
  about 20–25 minutes per file, only if assigned.
- **Part 9, `keyword_elicitation.html`** with a message file from `elicitation_sets/` (37–38 messages): about 20
  minutes, only if assigned.
- **Part 10, `part10_gold_new.json`** (162 sentences, same tool and task as Parts 1–3): about 75–90 minutes, only
  if the coordinator assigned it. It can be split into two sittings. See the Part 10 section below.
- **Part 11, `repair_audit_transfer.html`** (40 new sentences, same task as Part 4): about 15–20 minutes, only if
  assigned. See the Part 11 section below.

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

## Part 7 (if assigned, ~35 min): write sentence pairs, `write_pairs.html`
Here you **write** test sentences instead of labelling them. Your coordinator gives you a link or a dimension:
polarity (negation), speech act, politeness, certainty, agent (who does it) or time.

1. Open `write_pairs.html` with the fragment your coordinator gave you, e.g. `write_pairs.html#dim=agent&rot=4&id=P07`
   (this fixes your dimension and topic order and fills in your ID). Without a fragment, enter your ID, press `Enter`,
   and choose the dimension you were given (`1`–`6`).
2. Read the instructions and examples for your dimension, then read the release note below and tick the box.
3. **3 practice pairs** come first: say whether each pair is ready or what is wrong with it (`1`–`4`). You get feedback.
4. Then write **15 pairs**. For each pair:
   - **Sentence A**: an everyday message an adult might send or say (4 to 12 words). Each pair suggests a topic (health,
     sensory, boundaries, work/school, plans, food, transport, money, relationships, self-advocacy, hobbies). Please
     follow it unless it really does not work.
   - **Sentence B**: A changed **only** on your dimension. Everything else (people, action, objects, place) stays the same.
   - The **value** of each sentence on your dimension (e.g. affirmative / negated).
   - **Keywords**: 2 to 4 words found in both sentences, as someone would select them on a communication device. They
     must not give away the difference (no not/never/no, please/could/would, maybe/might/think, I/you/she, question words,
     time words), and someone seeing only the keywords should be able to mean either sentence.
   - Both sentences must share one more word that is not a keyword (a place, time, object or person).
   - Optionally a one-line **situation**, only if the message needs it.
5. The box under the form checks your pair as you type: **Fix** items must be fixed before the pair is saved; **Check**
   items are worth a second look. Keys: `Enter` moves to the next box and, in the keyword box, saves the pair;
   `Ctrl`+`Enter` saves from anywhere; `Page Down` / `Page Up` move between pairs without checking, so you can come back.
6. Avoid stereotypes (about gender, age, disability, culture or religion), real names and private details, and
   anything offensive. Use roles or invented first names ("my sister", "the nurse", "Sam").
7. Click **Download CSV** at the end: `write_pairs_<dimension>_<ID>.csv`.

**Release of your sentences (consent).** The tool shows this text and asks you to agree before you start:

> The sentences, keywords and situations you write will be published with the study data under the Creative Commons
> Attribution 4.0 licence (CC BY 4.0), so that other researchers can reuse them. You will be credited as an anonymous
> item writer by your writer ID only; no name or other personal data is collected. Do not include real names or private
> details. You can stop at any time; nothing is used unless you send your file.

If you do not agree, do not start Part 7. Your sentences are used only if the box is ticked in your file.

## Part 8 (if assigned, ~20–25 min per file): check other people's sentence pairs, `check_pairs.html`
This is the same task as Part 5, on pairs written by other annotators in Part 7. You never get a file with your own
pairs; the tool refuses to start if a file contains them.

1. Open `check_pairs.html`, click **Check file** and choose the file your coordinator sent you (e.g. `hwc007.json`).
   Enter **the same annotator ID** and press `Enter`.
2. Two practice families with feedback come first, as in Part 5.
3. For each pair answer the same four questions as in Part 5: the value of sentence **A** and of sentence **B** on the
   named dimension, *"Could the bare keywords reasonably mean either sentence?"*, and *"Do A and B differ ONLY on that
   dimension?"* (if not, type what else differs). The help panel defines each dimension, including certainty, agent
   and time.
4. Keys as in Part 5 (`1`–`7`, `S`, `↑`/`↓`, `Enter`, `Backspace`). Progress is saved per file.
5. Click **Download CSV** at the end: `check_pairs_<file>_<ID>.csv`.

Judge the words on the page. You are not told what the writer intended.

## Part 9 (if assigned, ~20 min): choose keywords, `keyword_elicitation.html`
Here you **choose keywords** for real messages written for communication devices (AACText, CC BY 4.0).

1. Open `keyword_elicitation.html`, click **Message file** and choose the file your coordinator named, from the
   `elicitation_sets` folder (e.g. `elic_s03_r2.json`). Enter **the same annotator ID** and press `Enter`.
2. You see one full message at a time with this instruction: *"Type the 2–4 words you would select on a keyword-based
   communication device to get this message across, as if each word takes a long time to select."*
3. Type your words, separated by spaces, and press `Enter`. There is no right answer: we want the words **you** would
   really choose, and you may use words that are not in the message. A symbol typed as its own word (for example `?`)
   counts as one selection. If a message makes no sense to you, use **I can't do this one**.
4. Two practice messages come first; the feedback only checks the number of words. `Page Up` goes back; an optional
   note box is under the keyword box. Progress is saved in the browser and time per message is recorded.
5. Click **Download CSV** at the end: `keyword_elicitation_<file>_<ID>.csv`.

You will not see any AI-generated sentences in this part.

## Part 10 (if assigned, ~75–90 min): more sentence labels, `part10_gold_new.json`
This is the same task as Parts 1–3, on 162 new sentences. Use the same tool and the same codebook.

1. Open `annotate.html`, enter **the same annotator ID**, and load `part10_gold_new.json`.
2. Do the 5 practice items again. They are the same as in Part 1, and they are a quick refresher.
3. Label every sentence as in Part 1. The main question (question 1) changes from sentence to sentence: it can be
   about polarity, speech act, agent or politeness. Read it each time. The input appears only for the last question,
   added content, as before.
4. Progress is saved in the browser, separately from Parts 1–3, so you can stop and come back with the same ID. Click
   **Download CSV** at the end: `labels_gold_new_<ID>.csv`.

Some sentences may look alike, or appear twice with different keywords. Label each one on its own.

## Part 11 (if assigned, ~15–20 min): second sentence check, `repair_audit_transfer.html`
This is the same task as Part 4, with 40 different sentences. Follow the Part 4 instructions above (Pass A
sentence alone, then Pass B with the input; 3 practice items per pass). Everything is inside the one file.

1. Open `repair_audit_transfer.html` and enter **the same annotator ID**. Press `Enter`.
2. Its progress is saved separately from Part 4, so doing one does not affect the other.
3. Click **Download CSV** at the end: `repair_audit_transfer_<ID>.csv`.

Don't compare these sentences with the ones in Part 4. Judge each sentence on its own.

## Returning your work
Send the downloaded CSV files, named like `labels_<run>_<ID>.csv` (and `repair_audit_<ID>.csv`,
`wc_source_check_<ID>.csv`, `wb_corpus_check_<ID>.csv` for Parts 4–6, `write_pairs_<dimension>_<ID>.csv`,
`check_pairs_<file>_<ID>.csv` and `keyword_elicitation_<file>_<ID>.csv` for Parts 7–9, `labels_gold_new_<ID>.csv` for Part 10 and
`repair_audit_transfer_<ID>.csv` for Part 11), to the study coordinator. Please also send:
- the time you spent;
- a short note on anything confusing in the codebook;
- optionally, whether you have AAC, speech-language or linguistics background. This is used only to describe the annotator pool.

Your labels are used to check how accurately an automatic labelling system reads these sentences. No personal data
beyond your annotator ID and the optional background note is collected.

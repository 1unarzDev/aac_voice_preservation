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

## Returning your work
Send the downloaded CSV files, named like `labels_<run>_<ID>.csv`, to the study coordinator. Please also send:
- the time you spent;
- a short note on anything confusing in the codebook;
- optionally, whether you have AAC, speech-language or linguistics background. This is used only to describe the annotator pool.

Your labels are used to check how accurately an automatic labelling system reads these sentences. No personal data
beyond your annotator ID and the optional background note is collected.

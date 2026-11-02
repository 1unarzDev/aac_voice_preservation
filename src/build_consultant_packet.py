"""Render the consultant packet (HTML + Markdown) from one content definition and expert_package/_build/consultant_items.json.

    python3 src/build_consultant_packet.py        (run src/build_expert_package.py first)

Writes expert_package/consultant/review.html and expert_package/consultant/REVIEW_PACKET.md.
No scoring or statistics are produced from consultant answers: the form only collects free design feedback.
"""
import csv
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "expert_package/consultant"
D = json.loads((ROOT / "expert_package/_build/consultant_items.json").read_text())
SEED = "expert-panel-2026-11-01"

CHIPS = [("[NOT]", "not"), ("[?]", "this is a question"), ("[ASK]", "this is a request"), ("[TELL]", "this is a statement"),
         ("[I]", "I do it"), ("[YOU]", "you do it"), ("[MAYBE]", "I am not sure"), ("[PLEASE]", "polite"), ("[PAST]", "it already happened"),
         ("[LATER]", "it will happen later")]


def show(inp):
    return inp["text"] if inp["mode"] == "typed" else inp["text"]


def how(inp):
    return "You typed the whole sentence:" if inp["mode"] == "typed" else "You picked these words and buttons:"


# a real chip / plain-word pair for the mock-up (from the SLP key: same input, chip vs word, text differs)
def mock_pair():
    rows = list(csv.DictReader(open(ROOT / "expert_package/slp_key.csv")))
    by = {}
    for r in rows:
        if r["arm"] in ("chip", "word"): by.setdefault(r["pair_id"], {})[r["arm"]] = r
    cand = [p for p in by.values() if len(p) == 2 and p["chip"]["text"] != p["word"]["text"]
            and "please" not in p["chip"]["input_text"].lower()]
    cand.sort(key=lambda p: hashlib.sha256(f"{SEED}|cons_mock|{p['chip']['pair_id']}".encode()).hexdigest())
    p = cand[0]
    return dict(chip_in=p["chip"]["input_text"].replace("Keywords: ", ""), chip_out=p["chip"]["text"],
                word_in=p["word"]["input_text"].replace("Keywords: ", ""), word_out=p["word"]["text"],
                src=f"{p['chip']['source']} / {p['word']['source']}")


MOCK = mock_pair()
R = D["requirements"]; R5 = D["r5"]; EX = D["examples"]

REQS = [
    dict(code="R1", title="Keep the button's meaning",
         plain="If I pick a meaning button, the sentence must keep that meaning. The system must not silently turn “not” into a yes, or a question into a statement.",
         why="A button is extra work. If the system ignores it, the work was wasted and the message can be wrong.",
         ex=[("A good case", R["R1_good"][0]), ("A bad case", R["R1_bad"][0])],
         exnote={"A good case": "The person picked the question button. The sentence is a question.",
                 "A bad case": "The person picked the NOT button. The sentence has no “not” and turns into a different message."}),
    dict(code="R2", title="Do not change a typed sentence",
         plain="If I type a whole sentence, the system must not change it. No added “please”, no added words, no new tone.",
         why="It is my sentence. This rule is a choice we made to protect the person's own words. Some people may want the system to rewrite for them. We want to know what you think.",
         ex=[("A good case", R["R2_good"][0]), ("A bad case", R["R2_bad"][0])],
         exnote={"A good case": "The person typed a sentence. The system kept it as it was.",
                 "A bad case": "The person picked the PLAIN button (no polite words). The system added “Please”."}),
    dict(code="R3", title="Do not quietly guess when the words are unclear",
         plain="If my words could mean more than one thing, the system must not quietly pick one. It should show me the choices, or ask.",
         why="Two words like “shop close” can mean “The shop closes”, “Is the shop closed?” or “Close the shop”. A silent guess can say the wrong thing.",
         ex=[("A case where the system guessed", R["R3_a"][0]), ("Another case where the system guessed", R["R3_b"][0])],
         exnote={"A case where the system guessed": "The words did not say when. The system chose “now”.",
                 "Another case where the system guessed": "The words did not say if it is a question or a statement. The system chose a statement."}),
    dict(code="R4", title="Adding a button must not break something that was right",
         plain="If I add another button, the parts of the message that were already right must stay right.",
         why="People often pick more than one button. A second button should help, not damage the first.",
         ex=[("Same words, more buttons", R["R4"][0])], exnote={}),
    dict(code="R5", title="The test screen must be honest (this one is for the people who test the system)",
         plain="When researchers test the system, the screen they show it must carry the meaning they say it carries. If the test screen is wrong, the system gets blamed for the test's mistake.",
         why="We found this mistake in our own test tool. A button said “maybe” for a sentence that was not unsure. The system followed the button, and the test counted it as a system error.",
         ex=[("Real case 1", R5[0]), ("Real case 2", R5[1])], exnote={}),
]

QUESTIONS_NEVER = "What should a system never change without asking? You can list things, for example words, tone, who does the action, or anything else."
QUESTION_CHIPWORD = "Think about the design only. Which is easier to imagine using: a button (chip) or a plain word?"
CW_OPTS = [("chip", "The button (chip) is easier to imagine"), ("word", "The plain word is easier to imagine"),
           ("both", "Both are fine"), ("neither", "Neither is good"), ("depends", "It depends (please say on what)")]
SEND_OPTS = [("ok", "Fine to send"), ("notok", "Not acceptable to send"), ("unsure", "Not sure")]
IMP_OPTS = [("important", "Important"), ("somewhat", "Somewhat important"), ("not", "Not important")]

INTRO = [
    ("What this is", [
        "We are building a tool that helps a person say a full sentence from a few words. A computer writes the sentence. "
        "Sometimes the computer changes the meaning by mistake. We have written five rules (R1 to R5) that say what the tool must do. "
        "We would like your help to check the rules.",
        "You are being asked as a paid design consultant. You are looking at our rules and at examples that we made. "
        "The examples are tests made by researchers and a computer. They are not real messages from anyone.",
    ]),
    ("What we are asking", [
        "Please tell us what you think about the rules, the button idea and the examples.",
        "We are asking about the tool and these pages only. You do not need to tell us about yourself, your health, how you talk, "
        "or your own life. Please do not write your name or personal stories in the answers. If you want to say something personal, you do not have to.",
        "We do not collect your age, your diagnosis or anything about your own communication. We do not record you.",
    ]),
    ("How to answer", [
        "There is no time limit. Take as long as you like. Take breaks. You can stop at any time and still be paid for the time you spent.",
        "You can answer in any way that works for you. You can type. You can use your AAC device. You can ask a support person to type or write what you say, "
        "word for word, while you are in charge of the answers. You can answer on more than one day. You can skip any question.",
        "The page can show bigger text. You can also print this packet and write on it, or use the .md copy.",
    ]),
]

MD_ANS = "\n\n> Your answer: ______________________________________________\n"


def esc(s): return html.escape(str(s))


# ------------------------------------------------------------------ markdown
def md():
    L = ["# Design review packet", "",
         "*Reading level: plain language. Print this page, or use the web page `review.html`. There is no time limit. You can skip any question, take breaks, "
         "and answer over several days. A support person may write what you say, word for word.*", ""]
    for h, ps in INTRO:
        L += [f"## {h}", ""] + [p + "\n" for p in ps]
    L += ["## The five rules", "", "For each rule: a plain statement, why it matters, real examples, and then questions for you.", ""]
    for q in REQS:
        L += [f"### {q['code']}. {q['title']}", "", f"**Rule:** {q['plain']}", "", f"**Why:** {q['why']}", ""]
        for name, c in q["ex"]:
            if "one_chip" in c:
                L += [f"**{name}.** Here the person picked one button:", f"- Picked: `{c['one_chip']['input']['text']}`", f"- The system wrote: “{c['one_chip']['text']}”",
                      "", "With more buttons on the same words:", f"- Picked: `{c['more_chips']['input']['text']}`", f"- The system wrote: “{c['more_chips']['text']}”",
                      "", "The more-buttons sentence changed the meaning that the one-button sentence kept.", ""]
            elif "source" in c:
                L += [f"**{name}.**", f"- The message the test was about: “{c['source']}”", f"- What the test screen showed the system: `{c['input']['text']}`",
                      f"- What the system wrote: “{c['text']}”", ""]
            else:
                L += [f"**{name}.** {how(c['input'])} `{show(c['input'])}`", f"- The system wrote: “{c['text']}”", f"- {q['exnote'].get(name, '')}", ""]
        L += [f"**Question A.** How important is {q['code']}? Important / Somewhat important / Not important / Skip", "",
              f"**Question B.** Is anything wrong with {q['code']}, or missing from it?" + MD_ANS]
    L += ["### Anything missing", "", "Is there a rule we forgot? What would you add?" + MD_ANS]
    L += ["## What a system should never change without asking", "", QUESTIONS_NEVER + MD_ANS]
    L += ["## A button or a plain word", "",
          "Here is the idea in words. A person picks a few words from a list. There are two ways to say the extra meaning (for example “not”).",
          "", "**Version 1, buttons (chips).** Under the word box is a row of small buttons: " + ", ".join(f"`{c}` ({m})" for c, m in CHIPS) +
          ". The person picks words, and may tap one or more buttons.", f"- Example, picked: `{MOCK['chip_in']}`. The system wrote: “{MOCK['chip_out']}”", "",
          "**Version 2, plain words.** There are no buttons. The extra meaning is a plain word in the same list (for example the word `not`).",
          f"- Example, picked: `{MOCK['word_in']}`. The system wrote: “{MOCK['word_out']}”", "",
          "These are descriptions, not a finished design. We are not saying one is better. A button may take more steps for some ways of using a device. "
          "A word may be easier to find. You tell us.", "", QUESTION_CHIPWORD, "",
          "- The button (chip) is easier to imagine", "- The plain word is easier to imagine", "- Both are fine", "- Neither is good", "- It depends (please say on what)", "",
          "Why?" + MD_ANS]
    L += ["## Ten example sentences", "",
          "Each one was made by the computer from the words shown. For each one: would it be acceptable to send as the person's message? Fine to send / Not acceptable to send / Not sure. If not, tell us why.", ""]
    for c in EX:
        L += [f"### Example {c['id']}", "", f"{how(c['input'])} `{show(c['input'])}`", ""]
        if c["kind"] == "repaired":
            L += [f"- The computer's first try: “{c['first_try']}”", f"- After the system fixed it: “{c['text']}”", "",
                  "Please answer about the fixed sentence. You can comment on the first try too.", ""]
        else:
            L += [f"- The system wrote: “{c['text']}”", ""]
        L += ["Fine to send / Not acceptable to send / Not sure", "", "Why?" + MD_ANS]
    L += ["## Free comments", "", "Anything else you want the authors to know about the design or these pages." + MD_ANS,
          "## Thank you", "", "Please return your answers as described in the agreement. You do not need to give your name with them."]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ html
def chips_html(text):
    out = []
    for p in re.split(r"(\[[A-Z?]+\])", text):
        if not p: continue
        out.append(f'<span class="chip">{esc(p)}</span>' if re.fullmatch(r"\[[A-Z?]+\]", p) else esc(p))
    return "".join(out)


def radios(name, opts, legend, hid=""):
    s = [f'<fieldset><legend>{esc(legend)}</legend><div class="opts">']
    for v, t in opts:
        s.append(f'<label class="opt"><input type="radio" name="{name}" value="{v}"> {esc(t)}</label>')
    s.append("</div></fieldset>")
    return "".join(s)


def text_q(name, label, rows=3):
    return (f'<div class="q"><label for="{name}">{esc(label)} <span class="small">(you can leave this blank)</span></label>'
            f'<textarea id="{name}" name="{name}" rows="{rows}"></textarea></div>')


def example_html(name, c, q):
    if "one_chip" in c:
        return (f'<div class="ex"><p class="lbl">{esc(name)}. One button:</p><p>You picked: {chips_html(c["one_chip"]["input"]["text"])}<br>'
                f'The system wrote: <span class="sent">{esc(c["one_chip"]["text"])}</span></p>'
                f'<p class="lbl">Same words, more buttons:</p><p>You picked: {chips_html(c["more_chips"]["input"]["text"])}<br>'
                f'The system wrote: <span class="sent">{esc(c["more_chips"]["text"])}</span></p>'
                f'<p class="small">The more-buttons sentence changed the meaning that the one-button sentence kept.</p></div>')
    if "source" in c:
        return (f'<div class="ex"><p class="lbl">{esc(name)}</p><p>The message the test was about: <span class="sent">{esc(c["source"])}</span><br>'
                f'What the test screen showed the system: {chips_html(c["input"]["text"])}<br>The system wrote: <span class="sent">{esc(c["text"])}</span></p></div>')
    return (f'<div class="ex"><p class="lbl">{esc(name)}</p><p>{esc(how(c["input"]))} {chips_html(show(c["input"]))}<br>'
            f'The system wrote: <span class="sent">{esc(c["text"])}</span></p><p class="small">{esc(q["exnote"].get(name, ""))}</p></div>')


def page():
    b = []
    for h, ps in INTRO:
        b.append(f'<section aria-labelledby="i-{h[:4]}"><h2 id="i-{h[:4]}">{esc(h)}</h2>' + "".join(f"<p>{esc(p)}</p>" for p in ps) + "</section>")
    b.append('<section aria-labelledby="h-req"><h2 id="h-req">The five rules</h2><p>For each rule you will see the rule, why it matters, real examples, and two questions.</p>')
    for q in REQS:
        b.append(f'<article class="card" id="{q["code"]}" aria-labelledby="h-{q["code"]}"><h3 id="h-{q["code"]}">{q["code"]}. {esc(q["title"])}</h3>'
                 f'<p><strong>Rule:</strong> {esc(q["plain"])}</p><p><strong>Why:</strong> {esc(q["why"])}</p>')
        for name, c in q["ex"]:
            b.append(example_html(name, c, q))
        b.append(radios(f"imp_{q['code']}", IMP_OPTS, f"How important is {q['code']}?"))
        b.append(text_q(f"wrong_{q['code']}", f"Is anything wrong with {q['code']}, or missing from it?"))
        b.append("</article>")
    b.append('<div class="card">' + text_q("missing_rule", "Is there a rule we forgot? What would you add?") + "</div></section>")
    b.append(f'<section aria-labelledby="h-never"><h2 id="h-never">What a system should never change without asking</h2><div class="card">{text_q("never_change", QUESTIONS_NEVER, 5)}</div></section>')
    b.append('<section aria-labelledby="h-cw"><h2 id="h-cw">A button or a plain word</h2>'
             '<p>A person picks a few words from a list. There are two ways to give the extra meaning (for example “not”).</p>'
             '<div class="mock"><p><strong>Version 1: buttons (chips).</strong> Under the word box is a row of small buttons: ' +
             " ".join(f'<span class="chip">{esc(c)}</span> {esc(m)};' for c, m in CHIPS) +
             f' The person picks words and may tap one or more buttons.</p><p>Example. Picked: {chips_html(MOCK["chip_in"])}. The system wrote: <span class="sent">{esc(MOCK["chip_out"])}</span></p></div>'
             '<div class="mock"><p><strong>Version 2: plain words.</strong> There are no buttons. The extra meaning is a plain word in the same list (for example the word “not”).</p>'
             f'<p>Example. Picked: {esc(MOCK["word_in"])}. The system wrote: <span class="sent">{esc(MOCK["word_out"])}</span></p></div>'
             '<p>These are descriptions, not a finished design, and we are not saying one is better. A button may take more steps for some ways of using a device. A word may be easier to find.</p>'
             '<div class="card">' + radios("chip_word", CW_OPTS, QUESTION_CHIPWORD) + text_q("chip_word_why", "Why?") + "</div></section>")
    b.append('<section aria-labelledby="h-ex"><h2 id="h-ex">Ten example sentences</h2>'
             '<p>Each one was made by the computer from the words shown. For each one: would it be acceptable to send as the person’s message? If not, tell us why.</p>')
    for c in EX:
        inner = (f'<h3 id="h-{c["id"]}">Example {c["id"]}</h3><p>{esc(how(c["input"]))} {chips_html(show(c["input"]))}</p>')
        if c["kind"] == "repaired":
            inner += (f'<p>The computer’s first try: <span class="sent">{esc(c["first_try"])}</span><br>After the system fixed it: <span class="sent">{esc(c["text"])}</span></p>'
                      '<p class="small">Please answer about the fixed sentence. You can comment on the first try too.</p>')
        else:
            inner += f'<p>The system wrote: <span class="sent">{esc(c["text"])}</span></p>'
        inner += radios(f"send_{c['id']}", SEND_OPTS, f"Example {c['id']}: acceptable to send?") + text_q(f"why_{c['id']}", "Why?")
        b.append(f'<article class="card" id="{c["id"]}" aria-labelledby="h-{c["id"]}">{inner}</article>')
    b.append("</section>")
    b.append('<section aria-labelledby="h-free"><h2 id="h-free">Free comments</h2><div class="card">' +
             text_q("free", "Anything else you want the authors to know about the design or these pages.", 6) + "</div></section>")
    return "\n".join(b)


FORM_META = []   # (name, label) for the text export, filled in from the page
HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Design Review Form</title>
<style>
  :root { --bg:#fff; --fg:#111; --muted:#333; --line:#6b6b6b; --panel:#f3f3f3; --accent:#0b4fa8; --accent-fg:#fff; --sel:#dbe8ff; --focus:#c25400; --chip:#fff3d6; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#111; --fg:#f2f2f2; --muted:#d0d0d0; --line:#9a9a9a; --panel:#1f1f1f; --accent:#8fb8ff; --accent-fg:#111; --sel:#23365a; --focus:#ffb366; --chip:#3a3016; } }
  :root[data-contrast="high"] { --bg:#000; --fg:#fff; --muted:#fff; --line:#fff; --panel:#000; --accent:#ffff00; --accent-fg:#000; --sel:#003a8c; --focus:#00ffff; --chip:#000; }
  * { box-sizing:border-box; transition:none !important; animation:none !important; }
  html { font-size:20px; } html[data-size="large"] { font-size:25px; } html[data-size="xlarge"] { font-size:31px; } html[data-size="huge"] { font-size:38px; }
  body { margin:0; background:var(--bg); color:var(--fg); line-height:1.6; font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; }
  .skip { position:absolute; left:-999px; top:0; background:var(--bg); padding:8px; border:2px solid var(--fg); } .skip:focus { left:8px; z-index:10; }
  header, main { max-width:900px; margin:0 auto; padding:10px 16px; }
  header { border-bottom:2px solid var(--line); }
  h1 { font-size:1.4rem; margin:.2em 0; } h2 { font-size:1.3rem; margin:1.6em 0 .4em; border-bottom:2px solid var(--line); } h3 { font-size:1.15rem; margin:0 0 .4em; }
  label { font-weight:600; } select, button { font:inherit; padding:6px 12px; border:2px solid var(--fg); background:var(--bg); color:var(--fg); cursor:pointer; }
  button.primary { background:var(--accent); color:var(--accent-fg); border-color:var(--accent); }
  textarea { font:inherit; width:100%; padding:8px; border:2px solid var(--line); background:var(--bg); color:var(--fg); }
  :focus-visible { outline:4px solid var(--focus); outline-offset:2px; }
  .card { border:3px solid var(--line); padding:12px 16px 16px; margin:16px 0; }
  .box { border:2px solid var(--line); background:var(--panel); padding:10px 16px; margin:12px 0; }
  .mock { border:2px dashed var(--fg); padding:6px 16px; margin:12px 0; }
  .ex { border-left:6px solid var(--line); padding:2px 14px; margin:12px 0; }
  .lbl { font-weight:700; margin:.2em 0; } .small { font-size:.85rem; color:var(--muted); }
  .sent { font-weight:700; background:var(--panel); border:2px solid var(--fg); padding:2px 8px; display:inline-block; margin:2px 0; }
  .chip { display:inline-block; background:var(--chip); border:2px solid var(--fg); border-radius:6px; padding:0 6px; font-family:ui-monospace,Menlo,Consolas,monospace; font-weight:700; }
  fieldset { border:2px solid var(--line); margin:12px 0; padding:6px 12px 10px; } legend { font-weight:700; padding:0 6px; }
  .opts { display:flex; flex-wrap:wrap; gap:8px 12px; } .opt { display:inline-flex; gap:8px; align-items:flex-start; border:2px solid var(--line); padding:4px 12px; cursor:pointer; font-weight:400; }
  .opt input { width:1.2em; height:1.2em; margin-top:.3em; }
  .q { margin:12px 0; } nav ul { columns:2; padding-left:1.2em; } .tools { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0; }
  .status { min-height:1.5em; font-weight:600; }
  @media print { .tools, nav, .skip { display:none; } .card { break-inside:avoid; } }
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the form</a>
<header>
  <h1>Design review: five rules and some examples</h1>
  <div class="tools" role="group" aria-label="Page settings">
    <label for="size">Text size</label>
    <select id="size"><option value="normal">Normal</option><option value="large">Large</option><option value="xlarge">Extra large</option><option value="huge">Huge</option></select>
    <label for="contrast">Colours</label>
    <select id="contrast"><option value="auto">Automatic</option><option value="light">Light</option><option value="dark">Dark</option><option value="high">High contrast</option></select>
  </div>
</header>
<main id="main">
  <div class="box"><p><strong>You are in charge.</strong> There is no time limit. Take a break whenever you want. You can skip any question, answer over more than one day, and stop at any time and still be paid for your time. A support person may type or write what you say, word for word. You can also use your AAC device.</p>
  <p>Your answers are saved in this browser as you go. The buttons at the bottom save a file. Nothing is sent anywhere by this page.</p></div>
  <nav aria-label="Sections"><ul>
    <li><a href="#R1">Rule R1</a></li><li><a href="#R2">Rule R2</a></li><li><a href="#R3">Rule R3</a></li><li><a href="#R4">Rule R4</a></li><li><a href="#R5">Rule R5</a></li>
    <li><a href="#h-never">What never to change</a></li><li><a href="#h-cw">Button or plain word</a></li><li><a href="#h-ex">Ten examples</a></li><li><a href="#h-free">Free comments</a></li><li><a href="#h-save">Save and return</a></li></ul></nav>
  <p class="status" id="status" role="status" aria-live="polite"></p>
  <form id="form" onsubmit="return false">
__PAGE__
  <section aria-labelledby="h-save"><h2 id="h-save">Save and return</h2>
    <p>You can save a readable file of your answers, and a progress file to carry on later. Do not put your name in the answers. How to return the file is in the consulting agreement.</p>
    <div class="tools"><button type="button" class="primary" id="savetxt">Save my answers as a text file</button>
    <button type="button" id="savejson">Save a progress file</button>
    <button type="button" id="loadjson">Load a progress file</button><input type="file" id="jsonfile" accept=".json,application/json" hidden aria-label="Choose a progress file"></div>
    <p class="small">Anonymous page. It collects no personal information, makes no recordings and does not use the network.</p></section>
  </form>
</main>
<script>
"use strict";
const $ = id => document.getElementById(id), KEY = "consultant_review_v1", form = $("form");
function say(m) { $("status").textContent = m; }
function collect() { const o = {}; form.querySelectorAll("textarea").forEach(t => { if (t.value.trim()) o[t.name] = t.value; });
  form.querySelectorAll("input[type=radio]:checked").forEach(r => { o[r.name] = r.value; }); return o; }
function save() { try { localStorage.setItem(KEY, JSON.stringify(collect())); } catch (e) {} }
function fill(o) { Object.keys(o).forEach(k => { const t = form.querySelector('textarea[name="' + k + '"]'); if (t) t.value = o[k];
  const r = form.querySelector('input[type=radio][name="' + k + '"][value="' + o[k] + '"]'); if (r) r.checked = true; }); }
function labelOf(name) { const t = form.querySelector('[name="' + name + '"]'); if (!t) return name;
  if (t.tagName === "TEXTAREA") { const l = form.querySelector('label[for="' + name + '"]'); return (l ? l.textContent : name).replace(/\\(you can leave this blank\\)/, "").trim(); }
  const fs = t.closest("fieldset"); return fs ? fs.querySelector("legend").textContent : name; }
function download(name, text, type) { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], {type})); a.download = name; document.body.append(a); a.click(); a.remove(); }
form.addEventListener("input", save); form.addEventListener("change", save);
$("savetxt").addEventListener("click", () => { const o = collect(); const lines = ["Design review answers", ""];
  Array.from(form.querySelectorAll("textarea,input[type=radio]")).forEach(el => { const n = el.name; if (lines.indexOf("\\u0000" + n) >= 0 || !(n in o)) return; lines.push("\\u0000" + n);
    const v = el.type === "radio" ? (form.querySelector('input[name="' + n + '"][value="' + o[n] + '"]').parentElement.textContent.trim()) : o[n];
    lines.push("Q: " + labelOf(n), "A: " + v, ""); });
  download("design_review_answers.txt", lines.filter(l => l[0] !== "\\u0000").join("\\n"), "text/plain"); say("Saved a text file."); });
$("savejson").addEventListener("click", () => { download("design_review_progress.json", JSON.stringify(collect()), "application/json"); say("Saved a progress file."); });
$("loadjson").addEventListener("click", () => $("jsonfile").click());
$("jsonfile").addEventListener("change", e => { const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = () => { try { fill(JSON.parse(r.result)); save(); say("Progress loaded."); } catch (x) { say("That file could not be read."); } }; r.readAsText(f); e.target.value = ""; });
$("size").addEventListener("change", () => { document.documentElement.dataset.size = $("size").value; try { localStorage.setItem(KEY + "_size", $("size").value); } catch (e) {} });
$("contrast").addEventListener("change", () => { const v = $("contrast").value, h = document.documentElement; if (v === "high") { h.dataset.contrast = "high"; delete h.dataset.theme; } else { delete h.dataset.contrast; if (v === "auto") delete h.dataset.theme; else h.dataset.theme = v; } try { localStorage.setItem(KEY + "_contrast", v); } catch (e) {} });
try { const s = localStorage.getItem(KEY + "_size"); if (s) { $("size").value = s; document.documentElement.dataset.size = s; }
  const c = localStorage.getItem(KEY + "_contrast"); if (c) { $("contrast").value = c; $("contrast").dispatchEvent(new Event("change")); }
  const o = localStorage.getItem(KEY); if (o) fill(JSON.parse(o)); } catch (e) {}
</script>
</body>
</html>
"""


def main():
    (OUT / "REVIEW_PACKET.md").write_text(md())
    (OUT / "review.html").write_text(HTML.replace("__PAGE__", page()))
    print("wrote review.html and REVIEW_PACKET.md; mock pair:", MOCK)


if __name__ == "__main__":
    main()

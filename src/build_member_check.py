"""Build the consultant member-check packets (HTML + MD) for C01 and C02.
Rows are neutral paraphrases of each consultant's OWN answers (annotation/returns_consultant/<id>/design_review_answers.txt)
and of the change log (paper/se4all/consultant_log.csv). Quotes are checked to be verbatim substrings of that consultant's answers."""
import html, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "expert_package/consultant/member_check"
DUE = "Nov 19, 18:00"

ROWS = {
"C01": [
 ("Who decides when a draft is spoken",
  "A made-up sentence should stay a draft until the person approves it. The person can hear or look at it privately, change it, or cancel. The person's own words stay available, and can be spoken directly.",
  "We added a new rule, R6. A draft is never spoken or sent without the person's approval, and the typed words stay available."),
 ("R1, keep the button's meaning",
  "A chosen button must keep its meaning and its reach. NOT must stay with the action it was meant for. If two choices clash, the system should ask instead of picking one.",
  "R1 now says NOT stays with the intended action, and that a clash between two choices is shown next to those choices."),
 ("R2, typed sentences",
  "A complete typed sentence should be spoken as typed, unless the person asks for a rewrite. A rewrite needs a visible proposed change and approval before speech. The bad example under R2 did not show this.",
  "R2 now says exact copy is the default, and a rewrite needs a request and a preview. We did not make a new R2 example for the packet. We wrote down that the old example missed the point."),
 ("R3, unclear words",
  "Show the one choice that is unclear, such as who acts or whether it is a question. The person can pick, keep the short words, or cancel. The extra steps should be short and easy to undo. One answer should not quietly become a lasting habit.",
  "R3 now pairs the logged guess with a short choice that can be undone. We have not written a rule about lasting habits."),
 ("R4, adding a button",
  "Keep every meaning that was already chosen and still fits. If a new button changes an earlier one on purpose, show the change for approval. TELL means a statement. It must not become the word \"tell\".",
  "R4 now covers who does what, not only button labels. We added a test: a TELL button must not produce a \"tell\" verb that the words did not have."),
 ("What never to change without asking",
  "Do not change yes or no, who acts, ownership, permission, consent, urgency, numbers, names, event time, or a chosen tone without asking. Do not invent reasons, feelings or promises. A blunt message must not become a polite suggestion.",
  "Partly. We test the things our coding scheme scores. We do not yet test names, amounts, ownership, consent or urgency, and we say so."),
 ("Button or plain word",
  "A button is easier to imagine, but this is a design preference, not proof that buttons need fewer steps. Plain words should stay an equal option. Test real steps on a working prototype. The two mockups also differed in event time.",
  "We have not picked a default and we do not say either is easier. Comparing real steps needs a study with users, which we have not done. We did not redo the mockups in the packet. Our tests use the same message for both ways."),
 ("The test examples",
  "Check what a test input really says before judging the output. A bad meaning button is a different problem from a system that ignores a good button.",
  "This was already in R5. The two inputs that were wrong became test cases in our checker."),
],
"C02": [
 ("Who decides when a draft is spoken",
  "Writing and editing a draft must never send or speak it. There should be one clear Send or Speak action, an editable preview, and a quick Undo. The chosen words stay visible while the person tries other versions.",
  "We added a new rule, R6. A draft is never spoken or sent without the person's approval, and the typed words stay available. We did not write the preview and Undo details into the rule."),
 ("R1, keep the button's meaning",
  "A question button must stay a question. NOT must cancel the intended action. ASK means asking the listener to act. TELL means a statement. Neither should be copied as the word \"ask\" or \"tell\". If two choices clash, show the clash next to them.",
  "R1 now says NOT stays with the intended action, and that a clash is shown next to the choices. The papers say TELL marks a statement and is not the verb."),
 ("R2, typed sentences",
  "Keep typed words as typed. Offer a Rewrite action as an option, with an editable preview, the original beside it, and Undo. Choosing Rewrite should make a draft, not send it. No extra pop-up for each spelling fix. The bad example under R2 did not show a rewritten typed sentence.",
  "R2 now says exact copy is the default, and a rewrite needs a request and a preview. We did not make a new R2 example for the packet. We wrote down that the old example missed the point."),
 ("R3, unclear words",
  "Do not quietly decide who acts, what is negated, the time, or whether it is a question. A few different drafts with the difference marked work better than a chain of questions. A preview is never spoken or sent by itself.",
  "R3 now pairs the logged guess with a short choice that can be undone."),
 ("R4, adding a button",
  "Keep relations too: who reads, what is negated, what the sentence is about. Adding TELL must not create a new event of telling someone. If a new button clashes with an earlier one, explain that and offer a direct change. Do not make the person confirm every unchanged part.",
  "R4 now covers who does what, not only button labels. We added a test: a TELL button must not produce a \"tell\" verb that the words did not have."),
 ("What never to change without asking",
  "Do not silently change yes or no, question or statement, who acts, names, places, amounts, dates, event time, doubt, or a chosen politeness. Fixing grammar is fine inside a rewrite the person asked for.",
  "Partly. We test the things our coding scheme scores. We do not yet test names, amounts or dates, and we say so."),
 ("Button or plain word",
  "It depends. Use the route that needs fewer sure steps for the person's access method. Both routes should set the same visible meaning and allow fixes in place. Compare the effort with users before choosing a default. The two mockups also differed in tense and added \"now\".",
  "We have not picked a default. Comparing effort needs a study with users, which we have not done. We did not redo the mockups in the packet. Our tests use the same message for both ways."),
 ("The test examples",
  "Check that each example really supports its buttons before using it to score the system. Keep wrong test inputs visible as test problems. A system that follows one wrong button has not made every other change right.",
  "This was already in R5. The two inputs that were wrong became test cases in our checker."),
],
}
QUOTES = {
"C01": ["the person decides when a draft is spoken",
        "A generated sentence must remain a draft until approved",
        "A direct boundary must not become a polite suggestion by default"],
"C02": ["drafting and editing must never send or speak a message",
        "The main screen should help someone finish a message, not turn every uncertainty into a questionnaire",
        "Keep exact typed wording by default, including direct or unusual wording"],
}
ACK = [("anon", "Yes. You may thank us as \"two paid AAC-user consultants\"."),
       ("none", "No. Do not thank us in the papers."),
       ("later", "I have not decided yet. (Until you decide, we do not thank you.)")]

def check_quotes():
    for c, qs in QUOTES.items():
        ans = (ROOT / f"annotation/returns_consultant/{c}/design_review_answers.txt").read_text()
        for q in qs:
            assert q in ans, (c, q)
            assert len(q.split()) < 25, (c, q)

INTRO_THANKS = ("Thank you for your review. Your answers helped us. Here is what we did with them.",
  "We added a new rule (R6): a draft is never spoken or sent until the person approves it. We changed R1, R2, R3 and R4. We added a test for the TELL button. "
  "Some of your points we could not follow yet. We say which ones below, and why.")
HOW = ["This takes about 20 minutes. There is no time limit.",
       "We want to be sure we described your points fairly. If we got something wrong, tell us. We will change it.",
       "You can answer in any way that works for you. You can type, use your AAC device, or ask a support person to write what you say, word for word. You can skip any question.",
       f"Please send your answers back by {DUE}. If you cannot, nothing bad happens. We will not quote you, and we will not thank you, unless you said yes.",
       "Please do not write your name or personal stories. We are asking only about the tool and our summary.",
       "Your answers go only to the authors. They are not published. Only your yes answers can be used."]
ANON_NOTE = "Only two people did this review. Someone who knows the project may guess who said a quote. If that worries you, answer no."

def esc(s): return html.escape(s, quote=True)

def items(c):
    """flat list of (name, kind, label) for text/CSV export"""
    out = []
    for i, (t, y, w) in enumerate(ROWS[c], 1):
        out.append((f"row{i}", "row", f"Row {i} ({t}). Is this a fair description of your point?"))
    for i, q in enumerate(QUOTES[c], 1):
        out.append((f"quote{i}", "quote", f"Quote {i}: \"{q}\". OK to quote anonymously?"))
    out.append(("ack", "ack", "Acknowledgement"))
    out.append(("disrespect", "text", "Does any wording in this summary feel disrespectful or wrong?"))
    return out

def build_html(c):
    rows = []
    for i, (t, y, w) in enumerate(ROWS[c], 1):
        rows.append(f'''<article class="card" id="row{i}" aria-labelledby="h-row{i}"><h3 id="h-row{i}">Point {i}. {esc(t)}</h3>
<p class="lbl">What you told us</p><p>{esc(y)}</p>
<p class="lbl">What we changed</p><p>{esc(w)}</p>
<fieldset><legend>Is this a fair description of your point?</legend><div class="opts">
<label class="opt"><input type="radio" name="row{i}" value="yes"> Yes, it is fair</label>
<label class="opt"><input type="radio" name="row{i}" value="change"> Change it (use the box)</label>
<label class="opt"><input type="radio" name="row{i}" value="remove"> Remove it</label></div></fieldset>
<div class="q"><label for="row{i}_text">If you want it changed, say how <span class="small">(you can leave this blank)</span></label><textarea id="row{i}_text" name="row{i}_text" rows="3"></textarea></div></article>''')
    qs = []
    for i, q in enumerate(QUOTES[c], 1):
        qs.append(f'''<article class="card" id="quote{i}" aria-labelledby="h-quote{i}"><h3 id="h-quote{i}">Quote {i}</h3>
<blockquote>&ldquo;{esc(q)}&rdquo;</blockquote>
<fieldset><legend>OK to quote anonymously?</legend><div class="opts">
<label class="opt"><input type="radio" name="quote{i}" value="yes"> Yes</label>
<label class="opt"><input type="radio" name="quote{i}" value="no"> No</label>
<label class="opt"><input type="radio" name="quote{i}" value="change"> Change the wording (use the box)</label></div></fieldset>
<div class="q"><label for="quote{i}_text">New wording <span class="small">(you can leave this blank)</span></label><textarea id="quote{i}_text" name="quote{i}_text" rows="2"></textarea></div></article>''')
    ack = "".join(f'<label class="opt"><input type="radio" name="ack" value="{v}"> {esc(l)}</label>' for v, l in ACK)
    how = "".join(f"<p>{esc(h)}</p>" for h in HOW)
    nav = "".join(f'<li><a href="#{a}">{b}</a></li>' for a, b in [("h-changed","What changed"),("h-rows","Your points"),("h-quotes","Quotes"),("h-ack","Thank-you"),("h-wrong","Wording"),("h-save","Save and return")])
    j = json.dumps({"key": f"consultant_membercheck_{c}", "id": c, "items": [list(x) for x in items(c)], "ackopts": dict(ACK), "due": DUE})
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Check our summary of your review</title>
<style>
  :root {{ --bg:#fff; --fg:#111; --muted:#333; --line:#6b6b6b; --panel:#f3f3f3; --accent:#0b4fa8; --accent-fg:#fff; --sel:#dbe8ff; --focus:#c25400; }}
  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#111; --fg:#f2f2f2; --muted:#d0d0d0; --line:#9a9a9a; --panel:#1f1f1f; --accent:#8fb8ff; --accent-fg:#111; --sel:#23365a; --focus:#ffb366; }} }}
  :root[data-theme="dark"] {{ --bg:#111; --fg:#f2f2f2; --muted:#d0d0d0; --line:#9a9a9a; --panel:#1f1f1f; --accent:#8fb8ff; --accent-fg:#111; --sel:#23365a; --focus:#ffb366; }}
  :root[data-contrast="high"] {{ --bg:#000; --fg:#fff; --muted:#fff; --line:#fff; --panel:#000; --accent:#ffff00; --accent-fg:#000; --sel:#003a8c; --focus:#00ffff; }}
  * {{ box-sizing:border-box; transition:none !important; animation:none !important; }}
  html {{ font-size:20px; }} html[data-size="large"] {{ font-size:25px; }} html[data-size="xlarge"] {{ font-size:31px; }} html[data-size="huge"] {{ font-size:38px; }}
  body {{ margin:0; background:var(--bg); color:var(--fg); line-height:1.6; font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; }}
  .skip {{ position:absolute; left:-999px; top:0; background:var(--bg); padding:8px; border:2px solid var(--fg); }} .skip:focus {{ left:8px; z-index:10; }}
  header, main {{ max-width:900px; margin:0 auto; padding:10px 16px; }}
  header {{ border-bottom:2px solid var(--line); }}
  h1 {{ font-size:1.4rem; margin:.2em 0; }} h2 {{ font-size:1.3rem; margin:1.6em 0 .4em; border-bottom:2px solid var(--line); }} h3 {{ font-size:1.15rem; margin:0 0 .4em; }}
  label {{ font-weight:600; }} select, button {{ font:inherit; padding:6px 12px; border:2px solid var(--fg); background:var(--bg); color:var(--fg); cursor:pointer; }}
  button.primary {{ background:var(--accent); color:var(--accent-fg); border-color:var(--accent); }}
  textarea {{ font:inherit; width:100%; padding:8px; border:2px solid var(--line); background:var(--bg); color:var(--fg); }}
  :focus-visible {{ outline:4px solid var(--focus); outline-offset:2px; }}
  .card {{ border:3px solid var(--line); padding:12px 16px 16px; margin:16px 0; }}
  .box {{ border:2px solid var(--line); background:var(--panel); padding:10px 16px; margin:12px 0; }}
  .lbl {{ font-weight:700; margin:.6em 0 .1em; }} .small {{ font-size:.85rem; color:var(--muted); }}
  blockquote {{ margin:8px 0; padding:4px 14px; border-left:6px solid var(--line); font-weight:700; }}
  fieldset {{ border:2px solid var(--line); margin:12px 0; padding:6px 12px 10px; }} legend {{ font-weight:700; padding:0 6px; }}
  .opts {{ display:flex; flex-wrap:wrap; gap:8px 12px; }} .opt {{ display:inline-flex; gap:8px; align-items:flex-start; border:2px solid var(--line); padding:4px 12px; cursor:pointer; font-weight:400; }}
  .opt input {{ width:1.2em; height:1.2em; margin-top:.3em; }}
  .q {{ margin:12px 0; }} nav ul {{ columns:2; padding-left:1.2em; }} .tools {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0; }}
  .status {{ min-height:1.5em; font-weight:600; }}
  @media print {{ .tools, nav, .skip {{ display:none; }} .card {{ break-inside:avoid; }} }}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the form</a>
<header>
  <h1>Check our summary of your review</h1>
  <div class="tools" role="group" aria-label="Page settings">
    <label for="size">Text size</label>
    <select id="size"><option value="normal">Normal</option><option value="large">Large</option><option value="xlarge">Extra large</option><option value="huge">Huge</option></select>
    <label for="contrast">Colours</label>
    <select id="contrast"><option value="auto">Automatic</option><option value="light">Light</option><option value="dark">Dark</option><option value="high">High contrast</option></select>
  </div>
</header>
<main id="main">
  <div class="box"><p><strong>You are in charge.</strong> {esc(HOW[0])} Take a break whenever you want. You can skip any question.</p><p>Your answers are saved in this browser as you go. The buttons at the bottom save a file. Nothing is sent anywhere by this page.</p></div>
  <nav aria-label="Sections"><ul>{nav}</ul></nav>
  <p class="status" id="status" role="status" aria-live="polite"></p>
  <form id="form" onsubmit="return false">
<section aria-labelledby="h-changed"><h2 id="h-changed">Thank you, and what changed</h2><p>{esc(INTRO_THANKS[0])}</p><p>{esc(INTRO_THANKS[1])}</p>
<h3>How to answer</h3>{how}</section>
<section aria-labelledby="h-rows"><h2 id="h-rows">Your points: what you told us, and what we changed</h2><p>Below are {len(ROWS[c])} points. Each one is our own short summary of what you wrote. For each one, tell us if it is a fair description of your point.</p>
{"".join(rows)}</section>
<section aria-labelledby="h-quotes"><h2 id="h-quotes">Words we might quote</h2><p>We might quote a few of your own words in a paper. We would not use your name. These are exact words from your answers. For each one, tell us if we may use it. If you do not answer, we will not use it.</p><p class="small">{esc(ANON_NOTE)}</p>
{"".join(qs)}</section>
<section aria-labelledby="h-ack"><h2 id="h-ack">Thank-you in the papers</h2><fieldset><legend>Do you want us to thank you in the papers?</legend><div class="opts">{ack}</div></fieldset><p class="small">If you want to be named, tell us in writing. That is a separate step, as in your agreement.</p></section>
<section aria-labelledby="h-wrong"><h2 id="h-wrong">Wording</h2><div class="q"><label for="disrespect">Does any wording in this summary feel disrespectful or wrong? Please tell us where, and how to fix it. <span class="small">(you can leave this blank)</span></label><textarea id="disrespect" name="disrespect" rows="5"></textarea></div></section>
<section aria-labelledby="h-save"><h2 id="h-save">Save and return</h2>
<p>When you are done, save a file and send it back to the authors by {esc(DUE)}. Saving does not send anything. You can save the text file, the spreadsheet file (CSV), or both. You can also save your progress and load it later.</p>
<div class="tools"><button type="button" class="primary" id="savecsv">Save answers (CSV)</button> <button type="button" id="savetxt">Save answers (text)</button> <button type="button" id="savejson">Save progress</button> <button type="button" id="loadjson">Load progress</button><input type="file" id="jsonfile" accept=".json" hidden></div>
<p class="small">You can also print this page and write on it, or use the MEMBER_CHECK.md copy. Anonymous page. It collects no personal information, makes no recordings and does not use the network.</p></section>
  </form>
</main>
<script>
"use strict";
const CFG = {j};
const $ = id => document.getElementById(id), KEY = CFG.key, form = $("form");
const VL = {{yes:"Yes", change:"Change it", remove:"Remove it", no:"No", anon:CFG.ackopts.anon, none:CFG.ackopts.none, later:CFG.ackopts.later}};
function say(m) {{ $("status").textContent = m; }}
function collect() {{ const o = {{}}; form.querySelectorAll("textarea").forEach(t => {{ if (t.value.trim()) o[t.name] = t.value; }});
  form.querySelectorAll("input[type=radio]:checked").forEach(r => {{ o[r.name] = r.value; }}); return o; }}
function save() {{ try {{ localStorage.setItem(KEY, JSON.stringify(collect())); }} catch (e) {{}} }}
function fill(o) {{ Object.keys(o).forEach(k => {{ const t = form.querySelector('textarea[name="' + k + '"]'); if (t) t.value = o[k];
  const r = form.querySelector('input[type=radio][name="' + k + '"][value="' + o[k] + '"]'); if (r) r.checked = true; }}); }}
function download(name, text, type) {{ const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], {{type}})); a.download = name; document.body.append(a); a.click(); a.remove(); }}
function rowsOut() {{ const o = collect(); return CFG.items.map(([n, kind, label]) => {{
  const ans = o[n] ? (VL[o[n]] || o[n]) : "(no answer)"; const cm = (kind === "row" || kind === "quote") ? (o[n + "_text"] || "") : "";
  return {{id: n, question: label, answer: kind === "text" ? (o[n] || "(no answer)") : ans, comment: cm}}; }}); }}
function csvq(s) {{ return '"' + String(s).replace(/"/g, '""') + '"'; }}
form.addEventListener("input", save); form.addEventListener("change", save);
$("savecsv").addEventListener("click", () => {{ const r = rowsOut(); const lines = [["consultant","id","question","answer","comment"].join(",")];
  r.forEach(x => lines.push([CFG.id, x.id, x.question, x.answer, x.comment].map(csvq).join(",")));
  download("member_check_" + CFG.id + ".csv", lines.join("\\r\\n") + "\\r\\n", "text/csv"); say("Saved a CSV file."); }});
$("savetxt").addEventListener("click", () => {{ const lines = ["Member check answers (" + CFG.id + ")", ""];
  rowsOut().forEach(x => {{ lines.push("Q: " + x.question, "A: " + x.answer); if (x.comment) lines.push("Comment: " + x.comment); lines.push(""); }});
  download("member_check_" + CFG.id + ".txt", lines.join("\\n"), "text/plain"); say("Saved a text file."); }});
$("savejson").addEventListener("click", () => {{ download("member_check_progress_" + CFG.id + ".json", JSON.stringify(collect()), "application/json"); say("Saved a progress file."); }});
$("loadjson").addEventListener("click", () => $("jsonfile").click());
$("jsonfile").addEventListener("change", e => {{ const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = () => {{ try {{ fill(JSON.parse(r.result)); save(); say("Progress loaded."); }} catch (x) {{ say("That file could not be read."); }} }}; r.readAsText(f); e.target.value = ""; }});
$("size").addEventListener("change", () => {{ document.documentElement.dataset.size = $("size").value; try {{ localStorage.setItem(KEY + "_size", $("size").value); }} catch (e) {{}} }});
$("contrast").addEventListener("change", () => {{ const v = $("contrast").value, h = document.documentElement; if (v === "high") {{ h.dataset.contrast = "high"; delete h.dataset.theme; }} else {{ delete h.dataset.contrast; if (v === "auto") delete h.dataset.theme; else h.dataset.theme = v; }} try {{ localStorage.setItem(KEY + "_contrast", v); }} catch (e) {{}} }});
try {{ const s = localStorage.getItem(KEY + "_size"); if (s) {{ $("size").value = s; document.documentElement.dataset.size = s; }}
  const c = localStorage.getItem(KEY + "_contrast"); if (c) {{ $("contrast").value = c; $("contrast").dispatchEvent(new Event("change")); }}
  const o = localStorage.getItem(KEY); if (o) fill(JSON.parse(o)); }} catch (e) {{}}
</script>
</body>
</html>
'''

def build_md(c):
    L = ["# Check our summary of your review", "",
         "*Plain language. You can print this page and write on it, or use the web page `member_check.html`. There is no time limit.*", "",
         "## Thank you, and what changed", "", INTRO_THANKS[0], "", INTRO_THANKS[1], "", "## How to answer", ""]
    L += [f"- {h}" for h in HOW]
    L += ["", "## Your points: what you told us, and what we changed", "",
          "For each row, tick one: [ ] yes, it is fair  [ ] change it  [ ] remove it. If you want it changed, write how in the box.", "",
          "| # | Topic | What you told us | What we changed |", "|---|---|---|---|"]
    for i, (t, y, w) in enumerate(ROWS[c], 1): L.append(f"| {i} | {t} | {y} | {w} |")
    L.append("")
    for i, (t, y, w) in enumerate(ROWS[c], 1):
        L += [f"**Point {i} ({t}).** Is this a fair description of your point?", "", "[ ] Yes, it is fair   [ ] Change it   [ ] Remove it", "", "If change, say how: ______________________________", ""]
    L += ["## Words we might quote", "", "We might quote a few of your own words in a paper. We would not use your name. These are exact words from your answers. If you do not answer, we will not use them.", "", ANON_NOTE, ""]
    for i, q in enumerate(QUOTES[c], 1):
        L += [f"**Quote {i}:** “{q}”", "", "OK to quote anonymously?  [ ] Yes   [ ] No   [ ] Change the wording", "", "New wording: ______________________________", ""]
    L += ["## Thank-you in the papers", "", "Do you want us to thank you in the papers?", ""]
    L += [f"- [ ] {l}" for _, l in ACK]
    L += ["", "If you want to be named, tell us in writing. That is a separate step, as in your agreement.", "",
          "## Wording", "", "Does any wording in this summary feel disrespectful or wrong? Please tell us where, and how to fix it.", "", "______________________________", "",
          "## Send it back", "", f"Please send your answers to the authors by {DUE}. Your answers are not published.", ""]
    return "\n".join(L)

if __name__ == "__main__":
    check_quotes()
    for c in ROWS:
        d = OUT / c; d.mkdir(parents=True, exist_ok=True)
        (d / "member_check.html").write_text(build_html(c))
        (d / "MEMBER_CHECK.md").write_text(build_md(c))
        print("wrote", d)

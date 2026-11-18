#!/usr/bin/env python3
"""Build the SLP design-implications check (expert_package/slp/implications_check/).
Numbers are read from src/score_slp_panel.py output at build time (no hand-typed figures)."""
import html, json, re, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "expert_package/slp/implications_check"

def scored():
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as d:
        p = Path(d) / "o.md"
        subprocess.run([sys.executable, str(ROOT / "src/score_slp_panel.py"), "--out", str(p)], check=True, capture_output=True, cwd=ROOT)
        t = p.read_text()
    sev = {}
    for m in re.finditer(r"^\| (negation|question/statement|actor|certainty|politeness|time|added)[^|]*\| ([\d.]+) ", t, re.M):
        sev[m.group(1)] = float(m.group(2))
    rows = {}
    for m in re.finditer(r"^\| (W-C speech-act[^|]*|hw1 human[^|]*)\| (\w+) \| \d+ \| ([\d.]+) \| ([\d.]+) \|", t, re.M):
        rows[(m.group(1).split(" ")[0], m.group(2))] = (float(m.group(3)), float(m.group(4)))
    return sev, rows

sev, rows = scored()
f = lambda x: f"{x:.1f}"
wc0, wc1 = rows[("W-C", "baseline_P0")], rows[("W-C", "guard_G1")]
hb, hc, hw = rows[("hw1", "baseline_noncrit")], rows[("hw1", "chip")], rows[("hw1", "word")]
top = max(sev, key=sev.get)
assert top == "negation" and sev["negation"] == 5.0 and all(v < 5 for k, v in sev.items() if k != "negation")

# (id, short title, statement, optional detail)
S = [
 ("S1", "Selection burden under access methods",
  "For a person who accesses a device by switch scanning or eye gaze, every extra selection costs time and effort. A cue that fixes one meaning (for example a NOT or question button) should therefore be one selection, and worth adding only where it prevents a change of meaning that would otherwise have to be noticed and corrected.",
  "Our studies count the cue as one tap. They did not measure selection time under scanning or eye gaze."),
 ("S2", "Reading drafts costs attention",
  "Reading and checking a generated draft costs the person attention and time, and more so for several drafts. A single draft by default, with further drafts only on request, is preferable to showing several drafts every time.",
  "In one writer study, three drafts without a cue covered fewer intended messages than one draft after a one-tap cue."),
 ("S3", "Approval before speaking",
  "A generated sentence stays a draft until the person approves it. It is never spoken automatically, and the person can hear or inspect it privately, change it, or cancel.",
  "Written design feedback on our requirements asked for this rule."),
 ("S4", "The cue is a choice",
  "The meaning cue is the person's choice, not a requirement. The person may use a button, type the same meaning as an ordinary word, or leave it out and accept that the system must then guess or ask.",
  None),
 ("S5", "Preserving typed wording",
  "When the person types a whole sentence, the default is to speak it exactly as typed. Rewriting happens only on explicit request, with the proposed change visible and approved before speech.",
  None),
 ("S6", "Event and role errors matter",
  "Changes to who acts, when something happens, or what happens (an added event or detail) matter clinically, not only changes to negation or tone. Such errors can send the listener a different message while the sentence still reads fluently.",
  f"In your earlier severity ratings, actor switched, time changed and added content each had mean severity {f(sev['actor'])}, {f(sev['time'])} and {f(sev['added'])} of 5."),
 ("S7", "Negation reversal is the most severe",
  "Dropping or adding a negation, so that the message says the opposite of what was meant, is the most severe of the silent changes and should be blocked rather than only flagged.",
  f"In your earlier ratings negation had mean severity {f(sev['negation'])} of 5, the highest of the seven types, and was marked block by both reviewers."),
 ("S8", "Severity-weighted failure figures",
  "When failures are weighted by clinical severity instead of simply counted, the ordering of the conditions is the one the unweighted counts suggest, and a cue or guard still lowers the failure rate. Weighting each failure by the severity you rated, the share of outputs with a failure was:",
  None),
]
FIG = [
 ("Speech-act targets", "Baseline", wc0), ("Speech-act targets", "With the guard", wc1),
 ("Human-written pairs", "Keywords with a neutral chip", hb), ("Human-written pairs", "With a one-tap cue (chip)", hc), ("Human-written pairs", "With the cue as a plain word", hw),
]
OPTS = [("yes", "Yes, clinically sound"), ("caveat", "Yes, with a caveat (please write it below)"), ("no", "No (please say why below)")]
E = html.escape
def fig_table(h=True):
    r = "".join(f"<tr><td>{E(a)}</td><td>{E(b)}</td><td>{f(v[0])}%</td><td>{f(v[1])}%</td></tr>" for a, b, v in FIG)
    return ('<table><caption class="small">Share of outputs with a meaning failure, in two separate sets of items. Compare rows only within a set.</caption>'
            '<tr><th scope="col">Items</th><th scope="col">Condition</th><th scope="col">Counted</th><th scope="col">Weighted by your severity</th></tr>' + r + '</table>')
def fig_md():
    return "\n".join(["| Items | Condition | Counted | Weighted by your severity |", "|---|---|---|---|"] + [f"| {a} | {b} | {f(v[0])}% | {f(v[1])}% |" for a, b, v in FIG])

def card(i, sid, title, text, detail):
    d = f'<p class="note"><em>Background:</em> {E(detail)}</p>' if detail else ""
    tb = fig_table() if sid == "S8" else ""
    opts = "".join(f'<label class="opt"><input type="radio" name="{sid}" value="{v}"> <span>{E(l)}</span></label>' for v, l in OPTS)
    return f'''<div class="card" id="c-{sid}"><h3>{i}. {E(title)}</h3><p class="sent">{E(text)}</p>{tb}{d}
<fieldset><legend>Is this clinically sound?</legend><div class="opts col">{opts}</div></fieldset>
<label for="{sid}_c" class="small">Caveat or reason (needed for "with a caveat" or "no"):</label><textarea id="{sid}_c" data-id="{sid}" aria-label="{sid} caveat or reason"></textarea></div>'''

CSS = (ROOT / "expert_package/slp/slp_rating.html").read_text()
CSS = CSS[CSS.index("<style>"):CSS.index("</style>") + 8]

JS = r'''
const IDS = %IDS%; const FIXED = %FIXED%;
const $ = id => document.getElementById(id);
let S = {rid: FIXED || "", a: {}, free: ""};
const key = () => "implcheck_" + (S.rid || "none");
function store(){ try{ localStorage.setItem(key(), JSON.stringify(S)); }catch(e){} }
function load(){ try{ const j = localStorage.getItem(key()); if (j) S = Object.assign(S, JSON.parse(j), {rid: FIXED || S.rid}); }catch(e){} }
function paint(){
  IDS.forEach(id => { const a = S.a[id] || {};
    document.querySelectorAll('input[name="'+id+'"]').forEach(r => { r.checked = a.v === r.value; r.closest(".opt").classList.toggle("checked", r.checked); });
    $(id+"_c").value = a.c || ""; $("c-"+id).classList.toggle("done", !!a.v); });
  $("free").value = S.free || ""; $("rid").value = S.rid;
  const n = IDS.filter(i => (S.a[i]||{}).v).length; $("prog").textContent = n + " of " + IDS.length + " answered";
}
function need(){ return IDS.filter(i => { const a = S.a[i]||{}; return (a.v==="caveat"||a.v==="no") && !(a.c||"").trim(); }); }
document.addEventListener("change", e => { if (e.target.name && IDS.includes(e.target.name)) { (S.a[e.target.name] = S.a[e.target.name]||{}).v = e.target.value; store(); paint(); } });
document.addEventListener("input", e => { const id = e.target.dataset && e.target.dataset.id; if (id) { (S.a[id] = S.a[id]||{}).c = e.target.value; store(); } if (e.target.id==="free"){ S.free = e.target.value; store(); } });
$("rid").addEventListener("input", e => { if (FIXED) return; S.rid = e.target.value.trim(); load(); paint(); });
$("size").addEventListener("change", e => { document.documentElement.dataset.size = e.target.value; });
const q = v => '"' + String(v||"").replace(/"/g, '""') + '"';
function csv(){ const L = ["reviewer_id,item,sound,comment"];
  IDS.forEach(i => { const a = S.a[i]||{}; L.push([q(S.rid), i, q(a.v||""), q((a.c||"").replace(/\s+/g," ").trim())].join(",")); });
  L.push([q(S.rid), "FREE", '""', q((S.free||"").replace(/\s+/g," ").trim())].join(",")); return L.join("\n") + "\n"; }
$("export").addEventListener("click", () => {
  if (!S.rid) { $("status").textContent = "Please enter your ID first."; return; }
  const m = need(); $("status").textContent = m.length ? "Reminder: " + m.join(", ") + " marked caveat or no without a note. The file is saved anyway." : "File saved. Thank you.";
  const b = new Blob([csv()], {type:"text/csv"}), a = document.createElement("a");
  a.href = URL.createObjectURL(b); a.download = "implications_check_" + S.rid + ".csv"; document.body.appendChild(a); a.click(); a.remove(); });
$("importbtn").addEventListener("click", () => $("importfile").click());
$("importfile").addEventListener("change", e => { const f = e.target.files[0]; if (!f) return; f.text().then(t => {
  const rows = []; let cur = [], cell = "", inq = false;
  for (let i=0;i<t.length;i++){ const c=t[i]; if(inq){ if(c==='"'&&t[i+1]==='"'){cell+='"';i++;} else if(c==='"') inq=false; else cell+=c; }
    else if(c==='"') inq=true; else if(c===','){cur.push(cell);cell="";} else if(c==='\n'){cur.push(cell);rows.push(cur);cur=[];cell="";} else if(c!=='\r') cell+=c; }
  rows.slice(1).forEach(r => { if (IDS.includes(r[1])) S.a[r[1]] = {v:r[2], c:r[3]}; else if (r[1]==="FREE") S.free = r[3]; });
  if (!FIXED && rows[1]) S.rid = rows[1][0]; store(); paint(); }); });
load(); paint();
'''

def page(fixed):
    ids = [s[0] for s in S]
    cards = "".join(card(i + 1, *s) for i, s in enumerate(S))
    idbox = (f'<span><strong>ID: {fixed}</strong></span><input id="rid" type="hidden" value="{fixed}">' if fixed else
             '<div><label for="rid">Your ID</label> <input id="rid" type="text" maxlength="16" autocomplete="off"></div>')
    js = JS.replace("%IDS%", json.dumps(ids)).replace("%FIXED%", json.dumps(fixed or ""))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Design implications check</title>
{CSS}</head><body>
<header><div class="bar"><h1>Design implications check</h1>{idbox}
<button id="export" class="primary" type="button">Download CSV</button><button id="importbtn" type="button">Resume from a CSV</button>
<input id="importfile" type="file" accept=".csv,text/csv" class="hidden" aria-label="Choose a CSV file to resume from">
<label for="size" class="small">Text size</label><select id="size"><option value="normal">Normal</option><option value="large">Large</option><option value="xlarge">Extra large</option></select>
<div class="small" id="prog" aria-live="polite"></div></div></header>
<main id="main"><p class="status" id="status" role="status" aria-live="polite"></p>
<h2>Before you start</h2>
<div class="box"><p><strong>About 10 minutes.</strong> You rated seven kinds of meaning change earlier. Here are eight short statements that our papers draw from the materials. For each, please tell us whether it is clinically sound. You are reviewing statements about a design, not any person, and we collect nothing about you beyond your reviewer ID. Please do not type your name, workplace, clients or any personal details in the boxes.</p>
<p>Choose <em>yes</em>, <em>yes with a caveat</em> or <em>no</em>. For the last two, a short note is welcome. A negative answer is as useful to us as a positive one. At the end there is one open box for anything clinically important that we have left out. Your answers save in this browser. Press <strong>Download CSV</strong> when you finish and return the file as described in the covering note. Please work alone.</p></div>
{cards}
<h2>Anything clinically important missing?</h2>
<label for="free" class="small">Anything clinically important missing from these statements? (optional; no personal or client details)</label><textarea id="free" rows="5"></textarea>
<p>Press <strong>Download CSV</strong> at the top and return the file. Thank you.</p></main>
<script>{js}</script></body></html>
'''

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "implications_check.html").write_text(page(None))
    for r in ("SLP1", "SLP2"):
        (OUT / f"implications_check_{r}.html").write_text(page(r))
    md = ["# Design implications check", "",
          "About 10 minutes. Anonymous expert review of study materials. You are asked about statements, not about any person; give only your reviewer ID and do not include personal, client or workplace details.", "",
          "For each statement: **clinically sound? yes / yes with a caveat (write it) / no (write why)**. At the end, one open question. The web page version (`implications_check.html`) is the same content and produces the file to return.", ""]
    for i, (sid, t, txt, d) in enumerate(S, 1):
        md += [f"## {i}. {t}", "", f"> {txt}", ""]
        if sid == "S8": md += [fig_md(), "", "Counts are shares of outputs with a failure in two separate sets of items; compare rows only within a set.", ""]
        if d: md += [f"*Background:* {d}", ""]
        md += ["Clinically sound?  [ ] yes   [ ] yes, with a caveat   [ ] no", "", "Caveat or reason: ______________________________", ""]
    md += ["## Anything clinically important missing?", "", "______________________________", ""]
    (OUT / "implications_check.md").write_text("\n".join(md))
    (ROOT / "annotation/returns_slp_implications").mkdir(exist_ok=True)
    print("built", sorted(p.name for p in OUT.iterdir()))
main()

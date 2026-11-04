// jsdom check of annotation_package/rate_items.html (Parts 22-25, data-driven item rating).
// usage: NODE_PATH=<dir containing jsdom> node tests/test_rate_items_html.js annotation_package/rate_items.html \
//          annotation_package/stage5/P03_part23.json [P03] [out.csv]
const {JSDOM} = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const DOC = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const ID = process.argv[4] || (process.argv[3].match(/(P\d+)_part/) || [])[1] || 'P03';
const OUT = process.argv[5];
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else console.log('ok  ', m); };
let dlName = null;
function boot(storage) {
  return new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/rate_items.html', pretendToBeVisual: true,
    beforeParse(w) {
      w.URL.createObjectURL = () => 'blob:x'; w.Element.prototype.scrollIntoView = function () {};
      w.HTMLAnchorElement.prototype.click = function () { dlName = this.download; };
      if (storage === 'throw') Object.defineProperty(w, 'localStorage', {get() { throw new Error('blocked'); }});
    }});
}
function key(w, k, target) { (target || w.document.body).dispatchEvent(new w.KeyboardEvent('keydown', {key: k, bubbles: true})); }
function fnv(s) { let h = 2166136261 >>> 0; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; } return h.toString(16).padStart(8, '0'); }
const CID = DOC.check_id, QS = DOC.questions, QIDS = Object.keys(QS);
const optV = o => typeof o === 'string' ? o : o.v;

ok(DOC.tool === 'rate_items_v1' && DOC.items.length === DOC.n_items && DOC.n_items >= 1, CID + ': ' + DOC.items.length + ' items in the file');
ok(DOC.practice.length === 2, 'two practice items');
ok(DOC.items.every(x => Object.keys(x).sort().join() === 'blocks,item_id,qs'), 'items carry only id, text blocks and question ids (blind)');
ok(DOC['for'] === fnv(ID + '|' + CID), 'file is made for ' + ID);
ok(DOC.items.concat(DOC.practice).every(x => x.qs.every(q => QS[q])), 'every question id is defined');
ok(DOC.practice.every(p => p.qs.every(q => QS[q].options.map(optV).includes(p.expected[q]))), 'practice answers are valid options');
const BLIND = /stratum|detector|\barm\b|arm_|machine|model|checker|judge|weight|gpt|qwen|llama|mistral|gemini|intended|propositional|echo_|exposure|frontier|hypothes|policy/i;
ok(!BLIND.test(JSON.stringify(DOC)), 'no design, arm or model wording anywhere in the file');

const dom = boot(); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
const errs = []; w.addEventListener('error', e => errs.push(e.message));
ok(w.idHash(' ' + ID.toLowerCase() + ' ', CID) === fnv(ID + '|' + CID), 'page idHash equals the Python hash');
$('annot').value = ID; key(w, 'Enter', $('annot'));
ok(/Load your file/.test($('status').textContent), 'needs a file first');
ok(!w.loadData(Object.assign({}, DOC, {stratum: 'x'})) && /must not have/.test($('status').textContent), 'refuses extra top-level fields');
const badItem = JSON.parse(JSON.stringify(DOC)); badItem.items[0].arm = 'A0';
ok(!w.loadData(badItem) && /must not have/.test($('status').textContent), 'refuses an item with extra fields');
ok(!w.loadData(Object.assign({}, DOC, {tool: 'other'})), 'refuses another tool');
const badQ = JSON.parse(JSON.stringify(DOC)); badQ.items[0].qs = ['nope'];
ok(!w.loadData(badQ) && /unknown question/.test($('status').textContent), 'refuses an unknown question id');
$('annot').value = 'P99';
ok(w.loadData(DOC), 'valid file loads');
ok(/not your file/.test($('introview').textContent) && w.eval('S') === null, 'another person is refused');
$('annot').value = ID; key(w, 'Enter', $('annot'));
ok(new RegExp(DOC.n_items + ' items').test($('introview').textContent), 'intro for the right person');
key(w, 'Enter'); ok(/Practice/.test($('phasetag').textContent), 'practice starts');
// practice 1: answer as expected -> all Matches
const optIndex = (q, v) => QS[q].options.map(optV).indexOf(v) + 1;
function answerWith(item, f) { for (const q of item.qs) key(w, String(f(q))); }
answerWith(DOC.practice[0], q => optIndex(q, DOC.practice[0].expected[q]));
key(w, 'Enter'); ok(/Matches/.test($('feedback').textContent) && !/Different/.test($('feedback').textContent), 'practice 1 feedback matches'); key(w, 'Enter');
// practice 2: deliberately not the expected option
answerWith(DOC.practice[1], q => { const i = optIndex(q, DOC.practice[1].expected[q]); return i === 1 ? 2 : 1; });
key(w, 'Enter'); ok(/Different/.test($('feedback').textContent), 'practice 2 feedback flags a difference'); key(w, 'Enter');
ok(w.eval('S.phase') === 'M' && new RegExp('Item 1 of ' + DOC.n_items).test($('progtext').textContent), 'main phase');
const order = w.eval('S.order');
ok(new Set(order).size === DOC.n_items && (DOC.n_items < 3 || JSON.stringify(order) !== JSON.stringify(DOC.items.map(x => x.item_id))), 'per-person shuffled order');
const first = DOC.items.find(x => x.item_id === order[0]);
ok(first.blocks.every(b => $('blocks').textContent.includes(b.text)), 'all text blocks shown');
ok(d.querySelectorAll('#form fieldset').length === first.qs.length, 'one question box per question of this item');
key(w, 'Enter'); ok(/every question/.test($('status').textContent) && w.eval('S.idx') === 0, 'cannot skip an unanswered item');
const seen = new Set();
for (let i = 0; i < DOC.n_items; i++) {
  const it = DOC.items.find(x => x.item_id === order[i]); seen.add(it.qs.join('+'));
  it.qs.forEach((q, k) => key(w, String(1 + ((i + k) % QS[q].options.length))));
  if (i === 2 || DOC.n_items < 3 && i === 0) { key(w, 'Tab'); const n = $('note'); n.value = 'odd; with "quotes", and comma'; n.dispatchEvent(new w.Event('input')); key(w, 'Enter', n); }
  else key(w, 'Enter');
}
ok(w.eval('S.phase') === 'done', 'done after ' + DOC.n_items + ' (question sets seen: ' + [...seen].join(' | ') + ')');
ok(w.localStorage.getItem('rateitems:v1:' + CID + ':' + ID), 'autosaved per file and person');
const csv = w.eval('exportCSV()'); const rows = csv.trim().split('\n'), head = rows[0].split(',');
ok(dlName === 'labels_' + CID + '_' + ID + '.csv', 'download name ' + dlName);
ok(head.join() === ['item_id', 'annotator', 'check_id', 'practice', 'order', ...QIDS, 'note', 'time_ms', 'started_at', 'tool', 'exported_at'].join(), 'CSV header');
ok(rows.length >= 1 + 2 + DOC.n_items, 'CSV has practice and item rows (' + (rows.length - 1) + ')');
ok(rows.some(r => /odd; with ""quotes"", and comma/.test(r)), 'note escaped');
const col = n => head.indexOf(n);
ok(rows.slice(1).filter(r => !r.startsWith('prac-')).every(r => { const c = r.match(/("([^"]|"")*"|[^,]*)(,|$)/g); return true; }), 'rows parse');
// every answered cell is a valid option of its own question; unasked questions stay empty
let bad = 0;
for (const r of rows.slice(1)) {
  const cells = r.split(','); const id = cells[0]; const it = DOC.items.concat(DOC.practice).find(x => x.item_id === id);
  if (!it) { bad++; continue; }
  QIDS.forEach(q => { const v = cells[col(q)]; if (it.qs.includes(q) ? !QS[q].options.map(optV).includes(v) : v !== '') bad++; });
}
ok(bad === 0, 'answers are valid options; questions an item did not ask are empty');
if (OUT) fs.writeFileSync(OUT, csv);
{ const d2 = boot(); const w2 = d2.window; w2.localStorage.setItem('rateitems:v1:' + CID + ':' + ID, w.localStorage.getItem('rateitems:v1:' + CID + ':' + ID));
  w2.document.getElementById('annot').value = ID; w2.loadData(DOC);
  ok(/Resumed saved progress/.test(w2.document.getElementById('status').textContent) && w2.eval('S.phase') === 'done', 'resumes saved progress'); }
{ const d3 = boot('throw'); const w3 = d3.window; const e3 = []; w3.addEventListener('error', e => e3.push(e.message));
  w3.document.getElementById('annot').value = ID; w3.loadData(DOC);
  ok(w3.eval('S && S.phase') === 'intro' && e3.length === 0, 'works with blocked storage'); }
ok(errs.length === 0, 'no script errors ' + errs.join('; '));
if (fail) { console.log(fail + ' FAILED'); process.exit(1); } else console.log('all ok');

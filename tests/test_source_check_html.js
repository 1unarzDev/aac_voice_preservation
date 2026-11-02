// jsdom check of annotation_package/source_check.html (Part 21, source-message check).
// usage: NODE_PATH=<dir containing jsdom> node tests/test_source_check_html.js annotation_package/source_check.html \
//          annotation_package/stage5/P03_part21.json [P03] [out.csv]
const {JSDOM} = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const DOC = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const ID = process.argv[4] || 'P03';
const OUT = process.argv[5];
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else console.log('ok  ', m); };
let blobText = null, dlName = null;
function boot(storage) {
  return new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/source_check.html', pretendToBeVisual: true,
    beforeParse(w) {
      w.URL.createObjectURL = () => 'blob:x'; w.Element.prototype.scrollIntoView = function () {};
      const B = w.Blob; w.Blob = function (parts, opts) { blobText = parts.join(''); return new B(parts, opts); };
      w.HTMLAnchorElement.prototype.click = function () { dlName = this.download; };
      if (storage === 'throw') Object.defineProperty(w, 'localStorage', {get() { throw new Error('blocked'); }});
    }});
}
function key(w, k, target) { (target || w.document.body).dispatchEvent(new w.KeyboardEvent('keydown', {key: k, bubbles: true})); }
// FNV-1a as src/make_source_check.py id_hash
function fnv(id) { let h = 2166136261 >>> 0; for (const c of id.trim().toUpperCase() + '|part21') { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; } return h.toString(16).padStart(8, '0'); }

ok(DOC.tool === 'source_check_v1' && DOC.items.length === DOC.n_items && DOC.n_items >= 5, DOC.items.length + ' messages in the file');
ok(DOC.items.every(x => Object.keys(x).sort().join() === 'item_id,text'), 'items carry only id and text (blind)');
ok(DOC['for'] === fnv(ID), 'file is made for ' + ID);
ok(!/detector|stratum|negated|polite|weight|sample|elic/.test(JSON.stringify(DOC).replace(/"text": "[^"]*"/g, '')), 'no label or design field in the file');

const dom = boot(); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
const errs = []; w.addEventListener('error', e => errs.push(e.message));
ok(w.idHash(' p03 ') === fnv('P03'), 'page idHash equals the Python hash');
$('annot').value = ID; key(w, 'Enter', $('annot'));
ok(/Load your message file/.test($('status').textContent), 'needs a file first');
ok(!w.loadData({check_id: 'x', tool: 'source_check_v1', items: [Object.assign({}, DOC.items[0], {detector: 'negated'})]}) && /must not have/.test($('status').textContent), 'refuses an item with extra fields');
ok(!w.loadData(Object.assign({}, DOC, {stratum: 'negated'})) && /must not have/.test($('status').textContent), 'refuses extra top-level fields');
ok(!w.loadData({check_id: 'x', tool: 'other', items: [{item_id: 'a', text: 'b'}]}), 'refuses another tool');
$('annot').value = 'P99';
ok(w.loadData(DOC), 'valid file loads');
ok(/not your file/.test($('introview').textContent) && w.eval('S') === null, 'another person is refused');
$('annot').value = ID; key(w, 'Enter', $('annot'));
ok(new RegExp('Message check').test($('introview').textContent) && new RegExp(DOC.n_items + ' short messages').test($('introview').textContent), 'intro for the right person');
key(w, 'Enter'); ok(/Practice/.test($('phasetag').textContent), 'practice starts');
// practice 1: no / yes / request -> options: negated 2 (no), polite 1 (yes), act 3 (request)
key(w, '2'); key(w, '1'); key(w, '3'); key(w, 'Enter'); ok(/Matches/.test($('feedback').textContent) && !/Different/.test($('feedback').textContent), 'practice 1 feedback matches'); key(w, 'Enter');
// practice 2: wrong on purpose (negated no), polite no, statement
key(w, '2'); key(w, '2'); key(w, '1'); key(w, 'Enter'); ok(/Different/.test($('feedback').textContent), 'practice 2 feedback flags a difference'); key(w, 'Enter');
// practice 3: unsure with S for Q1, no, question
key(w, 's'); key(w, '2'); key(w, '2'); key(w, 'Enter'); key(w, 'Enter');
ok(w.eval('S.phase') === 'M' && new RegExp('Message 1 of ' + DOC.n_items).test($('progtext').textContent), 'main phase');
const order = w.eval('S.order');
ok(new Set(order).size === DOC.n_items && JSON.stringify(order) !== JSON.stringify(DOC.items.map(x => x.item_id)), 'per-person shuffled order');
const first = w.eval(`BYID["${order[0]}"]`);
ok($('msg').textContent === first.text, 'message shown');
key(w, 'Enter'); ok(/every question/.test($('status').textContent) && w.eval('S.idx') === 0, 'cannot skip an unanswered message');
for (let i = 0; i < DOC.n_items; i++) {
  key(w, String(1 + (i % 3 === 0 ? 0 : 1))); key(w, i % 5 === 0 ? 's' : '2'); key(w, String(1 + (i % 4)));
  if (i === 2) { key(w, 'Tab'); const n = $('note'); n.value = 'odd; with "quotes", and comma'; n.dispatchEvent(new w.Event('input')); key(w, 'Enter', n); }
  else key(w, 'Enter');
}
ok(w.eval('S.phase') === 'done', 'done after ' + DOC.n_items);
ok(w.localStorage.getItem('sourcecheck:v1:part21:' + ID), 'autosaved per file and person');
const csv = w.eval('exportCSV()'); const rows = csv.trim().split('\n'), head = rows[0].split(',');
ok(dlName === 'labels_part21_' + ID + '.csv', 'download name ' + dlName);
ok(rows.length >= 1 + 3 + DOC.n_items && head.join() === 'item_id,annotator,check_id,practice,order,negated,polite,act,note,time_ms,started_at,tool,exported_at', 'CSV header');
ok(rows.slice(1).every(r => /^(p21-|prac-)/.test(r)), 'rows are items or practice');
ok(rows.some(r => /odd; with ""quotes"", and comma/.test(r)), 'note escaped');
ok(rows.some(r => r.startsWith('prac-3,') && r.split(',')[5] === 'unsure'), 'unsure exported');
if (OUT) fs.writeFileSync(OUT, csv);
// resume
{ const d2 = boot(); const w2 = d2.window; w2.localStorage.setItem('sourcecheck:v1:part21:' + ID, w.localStorage.getItem('sourcecheck:v1:part21:' + ID));
  w2.document.getElementById('annot').value = ID; w2.loadData(DOC);
  ok(/Resumed saved progress/.test(w2.document.getElementById('status').textContent) && w2.eval('S.phase') === 'done', 'resumes saved progress'); }
{ const d3 = boot('throw'); const w3 = d3.window; const e3 = []; w3.addEventListener('error', e => e3.push(e.message));
  w3.document.getElementById('annot').value = ID; w3.loadData(DOC);
  ok(w3.eval('S && S.phase') === 'intro' && e3.length === 0, 'works with blocked storage'); }
ok(errs.length === 0, 'no script errors ' + errs.join('; '));
if (fail) { console.log(fail + ' FAILED'); process.exit(1); } else console.log('all ok');

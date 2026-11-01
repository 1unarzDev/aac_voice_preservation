// jsdom check of annotation_package/check_pairs.html (Part 8, B1 blind checks).
// usage: NODE_PATH=<dir containing jsdom> node tests/test_check_pairs_html.js annotation_package/check_pairs.html
const {JSDOM} = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else if (m) console.log('ok  ', m); };
function boot(storage) {
  return new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/check_pairs.html', pretendToBeVisual: true,
    beforeParse(w) { w.URL.createObjectURL = () => 'blob:x'; if (storage === 'throw') Object.defineProperty(w, 'localStorage', {get() { throw new Error('blocked'); }}); } });
}
function key(w, k, target) { (target || w.document.body).dispatchEvent(new w.KeyboardEvent('keydown', {key: k, bubbles: true})); }
// FNV-1a as src/make_check_batches.py id_hash
function idHash(id) { let h = 2166136261 >>> 0; for (const c of id.trim().toUpperCase() + '|hwcheck') { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; } return h.toString(16).padStart(8, '0'); }
const OPTS = {polarity: ['negated', 'affirmative', 'unclear/mixed'], agent: ['speaker', 'addressee', 'we/joint', 'third party', 'unclear/mixed'],
  time_quantity: ['past', 'now', 'later', 'unclear/mixed'], certainty: ['plain assertion', 'hedged/uncertain', 'strongly certain/emphatic', 'unclear/mixed']};
const dims = ['polarity', 'agent', 'time_quantity', 'certainty'];
const items = Array.from({length: 30}, (_, i) => ({item_id: 'hc-' + (1000 + i), dimension: dims[i % 4], options: OPTS[dims[i % 4]], context: i === 3 ? 'At the bank.' : null,
  A: 'Sentence A number ' + i + ' about the bank.', B: 'Sentence B number ' + i + ' about the bank.', bare: 'bank number', noncritical: 'about'}));
const DOC = {check_id: 'hwc007', tool: 'check_pairs_v1', version: 1, n_items: 30, exclude: [idHash('P05'), idHash('P11')], items};
ok(idHash('P07') === '18a8be99', 'hash equals make_check_batches.id_hash("P07")');

const dom = boot(); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
const errs = []; w.addEventListener('error', e => errs.push(e.message));
ok(w.idHash(' p07 ') === '18a8be99', 'page idHash equals the Python hash');
$('annot').value = 'P20'; key(w, 'Enter', $('annot'));
ok(/Load your check file/.test($('status').textContent), 'needs a file first');
ok(!w.loadData({check_id: 'x', items: [Object.assign({}, items[0], {value_A: 'negated'})]}) && /must not have/.test($('status').textContent), 'refuses item with writer values');
ok(!w.loadData(Object.assign({}, DOC, {writer: 'P05'})) && /must not have/.test($('status').textContent), 'refuses extra top-level fields');
ok(!w.loadData({check_id: 'x', items: [Object.assign({}, items[0], {dimension: 'mood'})]}), 'refuses unknown dimension');
// excluded writer cannot check this file
$('annot').value = 'p05';
ok(w.loadData(DOC), 'valid file loads');
ok(/Please use a different check file/.test($('introview').textContent) && w.eval('S') === null, 'writer P05 refused (case-insensitive)');
$('annot').value = 'P20'; key(w, 'Enter', $('annot'));
ok(/Sentence pair check/.test($('introview').textContent) && /30 families/.test($('introview').textContent), 'intro for an independent checker');
key(w, 'Enter'); ok(/Practice/.test($('phasetag').textContent), 'practice');
key(w, '1'); key(w, '2'); key(w, '1'); key(w, '1'); key(w, 'Enter'); ok(/Matches/.test($('feedback').textContent), 'practice feedback'); key(w, 'Enter');
key(w, '1'); key(w, '2'); key(w, '2'); key(w, '2'); $('note').value = 'window vs door'; $('note').dispatchEvent(new w.Event('input')); key(w, 'Enter', $('note')); key(w, 'Enter');
ok(w.eval('S.phase') === 'M' && /Family 1 of 30/.test($('progtext').textContent), 'main phase');
const order = w.eval('S.order');
ok(new Set(order).size === 30 && JSON.stringify(order) !== JSON.stringify(items.map(x => x.item_id)), 'per-checker shuffled order');
const first = w.eval(`BYID["${order[0]}"]`);
ok($('sentA').textContent.includes(first.A) && $('inputbox').textContent.includes('bank number'), 'pair + keywords shown');
ok(/time|agent|certainty|polarity/.test($('help').textContent), 'dimension help shown');
for (let i = 0; i < 30; i++) {
  key(w, '1'); key(w, '2'); key(w, '1');
  if (i === 2) { key(w, '2'); $('note').value = 'object differs'; $('note').dispatchEvent(new w.Event('input')); key(w, 'Enter', $('note')); }
  else { key(w, '1'); key(w, 'Enter'); }
}
ok(w.eval('S.phase') === 'done', 'done after 30');
ok(w.localStorage.getItem('checkpairs:v1:hwc007:P20'), 'autosaved per check file and checker');
const csv = w.eval('exportCSV()'); const rows = csv.trim().split('\n'), head = rows[0].split(',');
ok(rows.length === 1 + 2 + 30 && head[2] === 'check_id' && rows.slice(1).every(r => r.split(',')[2] === 'hwc007'), 'CSV with check_id');
ok(rows.some(r => /object differs/.test(r)), 'note exported');
ok(errs.length === 0, 'no script errors ' + errs.join('; '));
{ const d2 = boot('throw'); const w2 = d2.window; const e2 = []; w2.addEventListener('error', e => e2.push(e.message));
  w2.document.getElementById('annot').value = 'P21'; w2.loadData(DOC);
  ok(w2.eval('S && S.phase') === 'intro' && e2.length === 0, 'works with blocked storage'); }
if (fail) { console.log(fail + ' FAILED'); process.exit(1); } else console.log('all ok');

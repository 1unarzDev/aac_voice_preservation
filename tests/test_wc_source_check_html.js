// jsdom check of annotation_package/wc_source_check.html (Part 5).
// usage: NODE_PATH=<dir containing jsdom> node tests/test_wc_source_check_html.js annotation_package/wc_source_check.html
const {JSDOM} = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else if (m) console.log('ok  ', m); };
function boot(storage) {
  return new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/wc_source_check.html', pretendToBeVisual: true,
    beforeParse(w) { w.URL.createObjectURL = () => 'blob:x'; if (storage === 'throw') Object.defineProperty(w, 'localStorage', {get() { throw new Error('blocked'); }}); } });
}
function key(w, k, target) { (target || w.document.body).dispatchEvent(new w.KeyboardEvent('keydown', {key: k, bubbles: true})); }
const dom = boot(); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
const errs = []; w.addEventListener('error', e => errs.push(e.message));
const items = w.eval('ITEMS');
ok(items.length === 20, '20 embedded families');
ok(items.every(x => Object.keys(x).sort().join() === 'A,B,bare,context,dimension,item_id,noncritical,options'), 'items carry only blind fields');
const blob = JSON.stringify(items);
ok(!/critical_value|construction|contrast|seeded|drafted|adversarial|r2pol|r2act|r2plt|cluster|template/.test(blob), 'no authored value / provenance strings');
const dims = items.reduce((a, x) => (a[x.dimension] = (a[x.dimension] || 0) + 1, a), {});
ok(dims.polarity === 7 && dims.speech_act === 7 && dims.politeness === 6, 'stratified 7/7/6');
// key file values must not appear as an answer column in the page
const keyCsv = fs.readFileSync(require('path').join(__dirname, '..', 'annotation', 'wc_source_check_key.csv'), 'utf8');
ok(!/authored_A/.test(html) && !keyCsv.split('\n').slice(1).some(l => l && html.includes(l.split(',')[1])), 'no family ids from the key in the page');
key(w, 'Enter'); ok($('itemview').classList.contains('hidden'), 'nothing starts without ID');
$('annot').value = 'T1'; key(w, 'Enter', $('annot'));
ok(/Sentence pair check/.test($('introview').textContent), 'intro shown');
key(w, 'Enter'); ok(/Practice/.test($('phasetag').textContent), 'practice started');
// practice 1 correct: negated, affirmative, yes, yes
key(w, '1'); key(w, '2'); key(w, '1'); key(w, '1'); key(w, 'Enter');
ok(!/Different/.test($('feedback').textContent) && /Matches/.test($('feedback').textContent), 'practice 1 feedback all match');
key(w, 'Enter');
// practice 2: polite, plain, only A, no -> note required
key(w, '1'); key(w, '2'); key(w, '2'); key(w, '2');
ok(d.activeElement && d.activeElement.id === 'note', 'note focused after "no"');
key(w, 'Enter', $('note')); ok(/note/.test($('status').textContent), 'note required');
$('note').value = 'window vs door'; $('note').dispatchEvent(new w.Event('input')); key(w, 'Enter', $('note'));
ok(/Matches/.test($('feedback').textContent) && !/Different/.test($('feedback').textContent), 'practice 2 feedback');
key(w, 'Enter');
ok(w.eval('S.phase') === 'M' && /Family 1 of 20/.test($('progtext').textContent), 'main begins');
const order = w.eval('S.order');
ok($('sentA').textContent.includes(w.eval(`BYID["${order[0]}"].A`)), 'sentence A displayed');
ok($('inputbox').textContent.includes(w.eval(`BYID["${order[0]}"].bare`)), 'bare keywords displayed');
// incomplete blocked
key(w, '1'); key(w, 'Enter'); ok(w.eval('S.idx') === 0 && /every question/.test($('status').textContent), 'incomplete blocked');
key(w, 'ArrowUp');
for (let i = 0; i < 20; i++) {
  key(w, '1'); key(w, '2');                                  // value A, value B
  if (i === 4) key(w, 's'); else key(w, String(1 + (i % 4))); // keywords fit (S = can't judge)
  if (i % 5 === 2) { key(w, '2'); $('note').value = 'tense differs ' + i; $('note').dispatchEvent(new w.Event('input')); key(w, 'Enter', $('note')); }
  else { key(w, '1'); key(w, 'Enter'); }
  if (i === 6) { key(w, 'Backspace'); ok(w.eval('S.idx') === 6, 'backspace goes back'); key(w, 'Enter'); }
}
ok(w.eval('S.phase') === 'done', 'done after 20 families: ' + w.eval('S.phase') + ' ' + $('status').textContent);
const saved = w.localStorage.getItem('wcsourcecheck:v1:T1'); ok(saved && JSON.parse(saved).phase === 'done', 'autosaved');
const csv = w.eval('exportCSV()'); const rows = csv.trim().split('\n');
ok(rows.length === 1 + 2 + 20, 'CSV header + 2 practice + 20 rows');
const head = rows[0].split(',');
ok(['value_A', 'value_B', 'bare_fits', 'differ_only', 'note', 'time_ms', 'unsure'].every(h => head.includes(h)), 'CSV columns');
ok(rows.some(r => /tense differs 2/.test(r) && /,no,/.test(r)), 'note + "no" exported');
ok(rows.some(r => /,bare,/.test(r) || /\|?bare\|?/.test(r.split(',')[9] || '')), 'unsure exported');
ok(rows.slice(3).every(r => /^wc-/.test(r)), 'item rows have ids');
ok(errs.length === 0, 'no script errors ' + errs.join(';'));
const dom2 = boot(); dom2.window.localStorage.setItem('wcsourcecheck:v1:T1', saved.replace('"phase":"done"', '"phase":"M"'));
dom2.window.document.getElementById('annot').value = 'T1'; key(dom2.window, 'Enter', dom2.window.document.getElementById('annot'));
ok(dom2.window.eval('S.phase') === 'M' && /Resumed/.test(dom2.window.document.getElementById('status').textContent), 'resume from saved state');
dom2.window.document.getElementById('annot').value = 'T2'; key(dom2.window, 'Enter', dom2.window.document.getElementById('annot'));
ok(dom2.window.eval('S.order.join()') !== order.join() && dom2.window.eval('S.phase') === 'intro', 'new ID: fresh state, different shuffle');
const dom3 = boot('throw'); const e3 = []; dom3.window.addEventListener('error', e => e3.push(e.message));
dom3.window.document.getElementById('annot').value = 'T3'; key(dom3.window, 'Enter', dom3.window.document.getElementById('annot'));
key(dom3.window, 'Enter'); key(dom3.window, '1');
ok(e3.length === 0 && dom3.window.eval('S.phase') === 'P', 'works with localStorage blocked');
console.log(fail ? fail + ' FAILED' : 'ALL PASSED');
process.exit(fail ? 1 : 0);

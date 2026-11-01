// jsdom check of annotation_package/repair_audit.html.
// usage: NODE_PATH=<dir containing jsdom> node tests/test_repair_audit_html.js annotation_package/repair_audit.html
const {JSDOM} = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else console.log('ok  ', m); };
function boot(storage) {
  const dom = new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/repair_audit.html', pretendToBeVisual: true,
    beforeParse(w) { w.URL.createObjectURL = () => 'blob:x'; if (storage === 'throw') Object.defineProperty(w, 'localStorage', {get() { throw new Error('blocked'); }}); } });
  return dom;
}
function key(w, k, target) { const ev = new w.KeyboardEvent('keydown', {key: k, bubbles: true}); (target || w.document.body).dispatchEvent(ev); }
const dom = boot(); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
const errs = []; w.addEventListener('error', e => errs.push(e.message));
ok(w.eval('ITEMS.length') === 40, '40 embedded items');
ok(w.eval('ITEMS.every(x => Object.keys(x).sort().join() === "input,item_id,text")'), 'items carry only id/text/input (blind)');
ok(!/repaired|control|gemma|llama|qwen|terra|G1|P0/.test(w.eval('JSON.stringify(ITEMS)')), 'no arm/model/condition strings in items');
// keys ignored before ID
key(w, 'Enter'); ok($('itemview').classList.contains('hidden'), 'nothing starts without ID');
$('annot').value = 'T1'; key(w, 'Enter', $('annot'));
ok(/Pass A/.test($('introview').textContent), 'intro A shown');
key(w, 'Enter'); ok(/Practice/.test($('phasetag').textContent), 'practice A started');
ok($('inputwrap').classList.contains('hidden'), 'pass A practice hides input');
// practice 1: answer yes -> feedback -> next
key(w, '1'); key(w, 'Enter'); ok(!$('feedback').classList.contains('hidden') && /Matches/.test($('feedback').textContent), 'practice feedback (match)');
key(w, 'Enter');
// practice 2: answer no -> note required
key(w, '3'); ok(d.activeElement && d.activeElement.id === 'note', 'note box focused after non-yes');
key(w, 'Enter', $('note')); ok(/note/.test($('status').textContent), 'note required message');
$('note').value = 'fragment'; $('note').dispatchEvent(new w.Event('input')); key(w, 'Enter', $('note'));
ok(/Matches/.test($('feedback').textContent), 'practice 2 feedback'); key(w, 'Enter');
key(w, '1'); key(w, 'Enter'); key(w, 'Enter');
ok(w.eval('S.phase') === 'A' && /item 1 of 40/.test($('progtext').textContent), 'pass A begins');
// pass A: all items, mix answers; test backspace and timing
const order = w.eval('S.orderA');
for (let i = 0; i < 40; i++) {
  ok($('sentence').textContent === w.eval(`BYID["${order[i]}"].text`) || false, i === 0 ? 'shuffled order displayed' : null) ;
  if (i === 5) { key(w, 'Backspace'); ok(w.eval('S.idx') === 4, 'backspace goes back'); key(w, 'Enter'); }
  if (i % 7 === 3) { key(w, '2'); $('note').value = 'missing word ' + i; $('note').dispatchEvent(new w.Event('input')); key(w, 'Enter', $('note')); }
  else if (i === 10) { key(w, 's'); key(w, 'Enter'); }
  else { key(w, '1'); key(w, 'Enter'); }
}
ok(w.eval('S.phase') === 'introB', 'after 40 A items -> intro B');
ok(w.eval('Object.keys(S.A).length') === 40, '40 A records');
ok(w.eval('Object.values(S.A).every(r => typeof r.time_ms === "number")'), 'time per item recorded');
key(w, 'Backspace'); ok(w.eval('S.phase') === 'introB', 'cannot go back into Pass A');
key(w, 'Enter'); ok(!$('inputwrap').classList.contains('hidden') && /Chip/.test($('inputbox').textContent), 'pass B practice shows input + chips');
// practice B item 3 wrong on purpose
for (let p = 0; p < 3; p++) { key(w, '1'); key(w, '2'); key(w, 'Enter'); if (p === 2) ok(/Different/.test($('feedback').textContent), 'practice B mismatch feedback'); key(w, 'Enter'); }
ok(w.eval('S.phase') === 'B', 'pass B begins');
// incomplete -> blocked
key(w, '1'); key(w, 'Enter'); ok(w.eval('S.idx') === 0 && /every question/.test($('status').textContent), 'B requires both answers');
key(w, '2'); key(w, 'Enter');
// autosave & resume in new dom
const saved = w.localStorage.getItem('repairaudit:v1:T1'); ok(saved && JSON.parse(saved).phase === 'B', 'autosaved to localStorage');
for (let i = 1; i < 40; i++) { key(w, String(1 + (i % 3))); key(w, String(1 + (i % 2))); key(w, 'Enter'); }
ok(w.eval('S.phase') === 'done', 'done after pass B');
const csv = w.eval('exportCSV()');  const rows = csv.trim().split('\n');
ok(rows.length === 1 + 3 + 40, 'CSV has header + 3 practice + 40 rows');
const head = rows[0].split(','); const r1 = rows.find(r => r.includes('missing word 3'));
ok(head.includes('a_time_ms') && head.includes('b_contract') && head.includes('a_note'), 'CSV columns');
ok(r1 && /minor fix needed/.test(r1), 'note + answer exported');
const bad = rows.slice(4).filter(r => !/^ra-/.test(r)); ok(bad.length === 0, 'item rows have ids');
ok(rows.slice(4).every(r => /,(yes|partly|no),(yes|no),/.test(r)), 'all B answers exported');
ok(errs.length === 0, 'no script errors ' + errs.join(';'));
// resume in a fresh DOM sharing storage: emulate by copying
const dom2 = boot(); dom2.window.localStorage.setItem('repairaudit:v1:T1', saved);
dom2.window.document.getElementById('annot').value = 'T1'; key(dom2.window, 'Enter', dom2.window.document.getElementById('annot'));
ok(dom2.window.eval('S.phase') === 'B' && /Resumed/.test(dom2.window.document.getElementById('status').textContent), 'resume from saved state');
// different annotator -> different order
dom2.window.document.getElementById('annot').value = 'T2'; key(dom2.window, 'Enter', dom2.window.document.getElementById('annot'));
ok(dom2.window.eval('S.orderA.join()') !== order.join() && dom2.window.eval('S.phase') === 'introA', 'new ID: fresh state, different shuffle');
// storage blocked
const dom3 = boot('throw'); const e3 = []; dom3.window.addEventListener('error', e => e3.push(e.message));
dom3.window.document.getElementById('annot').value = 'T3'; key(dom3.window, 'Enter', dom3.window.document.getElementById('annot'));
key(dom3.window, 'Enter'); key(dom3.window, '1'); key(dom3.window, 'Enter');
ok(e3.length === 0 && dom3.window.eval('S.phase') === 'PA', 'works with localStorage blocked');
console.log(fail ? fail + ' FAILED' : 'ALL PASSED');
process.exit(fail ? 1 : 0);

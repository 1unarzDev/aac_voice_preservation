// jsdom check of annotation_package/wb_corpus_check.html (Part 6).
// usage: NODE_PATH=<dir containing jsdom> node tests/test_wb_corpus_check_html.js annotation_package/wb_corpus_check.html
const {JSDOM} = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else if (m) console.log('ok  ', m); };
function boot(storage) {
  return new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/wb_corpus_check.html', pretendToBeVisual: true,
    beforeParse(w) { w.URL.createObjectURL = () => 'blob:x'; if (storage === 'throw') Object.defineProperty(w, 'localStorage', {get() { throw new Error('blocked'); }}); } });
}
function key(w, k, target) { (target || w.document.body).dispatchEvent(new w.KeyboardEvent('keydown', {key: k, bubbles: true})); }
const dom = boot(); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
const errs = []; w.addEventListener('error', e => errs.push(e.message));
const items = w.eval('ITEMS');
ok(items.length === 20, '20 embedded messages');
ok(items.every(x => Object.keys(x).sort().join() === 'item_id,keywords,message'), 'items carry only id/keywords/message');
ok(!/confirmed_ambiguous|supplied|coder|witness|gpt-|enriched|random|focal|status|aactext|"w\d{3}"/.test(JSON.stringify(w.eval('DATA'))), 'no panel labels / provenance in data');
ok(w.eval('DIMS.every(d => OPTIONS[d] && OPTIONS[d].length >= 3)'), 'options for all five dimensions');
$('annot').value = 'T1'; key(w, 'Enter', $('annot'));
ok(/Pass 1/.test($('introview').textContent), 'intro 1');
key(w, 'Enter'); ok(/Practice/.test($('phasetag').textContent) && $('msgwrap').classList.contains('hidden'), 'practice pass 1, message hidden');
ok(!d.querySelector('main').textContent.includes("I don't want soup"), 'practice message not shown in pass 1');
// practice 1: tick the suggested sets
const P = w.eval('OPTIONS');
const tick = (dim, vals) => vals.forEach(v => key(w, String(P[dim].indexOf(v) + 1)));
tick('polarity', ['affirmative', 'negated']); key(w, 'ArrowDown');
ok(w.eval('S.P1["prac1-1"].answers.polarity.join()') === 'affirmative,negated', 'multi-select ticks two values');
key(w, '1'); key(w, '1'); ok(w.eval('S.P1["prac1-1"].answers.speech_act.length') === 0, 'pressing again unticks');
tick('speech_act', ['statement', 'question']); key(w, 'ArrowDown');
key(w, 'Enter'); ok(/at least one value/.test($('status').textContent) && w.eval('active') === 2, 'incomplete -> jumps to first unanswered');
tick('agent', ['speaker', 'addressee', 'third party']); key(w, 'ArrowDown');
tick('certainty', ['plain assertion', 'n/a (question/request)']); key(w, 'ArrowDown');
tick('politeness', ['none']); key(w, 'Enter');
ok(/Matches/.test($('feedback').textContent) && !/Different/.test($('feedback').textContent), 'practice 1 feedback matches');
key(w, 'Enter');
tick('polarity', ['affirmative', 'negated']); for (let i = 0; i < 4; i++) { key(w, 'ArrowDown'); key(w, '1'); }
key(w, 'Enter'); ok(/Different/.test($('feedback').textContent), 'practice 2 mismatch feedback'); key(w, 'Enter');
ok(w.eval('S.phase') === 'X1', 'pass 1 begins');
const order1 = w.eval('S.order1');
ok($('keywords').textContent === w.eval(`BYID["${order1[0]}"].keywords`) && $('msgwrap').classList.contains('hidden') && $('message').textContent === '', 'pass 1 shows keywords only');
for (let i = 0; i < 20; i++) {
  ok(!d.querySelector('main').textContent.includes(w.eval(`BYID["${order1[i]}"].message`)) || w.eval(`BYID["${order1[i]}"].message`) === w.eval(`BYID["${order1[i]}"].keywords`), i === 0 ? 'message never visible in pass 1' : null);
  key(w, '1'); if (i % 2) key(w, '2'); key(w, 'ArrowDown');
  if (i === 3) key(w, 's'); else { key(w, '1'); key(w, '3'); key(w, 'ArrowDown'); }
  key(w, '2'); key(w, 'ArrowDown'); key(w, '1'); key(w, 'ArrowDown'); key(w, '1');
  if (i === 8) { $('note').value = 'could be sarcastic'; $('note').dispatchEvent(new w.Event('input')); key(w, 'Enter', $('note')); }
  else key(w, 'Enter');
  if (i === 5) { key(w, 'Backspace'); ok(w.eval('S.idx') === 5, 'backspace within pass'); key(w, 'Enter'); }
}
ok(w.eval('S.phase') === 'intro2', 'after 20 -> intro 2 (' + w.eval('S.phase') + ')');
key(w, 'Backspace'); ok(w.eval('S.phase') === 'intro2', 'cannot go back into pass 1');
ok(/locked/.test($('introview').textContent), 'pass 2 intro says pass 1 locked');
const snap1 = JSON.stringify(w.eval('S.X1'));
key(w, 'Enter'); ok(!$('msgwrap').classList.contains('hidden') && /don't want soup/.test($('message').textContent), 'pass 2 practice shows message');
for (let p = 0; p < 2; p++) { for (let q = 0; q < 5; q++) key(w, '1'); key(w, 'Enter'); key(w, 'Enter'); }
ok(w.eval('S.phase') === 'X2', 'pass 2 begins');
key(w, '1'); key(w, 'Enter'); ok(w.eval('S.idx') === 0 && /every question/.test($('status').textContent), 'pass 2 requires all five');
key(w, 'ArrowUp'); key(w, 'ArrowUp');
for (let i = 0; i < 20; i++) { key(w, '2'); key(w, String(1 + (i % 3))); key(w, '1'); key(w, '2'); key(w, '1'); key(w, 'Enter'); }
ok(w.eval('S.phase') === 'done', 'done after pass 2');
ok(Object.keys(JSON.parse(snap1)).length === 20 && JSON.stringify(Object.values(w.eval('S.X1')).map(r => r.answers)) === JSON.stringify(Object.values(JSON.parse(snap1)).map(r => r.answers)), 'pass 1 answers unchanged by pass 2');
const saved = w.localStorage.getItem('wbcorpuscheck:v1:T1'); ok(saved && JSON.parse(saved).phase === 'done', 'autosaved');
const csv = w.eval('exportCSV()'); const rows = csv.trim().split('\n');
ok(rows.length === 1 + 5 * 4 + 5 * 20, 'CSV header + practice + 100 rows (' + rows.length + ')');
const head = rows[0].split(',');
ok(['dimension', 'p1_plausible', 'p1_unsure', 'p2_value', 'p1_time_ms', 'p2_time_ms', 'p1_note'].every(h => head.includes(h)), 'CSV columns');
ok(rows.some(r => /affirmative\|negated/.test(r)), 'multi-select exported pipe-joined');
ok(rows.some(r => /could be sarcastic/.test(r)), 'note exported');
const main = rows.slice(21); ok(main.every(r => /^wb-/.test(r)) && main.filter(r => /,speech_act,/.test(r)).length === 20, 'item rows per dimension');
ok(errs.length === 0, 'no script errors ' + errs.join(';'));
const dom2 = boot(); dom2.window.localStorage.setItem('wbcorpuscheck:v1:T1', saved.replace('"phase":"done"', '"phase":"X2"'));
dom2.window.document.getElementById('annot').value = 'T1'; key(dom2.window, 'Enter', dom2.window.document.getElementById('annot'));
ok(dom2.window.eval('S.phase') === 'X2' && /Resumed/.test(dom2.window.document.getElementById('status').textContent), 'resume from saved state');
dom2.window.document.getElementById('annot').value = 'T2'; key(dom2.window, 'Enter', dom2.window.document.getElementById('annot'));
ok(dom2.window.eval('S.order1.join()') !== order1.join() && dom2.window.eval('S.phase') === 'intro1', 'new ID: fresh state, different shuffle');
const dom3 = boot('throw'); const e3 = []; dom3.window.addEventListener('error', e => e3.push(e.message));
dom3.window.document.getElementById('annot').value = 'T3'; key(dom3.window, 'Enter', dom3.window.document.getElementById('annot'));
key(dom3.window, 'Enter'); key(dom3.window, '1');
ok(e3.length === 0 && dom3.window.eval('S.phase') === 'P1', 'works with localStorage blocked');
console.log(fail ? fail + ' FAILED' : 'ALL PASSED');
process.exit(fail ? 1 : 0);

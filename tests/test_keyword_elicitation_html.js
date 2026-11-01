// jsdom check of annotation_package/keyword_elicitation.html (Part 9, B2) with a committed set file.
// usage: NODE_PATH=<dir containing jsdom> node tests/test_keyword_elicitation_html.js annotation_package/keyword_elicitation.html
const {JSDOM} = require('jsdom');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(process.argv[2], 'utf8');
const SET = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'annotation_package', 'elicitation_sets', 'elic_s01_r1.json'), 'utf8'));
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else if (m) console.log('ok  ', m); };
function boot(storage) {
  return new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/keyword_elicitation.html', pretendToBeVisual: true,
    beforeParse(w) { w.URL.createObjectURL = () => 'blob:x'; if (storage === 'throw') Object.defineProperty(w, 'localStorage', {get() { throw new Error('blocked'); }}); } });
}
function key(w, k, target) { (target || w.document.body).dispatchEvent(new w.KeyboardEvent('keydown', {key: k, bubbles: true})); }
function type(w, el, v) { el.value = v; el.dispatchEvent(new w.Event('input', {bubbles: true})); }

const dom = boot(); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
const errs = []; w.addEventListener('error', e => errs.push(e.message));
ok(w.eval('INSTRUCTION') === 'Type the 2–4 words you would select on a keyword-based communication device to get this message across, as if each word takes a long time to select.', 'exact instruction text');
ok(!/model|suggest|AI /i.test(d.querySelector('header').textContent + d.querySelector('main').textContent), 'no model wording on the page');
// no model output can ever be shown: files with any other field are refused
ok(!w.loadData(Object.assign({}, SET, {outputs: ['I want tea']})) && /must not be shown/.test($('status').textContent), 'refuses extra top-level field');
ok(!w.loadData(Object.assign({}, SET, {messages: [Object.assign({}, SET.messages[0], {pos_cap4: ['tea']})]})), 'refuses message with compressor keywords');
ok(!w.loadData(Object.assign({}, SET, {messages: [Object.assign({}, SET.messages[0], {model_output: 'x'})]})), 'refuses message with model output');
ok(w.loadData(SET), 'committed set file loads');
$('annot').value = 'E01'; key(w, 'Enter', $('annot'));
ok(/38 short messages|37 short messages/.test($('introview').textContent) && /2–4 words/.test($('introview').textContent), 'intro with instruction');
key(w, 'Enter'); ok(w.eval('S.phase') === 'P' && $('message').textContent === 'The bus to town leaves at nine.', 'practice 1 shown');
type(w, $('kw'), 'bus'); ok(/1 word/.test($('count').textContent), 'live word count');
key(w, 'Enter', $('kw')); ok(/2 to 4 words/.test($('status').textContent) && w.eval('S.idx') === 0, 'one word blocked');
type(w, $('kw'), 'bus town nine leaves early'); ok(/at most 4/.test($('count').textContent), 'five words flagged');
key(w, 'Enter', $('kw')); ok(w.eval('S.idx') === 0, 'five words blocked');
type(w, $('kw'), 'bus  town   nine'); key(w, 'Enter', $('kw'));
const fb = $('feedback').textContent;
ok(/3 words/.test(fb) && /no right answer/.test(fb), 'practice feedback: format only');
ok(!/bus town|example|suggested/i.test(fb.replace(/"bus town nine"/, '')), 'practice feedback shows no example answer');
key(w, 'Enter'); key(w, 'Escape'); type(w, $('kw'), 'sister visit weekend'); key(w, 'Enter', $('kw')); key(w, 'Enter');
ok(w.eval('S.phase') === 'M' && $('message').textContent === SET.messages[0].text, 'main phase shows message 1');
const n = SET.messages.length;
for (let i = 0; i < n; i++) {
  if (i === 4) { $('skip').click(); continue; }
  type(w, $('kw'), i % 3 === 0 ? 'not go ?' : 'word' + i + ' other');
  if (i === 6) { type(w, $('note'), 'odd message'); }
  key(w, 'Enter', $('kw'));
  if (i === 8) { key(w, 'PageUp'); ok(w.eval('S.idx') === 8 && $('kw').value === 'word8 other', 'Page Up goes back with saved words'); key(w, 'Enter', $('kw')); }
}
ok(w.eval('S.phase') === 'done', 'done after all messages: ' + $('status').textContent);
ok(w.localStorage.getItem('keywordelic:v1:elic_s01_r1:E01'), 'autosaved per set file and annotator');
const csv = w.eval('exportCSV()'); const rows = csv.trim().split('\n'), head = rows[0].split(',');
ok(rows.length === 1 + 2 + n, 'CSV: header + 2 practice + all messages');
ok(['item_id', 'annotator', 'set_file', 'keywords', 'n_words', 'skipped', 'note', 'time_ms', 'n_edits'].every(h => head.includes(h)), 'CSV columns');
const main = rows.slice(3);
ok(main.filter(r => r.split(',')[head.indexOf('skipped')] === '1').length === 1, 'one skip exported');
ok(rows[1].includes('bus town nine') && !rows[1].includes('  '), 'whitespace normalised');
ok(main.some(r => r.includes('not go ?')) && main.some(r => r.includes('odd message')), 'keywords and note exported');
ok(errs.length === 0, 'no script errors ' + errs.join('; '));
{ const d2 = boot('throw'); const w2 = d2.window; const e2 = []; w2.addEventListener('error', e => e2.push(e.message));
  w2.document.getElementById('annot').value = 'E02'; w2.loadData(SET); key(w2, 'Enter');
  ok(w2.eval('S.phase') === 'P' && e2.length === 0, 'works with blocked storage'); }
if (fail) { console.log(fail + ' FAILED'); process.exit(1); } else console.log('all ok');

// jsdom check of annotation_package/write_pairs.html (Part 7, B1 writers).
// usage: NODE_PATH=<dir containing jsdom> node tests/test_write_pairs_html.js annotation_package/write_pairs.html
// Also checks the page's rule port against src/hw_rules.py via tests/fixtures/hw_rule_cases.json.
const {JSDOM} = require('jsdom');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(process.argv[2], 'utf8');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'hw_rule_cases.json'), 'utf8'));
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else if (m) console.log('ok  ', m); };
function boot(hash, storage) {
  return new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/write_pairs.html' + (hash || ''), pretendToBeVisual: true,
    beforeParse(w) { w.URL.createObjectURL = () => 'blob:x'; if (storage === 'throw') Object.defineProperty(w, 'localStorage', {get() { throw new Error('blocked'); }}); } });
}
function key(w, k, target, opts) { (target || w.document.body).dispatchEvent(new w.KeyboardEvent('keydown', Object.assign({key: k, bubbles: true}, opts || {}))); }
function type(w, el, v) { el.value = v; el.dispatchEvent(new w.Event('input', {bubbles: true})); }

// ---- parity with the Python rules
{
  const dom = boot('#dim=polarity'); const w = dom.window;
  const lists = w.eval('({CUES_ALL: [...CUES_ALL].sort(), STOP: [...STOP].sort(), NONCRIT_TIME_OK: [...NONCRIT_TIME_OK].sort(), IRREG})');
  const sortPy = (a) => a.slice().sort((x, y) => (x < y ? -1 : x > y ? 1 : 0));
  ok(JSON.stringify(sortPy(lists.CUES_ALL)) === JSON.stringify(fixture.lists.CUES_ALL), 'cue list identical to hw_rules.py');
  ok(JSON.stringify(sortPy(lists.STOP)) === JSON.stringify(fixture.lists.STOP), 'stop list identical');
  ok(JSON.stringify(sortPy(lists.NONCRIT_TIME_OK)) === JSON.stringify(fixture.lists.NONCRIT_TIME_OK), 'extra-word time list identical');
  ok(JSON.stringify(lists.IRREG) === JSON.stringify(fixture.lists.IRREG), 'irregular forms identical');
  let same = 0;
  for (const c of fixture.cases) {
    const r = w.checkPair(c.pair, c.dim);
    const got = {ok: r.ok, keywords: r.keywords, extra: r.extra, problems: r.problems.map(x => x[1]), warnings: r.warnings.map(x => x[1])};
    const want = {ok: c.ok, keywords: c.keywords, extra: c.extra, problems: c.problems, warnings: c.warnings};
    if (JSON.stringify(got) === JSON.stringify(want)) same++; else console.log('  diff', c.dim, JSON.stringify(c.pair), JSON.stringify(got), JSON.stringify(want));
  }
  ok(same === fixture.cases.length, `checkPair matches Python on ${same}/${fixture.cases.length} fixture cases`);
  // every "ready" practice item passes the live checks; every problem item is flagged by the checks or by its values
  const D = w.eval('DIMS');
  ok(Object.keys(D).length === 6, 'six dimensions');
  ok(Object.values(D).every(d => d.practice.length === 3 && d.good.length >= 2 && d.bad.length >= 2), 'guidance + 3 practice items per dimension');
  ok(Object.entries(D).every(([k, d]) => d.practice.filter(p => p.expected === 0).every(p => w.checkPair(p, k).ok)), 'ready practice pairs pass the checks');
  ok(Object.entries(D).every(([k, d]) => d.good.every(([A, B, kw]) => w.checkPair({A, B, keywords: kw, valA: d.values[0][0], valB: d.values[1][0]}, k).ok)), 'good examples pass the hard checks');
}

// ---- full writer flow, dimension and topic rotation from the hash
{
  const dom = boot('#dim=agent&rot=4&n=15'); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
  const errs = []; w.addEventListener('error', e => errs.push(e.message));
  ok(/agent/.test($('introview').textContent) && !/Choose your dimension/.test($('introview').textContent), 'hash fixes the dimension');
  $('annot').value = 'P07'; key(w, 'Enter', $('annot'));
  ok(w.eval('S.dim') === 'agent' && w.eval('S.W.length') === 15, '15 agent pairs');
  const topics = w.eval('S.W.map(p => p.topic_suggested)');
  ok(topics[0] === 'plans' && topics[1] === 'food' && topics[7] === 'health' && topics[11] === 'plans' && new Set(topics).size === 11, 'topic rotation from rot=4: ' + topics.slice(0, 3).join(','));
  ok(/CC BY 4.0/.test($('introview').textContent), 'release text shown');
  key(w, 'Enter'); ok(w.eval('S.phase') === 'intro' && /tick the box/.test($('status').textContent), 'consent required before starting');
  $('consent').checked = true; $('consent').dispatchEvent(new w.Event('change'));
  key(w, 'Enter'); ok(w.eval('S.phase') === 'P', 'practice starts');
  const prac = w.eval('practiceOf("agent")');
  key(w, 'Enter'); ok(/Choose an answer/.test($('status').textContent), 'practice needs an answer');
  key(w, String(prac[0].expected + 1)); key(w, 'Enter');
  ok(/Matches/.test($('feedback').textContent), 'practice 1 feedback: matches');
  key(w, 'Enter'); key(w, '1'); key(w, 'Enter');
  ok(/Different/.test($('feedback').textContent) && /Suggested answer/.test($('feedback').textContent), 'practice 2 feedback: different + suggested');
  key(w, 'Enter'); key(w, String(prac[2].expected + 1)); key(w, 'Enter'); key(w, 'Enter');
  ok(w.eval('S.phase') === 'W' && d.activeElement.id === 'f_A', 'writing phase, focus on sentence A');
  ok(/Suggested topic: plans/.test($('topicline').textContent), 'topic suggestion shown');
  // a failing pair cannot be saved; the checks list says why
  type(w, $('f_A'), 'She walks the dog every morning.'); type(w, $('f_B'), 'I walk the dog every morning.');
  type(w, $('f_keywords'), 'walks dog');
  ok(/Fix:/.test($('checks').textContent) && /walks/.test($('checks').textContent), 'live check flags agreement leak');
  key(w, 'Enter', $('f_keywords'));
  ok(w.eval('S.idx') === 0 && /to fix/.test($('status').textContent), 'invalid pair not saved');
  // Enter moves through the fields
  $('f_A').focus(); key(w, 'Enter', $('f_A')); ok(d.activeElement.name === 'valA', 'Enter: sentence A -> value A');
  key(w, '3', d.activeElement); ok(w.eval('S.W[0].valA') === 'third party', 'digit picks value');
  key(w, 'Enter', d.activeElement); ok(d.activeElement.id === 'f_B', 'Enter: value A -> sentence B');
  key(w, 'Enter', $('f_B')); key(w, '1', d.activeElement); key(w, 'Enter', d.activeElement);
  ok(d.activeElement.id === 'f_keywords' && w.eval('S.W[0].valB') === 'speaker', 'value B chosen, focus on keywords');
  type(w, $('f_keywords'), 'walk dog');
  ok(/all fine/.test($('checks').textContent) && /Shared extra word: morning/.test($('checks').textContent), 'fixed pair passes');
  key(w, 'Enter', $('f_keywords'));
  ok(w.eval('S.idx') === 1, 'saved and moved to pair 2');
  // fill the other 14 pairs programmatically through the inputs
  const fill = (i) => {
    type(w, $('f_A'), `I booked the dentist appointment number ${i + 2} for Friday.`);
    type(w, $('f_B'), `You booked the dentist appointment number ${i + 2} for Friday.`);
    for (const [nm, v] of [['valA', 'speaker'], ['valB', 'addressee']]) { const r = [...d.querySelectorAll(`input[name=${nm}]`)].find(x => x.value === v); r.checked = true; r.dispatchEvent(new w.Event('change')); }
    type(w, $('f_keywords'), 'book appointment');
  };
  for (let i = 1; i < 15; i++) {
    fill(i);
    if (i === 3) { key(w, 'PageUp'); ok(w.eval('S.idx') === 2, 'Page Up: previous pair'); key(w, 'PageDown'); }
    if (i === 5) { type(w, $('f_situation'), 'At the dentist reception.'); }
    key(w, 'Enter', $('f_keywords'), {ctrlKey: true});
  }
  ok(w.eval('S.phase') === 'done', 'done after 15 valid pairs: ' + $('status').textContent);
  ok(/4 to 12/.test(w.eval('JSON.stringify(checkPair({A:"I booked it.",B:"You booked it.",valA:"speaker",valB:"addressee",keywords:"book it"},"agent"))')), 'short sentences rejected');
  const saved = w.localStorage.getItem('writepairs:v1:P07:agent'); ok(saved && JSON.parse(saved).phase === 'done', 'autosaved per writer and dimension');
  const csv = w.eval('exportCSV()'); const rows = csv.trim().split('\n');
  const head = rows[0].split(',');
  ok(rows.length === 1 + 3 + 15, 'CSV: header + 3 practice + 15 pairs');
  ok(['row_type', 'writer', 'dimension', 'pair_no', 'sentence_A', 'value_A', 'sentence_B', 'value_B', 'keywords', 'extra_word', 'checks_ok', 'time_ms', 'consent', 'consent_at', 'topic_suggested'].every(h => head.includes(h)), 'CSV columns');
  const pr = rows.filter(r => r.startsWith('pair,'));
  ok(pr.every(r => r.includes(',yes,') && r.split(',')[head.indexOf('checks_ok')] === '1'), 'every pair consented and checked');
  ok(pr[0].includes('walk dog') && pr[0].includes('morning') && pr[0].includes('third party'), 'first pair exported with keywords, extra word and values');
  ok(pr.some(r => r.includes('At the dentist reception.')), 'situation exported');
  ok(Number(pr[0].split(',')[head.indexOf('time_ms')]) >= 0, 'per-pair time recorded');
  ok(errs.length === 0, 'no script errors ' + errs.join('; '));
}

// ---- no hash: dimension chooser; blocked storage still works
{
  const dom = boot('', 'throw'); const w = dom.window, d = w.document, $ = id => d.getElementById(id);
  const errs = []; w.addEventListener('error', e => errs.push(e.message));
  ok(/Choose your dimension/.test($('introview').textContent), 'chooser shown without hash');
  $('annot').value = 'P08'; key(w, 'Enter', $('annot'));
  key(w, '6'); key(w, 'Enter');
  ok(w.eval('S.dim') === 'time' && w.eval('S.dim_source') === 'chosen' && w.eval('S.W.length') === 15, 'key 6 picks time');
  ok(w.eval('S.W[0].topic_suggested') === 'health', 'default rotation starts at health');
  $('consent').checked = true; $('consent').dispatchEvent(new w.Event('change')); key(w, 'Enter');
  ok(w.eval('S.phase') === 'P', 'works with blocked localStorage');
  ok(errs.length === 0, 'no script errors with blocked storage ' + errs.join('; '));
}
if (fail) { console.log(fail + ' FAILED'); process.exit(1); } else console.log('all ok');

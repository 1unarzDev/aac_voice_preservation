// jsdom check of annotation_package/annotate.html with one part file (e.g. Part 10).
// usage: NODE_PATH=<dir containing jsdom> node tests/test_annotate_part_html.js \
//          annotation_package/annotate.html annotation_package/part10_gold_new.json [out.csv]
// Loads the part, completes the practice items and every item with the keyboard, and
// writes the exported CSV to out.csv (if given) for an end-to-end scoring check.
const {JSDOM} = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const part = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else console.log('ok  ', m); };
let blobText = null, dlName = null;
const dom = new JSDOM(html, {runScripts: 'dangerously', url: 'http://localhost/annotate.html', pretendToBeVisual: true,
  beforeParse(w) {
    w.URL.createObjectURL = () => 'blob:x'; w.Element.prototype.scrollIntoView = function () {};  // not in jsdom
    const B = w.Blob; w.Blob = function (parts, opts) { blobText = parts.join(''); return new B(parts, opts); };
    w.HTMLAnchorElement.prototype.click = function () { dlName = this.download; };
  }});
const w = dom.window, d = w.document, $ = id => d.getElementById(id);
const errs = []; w.addEventListener('error', e => errs.push(e.message));
const key = (k) => d.body.dispatchEvent(new w.KeyboardEvent('keydown', {key: k, bubbles: true}));

// part file shape
ok(part.practice.length === 5, '5 practice items');
ok(part.items.length >= 100, part.items.length + ' items');
ok(part.items.every(x => Object.keys(x).sort().join() === 'critical,input_text,item_id,text'), 'items carry only id/text/critical/input (blind)');
ok(part.items.every(x => x.critical.options.length >= 3 && x.critical.question && x.critical.dimension), 'critical question + options');
ok(new Set(part.items.map(x => x.item_id)).size === part.items.length, 'unique item ids');
ok(!/r2c|r2d|guard|gemma|llama|qwen|terra|"G1|"P0|P2|S3/.test(JSON.stringify(part.items)), 'no run/model/condition strings in items');

$('annot').value = 'T1';
w.eval('load(' + JSON.stringify(part) + ')');
ok(/Loaded/.test($('status').textContent), 'loaded: ' + $('status').textContent);
const N = w.eval('ITEMS.length');
ok(N === part.items.length + 5, 'practice + items in sequence');
// added-content input is hidden until the other questions are answered
const nq = w.eval('questionsFor(ITEMS[0]).length');
ok(/appears after/.test($('form').textContent), 'input hidden before questions 1..n-1');
for (let i = 0; i < N; i++) {
  const it = w.eval('ITEMS[idx]');
  for (let q = 0; q < nq; q++) {
    if (i === 7 && q === 2) { key('s'); continue; }                   // one unsure answer
    key(String(1 + ((i + q) % 2)));
  }
  if (i === 0) ok(/Input the user typed/.test($('form').textContent), 'input shown after answering');
  key('Enter');
  if (it.practice) { ok(!$('feedback').classList.contains('hidden'), 'practice feedback ' + it.item_id); key('Enter'); }
}
ok(/All items done/.test($('status').textContent), 'all items done');
w.eval('exportCSV()');
ok(dlName === 'labels_' + part.run + '_T1.csv', 'download name ' + dlName);
const rows = blobText.trim().split('\n');
ok(rows.length === 1 + N, 'CSV rows: header + ' + N);
ok(rows[0] === 'item_id,annotator,practice,critical_dimension,critical,polarity,speech_act,agent,certainty,politeness,added_content,skip,unsure_dims,time_ms,exported_at', 'CSV header');
ok(rows.filter(r => /,1,[^,]*,/.test(r) && /\|?speech_act/.test(r)).length >= 1, 'unsure dim exported');
ok(w.localStorage.getItem('annot:' + part.run + ':T1') !== null, 'autosaved under annot:' + part.run + ':T1');
ok(errs.length === 0, 'no script errors ' + errs.join(';'));
if (process.argv[4]) fs.writeFileSync(process.argv[4], blobText);
console.log(fail ? fail + ' FAILED' : 'ALL PASSED');
process.exit(fail ? 1 : 0);

"""Write runs/r2c1/arbiter.jsonl from blind decisions (decisions.tsv) over the frozen inventory.
One row per J-unit (attribute.py key text_id, family_id, input_text); label comes from its A-unit.
Then (only after writing) compare with J1/J2 and write agreement.json.
"""
import csv, hashlib, json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; D = Path(__file__).resolve().parent
inv = json.loads((ROOT / 'analysis/r2c/arbiter_inventory.json').read_text())
canon = json.dumps({'a_units': inv['a_units'], 'j_units': inv['j_units']}, sort_keys=True, ensure_ascii=False).encode()
assert hashlib.sha256(canon).hexdigest() == inv['inventory_sha256'], 'inventory changed'
dec = {r['key']: r for r in csv.DictReader((D / 'decisions.tsv').open(), delimiter='\t')}
amap = {}
for a in inv['a_units']:
    hits = [k for k in dec if a['blind_order_key'].startswith(k)]
    assert len(hits) == 1, (a['a_unit'], hits)
    d = dec[hits[0]]
    assert d['critical'] in a['critical_options'], (hits, d)
    amap[a['a_unit']] = d
assert len(amap) == len(dec) == len(inv['a_units'])
J = {}
for l in (ROOT / 'runs/r2c1/judgments.jsonl').open():
    j = json.loads(l)
    if j.get('needs_arbiter'): J[(j['text_id'], j['family_id'], j['input_text'])] = j
out = []
for u in inv['j_units']:
    d = amap[u['a_unit']]; j = J[(u['text_id'], u['family_id'], u['input_text'])]
    out.append({'text_id': u['text_id'], 'family_id': u['family_id'], 'input_text': u['input_text'],
                'critical': d['critical'], 'rationale': d['rationale'], 'arbiter_model': 'claude-opus-5-5',
                'text': j['text'], 'dimension': u['dimension'], 'a_unit': u['a_unit'],
                'arbitration_view': 'blind: output text + production critical question/options only',
                'inventory_sha256': inv['inventory_sha256']})
p = ROOT / 'runs/r2c1/arbiter.jsonl'
p.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in out))
# ---- post-decision comparison with J1/J2 (A-unit level and J-unit/row level) ----
cmp = Counter(); by_dim = {}; types = Counter(); rows = []
for r in out:
    j = J[(r['text_id'], r['family_id'], r['input_text'])]
    side = 'J1' if r['critical'] == j['J1_critical'] else 'J2' if r['critical'] == j['J2_critical'] else 'neither'
    cmp[side] += 1; by_dim.setdefault(r['dimension'], Counter())[side] += 1
    types[(r['dimension'], ' vs '.join(sorted([str(j['J1_critical']), str(j['J2_critical'])])), r['critical'])] += 1
    rows.append({'a_unit': r['a_unit'], 'text': r['text'], 'dimension': r['dimension'], 'J1': j['J1_critical'],
                 'J2': j['J2_critical'], 'arbiter': r['critical'], 'side': side, 'rationale': r['rationale']})
res = {'n_units': len(out), 'arbiter_equals': dict(cmp), 'by_dimension': {k: dict(v) for k, v in by_dim.items()},
       'disagreement_types': [{'dimension': k[0], 'J1_J2_pair': k[1], 'arbiter': k[2], 'n_units': v}
                              for k, v in sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))],
       'arbiter_sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
(D / 'agreement.json').write_text(json.dumps(res, indent=1))
with (D / 'unit_comparison.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(json.dumps({k: res[k] for k in ('n_units', 'arbiter_equals', 'by_dimension', 'arbiter_sha256')}, indent=1))
for t in res['disagreement_types']: print(t)

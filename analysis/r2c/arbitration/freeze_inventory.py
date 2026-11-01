"""Freeze the W-C (runs/r2c1) critical-arbitration inventory BEFORE any label is decided.

Reads only keys from runs/r2c1/judgments.jsonl (needs_arbiter rows) and counts of fallback
rows in runs/r2c1/scored.parquet. Prints no J1/J2 label, reference value, model or arm.
Production extraction unit = judge.py A-unit (text_id, dimension, critical_options).
Writes analysis/r2c/arbiter_inventory.json. Refuses to overwrite an existing inventory.
"""
import hashlib, json, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'analysis/r2c/arbiter_inventory.json'
if OUT.exists():
    sys.exit(f'{OUT} exists; inventory is frozen')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
J = ROOT / 'runs/r2c1/judgments.jsonl'; S = ROOT / 'runs/r2c1/scored.parquet'
junits = []
for l in J.open():
    j = json.loads(l)
    if j.get('needs_arbiter'):
        junits.append({k: j[k] for k in ('text_id', 'family_id', 'input_text', 'dimension')} |
                      {'critical_options': j['critical_options']})
sc = pd.read_parquet(S, columns=['text_id', 'family_id', 'input_text', 'critical_source'])
fb = sc[sc.critical_source.isin(['J1', 'J2'])]
rows_per = fb.groupby(['text_id', 'family_id', 'input_text']).size().to_dict()
for u in junits:
    u['n_fallback_scored_rows'] = int(rows_per.get((u['text_id'], u['family_id'], u['input_text']), 0))
assert set(rows_per) == {(u['text_id'], u['family_id'], u['input_text']) for u in junits}
aunits = {}
for u in junits:
    ak = f"{u['text_id']}|{u['dimension']}|{'/'.join(u['critical_options'])}"
    u['a_unit'] = ak
    aunits.setdefault(ak, {'a_unit': ak, 'text_id': u['text_id'], 'dimension': u['dimension'],
                           'critical_options': u['critical_options'], 'n_junits': 0, 'n_fallback_scored_rows': 0})
    aunits[ak]['n_junits'] += 1; aunits[ak]['n_fallback_scored_rows'] += u['n_fallback_scored_rows']
junits.sort(key=lambda u: (u['a_unit'], u['family_id'], u['input_text']))
alist = sorted(aunits.values(), key=lambda a: a['a_unit'])
# blind presentation order: sha256 of a_unit (not family/model/channel order)
for a in alist:
    a['blind_order_key'] = hashlib.sha256(a['a_unit'].encode()).hexdigest()
canon = json.dumps({'a_units': alist, 'j_units': junits}, sort_keys=True, ensure_ascii=False).encode()
inv = {'recorded_note': 'Frozen before any arbiter label was decided (c2 decision ACTION 2).',
       'source_files': {'runs/r2c1/judgments.jsonl': sha(J), 'runs/r2c1/scored.parquet': sha(S)},
       'production_unit': 'judge.py A-unit = (text_id, critical dimension, critical_options); critical extraction is output-only',
       'counts': {'fallback_scored_rows': int(len(fb)), 'j_units': len(junits), 'a_units': len(alist)},
       'inventory_sha256': hashlib.sha256(canon).hexdigest(),
       'a_units': alist, 'j_units': junits}
OUT.write_text(json.dumps(inv, indent=1, ensure_ascii=False))
print(inv['counts'], inv['inventory_sha256'])

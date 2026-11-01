"""Blind arbiter view: for each frozen A-unit print ONLY output text, the production critical
question (src/judge.py CRITICAL_Q) and its options. No input, reference, family, model, arm,
J1/J2 label or evidence is printed. Order = sha256(a_unit) (arbiter_inventory.json).
Usage: python analysis/r2c/arbitration/blind_view.py [--dim polarity|speech_act|politeness]
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from judge import critical_question
inv = json.loads((ROOT / 'analysis/r2c/arbiter_inventory.json').read_text())
dim = sys.argv[sys.argv.index('--dim') + 1] if '--dim' in sys.argv else None
text = {}
for l in (ROOT / 'runs/r2c1/judgments.jsonl').open():
    j = json.loads(l)
    if j.get('needs_arbiter'):
        text[j['text_id']] = j['text']          # only the output string is retained
units = sorted(inv['a_units'], key=lambda a: a['blind_order_key'])
shown = set()
for a in units:
    if dim and a['dimension'] != dim: continue
    q = critical_question(a['dimension'], a['critical_options'])
    if a['dimension'] not in shown:
        print(f"=== {a['dimension']}: {q}\n    options: {a['critical_options']}"); shown.add(a['dimension'])
    print(f"[{a['blind_order_key'][:8]}] {text[a['text_id']]}")

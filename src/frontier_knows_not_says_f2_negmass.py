"""F2 S1: negation mass from stored greedy top-20 logprobs (E-cap4, both models). Rule: PLAN.md 'Follow-up F2'. CPU only.
Writes analysis/frontier/knows_not_says/followup/negmass_<alias>.csv"""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "analysis/frontier/knows_not_says/followup"; OUT.mkdir(exist_ok=True, parents=True)
NEGT = re.compile(r"^(?:not|no|never|none|nothing|nobody|nowhere|neither|nor|without|cannot|don|doesn|didn|won|isn|aren|wasn|weren|couldn|wouldn|shouldn|haven|hasn|hadn|can't|cant|dont|doesnt|didnt|wont|isnt|arent)$|n't$|n’t$|^'t$|^’t$")
def isneg(tok): return bool(NEGT.search(tok.strip().lower().replace("’", "'")))
for key, alias in (("qwen", "qwen2.5-7b"), ("llama", "llama3.1-8b")):
    rows = []
    for l in open(ROOT / f"runs/frontier_knows_not_says_stage1/{key}/gens.jsonl"):
        r = json.loads(l)
        if r["k"] >= 0 or not r["top"]: continue
        m = [sum(np.exp(lp) for t, lp in pos if isneg(t)) for pos in r["top"][:12]]
        m = np.clip(np.array(m), 0, 1)
        rows.append(dict(input=r["input"], negmass=float(1 - np.prod(1 - m)), negmass_max=float(m.max()), m1=float(m[0]) if len(m) else 0.0, greedy_text=r["text"]))
    pd.DataFrame(rows).to_csv(OUT / f"negmass_{alias}.csv", index=False); print(alias, len(rows))

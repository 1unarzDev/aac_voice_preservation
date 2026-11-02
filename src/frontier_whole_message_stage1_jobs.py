"""Stage 1 job builder + runner (calls M1)."""
import asyncio, hashlib, json, re, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import frontier_whole_message_m1 as m1
D = m1.D
it = pd.read_csv(ROOT / "analysis/intent_check/items.csv", keep_default_na=False)
it["r"] = [a if v == "A" else b for a, b, v in zip(it.version_A, it.version_B, it.intended_variant)]
slp = pd.read_csv(ROOT / "expert_package/slp_key.csv", keep_default_na=False)
def kw(x):
    return " ".join(re.sub(r"\[[^\]]+\]", " ", re.sub(r"^Keywords:\s*", "", x)).split())
h = lambda s: hashlib.sha256(("wm-gate|" + s).encode()).hexdigest()
gate = it.assign(_h=it.item_id.map(h)).sort_values("_h").head(100).reset_index(drop=True)
gate["r_other"] = gate.r.shift(-1).fillna(gate.r.iloc[0])
jobs = []
for _, r in it.iterrows():
    jobs += [("ref", r.input_text, r.text, r.r), ("free", r.input_text, r.text, None)]
for _, r in slp.iterrows():
    jobs.append(("free", r.input_text, r.text, None))
for _, r in gate.iterrows():
    jobs += [("ref", r.input_text, r.r, r.r), ("ref", r.input_text, r.r_other, r.r), ("free", r.input_text, kw(r.input_text), None)]
if __name__ == "__main__":
    asyncio.run(m1.run(jobs, conc=3))
    print("DONE")

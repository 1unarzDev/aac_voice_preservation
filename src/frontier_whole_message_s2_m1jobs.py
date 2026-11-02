import asyncio, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import frontier_whole_message_m1 as m1
d = pd.read_csv(ROOT / "runs/frontier_whole_message_s2/inputs.csv", keep_default_na=False)
items = {}
import json
for l in open(ROOT / "annotation/written/hw_candidates.jsonl"):
    o = json.loads(l); items[o["family_id"]] = o
def jobs():
    J = []
    for _, r in d.iterrows():
        ref = items[r.family_id]["variants"][r.variant]["source"]
        J += [("free", r.input_text, r.text, None), ("ref", r.input_text, r.text, ref)]
    return J
if __name__ == "__main__":
    asyncio.run(m1.run(jobs(), conc=3)); print("DONE")

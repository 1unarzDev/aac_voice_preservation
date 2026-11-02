"""E1 (T1 legend test): items + requests for the three-arm bare-channel test.

Arms (all on the bare channel, P0 wording):  a = P0 (legend), b = P0n (no legend), c = P0m (legend + "markers may be missing").
Families: hw1 polarity (data/items/hw.jsonl, 104) + W-C polarity (data/items/r2_c1.jsonl, 80). Arm a is also built un-salted
(= the cached original hw1 / r2c1 draw, free) and every arm is built with namespaces d1,d2 (fresh draws, same cache discipline as expB).
    python src/build_legend_requests.py
Writes data/items_ext/legend_items.jsonl (copies, same family_ids; kept OUT of data/items so no other analysis sees them)
and runs/requests/legend1.jsonl.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import build_requests as BR, models as M, prompts as P

fams = []
for pat, split in (("data/items/hw.jsonl", "hw"), ("data/items/r2_c1.jsonl", "r2")):
    f = [x for x in BR.load_families(str(ROOT / pat), split) if x["dimension"] == "polarity"]
    for x in f: x["source_set"] = "hw1" if split == "hw" else "WC"
    fams += f
print({s: sum(1 for x in fams if x["source_set"] == s) for s in ("hw1", "WC")})
out = ROOT / "data/items_ext/legend_items.jsonl"
with out.open("w") as fh:
    for x in fams:
        y = {k: v for k, v in x.items() if k != "_file"}; fh.write(json.dumps(y, ensure_ascii=False) + "\n")
models = M.UNDER_TEST
reqs = BR.build(fams, models, ["P0"], ["bare"], [None])                       # original draw (cached already)
reqs += BR.build(fams, models, ["P0", "P0n", "P0m"], ["bare"], ["d1", "d2"])  # 3 arms x 2 fresh draws
seen, uniq = set(), []
for r in reqs:
    if r["request_key"] in seen: continue
    seen.add(r["request_key"]); uniq.append(r)
rp = ROOT / "runs/requests/legend1.jsonl"
with rp.open("w") as fh:
    for r in uniq: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
cache = ROOT / "runs/cache"
hit = sum((cache / f"{r['request_key']}.json").exists() for r in uniq)
print(len(uniq), "unique requests;", hit, "already cached;", len(uniq) - hit, "to generate; models", models)

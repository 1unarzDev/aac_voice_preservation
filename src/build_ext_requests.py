"""Re-target existing request files to the larger local models (model-breadth extension).

Keeps every prompt/input/target byte-identical; only `model` changes and request_key is recomputed with
build_requests.request_key (same function). Source rows = the qwen2.5-7b rows of each file.

    python src/build_ext_requests.py --model qwen2.5-14b --model mistral-nemo-12b
Writes runs/requests/ext_<model>_{hw,legend1,hwctl}.jsonl
"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "src"))
import models as M
from build_requests import request_key
ap = argparse.ArgumentParser(); ap.add_argument("--model", action="append", required=True); a = ap.parse_args()
SRC = "qwen2.5-7b"
KEPT = {json.loads(l)["family_id"] for l in (ROOT / "data/items/hw.jsonl").read_text().splitlines() if l.strip()}  # 547 kept families
for name in a.model:
    spec = M.get(name)
    for f, tag in [("hw", "hw"), ("legend1", "legend1"), ("hwctl", "hwctl")]:
        rows = [json.loads(l) for l in (ROOT / f"runs/requests/{f}.jsonl").read_text().splitlines() if l.strip()]
        out = []
        for r in rows:
            if r["model"] != SRC: continue
            r = dict(r); r["model"] = name
            if tag == "hw":   # restrict to the 547 kept families (hw.jsonl holds all 574 candidates)
                r["targets"] = [t for t in r["targets"] if t["family_id"] in KEPT]
                if not r["targets"]: continue
                r["family_id"] = r["targets"][0]["family_id"] if r["family_id"] not in KEPT else r["family_id"]
            r["request_key"] = request_key(spec.model, r["prompt_id"], r["prompt"], r["temperature"], r["sample_idx"], r.get("namespace"))
            out.append(r)
        p = ROOT / f"runs/requests/ext_{name}_{tag}.jsonl"
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
        print(p.name, len(out), len({r["request_key"] for r in out}))

"""Render expert_package/slp/slp_rating.html from src/templates/slp_rating.tpl.html and expert_package/_build/slp_items.json.
No model calls. Run after src/build_expert_package.py:   python3 src/build_slp_tool.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "expert_package/_build/slp_items.json").read_text())
# the public data carries no arm labels: assert it before embedding
for it in data["task2"]:
    assert set(it) == {"id", "input", "text"}, it.keys()
blob = json.dumps({"task1": [{k: p[k] for k in ("type", "input", "text", "note")} for p in data["task1"]], "task2": data["task2"]},
                  ensure_ascii=False).replace("<", "\\u003c")
tpl = (ROOT / "src/templates/slp_rating.tpl.html").read_text()
(ROOT / "expert_package/slp/slp_rating.html").write_text(tpl.replace("__DATA__", blob))
print("wrote expert_package/slp/slp_rating.html", len(tpl) + len(blob), "bytes")

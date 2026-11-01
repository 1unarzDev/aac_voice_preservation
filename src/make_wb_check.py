"""Part 6 W-B corpus check: embed the 20 W-B audit messages in the offline two-pass tool.

Spec: round-2 protocol, W-B ("coders see the compressed input first ... humans
audit 20"). 0 generation, 0 judge calls.

Sample: the 20 messages already frozen in annotation/wb_audit.json by
`src/wb_admissibility.py audit` (random.Random(20261108).sample(panel, 20) over all 160
W-B messages, so random and enriched messages both occur). This script does not redraw.

Writes (private, never in the package):
  annotation/wb_check_key.csv   one row per (message, dimension): sample/stratum/focal dim,
                                primary panel status and both coders' admissible value sets
                                (values_1/2), strict (likely-only) status and value sets,
                                both coders' source values and the consensus source value
and embeds only item_id (opaque), the compressed keywords and the full message in
annotation_package/wb_corpus_check.html between the WB_ITEMS markers. No panel reading,
witness, status, sample type or focal dimension enters the package.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "annotation/wb_audit.json"
PANEL = ROOT / "annotation/wb_admissibility/panel.jsonl"
HTML = ROOT / "annotation_package/wb_corpus_check.html"
KEY = ROOT / "annotation/wb_check_key.csv"
DIMS = ["polarity", "speech_act", "agent", "certainty", "politeness"]


def main() -> int:
    audit = json.loads(AUDIT.read_text())
    panel = {p["wid"]: p for p in map(json.loads, PANEL.open())}
    assert list(audit["options"]) == DIMS
    rows, items = [], []
    for it in audit["items"]:
        p = panel[it["audit_id"]]
        assert p["pos_cap4"] == it["keywords_shown_first"] and p["text"] == it["full_source_reveal_after"]
        iid = "wb-" + hashlib.sha1(("wb-check|" + it["audit_id"]).encode()).hexdigest()[:6]
        items.append({"item_id": iid, "keywords": p["pos_cap4"], "message": p["text"]})
        for d in DIMS:
            e = p["dims"][d]
            assert e["status"] == it["dims"][d]["panel_status"]
            rows.append({
                "item_id": iid, "audit_id": it["audit_id"], "msg_id": p["id"], "sample": p["sample"],
                "stratum": p["stratum"], "focal_dim": p["focal_dim"], "dimension": d,
                "keywords": p["pos_cap4"], "message": p["text"],
                "status": e["status"], "values_1": "|".join(e["values_1"]), "values_2": "|".join(e["values_2"]),
                "status_strict": e.get("status_strict", ""),
                "values_likely_1": "|".join(e.get("values_likely_1", [])), "values_likely_2": "|".join(e.get("values_likely_2", [])),
                "src_1": e["src_1"], "src_2": e["src_2"], "source_value": e.get("source_value") or "",
            })
    items.sort(key=lambda x: x["item_id"]); rows.sort(key=lambda r: (r["item_id"], DIMS.index(r["dimension"])))
    with KEY.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    blob = json.dumps({"options": audit["options"], "items": items}, indent=0, ensure_ascii=False)
    html = HTML.read_text()
    html, n = re.subn(r"/\*WB_ITEMS_BEGIN\*/.*?/\*WB_ITEMS_END\*/",
                      lambda m: "/*WB_ITEMS_BEGIN*/" + blob + "/*WB_ITEMS_END*/", html, flags=re.S)
    assert n == 1, "markers not found"
    HTML.write_text(html)
    samp = {}
    for r in rows[::5]:
        samp[r["sample"]] = samp.get(r["sample"], 0) + 1
    print(f"{len(items)} messages ({samp}); key rows {len(rows)} -> {KEY.relative_to(ROOT)}")
    for x in items:
        print(x["item_id"], "|", x["keywords"], "|", x["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

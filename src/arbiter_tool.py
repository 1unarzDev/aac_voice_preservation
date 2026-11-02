"""Blind arbiter tooling for any run (generalises analysis/r2c/arbitration/*; same procedure, D-016).

    python src/arbiter_tool.py freeze --run legend1       # inventory of needs_arbiter A-units -> runs/<run>/arbiter_inventory.json
    python src/arbiter_tool.py view   --run legend1 [--start N --n M]   # prints ONLY output text + production critical question + options
    python src/arbiter_tool.py write  --run legend1 --decisions runs/legend1/arbiter_decisions.tsv   # key<TAB>critical<TAB>rationale
Then write the arbiter file; only after writing does `write` compare with J1/J2 (agreement report).
The view never shows input, family, model, arm, channel, J1/J2 labels or the reference. Order = sha256(a_unit).
"""
import argparse, csv, hashlib, json, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from judge import critical_question  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--run", required=True)
ap.add_argument("--decisions"); ap.add_argument("--start", type=int, default=0); ap.add_argument("--n", type=int, default=10**9)
ap.add_argument("--model", default="claude-sonnet-5-5")
a = ap.parse_args()
run = ROOT / "runs" / a.run; inv_p = run / "arbiter_inventory.json"


def judgments():
    return [json.loads(l) for l in (run / "judgments.jsonl").open() if l.strip()]


def opts(j):
    o = j["critical_options"]
    if isinstance(o, str):
        import ast; o = ast.literal_eval(o)
    return list(o)


if a.cmd == "freeze":
    ju, au = [], {}
    for j in judgments():
        if not j.get("needs_arbiter"): continue
        o = opts(j); key = f"{j['text_id']}|{j['dimension']}|{'/'.join(o)}"
        ju.append({"text_id": j["text_id"], "family_id": j["family_id"], "input_text": j["input_text"], "dimension": j["dimension"],
                   "critical_options": o, "a_unit": key})
        au.setdefault(key, {"a_unit": key, "text_id": j["text_id"], "dimension": j["dimension"], "critical_options": o,
                            "blind_order_key": hashlib.sha256(key.encode()).hexdigest()})
    inv = {"a_units": sorted(au.values(), key=lambda x: x["blind_order_key"]), "j_units": ju}
    inv["inventory_sha256"] = hashlib.sha256(json.dumps({"a_units": inv["a_units"], "j_units": inv["j_units"]}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    inv_p.write_text(json.dumps(inv, indent=1, ensure_ascii=False))
    print(len(inv["a_units"]), "A-units,", len(ju), "J-units; inventory sha256", inv["inventory_sha256"])
elif a.cmd == "view":
    inv = json.loads(inv_p.read_text()); text = {j["text_id"]: j["text"] for j in judgments() if j.get("needs_arbiter")}
    shown = set()
    for u in inv["a_units"][a.start:a.start + a.n]:
        q = critical_question(u["dimension"], u["critical_options"])
        if u["dimension"] not in shown:
            print(f"=== {u['dimension']}: {q}\n    options: {u['critical_options']}"); shown.add(u["dimension"])
        print(f"[{u['blind_order_key'][:8]}] {text[u['text_id']]}")
elif a.cmd == "write":
    inv = json.loads(inv_p.read_text())
    dec = {}
    for r in csv.reader(open(a.decisions), delimiter="\t"):
        if r and not r[0].startswith("#"): dec[r[0]] = (r[1], r[2] if len(r) > 2 else "")
    amap = {}
    for u in inv["a_units"]:
        hits = [k for k in dec if u["blind_order_key"].startswith(k)]
        assert len(hits) == 1, (u["a_unit"], hits)
        crit, why = dec[hits[0]]; assert crit in u["critical_options"], (hits, crit)
        amap[u["a_unit"]] = (crit, why)
    assert len(amap) == len(dec), (len(amap), len(dec))
    J = {(j["text_id"], j["family_id"], j["input_text"]): j for j in judgments() if j.get("needs_arbiter")}
    out = []
    for u in inv["j_units"]:
        crit, why = amap[u["a_unit"]]; j = J[(u["text_id"], u["family_id"], u["input_text"])]
        out.append({"text_id": u["text_id"], "family_id": u["family_id"], "input_text": u["input_text"], "critical": crit, "rationale": why,
                    "arbiter_model": a.model, "text": j["text"], "dimension": u["dimension"], "a_unit": u["a_unit"],
                    "arbitration_view": "blind: output text + production critical question/options only", "inventory_sha256": inv["inventory_sha256"]})
    p = run / "arbiter.jsonl"; p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
    cmp = Counter(); types = Counter()
    for r in out:
        j = J[(r["text_id"], r["family_id"], r["input_text"])]
        side = "J1" if r["critical"] == j["J1_critical"] else "J2" if r["critical"] == j["J2_critical"] else "neither"
        cmp[side] += 1; types[(r["dimension"], " vs ".join(sorted(map(str, [j["J1_critical"], j["J2_critical"]]))), r["critical"])] += 1
    res = {"n_units": len(out), "arbiter_equals": dict(cmp), "arbiter_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
           "types": [{"dimension": k[0], "J1_J2": k[1], "arbiter": k[2], "n": v} for k, v in types.most_common()]}
    (run / "arbiter_agreement.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))

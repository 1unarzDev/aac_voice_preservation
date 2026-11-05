"""Regression checks drawn from the AAC-user consultants' flagged flaws (Sec. on consultant review).
Reads runs/hw1/outputs.jsonl (stored, no model calls); writes paper/se4all/consultant_checks.json.
Check T1 (event leak): an input with the [TELL] (statement) chip, whose keywords do not contain a form of 'tell',
must not be realised with a reporting verb (tell/tells/told/telling).  Rate = outputs that do.  Same-source control: the
bare channel for the same source variant and model (no chip shown) -- a lexical rate, not a judge verdict."""
import json, re, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
rows = {}
for l in open(ROOT / "runs/hw1/outputs.jsonl"):
    r = json.loads(l)
    rows[(r["family_id"], r["variant"], r["channel"], r["model"], r["sample_idx"], r["suggestion_idx"])] = r
TELL = re.compile(r"\b(tell|tells|told|telling)\b", re.I)
out = {"n_tell_inputs": 0, "n_leak": 0, "by_model": {}, "n_ctrl": 0, "n_ctrl_leak": 0, "fam_leak": set(), "fam": set()}
bm = collections.defaultdict(lambda: [0, 0])
for k, r in rows.items():
    inp = r["input_text"]
    if "[TELL]" not in inp:
        continue
    kw = re.sub(r"\[[A-Z]+\]", "", inp.replace("Keywords:", ""))
    if TELL.search(kw):
        continue
    out["n_tell_inputs"] += 1
    leak = bool(TELL.search(r["text"]))
    out["n_leak"] += leak
    bm[r["model"]][0] += 1
    bm[r["model"]][1] += leak
    out["fam"].add(r["family_id"])
    if leak:
        out["fam_leak"].add(r["family_id"])
    # control: same family/variant/model, bare channel
    c = rows.get((r["family_id"], r["variant"], "bare", r["model"], r["sample_idx"], r["suggestion_idx"]))
    if c is not None:
        out["n_ctrl"] += 1
        out["n_ctrl_leak"] += bool(TELL.search(c["text"]))
out["by_model"] = {m: {"n": v[0], "leak": v[1]} for m, v in bm.items()}
out["n_fam"] = len(out.pop("fam"))
out["n_fam_leak"] = len(out.pop("fam_leak"))
json.dump(out, open(ROOT / "paper/se4all/consultant_checks.json", "w"), indent=1)
print(json.dumps(out, indent=1))

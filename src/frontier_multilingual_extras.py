import sys, json, collections, csv
from pathlib import Path
from scipy.stats import beta
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
S = json.load(open(OUT / "summary.json"))
def cp(k, n):
    lo = 0.0 if k == 0 else beta.ppf(0.025, k, n - k + 1); hi = 1.0 if k == n else beta.ppf(0.975, k + 1, n - k)
    return [round(float(lo), 3), round(float(hi), 3)]
ex = {"H1_exact_ci": {}, "polarity_LL": {}, "register_tables": []}
for lang in LANGS:
    b = S["register"][f"bare|pooled|{lang}"]; n = b["T"] + b["V"] + b["mixed"]
    ex["H1_exact_ci"][lang] = {"committed": b["T"] + b["V"], "of": n, "clopper_pearson": cp(b["T"] + b["V"], n)}
pol = []
for m in S["models"]:
    pol += jl(OUT / f"pol_labels_{m}.jsonl")
ar = {}
for l in jl(OUT / "pol_final.jsonl"):
    pass
for r in jl(OUT / "pol_final.jsonl"):
    if r["arm"] == "bare" and r["label"]:
        ar.setdefault((r["lang"], r["pset"]), collections.Counter())[r["label"]] += 1
ex["polarity_LL"] = {f"{l}|{p}": dict(c) for (l, p), c in sorted(ar.items())}
rows = []
for k, v in S["register"].items():
    rows.append({"key": k, **{a: (json.dumps(b) if isinstance(b, list) else b) for a, b in v.items()}})
cols = sorted({c for r in rows for c in r}, key=lambda c: (c != "key", c))
with open(OUT / "register_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
rows = [{"key": k, **{a: (json.dumps(b) if isinstance(b, (list, dict)) else b) for a, b in v.items()}} for k, v in S["polarity"].items()]
cols = sorted({c for r in rows for c in r}, key=lambda c: (c != "key", c))
with open(OUT / "polarity_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
json.dump(ex, open(OUT / "extras.json", "w"), indent=1)
print(json.dumps(ex, indent=1))

"""Part 5 W-C source check: freeze the hash-ordered 20-family sample and embed it in the tool.

Spec: round-2 protocol, W-C ("humans spot-check 20"). 0 generation, 0 judge calls.

Eligible: all W-C families in data/items/r2_c1.jsonl + r2_c2.jsonl except the two
primary exclusions (r2act-078, r2act-079): 80 polarity, 78 speech act, 80 politeness.

Selection (frozen, declared before any human label):
  quota      polarity 7, speech_act 7, politeness 6 (= 20)
  order      within each stratum, ascending sha1("wc-source-check-2026|" + family_id)
  pass 1     walk the order, accept a family while its stratum quota is open and its
             cluster_id (seed/construction cluster) is not already in the sample
  pass 2     only if a quota is still open: relax the cluster constraint
Inclusion probabilities are estimated by rerunning the identical rule under 4000 random
salts (Monte Carlo); the realised sample uses the fixed salt. Without the cluster rule
pi would be quota/N within the stratum.

Writes (private, never in the package):
  annotation/wc_source_check_key.csv     20 rows: item_id, family, authored values A/B,
                                         second-verifier values and bare_supports_both,
                                         construction, cluster, rank, pi_mc
  annotation/wc_source_check_sample.json  rule, counts, hashes of the item files
and embeds the blind items (item_id, dimension, options, context, A/B sentences, bare
keywords, noncritical word; no authored value, contrast, template, notes or construction)
in annotation_package/wc_source_check.html between the WC_ITEMS markers.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEM_FILES = [ROOT / "data/items/r2_c1.jsonl", ROOT / "data/items/r2_c2.jsonl"]
CODEX = ROOT / "analysis/item_verification/verifier_r2.csv"  # second verifier's item labels
HTML = ROOT / "annotation_package/wc_source_check.html"
KEY = ROOT / "annotation/wc_source_check_key.csv"
SUMMARY = ROOT / "annotation/wc_source_check_sample.json"
SALT = "wc-source-check-2026"
QUOTA = {"polarity": 7, "speech_act": 7, "politeness": 6}
EXCLUDE = {"r2act-078", "r2act-079"}   # frozen primary exclusions
MC = 4000


def sha(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def load():
    fams = [json.loads(l) for f in ITEM_FILES for l in f.open() if l.strip()]
    elig = [f for f in fams if f["family_id"] not in EXCLUDE]
    assert all(not f.get("primary_exclude") for f in elig), "unexpected primary_exclude"
    return fams, elig


def select(elig: list[dict], salt: str) -> list[str]:
    picked, clusters = [], set()
    for relax in (False, True):
        for dim, q in QUOTA.items():
            pool = sorted((f for f in elig if f["dimension"] == dim), key=lambda f: sha(salt + "|" + f["family_id"]))
            have = sum(1 for p in picked if p["dimension"] == dim)
            for f in pool:
                if have >= q:
                    break
                if f in picked or (not relax and f["cluster_id"] in clusters):
                    continue
                picked.append(f); clusters.add(f["cluster_id"]); have += 1
    return [f["family_id"] for f in picked]


def main() -> int:
    fams, elig = load()
    chosen = select(elig, SALT)
    assert len(chosen) == 20 and len(set(chosen)) == 20
    rnd = random.Random(20261101)
    hits = Counter()
    for _ in range(MC):
        hits.update(select(elig, "mc-%016x" % rnd.getrandbits(64)))
    codex = {}
    for r in csv.DictReader(CODEX.open(newline="", encoding="utf-8")):
        codex[(r["family_id"], r["variant"])] = r
    by = {f["family_id"]: f for f in elig}
    n_str = Counter(f["dimension"] for f in elig)
    rows, items = [], []
    for fid in chosen:
        f = by[fid]
        A, B = f["variants"]["A"], f["variants"]["B"]
        cA, cB = codex.get((fid, "A"), {}), codex.get((fid, "B"), {})
        iid = "wc-" + sha("wc-item|" + fid)[:6]
        pool = sorted((x for x in elig if x["dimension"] == f["dimension"]), key=lambda x: sha(SALT + "|" + x["family_id"]))
        rows.append({
            "item_id": iid, "family_id": fid, "dimension": f["dimension"],
            "source_A": A["source"], "source_B": B["source"], "bare": f["bare"], "noncritical": f["noncritical"],
            "options": json.dumps(f["critical_options"]),
            "authored_A": A["critical_value"], "authored_B": B["critical_value"],
            "codex_A": cA.get("your_critical", ""), "codex_B": cB.get("your_critical", ""),
            "codex_bare_supports_both_A": cA.get("bare_supports_both", ""),
            "codex_bare_supports_both_B": cB.get("bare_supports_both", ""),
            "codex_comment": " | ".join(x for x in (cA.get("comment", ""), cB.get("comment", "")) if x),
            "construction": f["construction"], "contrast": f.get("contrast", ""), "cluster_id": f["cluster_id"],
            "stratum_rank": pool.index(f) + 1, "stratum_eligible": n_str[f["dimension"]],
            "pi_mc": round(hits[fid] / MC, 4), "pi_srs": round(QUOTA[f["dimension"]] / n_str[f["dimension"]], 4),
        })
        items.append({"item_id": iid, "dimension": f["dimension"], "options": f["critical_options"],
                      "context": f.get("context"), "A": A["source"], "B": B["source"],
                      "bare": f["bare"], "noncritical": f["noncritical"]})
    rows.sort(key=lambda r: r["item_id"]); items.sort(key=lambda r: r["item_id"])
    KEY.parent.mkdir(parents=True, exist_ok=True)
    with KEY.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summ = {
        "rule": __doc__.split("Selection (frozen, declared before any human label):")[1].split("Writes")[0].strip(),
        "salt": SALT, "quota": QUOTA, "excluded": sorted(EXCLUDE), "eligible_by_stratum": dict(n_str),
        "selected": chosen,
        "selected_by_construction": dict(Counter(by[x]["construction"] for x in chosen)),
        "distinct_clusters": len({by[x]["cluster_id"] for x in chosen}),
        "codex_rows_found": sum(1 for r in rows if r["codex_A"] and r["codex_B"]),
        "item_file_sha1": {str(p.relative_to(ROOT)): hashlib.sha1(p.read_bytes()).hexdigest() for p in ITEM_FILES},
        "mc_salts": MC,
    }
    SUMMARY.write_text(json.dumps(summ, indent=1, ensure_ascii=False) + "\n")
    blob = json.dumps(items, indent=0, ensure_ascii=False)
    html = HTML.read_text()
    html, n = re.subn(r"/\*WC_ITEMS_BEGIN\*/.*?/\*WC_ITEMS_END\*/",
                      lambda m: "/*WC_ITEMS_BEGIN*/" + blob + "/*WC_ITEMS_END*/", html, flags=re.S)
    assert n == 1, "markers not found"
    HTML.write_text(html)
    print(json.dumps({k: summ[k] for k in ("eligible_by_stratum", "selected_by_construction", "distinct_clusters", "codex_rows_found")}))
    for r in rows:
        print(r["item_id"], r["family_id"], r["construction"], r["pi_mc"], "|", r["source_A"], "|", r["source_B"], "|", r["bare"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Pair-scoring arm (A7/A16): forced-decoding log-probabilities of the affirmative and the negated variant sentence (and placebo
paraphrases) given the bare keywords, P0n prompt. Needs a llama-server on <port> (GPU lock held by caller).
usage: python src/frontier_knows_not_says_pairs.py <port> <alias> <name>   -> runs/frontier_knows_not_says_stage1/<name>/pairs_raw.json"""
import json, sys, time
from pathlib import Path
import httpx
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import prompts as P, frontier_knows_not_says_lib as L
PORT, ALIAS, NAME = sys.argv[1], sys.argv[2], sys.argv[3]
B = f"http://127.0.0.1:{PORT}"; cli = httpx.Client(timeout=300)
OUT = ROOT / "runs/frontier_knows_not_says_stage1" / NAME; OUT.mkdir(parents=True, exist_ok=True)
pilot = json.load(open(ROOT / "analysis/frontier/knows_not_says/pilot/pilot_items.json")); excl = {p["family_id"] for p in pilot["e_pairs"]}
def load(path, dset):
    out = []
    for l in open(ROOT / path):
        h = json.loads(l)
        if h["dimension"] != "polarity" or h["family_id"] in excl: continue
        vs = h["variants"]; neg = [k for k, v in vs.items() if v["critical_value"] == "negated"]; aff = [k for k, v in vs.items() if v["critical_value"] == "affirmative"]
        if len(neg) != 1 or len(aff) != 1: continue
        out.append(dict(dataset=dset, family_id=h["family_id"], bare=h["bare"], neg=vs[neg[0]]["source"], aff=vs[aff[0]]["source"]))
    return out
pairs = load("data/items/hw.jsonl", "hw1") + load("data/items/r2_c1.jsonl", "wc")
def tmpl(c): return cli.post(B + "/apply-template", json={"messages": [{"role": "user", "content": c}]}).json()["prompt"]
def tok(t, sp=False): return cli.post(B + "/tokenize", json={"content": t, "add_special": sp, "parse_special": True}).json()["tokens"]
def score(pids, cids, n_probs=1000):
    ids = list(pids); lps = []; imp = 0
    for c in cids:
        r = cli.post(B + "/completion", json={"prompt": ids, "n_predict": 1, "n_probs": n_probs, "temperature": 1.0, "top_k": 0, "top_p": 1.0,
                     "min_p": 0.0, "cache_prompt": True, "post_sampling_probs": False}).json()
        top = r["completion_probabilities"][0]["top_logprobs"]; d = {t["id"]: t["logprob"] for t in top}
        if c in d: lps.append(d[c])
        else: lps.append(min(d.values())); imp += 1       # upper bound on the true logprob
        ids.append(c)
    return lps, imp
rows = []; t0 = time.time()
for p in pairs:
    pids = tok(tmpl(P.render("P0n", "Keywords: " + p["bare"])), True)
    cands = {"aff": p["aff"], "neg": p["neg"], "aff_nop": L.drop_final_period(p["aff"]), "neg_nop": L.drop_final_period(p["neg"]), "neg_tog": L.contraction_toggle(p["neg"])}
    row = dict(p)
    for k, s in cands.items():
        if s is None: continue
        ids = tok(s); lp, imp = score(pids, ids); row[k] = dict(text=s, ids=ids, lp=lp, imputed=imp)
    rows.append(row)
json.dump(rows, open(OUT / "pairs_raw.json", "w")); print(f"{len(rows)} pairs in {time.time()-t0:.0f}s")

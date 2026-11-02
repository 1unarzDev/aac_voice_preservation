"""Stage 1 generation for knows_not_says: for every unique P0n input of E-human and E-cap4 (pilot messages excluded) plus two
content-free inputs: 1 greedy (T=0, top-20 logprobs) + K=16 samples at T=1 with the sampler explicitly UNTRUNCATED
(top_k=0, top_p=1, min_p=0). All tokens' logprobs stored. Resumable (appends to gens.jsonl).
usage (GPU lock must be held by the caller): python src/frontier_knows_not_says_stage1.py <port> <alias> <outdir-name>"""
import json, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import prompts as P, frontier_knows_not_says_lib as L
PORT, ALIAS, NAME = sys.argv[1], sys.argv[2], sys.argv[3]
K = 16; UNTRUNC = dict(temperature=1.0, top_k=0, top_p=1.0, min_p=0.0)
OUT = ROOT / "runs/frontier_knows_not_says_stage1" / NAME; OUT.mkdir(parents=True, exist_ok=True)
pilot = json.load(open(ROOT / "analysis/frontier/knows_not_says/pilot/pilot_items.json"))
excl = {e["elic_item_id"] for e in pilot["e_human"]}
U = L.build_units(excl)
pair_inputs = set()
for path in ("data/items/hw.jsonl", "data/items/r2_c1.jsonl"):
    for l in open(ROOT / path):
        h = json.loads(l)
        if h["dimension"] == "polarity": pair_inputs.add("Keywords: " + h["bare"])
inputs = sorted(set(U.input) | {"Keywords: N/A", "Keywords: "} | pair_inputs)
done = set()
f = OUT / "gens.jsonl"
if f.exists():
    for l in open(f):
        try: r = json.loads(l); done.add((r["input"], r["k"]))
        except Exception: pass
jobs = [(i, k) for i in inputs for k in [-1] + list(range(K)) if (i, k) not in done]
print(f"{ALIAS}: {len(inputs)} unique inputs, {len(jobs)} requests to do", flush=True)
cli = httpx.Client(timeout=300, limits=httpx.Limits(max_connections=8)); lock = threading.Lock(); fh = open(f, "a"); t0 = time.time(); n = [0, 0]
def one(job):
    inp, k = job
    samp = dict(temperature=0.0) if k < 0 else UNTRUNC
    b = {"model": ALIAS, "messages": [{"role": "user", "content": P.render("P0n", inp)}], "max_tokens": 96, "logprobs": True,
         "top_logprobs": 20 if k < 0 else 1, **samp}
    for attempt in range(3):
        try:
            r = cli.post(f"http://127.0.0.1:{PORT}/v1/chat/completions", json=b); r.raise_for_status(); j = r.json(); ch = j["choices"][0]
            lp = ch["logprobs"]["content"]
            rec = dict(input=inp, k=k, text=ch["message"]["content"], finish=ch["finish_reason"], toks=[x["token"] for x in lp],
                       lp=[round(x["logprob"], 5) for x in lp],
                       top=([[[t["token"], round(t["logprob"], 4)] for t in x["top_logprobs"]] for x in lp] if k < 0 else None))
            with lock: fh.write(json.dumps(rec) + "\n"); n[0] += 1
            if n[0] % 500 == 0:
                fh.flush(); print(f"{time.strftime('%H:%M:%S')} {n[0]}/{len(jobs)} errs={n[1]} {n[0]/(time.time()-t0):.1f} req/s", flush=True)
            return
        except Exception as e: err = str(e)[:100]; time.sleep(2)
    with lock: n[1] += 1
    print("ERR", inp, k, err, flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(one, jobs))
fh.flush(); fh.close(); print(f"done {n[0]} ok, {n[1]} errors, {time.time()-t0:.0f}s", flush=True)

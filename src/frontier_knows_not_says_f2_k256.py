"""F2 S2 (K=256 sampling) and S3 (verbalised confidence). GPU lock must be held by the caller for local models.
  python src/frontier_knows_not_says_f2_k256.py k256 <port> <alias>
  python src/frontier_knows_not_says_f2_k256.py verbal <port|api> <alias>
Units: PLAN.md 'Follow-up F2'. Resumable. Outputs runs/frontier_knows_not_says_f2/<alias>/{k256,verbal}.jsonl"""
import json, sys, re, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, httpx
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "src"))
import prompts as P, frontier_knows_not_says_lib as L, models as M
mode, PORT, ALIAS = sys.argv[1:4]; K = 256; SEED = 20261103
OUT = ROOT / "runs/frontier_knows_not_says_f2" / ALIAS; OUT.mkdir(parents=True, exist_ok=True)
pilot = json.load(open(ROOT / "analysis/frontier/knows_not_says/pilot/pilot_items.json"))
U = L.build_units({e["elic_item_id"] for e in pilot["e_human"]}); C = U[(U.dataset == "cap4") & U.nocue_neg].reset_index(drop=True)
pos = C[C.neg]; neg = C[~C.neg]; rng = np.random.default_rng(SEED); negs = neg.iloc[np.sort(rng.choice(len(neg), 160, replace=False))]
S = C if mode == "verbal" else __import__("pandas").concat([pos, negs])
if mode == "k256": S[["item_id", "input", "neg", "w", "sample"]].assign(neg_weight=lambda d: np.where(d.neg, 1.0, len(neg) / 160)).to_csv(ROOT / "analysis/frontier/knows_not_says/followup/k256_units.csv", index=False)
inputs = sorted(set(S.input)); f = OUT / f"{mode}.jsonl"; done = set()
if f.exists():
    for l in open(f):
        try: r = json.loads(l); done.add((r["input"], r["k"]))
        except Exception: pass
UNTRUNC = dict(temperature=1.0, top_k=0, top_p=1.0, min_p=0.0)
VP = ("A person who cannot speak typed only these keywords on a communication device: \"{kw}\"\nThe device has to expand them into the full message the person meant.\n"
      "What is the probability, from 0 to 100, that the intended message contains a negation (for example not, no, never, n't)? Answer with only the number.")
jobs = [(i, k) for i in inputs for k in (range(K) if mode == "k256" else [0]) if (i, k) not in done]
print(f"{mode} {ALIAS}: {len(inputs)} inputs, {len(jobs)} requests", flush=True)
api = PORT == "api"; spec = M.get(ALIAS)
cli = httpx.Client(timeout=300, limits=httpx.Limits(max_connections=16)); lock = threading.Lock(); fh = open(f, "a"); t0 = time.time(); n = [0, 0]
def one(job):
    inp, k = job
    if mode == "k256": prompt = P.render("P0n", inp); b = {"model": ALIAS, "messages": [{"role": "user", "content": prompt}], "max_tokens": 40, **UNTRUNC}
    else:
        kw = inp.replace("Keywords:", "", 1).strip(); b = {"model": spec.model if api else ALIAS, "messages": [{"role": "user", "content": VP.format(kw=kw)}], "max_tokens": 8, "temperature": 0.0}
    url = (spec.base_url + "/chat/completions") if api else f"http://127.0.0.1:{PORT}/v1/chat/completions"; hd = M.headers(spec) if api else {}
    for attempt in range(4):
        try:
            r = cli.post(url, json=b, headers=hd); r.raise_for_status(); ch = r.json()["choices"][0]
            rec = dict(input=inp, k=k, text=ch["message"]["content"], finish=ch["finish_reason"])
            with lock: fh.write(json.dumps(rec) + "\n"); n[0] += 1
            if n[0] % 2000 == 0: fh.flush(); print(f"{time.strftime('%H:%M:%S')} {n[0]}/{len(jobs)} errs={n[1]} {n[0]/(time.time()-t0):.1f} req/s", flush=True)
            return
        except Exception as e: err = str(e)[:100]; time.sleep(2 + attempt * 3)
    with lock: n[1] += 1
    print("ERR", inp, k, err, flush=True)
conc = 3 if api else 8
with ThreadPoolExecutor(conc) as ex: list(ex.map(one, jobs))
fh.flush(); fh.close(); print(f"done {n[0]} ok, {n[1]} errors, {time.time()-t0:.0f}s", flush=True)

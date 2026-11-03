"""value_of_cue round 2, Stage 1 (GPU): model-internal signals per unit for ONE local model (server must be up, GPU lock held by caller).
Usage: python src/frontier_value_of_cue_s1gpu.py <port> <model_alias> [limit]
Writes runs/frontier_value_of_cue_s1/<model>.jsonl (resumable, one row per distinct input). See PLAN.md A2 R2-5."""
import json, math, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import prompts as P
PORT, MODEL = sys.argv[1], sys.argv[2]; LIM = int(sys.argv[3]) if len(sys.argv) > 3 else None
BASE = f"http://127.0.0.1:{PORT}"; K = 8; SEED = 20261102
OUT = ROOT / "runs/frontier_value_of_cue_s1"; OUT.mkdir(parents=True, exist_ok=True); fp = OUT / f"{MODEL}.jsonl"
PROBE = {"polarity": "contain a negation (not, no, never, n't)", "speech_act": "be a question or a request to someone rather than a plain statement",
         "politeness": "contain polite wording such as please or thank you"}
U = pd.read_parquet(ROOT / "analysis/frontier/value_of_cue/units.parquet")
E = {j["family_id"]: j for j in map(json.loads, open(ROOT / "data/items/elic.jsonl"))}
inputs = sorted({E[r.fam]["custom_channels"]["A"]["human_" + r.writer]["input"] for r in U.itertuples()})
if LIM: inputs = inputs[:LIM]
done = set()
if fp.exists():
    for l in fp.read_text().splitlines(): done.add(json.loads(l)["input"])
todo = [x for x in inputs if x not in done]; print(MODEL, "distinct inputs", len(inputs), "todo", len(todo), flush=True)
cli = httpx.Client(timeout=300, limits=httpx.Limits(max_connections=32)); lock = threading.Lock(); fh = fp.open("a")
def chat(content, max_tokens, lp=False, **kw):
    b = {"model": MODEL, "messages": [{"role": "user", "content": content}], "max_tokens": max_tokens, **kw}
    if lp: b.update(logprobs=True, top_logprobs=5 if max_tokens > 1 else 20)
    for a in range(4):
        try:
            r = cli.post(BASE + "/v1/chat/completions", json=b); r.raise_for_status(); return r.json()["choices"][0]
        except Exception as e: time.sleep(2 ** a)
    raise RuntimeError("chat failed")
def one(inp):
    kw = inp.replace("Keywords:", "", 1).strip(); p = P.render("P0", inp)
    g = chat(p, 96, lp=True, temperature=0.0, seed=SEED)
    toks = [{"t": c["token"], "lp": c["logprob"], "top": [(x["token"], x["logprob"]) for x in c["top_logprobs"]]} for c in g["logprobs"]["content"][:96]]
    samples = [chat(p, 64, temperature=1.0, top_k=0, top_p=1.0, min_p=0.0, seed=SEED + 1 + i)["message"]["content"] for i in range(K)]
    probe = {}
    for d, desc in PROBE.items():
        q = (f"An AAC user typed these keywords: {kw}\nCould the sentence they meant {desc}? Answer Yes or No.")
        c = chat(q, 1, lp=True, temperature=0.0); probe[d] = [(x["token"], x["logprob"]) for x in c["logprobs"]["content"][0]["top_logprobs"]]
    row = {"input": inp, "greedy_text": g["message"]["content"], "tokens": toks, "samples": samples, "probe": probe}
    with lock: fh.write(json.dumps(row) + "\n"); fh.flush()
t0 = time.time()
with ThreadPoolExecutor(8) as ex:
    for i, _ in enumerate(ex.map(one, todo)):
        if i % 100 == 0: print(i, round(time.time() - t0), "s", flush=True)
print("done", round(time.time() - t0), "s")

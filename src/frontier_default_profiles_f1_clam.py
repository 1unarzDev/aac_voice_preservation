"""F1 D4: CLAM-style generic clarification trigger. python src/frontier_default_profiles_f1_clam.py --model qwen2.5-7b --port 8091
One call per human keyword unit, few-shot yes/no, score = P(yes) from first-token logprobs. Output runs/frontier_default_profiles_clam/<model>.jsonl"""
import argparse, json, math, sys, time, concurrent.futures as cf
from pathlib import Path
import pandas as pd, httpx
ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ("A person who cannot speak types a few keywords on a communication device. The device must expand them into the full sentence the person meant.\n"
 "Sometimes the keywords leave out something that changes the meaning (for example whether the sentence is negated, whether it is a question or a request, or whether it is polite), and the device should ask the person before guessing.\n\n"
 "Keywords: \"coffee want\"\nDoes this need a clarifying question before it can be expanded faithfully? No\n\n"
 "Keywords: \"go store\"\nDoes this need a clarifying question before it can be expanded faithfully? Yes\n\n"
 "Keywords: \"you tired\"\nDoes this need a clarifying question before it can be expanded faithfully? Yes\n\n"
 "Keywords: \"please sit\"\nDoes this need a clarifying question before it can be expanded faithfully? No\n\n"
 "Keywords: \"{kw}\"\nDoes this need a clarifying question before it can be expanded faithfully? Answer with one word, Yes or No.")
def units():
    rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv")
    return [dict(unit=f"{r.item_id}|human_{r.annotator}", kw=str(r.keywords)) for r in rat.itertuples() if isinstance(r.keywords, str) and r.keywords.strip()]
def call(cli, model, kw):
    body = dict(model=model, messages=[{"role": "user", "content": TEMPLATE.format(kw=kw)}], max_tokens=1, temperature=0, logprobs=True, top_logprobs=20)
    for t in range(4):
        try:
            r = cli.post("/v1/chat/completions", json=body, timeout=120).json(); lp = {}
            for x in r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]:
                k = x["token"].strip().lower()
                if k in ("yes", "no"): lp[k] = max(lp.get(k, -99), x["logprob"])
            py, pn = math.exp(lp.get("yes", -30)), math.exp(lp.get("no", -30))
            return py / (py + pn) if py + pn > 1e-3 else None
        except Exception: time.sleep(1 + t)
    return None
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--port", type=int, required=True); ap.add_argument("--workers", type=int, default=4); a = ap.parse_args()
    out = ROOT / "runs/frontier_default_profiles_clam"; out.mkdir(exist_ok=True, parents=True); fn = out / f"{a.model}.jsonl"
    done = {j["unit"] for j in map(json.loads, open(fn))} if fn.exists() else set()
    jobs = [u for u in units() if u["unit"] not in done]; cli = httpx.Client(base_url=f"http://127.0.0.1:{a.port}"); t0 = time.time(); n = nulls = 0
    with open(fn, "a") as f, cf.ThreadPoolExecutor(a.workers) as ex:
        for u, p in zip(jobs, ex.map(lambda u: call(cli, a.model, u["kw"]), jobs)):
            f.write(json.dumps(dict(unit=u["unit"], kw=u["kw"], p_yes=p)) + "\n"); n += 1; nulls += p is None
            if n == 150 and nulls / n > .2: print("null rate too high", nulls / n); sys.exit(2)
            if n % 500 == 0: f.flush(); print(n, len(jobs), round(time.time() - t0), "s", flush=True)
    print("done", a.model, n, "nulls", nulls, round(time.time() - t0), "s")

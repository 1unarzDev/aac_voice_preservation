"""S1 forced-choice logprob probe.  python src/frontier_default_profiles_probe.py --model qwen2.5-7b --port 8091 [--limit N]
For every (keyword string, dimension) asks which of two readings is the intended message, in both option orders, and stores
P(non-default reading) from the first-token logprobs of 'A'/'B' (renormalised over the two). Output: runs/frontier_default_profiles_probe/<model>.jsonl"""
import argparse, json, math, sys, time, concurrent.futures as cf
from pathlib import Path
import pandas as pd, httpx
ROOT = Path(__file__).resolve().parents[1]
# (question about the NON-default reading, question about the DEFAULT reading); q = mean(P(yes|nondefault Q), 1 - P(yes|default Q)).
# Two framings in place of A/B letters: the first A/B pilot (qwen2.5-7b, 1,000 rows, discarded, never analysed) showed a position bias (always 'A') and ~65% unparseable first tokens.
OPT = {
 "polarity": ("Does the intended message contain a negation or a refusal (for example not, no, never, n't)?", "Is the intended message a plain affirmative one with no negation at all?"),
 "speech_act": ("Is the intended message a question or a request/command?", "Is the intended message a plain statement?"),
 "politeness": ("Is the intended message polite (it contains please, thank you, sorry, or softened wording)?", "Is the intended message plain, with no politeness markers?")}
TEMPLATE = ("A person who cannot speak typed only these keywords on a communication device: \"{kw}\"\n"
            "The device has to expand them into the full message the person meant.\n{q}\nAnswer with one word: Yes or No.")
def units():
    rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv"); msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv")
    U = [dict(unit=f"{r.item_id}|human_{r.annotator}", kw=str(r.keywords)) for r in rat.itertuples() if isinstance(r.keywords, str) and r.keywords.strip()]
    U += [dict(unit=f"{m.item_id}|pos_cap4", kw=str(m.pos_cap4)) for m in msg.itertuples()]
    return U
def call(cli, model, kw, dim, order):
    q = OPT[dim][order]
    body = dict(model=model, messages=[{"role": "user", "content": TEMPLATE.format(kw=kw, q=q)}], max_tokens=1, temperature=0, logprobs=True, top_logprobs=20)
    for t in range(4):
        try:
            r = cli.post("/v1/chat/completions", json=body, timeout=120).json()
            lp = {}
            for x in r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]:
                k = x["token"].strip().lower()
                if k in ("yes", "no"): lp[k] = max(lp.get(k, -99), x["logprob"])
            py, pn = math.exp(lp.get("yes", -30)), math.exp(lp.get("no", -30)); z = py + pn
            if z < 1e-3: return None
            pyes = py / z
            return pyes if order == 0 else 1 - pyes      # P(non-default reading)
        except Exception as e:
            time.sleep(1 + t)
    return None
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--workers", type=int, default=4); a = ap.parse_args()
    out = ROOT / "runs/frontier_default_profiles_probe"; out.mkdir(exist_ok=True, parents=True); fn = out / f"{a.model}.jsonl"
    done = set()
    if fn.exists(): done = {(j["unit"], j["dim"]) for j in map(json.loads, open(fn))}
    U = units(); U = U[:a.limit] if a.limit else U
    jobs = [(u, d) for u in U for d in OPT if (u["unit"], d) not in done]
    cli = httpx.Client(base_url=f"http://127.0.0.1:{a.port}")
    def run(j):
        u, d = j; q = [call(cli, a.model, u["kw"], d, o) for o in (0, 1)]
        return dict(unit=u["unit"], dim=d, kw=u["kw"], q0=q[0], q1=q[1])
    t0 = time.time(); n = 0; nulls = 0
    with open(fn, "a") as f, cf.ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(run, jobs):
            f.write(json.dumps(r) + "\n"); n += 1; nulls += (r["q0"] is None or r["q1"] is None)
            if n == 150: print("first-150 null rate", nulls / n, flush=True); sys.exit(2) if nulls / n > 0.2 else None
            if n % 500 == 0: f.flush(); print(n, len(jobs), round(time.time() - t0), "s", flush=True)
    print("done", a.model, n, round(time.time() - t0), "s")

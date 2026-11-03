"""Round 2 local independent-family judge (frontier whole_message). Runs against a llama-server (caller holds the GPU flock).
  python src/frontier_whole_message_r2_local.py <alias> <port> p18|gens|all
Queries (single-token, logprob readout, temperature 0):
  UC   P(Yes) that the OUTPUT adds content the INPUT does not support (reference-free)      -> uc_p
  SC   expected 1-5 score (digit logprobs)                                                  -> sc_e
  CRIT (Part 18 only) letter logprobs over the production critical-question options        -> dict option->prob
Cache: runs/frontier_whole_message_r2/local_<alias>.jsonl (key = sha256 of query)."""
import asyncio, hashlib, json, math, re, sys
from pathlib import Path
import httpx, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from judge import critical_question
R = ROOT / "runs/frontier_whole_message_r2"
CHIPS = ("Chip meanings: [NOT] negation; [YES] affirmative; [?] question; [ASK] request to the listener; [REFUSE] declining; [TELL] plain statement; "
         "[MAYBE] uncertain; [SURE] certain; [MUST] obligation; [WANT] desire; [I] [YOU] [WE] [THEY] who does it; [PAST] [NOW] [LATER] time; "
         "[PLEASE] polite marker; [PLAIN] no added politeness; [2], [5] an exact number.")
HEAD = ("You audit one sentence produced by a system that expands a few keywords into a full sentence for a person who communicates with an AAC device. "
        "The person can only veto, not verify, so ANY content the keywords do not support matters.\n\nINPUT (what the person typed): {x}\n" + CHIPS + "\nOUTPUT SENTENCE: {y}\n\n")
UCQ = ("Question: does the OUTPUT add people, places, times, reasons, objects, politeness, certainty words, quantities or intentions that the INPUT does not support? "
       "Grammatical glue (articles, auxiliaries, prepositions, the speaker's own pronoun, inflection) is NOT unrequested. Answer with exactly one word: Yes or No.")
SCQ = ("Rate the OUTPUT from 1 to 5: 5 = says exactly what the input supports and nothing else; 3 = noticeable addition or omission; 1 = a different message. "
       "Answer with exactly one digit.")
PROMPT_SHA = hashlib.sha256((HEAD + UCQ + SCQ).encode()).hexdigest()

def q_uc(x, y): return HEAD.format(x=x, y=y) + UCQ
def q_sc(x, y): return HEAD.format(x=x, y=y) + SCQ
def q_crit(y, dim, opts):
    L = "ABCDEFGH"
    return (f"SENTENCE: {y}\n\nQuestion: {critical_question(dim, opts)}\nOptions:\n" + "\n".join(f"{L[i]}) {o}" for i, o in enumerate(opts)) +
            "\nAnswer with exactly one letter.")

async def ask(client, model, prompt):
    r = await client.post("/v1/chat/completions", json=dict(model=model, temperature=0, max_tokens=1, logprobs=True, top_logprobs=20,
                          messages=[{"role": "user", "content": prompt}]), timeout=300)
    j = r.json()["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    return {t["token"].strip(): t["logprob"] for t in j[::-1]} if False else [(t["token"].strip(), t["logprob"]) for t in j]

def agg(tops, vocab):
    d = {}
    for tok, lp in tops:
        k = tok.strip()
        for v in vocab:
            if k.lower() == v.lower(): d[v] = d.get(v, 0) + math.exp(lp)
    return d

def jobs_p18():
    it = pd.read_csv(ROOT / "analysis/intent_check/items.csv", keep_default_na=False)
    fams = {}
    for l in open(ROOT / "annotation/written/hw_candidates.jsonl"):
        o = json.loads(l); fams[o["family_id"]] = o
    slp = pd.read_csv(ROOT / "expert_package/slp_key.csv", keep_default_na=False)
    J = []
    for _, r in it.iterrows():
        J += [("uc", r.input_text, r.text, None), ("sc", r.input_text, r.text, None)]
        f = fams[r.family_id]; J.append(("crit", None, r.text, (f["dimension"], tuple(f["critical_options"]))))
    for _, r in slp.iterrows():
        J += [("uc", r.input_text, r.text, None), ("sc", r.input_text, r.text, None)]
    return J

def jobs_gens():
    J = []
    for p in sorted(R.glob("gens_*.csv")):
        d = pd.read_csv(p, keep_default_na=False)
        for _, r in d.iterrows():
            if r.text: J += [("uc", r.input_text, r.text, None), ("sc", r.input_text, r.text, None)]
    return J

def qkey(j): return hashlib.sha256(json.dumps([PROMPT_SHA, j[0], j[1], j[2], j[3]]).encode()).hexdigest()

async def main(alias, port, which):
    cp = R / f"local_{alias}.jsonl"; cache = {}
    if cp.exists():
        for l in cp.read_text().splitlines():
            if l.strip(): o = json.loads(l); cache[o["k"]] = o["v"]
    which = "all" if which == "p18" else which   # the p18 stage also judges all generations that exist at that time (saves a second lock acquisition)
    J = (jobs_p18() if which in ("p18", "all") else []) + (jobs_gens() if which in ("gens", "all") else [])
    todo = {}
    for j in J:
        k = qkey(j)
        if k not in cache: todo[k] = j
    print(alias, len(J), "queries,", len(todo), "uncached", flush=True)
    client = httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}"); fh = cp.open("a"); sem = asyncio.Semaphore(4); n = 0
    async def one(k, j):
        nonlocal n
        kind, x, y, extra = j
        async with sem:
            if kind == "uc": tops = await ask(client, alias, q_uc(x, y)); d = agg(tops, ["Yes", "No"]); v = {"p": d.get("Yes", 0) / max(1e-9, d.get("Yes", 0) + d.get("No", 0)), "mass": d.get("Yes", 0) + d.get("No", 0)}
            elif kind == "sc":
                tops = await ask(client, alias, q_sc(x, y)); d = agg(tops, list("12345")); z = sum(d.values()) or 1e-9
                v = {"e": sum(int(a) * b for a, b in d.items()) / z, "mass": z}
            else:
                dim, opts = extra; opts = list(opts); L = "ABCDEFGH"
                tops = await ask(client, alias, q_crit(y, dim, opts)); d = agg(tops, [L[i] for i in range(len(opts))]); z = sum(d.values()) or 1e-9
                v = {"opts": {o: d.get(L[i], 0) / z for i, o in enumerate(opts)}, "mass": z}
        cache[k] = v; fh.write(json.dumps({"k": k, "v": v}) + "\n"); fh.flush(); n += 1
        if n % 500 == 0: print(" ", n, flush=True)
    await asyncio.gather(*[one(k, j) for k, j in todo.items()])
    print("DONE", alias, flush=True)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))

"""Stage 0 pilot (mechanics only) for frontier knows_not_says, amendment A1 numeric pass rule. Needs llama-server qwen on :8091
(GPU lock held by the caller). Outcomes of H1-H5 are NOT evaluated here.
Writes analysis/frontier/knows_not_says/pilot/ (raw jsonl + pilot_mechanics.json)."""
from __future__ import annotations
import json, math, random, sys, time, collections
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import prompts as P
OUT = ROOT / "analysis/frontier/knows_not_says/pilot"; OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:" + (sys.argv[1] if len(sys.argv) > 1 else "8091")
MODEL = sys.argv[2] if len(sys.argv) > 2 else "qwen2.5-7b"
SEED = 20261102
UNTRUNC = dict(temperature=1.0, top_k=0, top_p=1.0, min_p=0.0)
R: dict = {"started": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": MODEL}
cli = httpx.Client(timeout=300, limits=httpx.Limits(max_connections=16))

def chat(content, top=1, max_tokens=96, **samp):
    b = {"model": MODEL, "messages": [{"role": "user", "content": content}], "max_tokens": max_tokens,
         "logprobs": True, "top_logprobs": max(top, 1), **samp}
    r = cli.post(BASE + "/v1/chat/completions", json=b); r.raise_for_status(); return r.json()

# ------------------------------------------------------------------ items (seeded; saved so stage 1 can exclude them)
rng = random.Random(SEED)
elic = [json.loads(l) for l in open(ROOT / "data/items/elic.jsonl")]
sel = rng.sample(elic, 60); items = []
for e in sel:
    ch = sorted(k for k in e["custom_channels"]["A"] if k.startswith("human_")); c = rng.choice(ch)
    items.append({"elic_item_id": e["elic_item_id"], "family_id": e["family_id"], "channel": c,
                  "input": e["custom_channels"]["A"][c]["input"]})
hw = [json.loads(l) for l in open(ROOT / "data/items/hw.jsonl")]
pol = [h for h in hw if h["dimension"] == "polarity"]
pairs = [{"family_id": h["family_id"], "bare": h["bare"], "A": h["variants"]["A"]["source"], "B": h["variants"]["B"]["source"]}
         for h in rng.sample(pol, 20)]
json.dump({"seed": SEED, "e_human": items, "e_pairs": pairs}, open(OUT / "pilot_items.json", "w"), indent=1)

# ------------------------------------------------------------------ (a) server defaults, untruncated sampling check (20 prompts x 200)
props = cli.get(BASE + "/props").json()
dgs = props.get("default_generation_settings", {}); params = dgs.get("params", dgs)
R["server_defaults"] = {k: params.get(k) for k in ("temperature", "top_k", "top_p", "min_p", "samplers", "seed")}
R["build_info"] = props.get("build_info")
N = 200
chk_prompts = [P.render("P0n", it["input"]) for it in items[:20]]
def first_token_ref(p):
    j = chat(p, top=100, max_tokens=1, **UNTRUNC)
    tl = j["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    return {t["token"]: math.exp(t["logprob"]) for t in tl}
def draw(p, **samp):
    j = chat(p, top=1, max_tokens=1, **samp); return j["choices"][0]["logprobs"]["content"][0]["token"]
def run_draws(samp):
    cells = []
    with ThreadPoolExecutor(4) as ex:
        refs = list(ex.map(first_token_ref, chk_prompts))
        jobs = [(i, p) for i, p in enumerate(chk_prompts) for _ in range(N)]
        toks = list(ex.map(lambda ip: draw(ip[1], **samp), jobs))
    cnt = [collections.Counter() for _ in chk_prompts]
    for (i, _), t in zip(jobs, toks): cnt[i][t] += 1
    return refs, cnt
def summarise(refs, cnt):
    abs_dev, zs, tail_obs, tail_exp, ncell = [], [], 0, 0.0, 0
    for ref, c in zip(refs, cnt):
        for t, p in ref.items():
            f = c.get(t, 0) / N
            if p >= 0.01:
                abs_dev.append(abs(f - p)); zs.append((f - p) / math.sqrt(p * (1 - p) / N))
            if p < 0.02: tail_exp += p * N
        tail_obs += sum(v for t, v in c.items() if ref.get(t, 0) < 0.02)   # includes tokens outside the top-100
        # mass of tokens outside top-100 is in tail_obs only; add it to expected
        tail_exp += max(0.0, 1 - sum(ref.values())) * N
        ncell += 1
    return {"cells_p_ge_0.01": len(abs_dev), "mean_abs_dev": round(sum(abs_dev) / len(abs_dev), 4), "max_abs_dev": round(max(abs_dev), 4),
            "frac_cells_abs_z_gt_2": round(sum(abs(z) > 2 for z in zs) / len(zs), 3),
            "tail_draws_observed(p<0.02)": tail_obs, "tail_draws_expected": round(tail_exp, 1)}
refs_u, cnt_u = run_draws(UNTRUNC)
R["untruncated_20x200"] = summarise(refs_u, cnt_u)
_, cnt_d = run_draws({})        # no sampler fields: server defaults
R["server_default_sampling_20x200_vs_untruncated_ref"] = summarise(refs_u, cnt_d)
print("a done", json.dumps(R["untruncated_20x200"]), json.dumps(R["server_default_sampling_20x200_vs_untruncated_ref"]), flush=True)

# ------------------------------------------------------------------ (d) sweep: 60 inputs x (1 greedy + 16 T=1 untruncated), concurrency 4, logprobs recorded
K = 16
def one(job):
    it, k = job
    samp = dict(temperature=0.0) if k < 0 else UNTRUNC
    top = 20 if k < 0 else 1
    try:
        j = chat(P.render("P0n", it["input"]), top=top, **samp); ch = j["choices"][0]
        lp = ch["logprobs"]["content"]
        return dict(elic_item_id=it["elic_item_id"], k=k, text=ch["message"]["content"], finish=ch["finish_reason"],
                    n_tok=j["usage"]["completion_tokens"], toks=[x["token"] for x in lp], lp=[round(x["logprob"], 5) for x in lp],
                    top0=([[t["token"], round(t["logprob"], 4)] for t in lp[0]["top_logprobs"]] if k < 0 else None))
    except Exception as e:
        return dict(elic_item_id=it["elic_item_id"], k=k, error=str(e)[:200])
t0 = time.time()
with ThreadPoolExecutor(4) as ex: rows = list(ex.map(one, [(it, k) for it in items for k in [-1] + list(range(K))]))
dt = time.time() - t0
good = [r for r in rows if "error" not in r]
with open(OUT / "pilot_generations.jsonl", "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
ntok = sum(r["n_tok"] for r in good); nlp = sum(len(r["lp"]) for r in good)
R["logprob_coverage"] = {"tokens_generated": ntok, "tokens_with_logprob": nlp, "coverage": round(nlp / ntok, 5)}
R["throughput"] = {"requests": len(rows), "errors": len(rows) - len(good), "seconds": round(dt, 1), "req_per_s": round(len(good) / dt, 2),
                   "tok_per_s": round(ntok / dt, 1), "mean_out_tokens": round(ntok / len(good), 1),
                   "finish_length": sum(r["finish"] == "length" for r in good),
                   "unique_texts_among_16_samples_mean": round(sum(len({r["text"] for r in good if r["elic_item_id"] == it["elic_item_id"] and r["k"] >= 0}) for it in items) / len(items), 2)}
R["projection_hours_per_model_unique_inputs_2400_x17"] = round(2400 * 17 / (len(good) / dt) / 3600, 2)
print("d done", json.dumps(R["throughput"]), flush=True)

# ------------------------------------------------------------------ (b/c) teacher-forced scorer
def tmpl(content):
    r = cli.post(BASE + "/apply-template", json={"messages": [{"role": "user", "content": content}]}); r.raise_for_status()
    return r.json()["prompt"]
def tok(text, special=False):
    return cli.post(BASE + "/tokenize", json={"content": text, "add_special": special, "parse_special": True}).json()["tokens"]
def piece(i): return cli.post(BASE + "/detokenize", json={"tokens": [i]}).json()["content"]
def score_ids(prompt_ids, cand_ids, n_probs=1000):
    """Forced decoding: log P(cand tokens | prompt), one /completion call per token (prefix cache on). None where token is outside top-n_probs."""
    ids = list(prompt_ids); lps = []
    for c in cand_ids:
        r = cli.post(BASE + "/completion", json={"prompt": ids, "n_predict": 1, "n_probs": n_probs, "temperature": 1.0, "top_k": 0,
                     "top_p": 1.0, "min_p": 0.0, "cache_prompt": True, "post_sampling_probs": False}).json()
        cp = r["completion_probabilities"][0]; top = cp.get("top_logprobs") or []
        d = {t["id"]: t["logprob"] for t in top}
        lps.append(d.get(c)); ids.append(c)
    return lps
probe = {}
txt0 = tmpl(P.render("P0n", "Keywords: take bus"))
for name, path, body in [("completion_n_predict0_nprobs", "/completion", {"prompt": txt0, "n_predict": 0, "n_probs": 5}),
                         ("completion_echo", "/completion", {"prompt": txt0, "n_predict": 1, "n_probs": 5, "echo": True}),
                         ("v1_completions_echo", "/v1/completions", {"prompt": txt0, "max_tokens": 1, "logprobs": 5, "echo": True})]:
    try:
        r = cli.post(BASE + path, json=body); probe[name] = {"status": r.status_code, "has_prompt_logprobs_field": "prompt_logprobs" in r.text}
    except Exception as e: probe[name] = {"error": str(e)[:200]}
R["prompt_logprob_endpoints"] = probe

# 50 sequences: 25 greedy + 25 sampled whose canonical tokenisation equals the generated token pieces
rr = random.Random(SEED + 1)
pool_g = [r for r in good if r["k"] < 0]; pool_s = [r for r in good if r["k"] >= 0]
rr.shuffle(pool_g); rr.shuffle(pool_s)
item_by_id = {it["elic_item_id"]: it for it in items}
checked, skipped_noncanon = [], 0; t0 = time.time()
for pool, need in ((pool_g, 25), (pool_s, 25)):
    got = 0
    for r in pool:
        if got >= need: break
        prompt = tmpl(P.render("P0n", item_by_id[r["elic_item_id"]]["input"])); pids = tok(prompt, special=True)
        cids = tok(r["text"].rstrip("\n") if False else r["text"])
        if [piece(i) for i in cids] != r["toks"][:len(cids)] or len(cids) != len(r["toks"]):
            # generated stream may end with an EOS-like stop piece not present in the text: compare on the common prefix only if lengths match
            if not (len(cids) <= len(r["toks"]) and [piece(i) for i in cids] == r["toks"][:len(cids)]):
                skipped_noncanon += 1; continue
        lps = score_ids(pids, cids)
        if any(x is None for x in lps): checked.append(dict(k=r["k"], miss=True)); got += 1; continue
        diffs = [abs(a - b) for a, b in zip(lps, r["lp"][:len(cids)])]
        checked.append(dict(k=r["k"], n=len(cids), max_abs_diff=round(max(diffs), 4), mean_abs_diff=round(sum(diffs) / len(diffs), 4))); got += 1
ok = [c for c in checked if not c.get("miss") and c["max_abs_diff"] <= 0.05]
R["forced_vs_generation_logprob"] = {"n_checked": len(checked), "n_within_0.05_nats_every_token": len(ok), "frac_ok": round(len(ok) / max(len(checked), 1), 3),
                                     "n_missing_top1000": sum(c.get("miss", False) for c in checked), "skipped_noncanonical_tokenisation": skipped_noncanon,
                                     "worst_max_abs_diff": max((c["max_abs_diff"] for c in checked if not c.get("miss")), default=None), "detail": checked}
R["forced_check_seconds"] = round(time.time() - t0, 1)
print("c done", R["forced_vs_generation_logprob"]["frac_ok"], flush=True)

# pair scoring mechanics on 20 E-pairs: raw token logprobs saved, NOT summarised for outcomes
t0 = time.time(); pair_rows = []; pmiss = 0
for p in pairs:
    pr = tok(tmpl(P.render("P0n", "Keywords: " + p["bare"])), special=True); row = dict(family_id=p["family_id"])
    for v in "AB":
        cids = tok(p[v]); l = score_ids(pr, cids); pmiss += sum(x is None for x in l)
        row[v] = {"ids": cids, "lp": l}
    pair_rows.append(row)
json.dump(pair_rows, open(OUT / "pair_scores_raw.json", "w"))
R["pair_scoring"] = {"n_pairs": len(pairs), "missing_token_probs": pmiss, "seconds_total": round(time.time() - t0, 1),
                     "seconds_per_candidate": round((time.time() - t0) / 40, 2)}

# ------------------------------------------------------------------ (e) /embedding
emb = {}
for path, body in [("/embedding", {"content": "Keywords: take bus"}), ("/v1/embeddings", {"input": "Keywords: take bus", "model": MODEL})]:
    try:
        r = cli.post(BASE + path, json=body); emb[path] = {"status": r.status_code, "body_head": r.text[:160]}
        if r.status_code == 200:
            j = r.json(); v = (j[0]["embedding"] if isinstance(j, list) else j["data"][0]["embedding"])
            v = v[0] if v and isinstance(v[0], list) else v
            emb[path]["dim"] = len(v); emb[path]["finite"] = all(math.isfinite(x) for x in v)
    except Exception as e: emb[path] = {"error": str(e)[:200]}
R["embedding"] = emb
R["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
json.dump(R, open(OUT / "pilot_mechanics.json", "w"), indent=1)
print(json.dumps({k: v for k, v in R.items() if k not in ("forced_vs_generation_logprob",)}, indent=1))

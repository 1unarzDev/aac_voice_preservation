"""Build plain-generation requests for the local replication models (PLAN section 2): G1 (bare, chip), W1 (word) greedy and 8 samples (T=1.0,
no top_p: generate.py has none) per bare/chip input, prompt P0, on the 200 main items. Stage 2 contrast arms need the stored G1 and are
not part of this file. Output runs/requests/coverage_local.jsonl; submit with research submit aac-llm."""
import json, sys
import coverage_lib as L, prompts as P, build_requests as BR
items = [x for x in json.load(open(L.OUT / "items_draw.json"))["items"] if not x["reserve"]]
reqs = {}
for it in items:
    for cond in ("bare", "chip", "word"):
        x = it["inputs"][cond]
        draws = [(0.0, 0)] if cond == "word" else [(0.0, 0)] + [(1.0, i) for i in range(8)]
        for mname in ("qwen2.5-14b", "llama3.1-8b"):
            for temp, s in draws:
                prompt = P.render("P0", x)
                key = BR.request_key(mname, "P0", prompt, temp, s)
                if key in reqs: reqs[key]["targets"].append({"item_id": it["item_id"], "cond": cond}); continue
                reqs[key] = {"request_key": key, "model": mname, "prompt_id": "P0", "prompt_sha": P.template_sha("P0"), "temperature": temp,
                             "sample_idx": s, "max_tokens": 96, "n_suggestions": 1, "family_id": it["family_id"], "dimension": it["dimension"],
                             "split": "coverage", "items_file": "analysis/coverage/items_draw.json", "input_text": x, "prompt": prompt,
                             "targets": [{"item_id": it["item_id"], "cond": cond}]}
p = L.ROOT / "runs/requests/coverage_local.jsonl"
with p.open("w") as fh:
    for r in reqs.values(): fh.write(json.dumps(r, ensure_ascii=False) + "\n")
print(len(reqs), "requests")

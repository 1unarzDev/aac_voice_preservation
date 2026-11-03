"""Round-2 item + request builder (A5/A7). Needs turns2.jsonl (+ turns2_q14.jsonl). Writes items_r2.jsonl and runs/frontier_partner_context_req/r2.jsonl.
Channels: <kind>|<turn> (P0c; turn 0 = plain P0), <kind>|<turn>|cb (P0cb, turns != 0); kind in bare, chip, word; turn in 0 D Xa Xb Xc Q (+ q14Xa/q14Xb/q14Xc for the author-subset, bare+chip only)."""
import hashlib, json, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import build_requests as BR, models as M, prompts as P
OUT = ROOT / "analysis/frontier/partner_context"
CTX = 'The conversation partner just said: "{turn}"\n'
CB = "The partner's words are background. Do not take your reading from them; write what the user's keywords mean.\n"
NL = {"[NOT]": "not", "[YES]": "yes"}
MODELS = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]
TT = ["0", "D", "Xa", "Xb", "Xc", "Q"]

def render(turn, text, cb=False):
    ctx = "" if turn is None else CTX.format(turn=turn) + (CB if cb else "")
    return P._read("P0.txt").replace("{legend}", P._read("chip_legend.txt")).replace("{context}", ctx).replace("{input}", text)
def sha(cb): return hashlib.sha256((P.template_sha("P0") + CTX + (CB if cb else "")).encode()).hexdigest()

def main():
    turns = collections.defaultdict(dict)
    for l in open(OUT / "turns2.jsonl"):
        r = json.loads(l); turns[r["family_id"]][r["type"]] = r["turn"]
    if (OUT / "turns2_q14.jsonl").exists():
        for l in open(OUT / "turns2_q14.jsonl"):
            r = json.loads(l); turns[r["family_id"]]["q14" + r["type"]] = r["turn"]
    ids = json.load(open(OUT / "turns2_meta_mistral-nemo-12b.json"))["draw_all130"]
    fams = {}
    for fn in ("hw", "r2_c1"):
        for l in open(ROOT / f"data/items/{fn}.jsonl"):
            f = json.loads(l); fams[f["family_id"]] = f
    items, reqs = [], {}
    for fid in sorted(ids):
        f = {k: v for k, v in fams[fid].items() if k != "_file"}
        types = [t for t in TT if t == "0" or t in turns[fid]] + [t for t in turns[fid] if t.startswith("q14")]
        cc = {}
        for vn, v in f["variants"].items():
            cc[vn] = {}
            cue = v["chips"][0]
            for t in types:
                kinds = ("bare", "chip") if t.startswith("q14") else ("bare", "chip", "word")
                for k in kinds:
                    inp = {"bare": f"Keywords: {f['bare']}", "chip": f"Keywords: {cue} {f['bare']}", "word": f"Keywords: {NL[cue]} {f['bare']}"}[k]
                    com = [cue] if k == "chip" else []
                    cc[vn][f"{k}|{t}"] = {"input": inp, "commitments": com}
                    if t not in ("0",) and not t.startswith("q14"):
                        cc[vn][f"{k}|{t}|cb"] = {"input": inp, "commitments": com}
        f.update(split="pcr2", custom_channels=cc, base_family_id=fid, partner_turns=turns[fid])
        items.append(f)
        for vn in f["variants"]:
            for ch, spec in cc[vn].items():
                parts = ch.split("|"); t = parts[1]; cb = len(parts) == 3
                turn = None if t == "0" else turns[fid][t]
                pid = "P0" if t == "0" else ("P0cb" if cb else "P0c")
                prompt = render(turn, spec["input"], cb)
                for m in MODELS:
                    ms = M.get(m); key = BR.request_key(ms.model, pid, prompt, 0.0, 0)
                    tgt = {"family_id": fid, "variant": vn, "channel": ch}
                    if key in reqs: reqs[key]["targets"].append(tgt); continue
                    reqs[key] = {"request_key": key, "model": m, "prompt_id": pid, "prompt_sha": P.template_sha("P0") if pid == "P0" else sha(cb),
                                 "temperature": 0.0, "sample_idx": 0, "max_tokens": 96, "n_suggestions": 1, "family_id": fid, "dimension": "polarity",
                                 "split": "pcr2", "items_file": "items_r2.jsonl", "input_text": spec["input"], "prompt": prompt, "targets": [tgt]}
    with (OUT / "items_r2.jsonl").open("w") as fh:
        for g in items: fh.write(json.dumps(g, ensure_ascii=False) + "\n")
    rd = ROOT / "runs/frontier_partner_context_req"; rd.mkdir(exist_ok=True, parents=True)
    with (rd / "r2.jsonl").open("w") as fh:
        for r in reqs.values(): fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    hit = collections.Counter((r["model"], (ROOT / f"runs/cache/{r['request_key']}.json").exists()) for r in reqs.values())
    print(len(items), "families;", len(reqs), "unique requests; cached:", dict(hit))
main()

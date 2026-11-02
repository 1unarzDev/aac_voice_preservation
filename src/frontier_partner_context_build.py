"""Build E0 pilot items (custom channels) + generation requests for P0c (partner turn in prompt) and turn 0 (plain P0, cache-shared with hw1).
  python src/frontier_partner_context_build.py
Reads analysis/frontier/partner_context/turns.jsonl (passing turns only; families with any failing turn are dropped, never hand-edited).
Writes analysis/frontier/partner_context/items_e0.jsonl and runs/frontier_partner_context_req/e0.jsonl."""
import hashlib, json, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import build_requests as BR, models as M, prompts as P
OUT = ROOT / "analysis/frontier/partner_context"
CTX = 'The conversation partner just said: "{turn}"\n'
P0CB_LINE = "The partner's words are background. Do not take your reading from them; write what the user's keywords mean.\n"
TURN_TYPES = ["0", "N", "D", "X", "Q"]
MODELS = ["qwen2.5-7b", "gpt-6.1-terra"]

def render(turn, text, pid="P0c"):
    ctx = "" if turn is None else CTX.format(turn=turn) + (P0CB_LINE if pid == "P0cb" else "")
    return P._read("P0.txt").replace("{legend}", P._read("chip_legend.txt")).replace("{context}", ctx).replace("{input}", text)

def p0c_sha():
    return hashlib.sha256((P.template_sha("P0") + CTX + P0CB_LINE).encode()).hexdigest()

def main():
    turns = collections.defaultdict(dict); ok = collections.defaultdict(lambda: True)
    for l in open(OUT / "turns.jsonl"):
        r = json.loads(l); turns[r["family_id"]][r["type"]] = r["turn"]; ok[r["family_id"]] &= r["pass"]
    keep = [i for i in turns if ok[i]]
    print("families authored", len(turns), "kept", len(keep), "dropped", sorted(set(turns) - set(keep)))
    fams = {json.loads(l)["family_id"]: json.loads(l) for l in open(ROOT / "data/items/hw.jsonl")}
    items, reqs = [], {}
    for fid in sorted(keep):
        f = {k: v for k, v in fams[fid].items() if k != "_file"}
        cc = {}
        for vn, v in f["variants"].items():
            cc[vn] = {}
            for t in TURN_TYPES:
                cc[vn][f"bare|{t}"] = {"input": f"Keywords: {f['bare']}", "commitments": []}
                cc[vn][f"chip|{t}"] = {"input": f"Keywords: {' '.join(P.sort_chips(v['chips']))} {f['bare']}", "commitments": list(v["chips"])}
        f.update(split="pcpilot", custom_channels=cc, base_family_id=fid, partner_turns=turns[fid])
        items.append(f)
        for vn in f["variants"]:
            for ch, spec in cc[vn].items():
                kind, t = ch.split("|")
                turn = None if t == "0" else turns[fid][t]
                pid = "P0" if t == "0" else "P0c"
                text = spec["input"]; prompt = render(turn, text, pid)
                for m in MODELS:
                    ms = M.get(m)
                    key = BR.request_key(ms.model, pid, prompt, 0.0, 0)
                    tgt = {"family_id": fid, "variant": vn, "channel": ch}
                    if key in reqs: reqs[key]["targets"].append(tgt); continue
                    reqs[key] = {"request_key": key, "model": m, "prompt_id": pid,
                                 "prompt_sha": P.template_sha("P0") if pid == "P0" else p0c_sha(), "temperature": 0.0, "sample_idx": 0,
                                 "max_tokens": 96, "n_suggestions": 1, "family_id": fid, "dimension": "polarity", "split": "pcpilot",
                                 "items_file": "items_e0.jsonl", "input_text": text, "prompt": prompt, "targets": [tgt]}
    with (OUT / "items_e0.jsonl").open("w") as fh:
        for g in items: fh.write(json.dumps(g, ensure_ascii=False) + "\n")
    rd = ROOT / "runs/frontier_partner_context_req"; rd.mkdir(exist_ok=True, parents=True)
    with (rd / "e0.jsonl").open("w") as fh:
        for r in reqs.values(): fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    hit = collections.Counter((r["model"], (ROOT / f"runs/cache/{r['request_key']}.json").exists()) for r in reqs.values())
    print(len(reqs), "unique requests; cached:", dict(hit))
main()

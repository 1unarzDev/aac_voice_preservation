"""G1 on the chip|<turn> P0c outputs (A8). Local reimplementation wrapper over interventions.guard_one (prompt re-render patched to the stored P0c prompt).
  python src/frontier_partner_context_guard.py --models qwen2.5-7b[,...]   (server must be up for local models; wrapper takes the lock)
Writes runs/frontier_partner_context_r2g/parts/guard_<model>.jsonl; `assemble` mode builds generations.jsonl (G1 rows only) for judge/attribute."""
import asyncio, json, sys, argparse, httpx
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import interventions as I, runio
ap = argparse.ArgumentParser(); ap.add_argument("--models"); ap.add_argument("--assemble", action="store_true"); ap.add_argument("--api-concurrency", type=int, default=4)
a = ap.parse_args()
RUN = ROOT / "runs/frontier_partner_context_r2g"; (RUN / "parts").mkdir(parents=True, exist_ok=True)
base = ROOT / "runs/frontier_partner_context_r2"
if a.assemble:
    rows = []
    for p in sorted((RUN / "parts").glob("guard_*.jsonl")):
        rows += [r for r in runio.read_jsonl(p) if r["prompt_id"] == "G1"]
    runio.write_jsonl(RUN / "generations.jsonl", rows); print(len(rows), "G1 rows"); sys.exit()
req = {r["request_key"]: r for r in map(json.loads, open(ROOT / "runs/frontier_partner_context_req/r2.jsonl"))}
I.render_checked = lambda g, items: req[g["request_key"]]["prompt"]
async def main():
    caller = I.Caller(conc_local=4, conc_api=a.api_concurrency)
    gens = []
    for k, r in req.items():
        if r["model"] not in a.models.split(",") or r["prompt_id"] != "P0c": continue
        tg = [t for t in r["targets"] if t["channel"].startswith("chip|") and not t["channel"].endswith("|cb")]
        cp = ROOT / f"runs/cache/{k}.json"
        if not tg or not cp.exists(): continue
        raw = json.loads(cp.read_text())["raw_text"]; sug, ok, _ = I.parse_output(raw, 1)
        g = {x: v for x, v in r.items() if x not in ("prompt",)}; g.update(raw_text=raw, suggestions=sug, parse_ok=ok, targets=tg); gens.append(g)
    print(len(gens), "chip P0c generations to guard")
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=32)) as client:
        caller.client = client; src = {}
        outs = await asyncio.gather(*(I.guard_one(caller, g, {}, 2, src) for g in gens))
    for m in a.models.split(","):
        part = [r for o in outs for r in o if r["model"] == m]
        runio.write_jsonl(RUN / "parts" / f"guard_{m}.jsonl", part)
        g1 = [r for r in part if r["prompt_id"] == "G1"]
        print(m, len(g1), "G1 rows; initially flagged", sum(bool(r["flags_initial"]) for r in g1), "extra calls", sum(r["extra_calls"] for r in g1), "errors", sum(bool(r["guard_errors"]) for r in g1))
asyncio.run(main())

"""Priority-queue runner for the Google AI Studio daily allowance. Resumable, quota-aware, never hammers.

    python src/gemini_daily.py                       # one day's pass over the default queue, then finalize (judge+attribute)
    python src/gemini_daily.py --queue a.jsonl b.jsonl   # explicit ordered request files (first = highest priority)
    python src/gemini_daily.py --no-finalize         # send only
    python src/gemini_daily.py --finalize-only       # assemble runs / judge / attribute what is cached, send nothing
    python src/gemini_daily.py --status              # print progress per request file and the saved quota state

Queue = request files in priority order (default: runs/gemini_queue.json, a JSON list of paths). Each row is a
request as written by build_gemini_requests.py. Cached requests (runs/cache/<request_key>.json) are skipped, so the
queue can be relaunched at any time. Requests are sent in file order at the per-model rate in runs/gemini_limits.json
(rpm_safe, below the discovered RPM; see gemini_backend.Limiter) with `--concurrency` in flight (default 2).

Daily quota: a 429 whose QuotaFailure.quotaId contains "PerDay" (or whose message says per day / limit 0) stops THAT
model for the day (its remaining files are skipped, other models continue), is logged to runs/gemini_daily.log and
runs/gemini_429.jsonl, and saved to runs/gemini_daily_state.json with the next reset (midnight America/Los_Angeles,
the AI Studio quota reset) so the timer / loop knows when to relaunch. A model that has "limit: 0" on the free tier
is marked unavailable. Server errors (503 high demand) back off and, after repeated failures in a row, pause the
model for 10 minutes instead of retrying quickly. A lock (runs/gemini_daily.lock) prevents two copies running.

Finalize (per runs/requests/gemini_<model>_run_<legend|hw|hwctl>.jsonl): generate.py --no-network (assemble from cache),
explode.py, judge.py --concurrency 8 (existing gpt judge, codex-lb; no Gemini quota), arbiter_tool.py freeze (writes
runs/<run>/arbiter_inventory.json), attribute.py WITHOUT fallback (rows without arbiter label stay missing). The blind
arbiter is an agent step (src/arbiter_tool.py view/write): finalize records `arbiter_pending` in the state file and
re-runs attribute.py so decisions written later are picked up on the next finalize.
"""
from __future__ import annotations

import argparse
import asyncio
import fcntl
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import gemini_backend as GB  # noqa: E402
import models as M  # noqa: E402

CACHE = ROOT / "runs" / "cache"
LOG = ROOT / "runs" / "gemini_daily.log"
STATE = ROOT / "runs" / "gemini_daily_state.json"
QUEUE = ROOT / "runs" / "gemini_queue.json"
LOCK = ROOT / "runs" / "gemini_daily.lock"
PT = ZoneInfo("America/Los_Angeles")
FIN_EVERY_S = 2 * 3600
MIN_FINALIZE = 20
ITEMS = {"legend": "data/items_ext/legend_items.jsonl", "hw": "data/items/hw.jsonl",
         "hwctl": "data/items_ext/hwctl_items.jsonl"}


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def next_reset(now: datetime | None = None) -> datetime:
    """Next midnight Pacific (AI Studio daily quota reset), as an aware UTC datetime."""
    now = (now or datetime.now(timezone.utc)).astimezone(PT)
    nxt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return nxt.astimezone(timezone.utc)


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except Exception:  # noqa: BLE001
        return {}


def save_state(st: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1, default=str)); tmp.replace(STATE)


def read_rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def cached(r: dict) -> bool:
    return (CACHE / f"{r['request_key']}.json").exists()


def progress(files: list[Path]) -> dict:
    out = {}
    for p in files:
        rows = read_rows(p)
        out[p.name] = {"total": len(rows), "cached": sum(map(cached, rows))}
    return out


def queue_files(args) -> list[Path]:
    q = args.queue or json.loads(QUEUE.read_text())
    return [Path(x) if Path(x).is_absolute() else ROOT / x for x in q]


async def send(files: list[Path], conc: int, max_req: int | None, st: dict, follow: bool = False) -> dict:
    """Per-model queues run concurrently (daily/minute quotas are per model, so one model's exhaustion never blocks
    another); inside a model, request files are processed strictly in the given priority order.
    follow=False: a model's queue ends at its daily quota (one day's pass). follow=True: after a daily-quota 429 the model
    sleeps until the AI Studio reset (midnight Pacific) + 90 s and resumes, until its files are all cached; a periodic
    finalize (judge + attribute) runs every FIN_EVERY_S while new requests arrive."""
    today = datetime.now(PT).date().isoformat()
    sent = {"date_pt": today, "ok": 0, "err": 0, "per_model": {}, "first_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    exhausted: dict[str, str] = {}
    by_model: dict[str, list[Path]] = {}
    for f in files:
        rows = read_rows(f)
        if rows:
            by_model.setdefault(rows[0]["model"], []).append(f)
    stop = asyncio.Event()

    async def nap(seconds: float) -> None:
        try:
            await asyncio.wait_for(stop.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    async def model_queue(client: httpx.AsyncClient, m: str, mfiles: list[Path]) -> None:
        pm = sent["per_model"].setdefault(m, {"ok": 0, "err": 0})
        fails = 0
        until = (st.get("exhausted_until") or {}).get(m)
        if until and datetime.now(timezone.utc) < datetime.fromisoformat(until):
            if not follow:
                log(f"{m}: daily quota exhausted until {until}; skipping"); return
            wait = (datetime.fromisoformat(until) - datetime.now(timezone.utc)).total_seconds() + 90
            log(f"{m}: daily quota exhausted until {until}; sleeping {wait/60:.0f} min"); await nap(wait)
        while not stop.is_set():
            for f in mfiles:
                rows = [r for r in read_rows(f) if not cached(r)]
                if not rows:
                    continue
                log(f"{f.name}: {len(rows)} to send")
                idx = 0

                async def worker() -> None:
                    nonlocal idx, fails
                    while not stop.is_set() and m not in exhausted:
                        if idx >= len(rows) or (max_req and pm["ok"] >= max_req):
                            return
                        r = rows[idx]; idx += 1
                        res = await GB.call(client, r, M.get(m), 4)
                        if "error" not in res:
                            tmp = CACHE / f"{r['request_key']}.tmp"
                            tmp.write_text(json.dumps(res, ensure_ascii=False)); tmp.replace(CACHE / f"{r['request_key']}.json")
                            sent["ok"] += 1; pm["ok"] += 1; fails = 0
                            if pm["ok"] % 25 == 0:
                                log(f"progress {m}: {pm['ok']} sent this process (tier {r.get('tier')}, {f.name})")
                        elif res.get("quota") == "daily":
                            exhausted[m] = res["error"]
                            log(f"DAILY QUOTA for {m}: {res['error'][:200]} after {pm['ok']} ok this process; stopping {m} for today")
                            return
                        else:
                            sent["err"] += 1; pm["err"] += 1; fails += 1
                            log(f"error {m} {r['request_key'][:8]}: {str(res['error'])[:160]}")
                            if fails >= 5:
                                log(f"{m}: 5 consecutive failures, pausing 10 min"); GB.LIMITER.pause(600); fails = 0
                        if sent["err"] >= 200:
                            log("too many errors, stopping all"); stop.set()

                await asyncio.gather(*(worker() for _ in range(conc)))
                if m in exhausted or stop.is_set() or (max_req and pm["ok"] >= max_req):
                    break
            if not any(not cached(r) for f in mfiles for r in read_rows(f)):
                log(f"{m}: queue complete"); return
            if (max_req and pm["ok"] >= max_req) or stop.is_set():
                return
            if m in exhausted:
                if not follow:
                    return
                rst = next_reset()
                st.setdefault("exhausted_until", {})[m] = rst.isoformat(timespec="seconds"); save_state(st)
                wait = (rst - datetime.now(timezone.utc)).total_seconds() + 90
                log(f"{m}: sleeping {wait/60:.0f} min until quota reset {rst.isoformat(timespec='minutes')}")
                await nap(wait)
                exhausted.pop(m, None)
                log(f"{m}: resuming after quota reset")
            else:
                await nap(60)   # nothing exhausted but rows remain uncached (errors): do not spin

    async def periodic_finalize(tasks: list[asyncio.Task]) -> None:
        last = -1
        while not all(t.done() for t in tasks) and not stop.is_set():
            await nap(FIN_EVERY_S)
            n = sum(cached(r) for f in files for r in read_rows(f))
            if n != last and any(not t.done() for t in tasks):
                last = n
                st["finalize"] = await asyncio.to_thread(finalize); st["finalized_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                st["progress"] = progress(files); save_state(st)

    async with httpx.AsyncClient() as client:
        tasks = [asyncio.create_task(model_queue(client, m, fs)) for m, fs in by_model.items()]
        fin = asyncio.create_task(periodic_finalize(tasks)) if follow else None
        await asyncio.gather(*tasks)
        if fin:
            fin.cancel()
    sent["exhausted"] = exhausted
    sent["last_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return sent


def run(cmd: list[str], logname: str) -> int:
    with (ROOT / "runs" / logname).open("a") as lf:
        lf.write(f"\n$ {' '.join(cmd)}\n"); lf.flush()
        return subprocess.call(cmd, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT)


def finalize() -> dict:
    """Assemble, judge and attribute whatever is cached, per (model, run). Idempotent."""
    py = sys.executable
    info = {}
    for rf in sorted((ROOT / "runs/requests").glob("gemini_*_run_*.jsonl")):
        stem = rf.stem                                   # gemini_<model>_run_<name>
        model, name = stem[len("gemini_"):].rsplit("_run_", 1)
        rows = read_rows(rf)
        n_cached = sum(map(cached, rows))
        if n_cached < MIN_FINALIZE:   # the judge endpoint has a large fixed latency; do not spend it on a handful of rows
            continue
        run_id = f"gem_{model.replace('gemini-2.5-', '').replace('gemini-', '').replace('.', '')}_{name}"
        rd = ROOT / "runs" / run_id
        lg = f"{run_id}_pipeline.log"
        log(f"finalize {run_id}: {n_cached}/{len(rows)} cached")
        ok = run([py, "src/generate.py", "--requests", str(rf), "--run-id", run_id, "--no-network"], lg) == 0
        ok = ok and run([py, "src/explode.py", "--run", f"runs/{run_id}"], lg) == 0
        ok = ok and run([py, "src/explode.py", "--run", f"runs/{run_id}", "--by-input"], lg) == 0
        ok = ok and run([py, "src/judge.py", "--run", run_id, "--items", ITEMS[name], "--concurrency", "8"], lg) == 0
        if ok:
            run([py, "src/arbiter_tool.py", "freeze", "--run", run_id], lg)
            run([py, "src/attribute.py", "--run", run_id, "--items", ITEMS[name]], lg)
        inv = rd / "arbiter_inventory.json"
        n_inv = len(json.loads(inv.read_text()).get("a_units", [])) if inv.exists() and inv.stat().st_size else None
        info[run_id] = {"requests": len(rows), "cached": n_cached, "ok": ok, "arbiter_inventory_units": n_inv,
                        "arbiter_decided": (rd / "arbiter.jsonl").exists()}
        log(f"finalize {run_id}: ok={ok} {info[run_id]}")
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--queue", nargs="*")
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--max-requests", type=int)
    ap.add_argument("--follow", action="store_true", help="daemon mode: sleep to each midnight-Pacific reset and resume until the queue is complete")
    ap.add_argument("--no-finalize", action="store_true")
    ap.add_argument("--finalize-only", action="store_true")
    ap.add_argument("--lock", default=str(LOCK), help="lock file (use another name only for a disjoint model set, e.g. limit discovery)")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    files = queue_files(a)
    if a.status:
        print(json.dumps({"progress": progress(files), "state": load_state()}, indent=1)); return 0
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    lk = (LOCK.with_name("gemini_finalize.lock") if a.finalize_only else Path(a.lock)).open("w")
    try:
        fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("another gemini_daily is running; exit"); return 0
    st = load_state()
    if not a.finalize_only:
        log(f"start: queue={[f.name for f in files]} progress={json.dumps(progress(files))}")
        sent = asyncio.run(send(files, a.concurrency, a.max_requests, st, a.follow))
        eu = {m: v for m, v in (st.get("exhausted_until") or {}).items()
              if datetime.now(timezone.utc) < datetime.fromisoformat(v)}
        eu.update({m: next_reset().isoformat(timespec="seconds") for m in sent["exhausted"]})
        prog = progress(files)
        st.update({"exhausted_until": eu, "last_run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sent": sent,
                   "exhausted_models": sent["exhausted"], "reset_utc": next_reset().isoformat(timespec="seconds"),
                   "progress": prog, "queue_complete": all(v["cached"] == v["total"] for v in prog.values())})
        save_state(st)
        if True:
            log(f"done sending: ok={sent['ok']} err={sent['err']} exhausted={list(sent['exhausted'])} next reset {st['reset_utc']}")
    if not a.no_finalize:
        st["finalize"] = finalize(); st["finalized_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        st["progress"] = progress(files); save_state(st)
    return 0


if __name__ == "__main__":
    sys.exit(main())

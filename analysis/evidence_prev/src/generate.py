"""Async generation over a requests file, with a disk cache and per-endpoint concurrency.

  python src/generate.py --requests runs/requests/requests.jsonl [--run-id smoke1] \
      [--models gemma3-4b] [--api-concurrency 16] [--local-concurrency 8] [--limit N]

- Cache: runs/cache/<request_key>.json holds the raw server response summary. A cached
  key is never re-requested, so re-runs are free and an interrupted run resumes.
  Only successful calls are cached; failures are logged with `error` and retried next run.
- Retries: up to --retries attempts, exponential backoff (2,4,8,... s) on transport
  errors, 429 and 5xx. Other 4xx fail immediately.
- Seed: local servers get seed=1000+sample_idx; API models get no seed (rejected).
- Parsing happens on every run from the cached raw text (parse changes need no re-calls):
  `suggestions` (1 for P0/P1/S3, 3 for P2), `parse_ok`, `parse_method`.
Writes runs/<run_id>/generations.jsonl and runs/<run_id>/config.json.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models as M  # noqa: E402
import prompts as P  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "runs" / "cache"
SEED_BASE = 1000

# ---------------------------------------------------------------- parsing
_LABEL = re.compile(
    r"^\s*(?:[-*•]\s+|\(?\d+[.):]\s+|(?:suggestion|option|sentence|output|answer|response)"
    r"\s*\d*\s*[:.\-)]\s*)+", re.I)
_PREFACE = re.compile(r"^\s*(?:here(?:'s| is| are)\b[^:\n]*|sure[^:\n]*|the sentence[^:\n]*):\s*$", re.I)
_QUOTES = [('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"), ("`", "`")]


def clean_one(s: str) -> str:
    """Strip list markers/labels and surrounding quotes or markdown emphasis."""
    s = _LABEL.sub("", s.strip()).strip()
    changed = True
    while changed and len(s) >= 2:
        changed = False
        for a, b in _QUOTES + [("**", "**"), ("*", "*")]:
            if s.startswith(a) and s.endswith(b) and len(s) > len(a) + len(b) - 1:
                s, changed = s[len(a):len(s) - len(b)].strip(), True
    return s.rstrip(",").strip()


def _strip_fences(t: str) -> str:
    return re.sub(r"```(?:json|JSON)?", "", t).strip()


def parse_output(text: str | None, n_expected: int) -> tuple[list[str], bool, str]:
    """Return (suggestions, parse_ok, method). parse_ok means exactly n_expected
    non-empty suggestions were found by the expected route (JSON list for n>1,
    a single line for n=1)."""
    if not text or not text.strip():
        return [], False, "empty"
    t = _strip_fences(text)
    if n_expected > 1:
        spans = re.findall(r"\[.*\]", t, re.S)
        for cand in [t] + spans + [f"[{c}]" for c in spans]:  # last: '["a"], ["b"]' shape
            try:
                obj = json.loads(cand)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(obj, dict):  # {"suggestions":[...]}
                obj = next((v for v in obj.values() if isinstance(v, list)), None)
            if isinstance(obj, list):
                items = []
                flat = [y for x in obj for y in (x if isinstance(x, list) else [x])]
                for x in flat:
                    if isinstance(x, dict):
                        x = next((v for v in x.values() if isinstance(v, str)), "")
                    if isinstance(x, str) and clean_one(x):
                        items.append(clean_one(x))
                if items:
                    return items[:n_expected], len(items) == n_expected, "json"
    lines = [ln for ln in t.splitlines() if ln.strip() and not _PREFACE.match(ln)]
    lines = [clean_one(ln) for ln in lines]
    lines = [ln for ln in lines if ln and ln not in "[]"]
    if n_expected == 1:
        if not lines:
            return [], False, "empty"
        return [lines[0]], len(lines) == 1, "single" if len(lines) == 1 else "first_line"
    return lines[:n_expected], len(lines) == n_expected, "lines"


# ---------------------------------------------------------------- calling
def code_sha() -> str:
    h = hashlib.sha256()
    for p in sorted((ROOT / "src").glob("*.py")) + sorted((ROOT / "src").glob("*.sh")):
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()


def body_for(req: dict, spec: M.ModelSpec) -> dict:
    body = {"model": spec.model, "messages": [{"role": "user", "content": req["prompt"]}],
            "temperature": req["temperature"], "max_tokens": req["max_tokens"]}
    if spec.supports_seed:
        body["seed"] = SEED_BASE + req["sample_idx"]
    return body


async def call(client: httpx.AsyncClient, req: dict, spec: M.ModelSpec, retries: int) -> dict:
    body = body_for(req, spec)
    err = None
    for attempt in range(1, retries + 1):
        t0 = time.perf_counter()
        try:
            r = await client.post(spec.base_url + "/chat/completions", json=body,
                                  headers=M.headers(spec), timeout=180)
            lat = time.perf_counter() - t0
            if r.status_code == 200:
                j = r.json()
                ch = j["choices"][0]
                return {"raw_text": ch["message"].get("content") or "",
                        "finish_reason": ch.get("finish_reason"), "latency_s": round(lat, 3),
                        "usage": j.get("usage"), "model_reported": j.get("model"),
                        "system_fingerprint": j.get("system_fingerprint"),
                        "seed": body.get("seed"), "attempts": attempt,
                        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            err = f"HTTP {r.status_code}: {r.text[:300]}"
            if r.status_code < 500 and r.status_code != 429:
                break
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
            err = f"{type(e).__name__}: {e}"[:300]
        if attempt < retries:
            await asyncio.sleep(2 ** attempt)
    return {"error": err, "attempts": attempt}


async def run(reqs: list[dict], conc: dict[str, int], retries: int, out_rows: list[dict],
              cache: Path = CACHE) -> dict:
    sems = {m: asyncio.Semaphore(n) for m, n in conc.items()}
    stats = defaultdict(lambda: {"n": 0, "cached": 0, "errors": 0, "t_first": None, "t_last": None,
                                 "completion_tokens": 0})
    cache.mkdir(parents=True, exist_ok=True)
    limits = httpx.Limits(max_connections=sum(conc.values()) + 8)
    done = 0
    async with httpx.AsyncClient(limits=limits) as client:
        async def one(req: dict) -> None:
            nonlocal done
            spec, st = M.get(req["model"]), stats[req["model"]]
            cpath = cache / f"{req['request_key']}.json"
            if cpath.exists():
                res, cached = json.loads(cpath.read_text()), True
            else:
                async with sems[req["model"]]:
                    st["t_first"] = st["t_first"] or time.perf_counter()
                    res, cached = await call(client, req, spec, retries), False
                    st["t_last"] = time.perf_counter()
                if "error" not in res:
                    tmp = cpath.with_suffix(".tmp")
                    tmp.write_text(json.dumps(res, ensure_ascii=False)); tmp.replace(cpath)
            st["n"] += 1; st["cached"] += cached; st["errors"] += "error" in res
            if not cached and res.get("usage"):
                st["completion_tokens"] += res["usage"].get("completion_tokens") or 0
            sugg, ok, method = parse_output(res.get("raw_text"), req["n_suggestions"])
            row = {k: v for k, v in req.items() if k != "prompt"}
            row.update(res, cached=cached, suggestions=sugg, parse_ok=ok, parse_method=method)
            out_rows.append(row)
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(reqs)} done", file=sys.stderr)

        await asyncio.gather(*(one(r) for r in reqs))
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--requests", required=True)
    ap.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    ap.add_argument("--models", help="only these models (comma list)")
    ap.add_argument("--local-concurrency", type=int, default=8)
    ap.add_argument("--api-concurrency", type=int, default=16)
    ap.add_argument("--retries", type=int, default=5)
    ap.add_argument("--limit", type=int, help="first N requests only (debug)")
    ap.add_argument("--cache-dir", default=str(CACHE), help="default runs/cache (use a fresh dir to benchmark)")
    a = ap.parse_args()

    reqs = [json.loads(l) for l in Path(a.requests).read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.models:
        keep = set(a.models.split(","))
        reqs = [r for r in reqs if r["model"] in keep]
    if a.limit:
        reqs = reqs[: a.limit]
    used = sorted({r["model"] for r in reqs})
    conc = {m: (a.api_concurrency if M.get(m).kind == "api" else a.local_concurrency) for m in used}

    rows: list[dict] = []
    t0 = time.perf_counter()
    stats = asyncio.run(run(reqs, conc, a.retries, rows, Path(a.cache_dir)))
    wall = time.perf_counter() - t0

    order = {r["request_key"]: i for i, r in enumerate(reqs)}
    rows.sort(key=lambda r: order[r["request_key"]])
    out_dir = ROOT / "runs" / a.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "generations.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    thr = {}
    for m, st in stats.items():
        fresh = st["n"] - st["cached"]
        span = (st["t_last"] - st["t_first"]) if st["t_first"] and st["t_last"] else 0.0
        n_out = sum(len(r["suggestions"]) for r in rows if r["model"] == m and not r["cached"])
        thr[m] = {"requests": st["n"], "cached": st["cached"], "errors": st["errors"],
                  "fresh_requests": fresh, "active_s": round(span, 1),
                  "requests_per_min": round(60 * fresh / span, 1) if span else None,
                  "outputs_per_min": round(60 * n_out / span, 1) if span else None,
                  "completion_tok_per_s": round(st["completion_tokens"] / span, 1) if span else None,
                  "concurrency": conc[m]}
    parse_fail = Counter(r["model"] for r in rows if not r["parse_ok"])
    config = {
        "run_id": a.run_id, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requests_file": str(Path(a.requests).resolve()),
        "requests_sha256": hashlib.sha256(Path(a.requests).read_bytes()).hexdigest(),
        "n_requests": len(reqs), "wall_s": round(wall, 1),
        "models": {m: M.public_dict(M.get(m)) for m in used},
        "prompts": {pid: {**P.PROMPTS[pid].__dict__, "sha256": P.template_sha(pid)} for pid in P.PROMPTS},
        "seed_base": SEED_BASE, "cache_dir": a.cache_dir, "retries": a.retries, "code_sha256": code_sha(),
        "python": platform.python_version(), "httpx": httpx.__version__,
        "throughput": thr, "parse_failures": dict(parse_fail),
        "finish_reasons": dict(Counter(f"{r['model']}:{r.get('finish_reason')}" for r in rows)),
    }
    (out_dir / "config.json").write_text(json.dumps(config, indent=2))
    # throughput of every invocation is appended, so a fully cached re-run keeps history
    with (out_dir / "throughput.jsonl").open("a") as f:
        f.write(json.dumps({"created_utc": config["created_utc"], "wall_s": config["wall_s"],
                            "throughput": thr}) + "\n")

    print(f"\nrun {a.run_id}: {len(rows)} requests in {wall:.1f}s -> {out_dir}/generations.jsonl")
    print(f"{'model':15s} {'req':>5s} {'cached':>6s} {'err':>4s} {'req/min':>8s} {'out/min':>8s} {'tok/s':>7s}")
    for m, t in thr.items():
        print(f"{m:15s} {t['requests']:5d} {t['cached']:6d} {t['errors']:4d} "
              f"{t['requests_per_min'] or 0:8.1f} {t['outputs_per_min'] or 0:8.1f} {t['completion_tok_per_s'] or 0:7.1f}")
    if parse_fail:
        print(f"parse_ok=False: {dict(parse_fail)}")
    if any(t["errors"] for t in thr.values()):
        print("some requests FAILED (not cached); re-run the same command to retry them", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

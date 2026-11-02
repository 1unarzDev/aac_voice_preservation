"""Google AI Studio (Gemini generateContent) backend for generate.py / gemini_daily.py.

Same prompt text as every other API model (the whole rendered prompt as ONE user message, no system
message), temperature from the request (0), maxOutputTokens as the request (96, same as terra).
Thinking: gemini-2.5-flash gets thinkingConfig.thinkingBudget=0 (off). gemini-2.5-pro cannot disable
thinking (minimum budget 128), so it is sent thinkingBudget=128 and maxOutputTokens is raised by
PRO_HEADROOM so thinking tokens cannot starve the visible sentence. Both settings are written into every
cache entry (`thinking_budget`, `max_output_tokens_sent`). The request key does NOT include them (it is
model + prompt + temperature + sample + namespace, as for every model), so they are per-model constants
recorded in models.py.

Cache entry = the same schema as generate.call (raw_text, finish_reason, latency_s, usage, model_reported,
system_fingerprint, seed, attempts, created_utc) plus backend/thinking fields. Cached: any HTTP 200
(including a deterministic empty/blocked answer, finish_reason says why). Not cached: transport errors,
429, 5xx.

Quota handling. 429 bodies carry google.rpc.QuotaFailure (quotaId, quotaMetric, quotaValue) and
google.rpc.RetryInfo (retryDelay). A quotaId containing "PerDay" is a DAILY quota: call() returns
{"error": ..., "quota": "daily"} immediately and never retries (the caller stops the day). A per-minute 429
sleeps retryDelay (+1 s) and retries up to `retries` times. Every 429 is appended to runs/gemini_429.jsonl
(no key material) so the real limits can be read off. A shared limiter spaces calls per model by
runs/gemini_limits.json {"<model>": {"rpm_safe": N}} (written by gemini_daily.py --probe / by hand).

The API key (GOOGLE_AI_STUDIO_KEY, fallback BACKUP_GOOGLE_AI_STUDIO_KEY) is parsed from the fish-syntax
~/.config/caelestia/.env.secrets. It is never printed or logged. The backup is used only if the primary is
missing or rejected as invalid (HTTP 400 API_KEY_INVALID / 403), never to double the daily quota.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
SECRETS_FILE = Path.home() / ".config/caelestia/.env.secrets"
LOG_429 = ROOT / "runs" / "gemini_429.jsonl"
LIMITS_FILE = ROOT / "runs" / "gemini_limits.json"
PRO_HEADROOM = 256
DEFAULT_RPM_SAFE = 4.0
KEY_NAMES = ("GOOGLE_AI_STUDIO_KEY", "BACKUP_GOOGLE_AI_STUDIO_KEY")


def _parse_secret(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    if SECRETS_FILE.exists():
        pat = re.compile(rf'^\s*(?:set\s+-gx\s+|export\s+)?{name}[\s=]+["\']?([^"\'\s]+)')
        for line in SECRETS_FILE.read_text().splitlines():
            m = pat.match(line)
            if m:
                return m.group(1)
    return None


_key_idx = 0


def current_key() -> str:
    for i in range(_key_idx, len(KEY_NAMES)):
        k = _parse_secret(KEY_NAMES[i])
        if k:
            return k
    raise SystemExit("no GOOGLE_AI_STUDIO_KEY found (nor backup) in env or secrets file")


def _demote_key() -> bool:
    """Primary rejected as invalid: move to the backup. Returns False when none is left."""
    global _key_idx
    if _key_idx + 1 < len(KEY_NAMES) and _parse_secret(KEY_NAMES[_key_idx + 1]):
        _key_idx += 1
        return True
    return False


def key_in_use() -> str:
    return KEY_NAMES[_key_idx]


def rpm_safe(model: str) -> float:
    try:
        return float(json.loads(LIMITS_FILE.read_text())[model]["rpm_safe"])
    except Exception:  # noqa: BLE001
        return DEFAULT_RPM_SAFE


class Limiter:
    """Spaces request START times >= 60/rpm seconds apart per model, across all tasks in the process."""

    def __init__(self) -> None:
        self._next: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self.pause_until = 0.0

    async def wait(self, model: str) -> None:
        async with self._lock:
            now = time.monotonic()
            t = max(self._next.get(model, 0.0), self.pause_until, now)
            self._next[model] = t + 60.0 / rpm_safe(model)
        if t > now:
            await asyncio.sleep(t - now)

    def pause(self, seconds: float) -> None:
        self.pause_until = max(self.pause_until, time.monotonic() + seconds)


LIMITER = Limiter()


def _log429(model: str, status: int, info: dict) -> None:
    LOG_429.parent.mkdir(parents=True, exist_ok=True)
    with LOG_429.open("a") as f:
        f.write(json.dumps({"t_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "model": model, "status": status, **info}) + "\n")


def parse_429(r: httpx.Response) -> dict:
    """-> {daily: bool, retry_s: float|None, quota_ids: [...], metrics: [...], message: str}"""
    out = {"daily": False, "retry_s": None, "quota_ids": [], "metrics": [], "values": [], "message": ""}
    try:
        err = r.json().get("error", {})
    except Exception:  # noqa: BLE001
        out["message"] = r.text[:200]
        return out
    out["message"] = (err.get("message") or "")[:300]
    for d in err.get("details", []):
        t = d.get("@type", "")
        if t.endswith("QuotaFailure"):
            for v in d.get("violations", []):
                out["quota_ids"].append(v.get("quotaId")); out["metrics"].append(v.get("quotaMetric"))
                out["values"].append(v.get("quotaValue"))
        elif t.endswith("RetryInfo"):
            m = re.match(r"([\d.]+)s", str(d.get("retryDelay", "")))
            if m:
                out["retry_s"] = float(m.group(1))
    ids = " ".join(x or "" for x in out["quota_ids"])
    out["daily"] = "PerDay" in ids or bool(re.search(r"per day|daily", out["message"], re.I))
    return out


def body_for(req: dict, spec) -> dict:
    gc = {"temperature": req["temperature"], "maxOutputTokens": req["max_tokens"]}
    if spec.thinking_budget is not None:
        gc["thinkingConfig"] = {"thinkingBudget": spec.thinking_budget}
        if spec.thinking_budget > 0:
            gc["maxOutputTokens"] = req["max_tokens"] + PRO_HEADROOM
    return {"contents": [{"role": "user", "parts": [{"text": req["prompt"]}]}], "generationConfig": gc}


def parse_ok(j: dict, spec, body: dict, lat: float, attempts: int) -> dict:
    cands = j.get("candidates") or []
    cand = cands[0] if cands else {}
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    fin = cand.get("finishReason")
    if not cands:
        fin = "BLOCKED:" + str((j.get("promptFeedback") or {}).get("blockReason"))
    u = j.get("usageMetadata") or {}
    usage = {"prompt_tokens": u.get("promptTokenCount"), "completion_tokens": u.get("candidatesTokenCount"),
             "thoughts_tokens": u.get("thoughtsTokenCount"), "total_tokens": u.get("totalTokenCount")}
    return {"raw_text": text, "finish_reason": fin, "latency_s": round(lat, 3), "usage": usage,
            "model_reported": j.get("modelVersion"), "system_fingerprint": None, "seed": None,
            "attempts": attempts, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "backend": "gemini", "thinking_budget": spec.thinking_budget,
            "max_output_tokens_sent": body["generationConfig"]["maxOutputTokens"]}


async def call(client: httpx.AsyncClient, req: dict, spec, retries: int = 5) -> dict:
    """One logical request. Returns a cache entry, or {"error", "attempts"[, "quota": "daily"]}."""
    body = body_for(req, spec)
    url = f"{spec.base_url}/models/{spec.model}:generateContent"
    err = None
    attempt = 0
    while attempt < retries:
        attempt += 1
        await LIMITER.wait(spec.model)
        t0 = time.perf_counter()
        try:
            r = await client.post(url, json=body, headers={"x-goog-api-key": current_key()}, timeout=120)
        except httpx.HTTPError as e:
            err = f"{type(e).__name__}: {e}"[:300]
            await asyncio.sleep(2 ** attempt)
            continue
        lat = time.perf_counter() - t0
        if r.status_code == 200:
            try:
                return parse_ok(r.json(), spec, body, lat, attempt)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                err = f"bad 200 body: {type(e).__name__}"
                continue
        if r.status_code == 429:
            info = parse_429(r)
            _log429(spec.model, 429, {k: info[k] for k in ("daily", "retry_s", "quota_ids", "metrics", "values", "message")})
            if info["daily"]:
                return {"error": "HTTP 429 daily quota: " + info["message"][:200], "quota": "daily", "attempts": attempt}
            wait = (info["retry_s"] or 30.0) + 1.0
            LIMITER.pause(wait)
            err = f"HTTP 429 per-minute: retry in {wait:.0f}s"
            continue
        if r.status_code in (400, 403) and re.search(r"API_KEY_INVALID|API key not valid|PERMISSION_DENIED", r.text):
            if _demote_key():
                attempt -= 1
                continue
        err = f"HTTP {r.status_code}: {r.text[:300]}"
        if r.status_code < 500:
            break
        await asyncio.sleep(2 ** attempt)
    return {"error": err, "attempts": attempt}

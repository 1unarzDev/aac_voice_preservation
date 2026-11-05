"""Shared helpers for the intent-coverage pilot (analysis/coverage/PLAN.md). Cached async chat via codex-lb.
Generation concurrency <= 4, judge <= 3 (set by callers). No Gemini."""
from __future__ import annotations
import asyncio, hashlib, json, random, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import models as M  # noqa: E402
import prompts as P  # noqa: E402
OUT = ROOT / "analysis/coverage"
CACHE_DIR = OUT / "cache"; CACHE_DIR.mkdir(parents=True, exist_ok=True)
DIMS = ["polarity", "speech_act", "agent", "certainty", "politeness", "time_quantity"]
STATIC_ORDER = DIMS  # polarity, speech_act, agent, certainty, politeness, time_quantity? plan order: polarity, speech_act, agent, time_quantity, certainty, politeness
STATIC_ORDER = ["polarity", "speech_act", "agent", "time_quantity", "certainty", "politeness"]
OPTIONS = {"speech_act": ["statement", "question", "request/command", "refusal", "acceptance", "offer/suggestion", "unclear/mixed"],
           "agent": ["speaker", "addressee", "we/joint", "third party", "unclear/mixed"],
           "certainty": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic", "unclear/mixed"],
           "politeness": ["polite", "plain", "unclear/mixed"],
           "polarity": ["negated", "affirmative", "unclear/mixed"],
           "time_quantity": ["past", "now", "later", "unclear/mixed"]}
NL = {"[NOT]": "not", "[YES]": "yes", "[?]": "question", "[TELL]": "statement", "[ASK]": "request", "[REFUSE]": "refuse",
      "[I]": "I", "[YOU]": "you", "[THEY]": "they", "[WE]": "we", "[MAYBE]": "maybe", "[SURE]": "sure",
      "[PLEASE]": "please", "[PLAIN]": "plain", "[PAST]": "past", "[NOW]": "now", "[LATER]": "later"}  # copy of build_chip_controls.NL


def prompt_text(name: str) -> str:
    return (ROOT / "prompts" / name).read_text().strip()


def fill(tpl: str, **kw) -> str:
    for k, v in kw.items():
        tpl = tpl.replace("{" + k + "}", str(v))
    return tpl


def defn(dim: str) -> str:
    import judge as J
    return J.critical_question(dim, OPTIONS[dim])


def resolve_models() -> dict:
    """Fixed once per study in models_used.json (gpt-6.1-* preferred; fallback frozen at first use and logged)."""
    p = OUT / "models_used.json"
    if p.exists():
        return json.loads(p.read_text())
    raise SystemExit("models_used.json missing; run coverage_draw.py first")


class Chat:
    pause_until = 0.0

    def __init__(self, cache_name: str, conc: int):
        self.path = CACHE_DIR / f"{cache_name}.jsonl"
        self.cache = {}
        if self.path.exists():
            for l in self.path.read_text().splitlines():
                if l.strip():
                    try:
                        o = json.loads(l); self.cache[o["k"]] = o["v"]
                    except Exception:  # noqa: BLE001
                        pass
        self.fh = self.path.open("a")
        self.sem = asyncio.Semaphore(conc)
        self.client = None
        self.n_err = 0; self.n_call = 0; self.t0 = time.time()

    def key(self, model, prompt, temp, top_p, schema, effort, draw, tag) -> str:
        return hashlib.sha256(json.dumps([model, prompt, temp, top_p, schema, effort, draw, tag], sort_keys=True).encode()).hexdigest()

    async def one(self, model, prompt, *, temp=0.0, top_p=None, schema=None, effort=None, draw=0, tag="", max_tokens=400):
        k = self.key(model, prompt, temp, top_p, schema, effort, draw, tag)
        if k in self.cache:
            return self.cache[k]
        if self.client is None:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(base_url=M.API_BASE, api_key=M.api_key(), max_retries=0)
        kw = dict(model=model, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens, timeout=180)
        if temp is not None:
            kw["temperature"] = temp
        if top_p is not None:
            kw["top_p"] = top_p
        if effort:
            kw["reasoning_effort"] = effort
        if schema:
            kw["response_format"] = {"type": "json_schema", "json_schema": {"name": "r", "strict": True, "schema": schema}}
        att = 0
        while att < 10:
            try:
                now = time.time()
                if Chat.pause_until > now:
                    await asyncio.sleep(Chat.pause_until - now + random.random() * 5)
                async with self.sem:
                    r = await self.client.chat.completions.create(**kw)
                v = r.choices[0].message.content or ""
                if schema:
                    v = json.loads(v)
                self.cache[k] = v
                self.fh.write(json.dumps({"k": k, "v": v, "model": model, "draw": draw, "tag": tag}, ensure_ascii=False) + "\n"); self.fh.flush()
                self.n_call += 1
                if self.n_call % 200 == 0:
                    print(f"  [{self.path.stem}] {self.n_call} calls, {self.n_err} errors, {time.time()-self.t0:.0f}s", flush=True)
                return v
            except Exception as e:  # noqa: BLE001
                self.n_err += 1
                msg = str(e)
                wait = min(300, 3 * 2 ** att) + random.random()
                if "429" in msg[:40] or "usage limit" in msg.lower() or "rate limit" in msg.lower():
                    # global pause shared by all callers; does not consume an attempt (the quota resets within 1-5 h)
                    if Chat.pause_until < time.time() + 60:
                        print("  quota/rate limit: pausing all calls 300 s:", msg[:100], flush=True)
                    Chat.pause_until = time.time() + 300
                    continue
                att += 1
                if att in (1, 5, 9):
                    print("  retry", type(e).__name__, msg[:120], flush=True)
                await asyncio.sleep(wait)
        return None


def schema_obj(props: dict, required=None):
    return {"type": "object", "additionalProperties": False, "required": required or list(props), "properties": props}


def clean_sentence(t) -> str:
    t = (t or "").strip()
    if not t:
        return ""
    t = t.splitlines()[0].strip().strip('"').strip()
    return t


def norm(t: str) -> str:
    return " ".join("".join(c.lower() if c.isalnum() or c.isspace() else " " for c in (t or "")).split())

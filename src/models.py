"""Model registry: name -> endpoint, served model id, quantization, GGUF sha256.

Local models are llama.cpp servers started by src/serve_local.sh (alias == `model`).
API models use the OpenAI-compatible chat/completions endpoint at codex.lunarz.dev.
The API key is read from env CODEX_LB_API_KEY, or else parsed from
~/.config/caelestia/.env.secrets (fish syntax: `set -gx NAME "value"`). It is never
printed, logged or written anywhere.

Checked 2026-10-31: the API rejects `seed` (HTTP 400 "Unsupported parameter: seed")
for gpt-6.1-terra and gpt-6.1-sol, so supports_seed=False there. `temperature` works.
gpt-6.1-sol spends hidden reasoning tokens, so give it a larger max_tokens.

  python src/models.py               # list the registry + health of each endpoint
  python src/models.py --verify-sha  # also sha256 the GGUFs (~30 s)
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
SECRETS_FILE = Path.home() / ".config/caelestia/.env.secrets"
API_BASE = "https://codex.lunarz.dev/v1"
API_KEY_ENV = "CODEX_LB_API_KEY"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


@dataclass(frozen=True)
class ModelSpec:
    name: str              # short id used everywhere in the harness
    base_url: str
    model: str             # model id sent in the request body
    kind: str              # "local" | "api"
    role: str              # "under_test" | "judge"
    quant: str | None = None
    gguf: str | None = None
    sha256: str | None = None
    concurrency: int = 8   # max in-flight requests to this endpoint
    supports_seed: bool = True
    backend: str = "openai"            # "openai" (chat/completions) | "gemini" (src/gemini_backend.py)
    thinking_budget: int | None = None  # gemini only; 0 = thinking off (recorded in every cache entry)


REGISTRY: dict[str, ModelSpec] = {m.name: m for m in [
    ModelSpec("qwen2.5-7b", "http://127.0.0.1:8091/v1", "qwen2.5-7b", "local", "under_test",
              "Q4_K_M", "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
              "65b8fcd92af6b4fefa935c625d1ac27ea29dcb6ee14589c55a8f115ceaaa1423"),
    ModelSpec("llama3.1-8b", "http://127.0.0.1:8092/v1", "llama3.1-8b", "local", "under_test",
              "Q4_K_M", "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
              "7b064f5842bf9532c91456deda288a1b672397a54fa729aa665952863033557c"),
    ModelSpec("gemma3-4b", "http://127.0.0.1:8093/v1", "gemma3-4b", "local", "under_test",
              "Q4_K_M", "google_gemma-3-4b-it-Q4_K_M.gguf",
              "4996030242583a40aa151ff93f49ed787ac8c25e4120c3ae4588b2e2a7d1ae94"),
    # model-breadth extension: role "ext_under_test" keeps UNDER_TEST (and every default model list) unchanged
    ModelSpec("qwen2.5-14b", "http://127.0.0.1:8094/v1", "qwen2.5-14b", "local", "ext_under_test",
              "Q4_K_M", "qwen2.5-14b/qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf", "a09ea5e7b1eafb1b30b241726c3cc3c905c96f14ad41e246ffa5f44e53904f68"),
    ModelSpec("mistral-nemo-12b", "http://127.0.0.1:8095/v1", "mistral-nemo-12b", "local", "ext_under_test",
              "Q4_K_M", "mistral-nemo-12b/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf", "7c1a10d202d8788dbe5628dc962254d10654c853cae6aaeca0618f05490d4a46"),
    # Google AI Studio (free-tier daily allowance), see src/gemini_backend.py, src/gemini_daily.py.
    # Flash can switch thinking off (budget 0); Pro cannot (min 128), so its budget is the minimum.
    ModelSpec("gemini-2.5-flash", GEMINI_BASE, "gemini-2.5-flash", "api", "ext_under_test",
              concurrency=1, supports_seed=False, backend="gemini", thinking_budget=0),
    ModelSpec("gemini-2.5-pro", GEMINI_BASE, "gemini-2.5-pro", "api", "ext_under_test",
              concurrency=1, supports_seed=False, backend="gemini", thinking_budget=128),
    ModelSpec("gpt-6.1-terra", API_BASE, "gpt-6.1-terra", "api", "under_test",
              concurrency=16, supports_seed=False),
    ModelSpec("gpt-6.1-sol", API_BASE, "gpt-6.1-sol", "api", "judge",
              concurrency=16, supports_seed=False),
]}

UNDER_TEST = [n for n, m in REGISTRY.items() if m.role == "under_test"]
LOCAL = [n for n, m in REGISTRY.items() if m.kind == "local"]


def get(name: str) -> ModelSpec:
    try:
        return REGISTRY[name]
    except KeyError:
        raise SystemExit(f"unknown model {name!r}; known: {', '.join(REGISTRY)}")


def api_key() -> str:
    """CODEX_LB_API_KEY from env, else from the secrets file. Never print the result."""
    key = os.environ.get(API_KEY_ENV)
    if key:
        return key
    if SECRETS_FILE.exists():
        pat = re.compile(rf'^\s*(?:set\s+-gx\s+|export\s+)?{API_KEY_ENV}[\s=]+["\']?([^"\'\s]+)')
        for line in SECRETS_FILE.read_text().splitlines():
            m = pat.match(line)
            if m:
                return m.group(1)
    raise SystemExit(f"{API_KEY_ENV} not set and not found in {SECRETS_FILE}")


def headers(spec: ModelSpec) -> dict[str, str]:
    if spec.kind == "api" and spec.backend == "openai":
        return {"Authorization": f"Bearer {api_key()}"}
    return {}


def public_dict(spec: ModelSpec) -> dict:
    """Registry entry safe to write to config snapshots (contains no secrets)."""
    return asdict(spec)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    import httpx
    verify = "--verify-sha" in sys.argv
    for spec in REGISTRY.values():
        status = "?"
        try:
            r = httpx.get(spec.base_url + "/models", headers=headers(spec), timeout=10)
            ids = [m["id"] for m in r.json().get("data", [])]
            status = "ok" if spec.model in ids else f"model not listed ({r.status_code})"
        except Exception as e:  # noqa: BLE001
            status = f"down ({type(e).__name__})"
        extra = ""
        if verify and spec.gguf:
            got = sha256_file(MODELS_DIR / spec.gguf)
            extra = " sha256 OK" if got == spec.sha256 else f" SHA MISMATCH {got}"
        print(f"{spec.name:15s} {spec.kind:5s} {spec.role:10s} {spec.base_url:28s} {status}{extra}")


if __name__ == "__main__":
    main()

"""Build the Gemini priority-tier request files by re-targeting existing gpt-6.1-terra requests.

Prompt text, input, targets, namespace, temperature and max_tokens stay byte-identical; only `model` changes and
request_key is recomputed with build_requests.request_key (same function as every other model). Source rows = the
terra rows of runs/requests/{legend1,hw,hwctl}.jsonl. Existing request keys are never touched.

Tiers (priority order, plan in analysis/model_breadth/GEMINI_PLAN.md):
  t1  legend test: polarity bare, arm a (P0) and arm c (P0m), draw d1                (src legend1)
  t2  cue restoration: hw1 polarity + speech_act, channels chip1, noncrit            (src hw)
                       and irrel, nlcue                                              (src hwctl)
  t3  rest of hw1 P0: bare, chip1, full on all 6 dimensions (minus what t2 already holds)  (src hw)
Every row gets `tier` and `gemini_run` (legend | hw | hwctl: which items file / run directory the row belongs to).

    python src/build_gemini_requests.py                       # both models, full tiers
    python src/build_gemini_requests.py --subset gemini-2.5-pro:1:200   # tier 1 for pro capped to a stratified 200
Writes runs/requests/gemini_<model>_t<k>.jsonl, runs/requests/gemini_<model>_run_<run>.jsonl and
analysis/model_breadth/gemini_request_counts.json.
"""
import argparse, hashlib, json, random, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "src"))
import models as M
from build_requests import request_key

SRC = "gpt-6.1-terra"
POL_SA = {"polarity", "speech_act"}


def load(name):
    return [json.loads(l) for l in (ROOT / f"runs/requests/{name}.jsonl").read_text().splitlines() if l.strip()]


def tiers():
    leg, hw, ctl = ([r for r in load(n) if r["model"] == SRC] for n in ("legend1", "hw", "hwctl"))
    chans = lambda r: {t["channel"] for t in r["targets"]}
    t1 = [("legend", r) for r in leg if r.get("namespace") == "d1" and r["prompt_id"] in ("P0", "P0m")]
    t2 = [("hw", r) for r in hw if r["dimension"] in POL_SA and r["prompt_id"] == "P0" and chans(r) & {"chip1", "noncrit"}]
    t2 += [("hwctl", r) for r in ctl if r["dimension"] in POL_SA and r["prompt_id"] == "P0" and chans(r) & {"irrel", "nlcue"}]
    have = {r["request_key"] for _, r in t2}
    t3 = [("hw", r) for r in hw if r["prompt_id"] == "P0" and chans(r) & {"bare", "chip1", "full"} and r["request_key"] not in have]
    return [t1, t2, t3]


def stratified(rows, n, seed=20261101):
    """Deterministic stratified subset: strata = (gemini_run, dimension, first target channel, prompt_id, namespace);
    each stratum contributes round-robin by sha256(request_key) order until n rows are taken."""
    strata = {}
    for r in sorted(rows, key=lambda r: hashlib.sha256((str(seed) + r["request_key"]).encode()).hexdigest()):
        k = (r["gemini_run"], r["dimension"], r["targets"][0]["channel"], r["prompt_id"], r.get("namespace"))
        strata.setdefault(k, []).append(r)
    out, lists = [], [strata[k] for k in sorted(strata, key=str)]
    while len(out) < n and any(lists):
        for l in lists:
            if l and len(out) < n:
                out.append(l.pop(0))
    keep = {r["request_key"] for r in out}
    return [r for r in rows if r["request_key"] in keep]   # original order


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="gemini-3.5-flash,gemini-3.1-flash-lite")
    ap.add_argument("--subset", action="append", default=[], help="MODEL:TIER:N stratified cap (repeatable)")
    a = ap.parse_args()
    caps = {(m, int(t)): int(n) for m, t, n in (s.split(":") for s in a.subset)}
    T = tiers(); counts = {}
    cache = ROOT / "runs/cache"
    for name in a.models.split(","):
        spec = M.get(name); runs = {}
        for ti, rows in enumerate(T, 1):
            out, seen = [], set()
            for run, r in rows:
                r = dict(r); r["model"] = name; r["tier"] = ti; r["gemini_run"] = run
                r["request_key"] = request_key(spec.model, r["prompt_id"], r["prompt"], r["temperature"], r["sample_idx"], r.get("namespace"))
                if r["request_key"] in seen:
                    continue
                seen.add(r["request_key"]); out.append(r)
            full = len(out)
            if (name, ti) in caps:
                out = stratified(out, caps[(name, ti)])
            (ROOT / f"runs/requests/gemini_{name}_t{ti}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
            for r in out:
                runs.setdefault(r["gemini_run"], []).append(r)
            cached = sum((cache / f"{r['request_key']}.json").exists() for r in out)
            counts[f"{name}:t{ti}"] = {"requests": len(out), "full_tier": full, "cached": cached,
                                        "by_run": dict(Counter(r["gemini_run"] for r in out)),
                                        "by_dimension": dict(Counter(r["dimension"] for r in out))}
        for run, rows in runs.items():
            (ROOT / f"runs/requests/gemini_{name}_run_{run}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    p = ROOT / "analysis/model_breadth"; p.mkdir(parents=True, exist_ok=True)
    (p / "gemini_request_counts.json").write_text(json.dumps(counts, indent=1))
    for k, v in counts.items():
        print(k, v["requests"], "of", v["full_tier"], "cached", v["cached"], v["by_run"])


if __name__ == "__main__":
    main()

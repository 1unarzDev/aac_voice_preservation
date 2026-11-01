"""Build generation requests from family files (SPEC v0.1).

One request per unique (model, prompt_id, rendered prompt, temperature, sample_idx).
Identical renders are deduplicated: e.g. `bare`/`noncrit` are the same for variants A and
B, so they become ONE request whose `targets` list maps back to every
(family_id, variant, channel) that uses it.

Channels (input_text):
  bare     "Keywords: <bare>"
  noncrit  "Keywords: <bare with the noncritical word inserted in source order>"
  chip1    "Keywords: <variant chips> <bare>"
  chipall  "Keywords: <all_chips> <bare>"
  full     "The user typed: <source>"
Chips go first, in the fixed legend order (prompts.CHIP_ORDER); words keep source order.

Custom channels (follow-up experiments, D-012): a family may carry
  "custom_channels": {variant: {channel_id: input_text | {"input": str,
                      "commitments": [chips], "prompts": [prompt ids]}}}
and then ONLY those channels are rendered for it (the 5 standard ones are skipped).
`commitments` = the chip-equivalent commitments the input carries (for alias / natural-
language encodings; default: the vocabulary chips found in the text); attribute.py uses it.
`prompts` restricts a channel to some prompt ids (e.g. channels that need the P0x legend).
--namespace d1[,d2] salts request_key (fresh cache entries per draw); without it keys are
unchanged. Families with split smoke/expB/expC are only included when --split names them.

  python src/build_requests.py --items 'data/items/*.jsonl' --out runs/requests/all.jsonl \
      [--split pilot] [--models qwen2.5-7b,gpt-6.1-terra] [--prompts P0,P2] [--channels bare,full]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models as M  # noqa: E402
import prompts as P  # noqa: E402

CHANNELS = ["bare", "noncrit", "chip1", "chipall", "full"]
OPT_IN_SPLITS = {"smoke", "expB", "expC", "wb", "r2", "r2d"}   # never included by default (wb = W-B corpus items; r2/r2d = PREREG_R2 W-C/W-D)


def custom_spec(fam: dict, vname: str, channel: str) -> dict:
    """Normalised custom channel: {"input", "commitments", "prompts"}."""
    c = fam["custom_channels"][vname][channel]
    if isinstance(c, str):
        c = {"input": c}
    chips = c.get("commitments")
    if chips is None:
        chips = [t for t in re.findall(r"\[[^\]]+\]", c["input"]) if t in P.CHIP_ORDER]
    return {"input": c["input"], "commitments": list(chips), "prompts": c.get("prompts")}


def channels_for(fam: dict, vname: str, channels: list[str]) -> list[str]:
    if fam.get("custom_channels"):
        return list(fam["custom_channels"][vname])
    return channels


def _tokens(s: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", s.lower())


def insert_in_source_order(bare: str, word: str, source: str) -> str:
    """Insert `word` among the bare keywords at its position in the source sentence.
    Keywords are matched to source tokens by a 3-letter prefix (go~going); if the
    noncritical word can't be located it is appended."""
    src = _tokens(source)
    kws = bare.split()
    try:
        wpos = src.index(word.lower().split()[0])
    except ValueError:
        return f"{bare} {word}"
    pos, cursor = [], 0
    for kw in kws:
        k = kw.lower()[:3]
        hit = next((i for i in range(cursor, len(src)) if src[i].startswith(k)), None)
        pos.append(hit if hit is not None else 10**6)
        cursor = hit + 1 if hit is not None else cursor
    i = next((j for j, p in enumerate(pos) if p > wpos), len(kws))
    return " ".join(kws[:i] + [word] + kws[i:])


def input_text(fam: dict, vname: str, channel: str) -> str:
    v = fam["variants"][vname]
    if fam.get("custom_channels"):
        return custom_spec(fam, vname, channel)["input"]
    if channel == "full":
        return f"The user typed: {v['source']}"
    if channel == "bare":
        words = fam["bare"]
    elif channel == "noncrit":
        words = insert_in_source_order(fam["bare"], fam["noncritical"], v["source"])
    elif channel == "chip1":
        words = " ".join(P.sort_chips(v["chips"]) + [fam["bare"]])
    elif channel == "chipall":
        words = " ".join(P.sort_chips(v["all_chips"]) + [fam["bare"]])
    else:
        raise ValueError(channel)
    return f"Keywords: {words}"


def validate(fam: dict) -> None:
    fid = fam.get("family_id", "?")
    for vn, v in fam["variants"].items():
        if not v.get("chips"):
            raise ValueError(f"{fid}/{vn}: every variant needs >=1 chip (use a counter-chip)")
        P.sort_chips(v["chips"]); P.sort_chips(v["all_chips"])
        if not set(v["chips"]) <= set(v["all_chips"]):
            print(f"warning: {fid}/{vn}: chips not a subset of all_chips", file=sys.stderr)
        if v["critical_value"] not in fam["critical_options"]:
            raise ValueError(f"{fid}/{vn}: critical_value not in critical_options")
    if fam.get("custom_channels"):
        if set(fam["custom_channels"]) != set(fam["variants"]):
            raise ValueError(f"{fid}: custom_channels must have one entry per variant")
        for vn, chs in fam["custom_channels"].items():
            for ch in chs:
                cs = custom_spec(fam, vn, ch)
                P.sort_chips(cs["commitments"])
                for pid in cs["prompts"] or []:
                    if pid not in P.PROMPTS:
                        raise ValueError(f"{fid}/{vn}/{ch}: unknown prompt {pid}")


def request_key(model: str, prompt_id: str, prompt: str, temperature: float, sample_idx: int,
                namespace: str | None = None) -> str:
    parts = [model, prompt_id, prompt, temperature, sample_idx]
    if namespace:   # salt only when given: un-namespaced keys are byte-identical to before
        parts.append(f"ns:{namespace}")
    blob = json.dumps(parts, ensure_ascii=False)
    return hashlib.sha1(blob.encode()).hexdigest()


def load_families(pattern: str, split: str | None) -> list[dict]:
    fams = []
    for path in sorted(glob.glob(pattern)):
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                fam = json.loads(line)
                fam["_file"] = Path(path).name
                if fam.get("dropped") is True:   # verifier DROP (keeps the record, never builds it); absent = included
                    print(f"skip dropped family {fam.get('family_id')}: {fam.get('drop_reason', '')}", file=sys.stderr)
                    continue
                # smoke families live in data/items too; only included when asked for explicitly
                if (split is None and fam.get("split") not in OPT_IN_SPLITS) or fam.get("split") == split:
                    validate(fam)
                    fams.append(fam)
    return fams


def build(fams: list[dict], model_names: list[str], prompt_ids: list[str],
          channels: list[str], namespaces: list[str | None] = (None,)) -> list[dict]:
    reqs: dict[str, dict] = {}
    for ns, fam in [(n, f) for n in namespaces for f in fams]:
        for vname in fam["variants"]:
            for ch in channels_for(fam, vname, channels):
                text = input_text(fam, vname, ch)
                only = custom_spec(fam, vname, ch)["prompts"] if fam.get("custom_channels") else None
                for pid in prompt_ids:
                    if only and pid not in only:
                        continue
                    ps = P.PROMPTS[pid]
                    prompt = P.render(pid, text, fam.get("context"))
                    for mname in model_names:
                        spec = M.get(mname)
                        for s in range(ps.k):
                            key = request_key(spec.model, pid, prompt, ps.temperature, s, ns)
                            target = {"family_id": fam["family_id"], "variant": vname, "channel": ch}
                            if key in reqs:
                                reqs[key]["targets"].append(target)
                                continue
                            reqs[key] = {
                                "request_key": key, "model": mname, "prompt_id": pid,
                                "prompt_sha": P.template_sha(pid), "temperature": ps.temperature,
                                "sample_idx": s, "max_tokens": ps.max_tokens,
                                "n_suggestions": ps.n_suggestions,
                                "family_id": fam["family_id"], "dimension": fam["dimension"],
                                "split": fam.get("split"), "items_file": fam["_file"],
                                "input_text": text, "prompt": prompt, "targets": [target]}
                            if ns:
                                reqs[key]["namespace"] = ns
    return list(reqs.values())


def _csv(s: str | None, default: list[str]) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()] if s else default


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--items", default="data/items/*.jsonl")
    ap.add_argument("--out", default="runs/requests/requests.jsonl")
    ap.add_argument("--split")
    ap.add_argument("--models", help=f"comma list (default: {','.join(M.UNDER_TEST)})")
    ap.add_argument("--prompts", help=f"comma list of {','.join(P.PROMPTS)} (default {','.join(P.DEFAULT_PROMPTS)})")
    ap.add_argument("--channels", help=f"comma list of {','.join(CHANNELS)} (default all)")
    ap.add_argument("--namespace", help="comma list of cache-key salts, one request set each (e.g. d1,d2)")
    a = ap.parse_args()
    model_names = _csv(a.models, M.UNDER_TEST)
    prompt_ids = _csv(a.prompts, P.DEFAULT_PROMPTS)
    channels = _csv(a.channels, CHANNELS)
    for c in channels:
        if c not in CHANNELS:
            raise SystemExit(f"unknown channel {c}")
    for p in prompt_ids:
        if p not in P.PROMPTS:
            raise SystemExit(f"unknown prompt {p}")
    fams = load_families(a.items, a.split)
    reqs = build(fams, model_names, prompt_ids, channels, _csv(a.namespace, [None]))
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in reqs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_targets = sum(len(r["targets"]) for r in reqs)
    print(f"{len(fams)} families -> {n_targets} (target x sample) cells -> {len(reqs)} unique requests -> {out}")


if __name__ == "__main__":
    main()

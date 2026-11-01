"""Run-directory adapter shared by judge.py, attribute.py and make_gold.py.

The harness (generate.py / explode.py, not ours) writes runs/<run_id>/unique_outputs.jsonl.
We normalise whatever mapping it provides into OCCURRENCE rows, one per
(request, sample, suggestion):

  output_id, text, request_id, model, prompt_id, channel, family_id, variant,
  input_text (the VISIBLE input string), sample_idx, suggestion_idx, valid

Accepted layouts (first match wins):
  1. runs/<run>/exploded.jsonl (or explode.jsonl / occurrences.jsonl): one occurrence
     per line, with output_id; text is taken from unique_outputs.jsonl if absent.
  2. unique_outputs.jsonl rows carrying a list field `occurrences` / `requests` /
     `members` / `sources` of occurrence dicts.
  3. unique_outputs.jsonl rows that are themselves occurrences (have family_id).
Field aliases are resolved by ALIASES below; extend it rather than editing callers.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALIASES = {
    "prompt_id": ["prompt_id", "prompt", "prompt_name"],
    "channel": ["channel", "channel_id"],
    "model": ["model", "model_name", "model_id"],
    "input_text": ["input_text", "visible_input", "input", "user_input", "input_str"],
    "family_id": ["family_id", "family", "item_id"],
    "variant": ["variant", "variant_id"],
    "request_id": ["request_id", "req_id", "generation_id", "gen_id"],
    "sample_idx": ["sample_idx", "sample", "k_idx"],
    "suggestion_idx": ["suggestion_idx", "suggestion", "sugg_idx", "idx_in_response"],
    "valid": ["valid"],
    "text": ["text", "output", "suggestion_text", "sentence"],
}
# outputs.jsonl is what src/explode.py writes (one row per generation x suggestion x target)
MAP_FILES = ["outputs.jsonl", "exploded.jsonl", "explode.jsonl", "occurrences.jsonl"]
LIST_FIELDS = ["occurrences", "requests", "members", "sources"]


def text_key(text: str) -> str:
    """Same key explode.py uses (sha1 of its normalised text), so judgments join on text."""
    try:
        from explode import normalise, sha1
    except Exception:  # noqa: BLE001 -- harness module missing: equivalent fallback
        import hashlib
        import re
        import unicodedata

        def normalise(t):
            t = unicodedata.normalize("NFKC", t).replace("\u2019", "'").replace("\u2018", "'")
            t = re.sub(r"\s+", " ", t.lower()).strip()
            return t[:-1].rstrip() if t.endswith(".") and not t.endswith("..") else t

        def sha1(*parts):
            return hashlib.sha1(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()[:16]
    return sha1(normalise(text))


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def _norm(r: dict) -> dict:
    out = dict(r)
    for canon, names in ALIASES.items():
        for n in names:
            if n in r and r[n] is not None:
                out[canon] = r[n]
                break
    out.setdefault("sample_idx", 0)
    out.setdefault("text_id", text_key(out.get("text") or ""))
    out.setdefault("suggestion_idx", 0)
    txt = (out.get("text") or "")
    out["text"] = txt
    if "valid" not in out:
        out["valid"] = bool(txt.strip())
    out["valid"] = bool(out["valid"]) and bool(txt.strip())
    return out


def load_occurrences(run_dir: Path) -> list[dict]:
    run_dir = Path(run_dir)
    uo_path = run_dir / "unique_outputs.jsonl"
    uniq = read_jsonl(uo_path) if uo_path.exists() else []
    text_of = {u["output_id"]: _norm(u)["text"] for u in uniq if "output_id" in u}

    for name in MAP_FILES:
        p = run_dir / name
        if p.exists():
            occ = []
            for r in read_jsonl(p):
                r = dict(r)
                if not r.get("text") and r.get("output_id") in text_of:
                    r["text"] = text_of[r["output_id"]]
                occ.append(_norm(r))
            return occ
    occ = []
    for u in uniq:
        lf = next((f for f in LIST_FIELDS if isinstance(u.get(f), list)), None)
        if lf:
            for m in u[lf]:
                occ.append(_norm({**m, "output_id": u["output_id"],
                                  "text": u.get("text", m.get("text", ""))}))
        elif "family_id" in u or "family" in u:
            occ.append(_norm(u))
    if not occ:
        raise SystemExit(f"no occurrence mapping found in {run_dir} "
                         f"(looked for {MAP_FILES} or list fields {LIST_FIELDS})")
    return occ


def load_items(paths=None) -> dict[str, dict]:
    """family_id -> item. Default: every data/items/*.jsonl (family ids are unique)."""
    if paths is None:
        paths = sorted((ROOT / "data/items").glob("*.jsonl"))
    elif isinstance(paths, (str, Path)):
        paths = [Path(paths)]
    out: dict[str, dict] = {}
    for p in paths:
        for r in read_jsonl(Path(p)):
            if r["family_id"] in out:
                raise SystemExit(f"duplicate family_id {r['family_id']} in {p}")
            out[r["family_id"]] = r
    return out


def items_path_for(run_dir: Path, explicit: Path | None) -> Path:
    """--items, else runs/<run>/config.json:items_path, else None (= all data/items/*.jsonl)."""
    if explicit:
        return Path(explicit)
    cfg = Path(run_dir) / "config.json"
    if cfg.exists():
        c = json.loads(cfg.read_text())
        for k in ("items_path", "items", "probes"):
            if isinstance(c.get(k), str):
                p = Path(c[k])
                return p if p.is_absolute() else ROOT / p
    return None

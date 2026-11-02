"""Resample-without-feedback baseline (G1r) and matched-decoding feedback guard (G1t).

Design: analysis/guard_baseline/PLAN.md (written before any generation).

  python src/guard_baseline.py inventory
  python src/guard_baseline.py gen --set disc|wc --model <model> [--concurrency N]
  python src/guard_baseline.py assemble --set disc|wc      # runs/guard_baseline_<set>/generations.jsonl + explode
  (judge:)  python src/judge.py --run guard_baseline_<set> [--items analysis/guard_wc/items.jsonl] --concurrency 8
  python src/guard_baseline.py resolve --set S             # reuse existing critical resolutions, list new A-units
  python src/guard_baseline.py arbview --set S             # blind view of unresolved A-units (text + question only)
  python src/guard_baseline.py arbwrite --set S --decisions file.tsv
  python src/guard_baseline.py analyze

The monitor (supplied/check/feedback) and the selection rule are imported unchanged from
src/interventions.py. Only the retry decoding and the (absent) feedback text differ.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import interventions as I  # noqa: E402
import layer0  # noqa: E402
import models as M  # noqa: E402
import runio  # noqa: E402
from generate import CACHE, parse_output  # noqa: E402

ROOT = runio.ROOT
OUT = ROOT / "analysis/guard_baseline"
RETRY_T = 0.7          # the single decoding change (G1 retries ran at T=0)
SEED0 = 3000           # local seed for attempt k is SEED0 + k (distinct from the S3 seeds 1000..1002)
MAX_RETRIES = 2
ARMS = {"G1r": "resample", "G1t": "feedback"}
SETS = {
    "disc": dict(src=ROOT / "runs/guard1", items=None, run=ROOT / "runs/guard_baseline_disc"),
    "wc": dict(src=ROOT / "runs/guard_wc", items=ROOT / "analysis/guard_wc/items.jsonl",
               run=ROOT / "runs/guard_baseline_wc"),
}


def sha1(*p):
    return I.sha1(*p)


def flagged_firstpasses(s: str, model: str | None = None) -> list[dict]:
    rows = runio.read_jsonl(SETS[s]["src"] / "generations.jsonl")
    keep = ("attempts", "flags_final", "flags_initial", "guard_spec", "check_ms", "base_request_key", "changed",
            "extra_calls", "extra_latency_s", "extra_completion_tokens", "chosen_attempt", "guard_errors")
    out = []
    for r in rows:
        if r["prompt_id"] != "P0" or not r["flags_initial"] or not r["suggestions"]:
            continue
        if model and r["model"] != model:
            continue
        out.append({k: v for k, v in r.items() if k not in keep})
    return out


class Caller(I.Caller):
    """Same transport as the guard; decoding temperature and seed are per call and part of the cache key."""

    def __init__(self, conc_local=4, conc_api=4):
        super().__init__(conc_local=conc_local, conc_api=conc_api, retries=3)

    async def chat_t(self, model, tag, messages, temperature, seed, max_tokens=96):
        spec = M.get(model)
        body = {"model": spec.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if spec.supports_seed:
            body["seed"] = seed
        key = sha1(spec.model, tag, messages, temperature, body.get("seed"))
        cpath = CACHE / f"{key}.json"
        if cpath.exists():
            return {**json.loads(cpath.read_text()), "cached": True, "key": key}
        err = None
        async with self._sem(spec):
            for attempt in range(1, self.retries + 1):
                t0 = time.perf_counter()
                try:
                    r = await self.client.post(spec.base_url + "/chat/completions", json=body,
                                               headers=M.headers(spec), timeout=180)
                    if r.status_code == 200:
                        j = r.json()
                        res = {"raw_text": j["choices"][0]["message"].get("content") or "",
                               "finish_reason": j["choices"][0].get("finish_reason"),
                               "latency_s": round(time.perf_counter() - t0, 3), "usage": j.get("usage")}
                        tmp = cpath.with_suffix(".tmp")
                        tmp.write_text(json.dumps(res, ensure_ascii=False)); tmp.replace(cpath)
                        return {**res, "cached": False, "key": key}
                    err = f"HTTP {r.status_code}: {r.text[:200]}"
                    if r.status_code < 500 and r.status_code != 429:
                        break
                except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
                    err = f"{type(e).__name__}: {e}"[:200]
                await asyncio.sleep(2 ** attempt)
        return {"error": err, "key": key}


async def variant_one(caller: Caller, g: dict, items: dict, arm: str, src_cache: dict, log: Path) -> dict:
    """arm G1r: retry = original single-turn prompt, no feedback, T=0.7, new seed per attempt.
    arm G1t: retry = G1's conversation (assistant raw + feedback turn), T=0.7, new seed per attempt."""
    prompt = I.render_checked(g, items)
    text0 = g["suggestions"][0]
    src_lab = None
    if g["input_text"].startswith("The user typed:"):
        s = g["input_text"].split(":", 1)[1].strip()
        src_lab = src_cache.setdefault(s, layer0.label(s))
    spec = I.supplied(g["input_text"], src_lab)
    flags0 = I.check(text0, spec)
    attempts = [{"text": text0, "flags": flags0, "raw": g.get("raw_text") or text0}]
    calls, lat, ctok, errors, cached = 0, 0.0, 0, [], 0
    msgs = [{"role": "user", "content": prompt}]
    flags = flags0
    while flags and len(attempts) <= MAX_RETRIES:
        k = len(attempts)
        if arm == "G1t":
            msgs = msgs + [{"role": "assistant", "content": attempts[-1]["raw"]},
                           {"role": "user", "content": I.feedback(flags)}]
            send = msgs
        else:
            send = [{"role": "user", "content": prompt}]
        res = await caller.chat_t(g["model"], f"{arm}-v1-a{k}", send, RETRY_T, SEED0 + k)
        calls += 1
        with log.open("a") as f:
            f.write(json.dumps(dict(arm=arm, model=g["model"], key=res.get("key"), cached=res.get("cached", False),
                                    error=res.get("error"), t=time.time())) + "\n")
        if "error" in res:
            errors.append(res["error"]); break
        cached += bool(res.get("cached"))
        lat += res.get("latency_s") or 0.0
        ctok += I._ctok(res)
        sug, _, _ = parse_output(res["raw_text"], 1)
        t = sug[0] if sug else ""
        flags = I.check(t, spec) if t else ["empty"]
        attempts.append({"text": t, "flags": flags, "raw": res["raw_text"] or t})
    best = min(range(len(attempts)), key=lambda i: (len(attempts[i]["flags"]), i))
    final = attempts[best]
    base = {k: v for k, v in g.items() if k not in ("suggestions", "raw_text", "cached")}
    return {**base, "base_request_key": g["request_key"], "flags_initial": flags0,
            "prompt_id": arm, "request_key": sha1(g["request_key"], arm, "gb-v1")[:40],
            "raw_text": final["raw"], "suggestions": [final["text"]] if final["text"] else [],
            "parse_ok": bool(final["text"]), "flags_final": final["flags"], "chosen_attempt": best,
            "attempts": [{"text": a["text"], "flags": a["flags"]} for a in attempts],
            "extra_calls": calls, "cached_calls": cached, "extra_latency_s": round(lat, 3),
            "extra_completion_tokens": ctok, "changed": final["text"] != text0, "guard_errors": errors,
            "retry_temperature": RETRY_T, "retry_seed0": SEED0}


async def gen(a) -> None:
    items = runio.load_items(SETS[a.set]["items"]) if SETS[a.set]["items"] else runio.load_items()
    gs = flagged_firstpasses(a.set, a.model)
    run = SETS[a.set]["run"]
    (run / "parts").mkdir(parents=True, exist_ok=True)
    path = run / "parts" / f"gb_{a.model}.jsonl"
    done = {(r["base_request_key"], r["prompt_id"]) for r in runio.read_jsonl(path)} if path.exists() else set()
    caller = Caller(conc_local=a.concurrency, conc_api=a.concurrency)
    log = run / "calls.jsonl"
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=16)) as client:
        caller.client = client
        src_cache: dict = {}

        async def one(g, arm):
            row = await variant_one(caller, g, items, arm, src_cache, log)
            with path.open("a") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            return row
        rows = await asyncio.gather(*(one(g, arm) for g in gs for arm in ARMS
                                      if (g["request_key"], arm) not in done))
    errs = sum(bool(r["guard_errors"]) for r in rows)
    print(f"{a.set} {a.model}: {len(gs)} flagged first passes, {len(rows)} new rows, {errs} with call errors", flush=True)


def inventory(a=None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inv = {}
    for s in SETS:
        gs = flagged_firstpasses(s)
        g1 = [r for r in runio.read_jsonl(SETS[s]["src"] / "generations.jsonl") if r["prompt_id"] == "G1" and r["flags_initial"]]
        inv[s] = dict(flagged_unique_requests=len(gs), by_model=dict(Counter(g["model"] for g in gs)),
                      g1_logical_calls=sum(r["extra_calls"] for r in g1),
                      max_new_calls_per_arm=MAX_RETRIES * len(gs), arms=sorted(ARMS))
    (OUT / "inventory.json").write_text(json.dumps(inv, indent=2) + "\n")
    print(json.dumps(inv, indent=2))


def assemble(a) -> None:
    run = SETS[a.set]["run"]
    rows = []
    for p in sorted((run / "parts").glob("gb_*.jsonl")):
        rows += runio.read_jsonl(p)
    exp = 2 * len(flagged_firstpasses(a.set))
    assert len(rows) == exp and len({(r["request_key"]) for r in rows}) == exp, (len(rows), exp)
    runio.write_jsonl(run / "generations.jsonl", rows)
    (run / "config.json").write_text(json.dumps(dict(
        run_id=run.name, kind="guard baseline G1r/G1t", n_rows=len(rows),
        items_path=str(SETS[a.set]["items"].relative_to(ROOT)) if SETS[a.set]["items"] else None,
        by_prompt=dict(Counter(r["prompt_id"] for r in rows)), retry_temperature=RETRY_T, seed0=SEED0), indent=2) + "\n")
    subprocess.run([sys.executable, "src/explode.py", "--run", str(run)], cwd=ROOT, check=True)


# ----------------------------------------------------------------------------- arbitration
def _akey(text_id, dim, opts):
    return (text_id, dim, tuple(opts))


def _existing_arbiter_units(s: str) -> dict:
    """A-unit (text_id, dim, options) -> existing arbiter decision (frozen runs only)."""
    paths = ([ROOT / "analysis/guard_wc/frozen/runs/r2c1/arbiter.jsonl", ROOT / "runs/guard_wc/arbiter.jsonl",
              ROOT / "runs/r2c1/arbiter.jsonl"] if s == "wc" else [])
    items = runio.load_items(SETS[s]["items"]) if SETS[s]["items"] else runio.load_items()
    old = {}
    for p in paths:
        if not p.exists():
            continue
        for r in runio.read_jsonl(p):
            it = items.get(r["family_id"])
            if it is None:
                continue
            old.setdefault(_akey(r["text_id"], it["dimension"], it["critical_options"]), r["critical"])
    return old


def _resolution_table() -> dict:
    t = {}
    for r in runio.read_jsonl(ROOT / "annotation/label_resolution.jsonl"):
        if r.get("critical") is not None:
            t[(r["text_id"], r["input_text"], r["dimension"])] = r["critical"]
    return t


def resolve(a) -> None:
    run = SETS[a.set]["run"]
    js = runio.read_jsonl(run / "judgments.jsonl")
    old, table = _existing_arbiter_units(a.set), _resolution_table()
    arb, need = [], {}
    for j in js:
        if j.get("critical") is not None and j.get("needs_arbiter") is not True:
            continue
        o = j["critical_options"]
        o = list(o) if not isinstance(o, str) else __import__("ast").literal_eval(o)
        k = _akey(j["text_id"], j["dimension"], o)
        c = old.get(k) or table.get((j["text_id"], j["input_text"], j["dimension"]))
        if j.get("critical") is not None:
            continue
        if c is not None:
            arb.append(dict(text_id=j["text_id"], family_id=j["family_id"], input_text=j["input_text"], critical=c,
                            dimension=j["dimension"], text=j["text"], provenance="reused existing resolution"))
        else:
            need.setdefault(k, j)
    existing_new = {}
    p = run / "arbiter_new.jsonl"
    if p.exists():
        for r in runio.read_jsonl(p):
            existing_new[_akey(r["text_id"], r["dimension"], r["critical_options"])] = r["critical"]
    for k, j in list(need.items()):
        if k in existing_new:
            for jj in js:
                if jj["text_id"] == j["text_id"] and jj["dimension"] == j["dimension"] and jj.get("critical") is None:
                    arb.append(dict(text_id=jj["text_id"], family_id=jj["family_id"], input_text=jj["input_text"],
                                    critical=existing_new[k], dimension=jj["dimension"], text=jj["text"],
                                    provenance="new blind arbiter"))
            del need[k]
    runio.write_jsonl(run / "arbiter.jsonl", arb)
    inv = [dict(a_unit="|".join([k[0], k[1], "/".join(k[2])]), text_id=k[0], dimension=k[1], critical_options=list(k[2]),
                text=j["text"], blind_order_key=hashlib.sha256("|".join([k[0], k[1], "/".join(k[2])]).encode()).hexdigest())
           for k, j in need.items()]
    inv.sort(key=lambda x: x["blind_order_key"])
    (run / "arbiter_inventory.json").write_text(json.dumps(inv, indent=1, ensure_ascii=False))
    print(f"{a.set}: {len(arb)} J-units resolved from existing/new arbitration; {len(inv)} A-units need a blind arbiter")


def arbview(a) -> None:
    from judge import critical_question
    inv = json.loads((SETS[a.set]["run"] / "arbiter_inventory.json").read_text())
    shown = set()
    for u in inv:
        if u["dimension"] not in shown:
            print(f"=== {u['dimension']}: {critical_question(u['dimension'], u['critical_options'])}\n    options: {u['critical_options']}")
            shown.add(u["dimension"])
        print(f"[{u['blind_order_key'][:8]}] {u['text']}")


def arbwrite(a) -> None:
    run = SETS[a.set]["run"]
    inv = json.loads((run / "arbiter_inventory.json").read_text())
    dec = {}
    for r in csv.reader(open(a.decisions), delimiter="\t"):
        if r and not r[0].startswith("#"):
            dec[r[0]] = (r[1], r[2] if len(r) > 2 else "")
    out = []
    for u in inv:
        hits = [k for k in dec if u["blind_order_key"].startswith(k)]
        assert len(hits) == 1, (u["a_unit"], hits)
        c, why = dec[hits[0]]
        assert c in u["critical_options"], (hits, c)
        out.append(dict(text_id=u["text_id"], dimension=u["dimension"], critical_options=u["critical_options"], text=u["text"],
                        critical=c, rationale=why, arbiter_model="claude-sonnet-5-5",
                        arbitration_view="blind: output text + production critical question/options only"))
    with (run / "arbiter_new.jsonl").open("a") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} decisions")


# ------------------------------------------------------------------------------ analysis
def _load_wc_analyze():
    sys.path.insert(0, str(ROOT / "src"))
    spec = importlib.util.spec_from_file_location("guard_wc_analyze", ROOT / "analysis/guard_wc/analyze.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def build_raw(s: str):
    """Raw scored table with P0, G1, G1s (existing labels) plus G1r, G1t: unflagged inputs inherit the G1 row
    (identical to P0); flagged inputs take the new output; an unchanged text keeps the baseline P0 labels."""
    import pandas as pd
    import attribute
    run, cfg = SETS[s]["run"], SETS[s]
    if s == "wc":
        base = pd.read_parquet(ROOT / "runs/guard_wc/scored.parquet")
    else:
        base = attribute.score(cfg["src"], None, resolution=ROOT / "annotation/label_resolution.jsonl")
    new = attribute.score(run, cfg["items"])
    KEY = ["model", "family_id", "variant", "channel"]
    b0 = {tuple(r[k] for k in KEY): r for r in base[base.prompt_id == "P0"].to_dict("records")}
    g1 = {tuple(r[k] for k in KEY): r for r in base[base.prompt_id == "G1"].to_dict("records")}
    newd = {(tuple(r[k] for k in KEY), r["prompt_id"]): r for r in new.to_dict("records")}
    rows = base.to_dict("records")
    gens = {g["request_key"]: g for g in runio.read_jsonl(cfg["src"] / "generations.jsonl")}
    ngens = {g["request_key"]: g for g in runio.read_jsonl(run / "generations.jsonl")}
    for key, g in g1.items():
        for arm in ARMS:
            if (key, arm) in newd:
                r = newd[(key, arm)]
                if r["text"] == b0[key]["text"]:
                    ident = {k: r[k] for k in ("output_id", "text_id", "request_key", "prompt_id", "text", "input_text")}
                    r = {**b0[key], **ident}
            else:
                r = {**g, "prompt_id": arm}      # not flagged: no retry, identical to P0/G1
            rows.append(r)
    return pd.DataFrame(rows), {**gens, **ngens}


def analyze(a) -> None:
    import numpy as np
    import pandas as pd
    import analyze as A
    import labels
    W = _load_wc_analyze()
    W.OUT = OUT
    KEY = W.KEY
    summary, tables, cost = {}, {}, {}
    for s in SETS:
        cfg = SETS[s]
        items = runio.load_items(cfg["items"]) if cfg["items"] else runio.load_items()
        raw, gens = build_raw(s)
        raw["quarantine_refusal_acceptance"] = raw.quarantine_refusal_acceptance.fillna(False).astype(bool)
        if s == "disc":
            raw = raw[~raw.quarantine_refusal_acceptance]
        frame = A.normalize_table(raw, items)
        for col in ("base_key", "flags_initial", "flags_final", "changed", "extra_calls"):
            if col == "base_key":
                frame[col] = [gens[k].get("base_request_key", k) if k in gens else k for k in frame.request_key]
            elif col == "changed":
                frame[col] = [bool(gens.get(k, {}).get(col, False)) for k in frame.request_key]
            else:
                frame[col] = [gens.get(k, {}).get(col) for k in frame.request_key]
        frame["cluster_id"] = frame.family_id.map(lambda f: items[f].get("cluster_id", f))
        frame["joint"] = pd.to_numeric(frame.constraint_preserving).astype(float)
        strict = []
        for r in frame.itertuples():
            if not r.cue_in_input:
                strict.append(np.nan); continue
            cp = r.joint
            spec = labels.general_spec(items[r.family_id]["variants"][r.variant].get("all_chips", []),
                                       items[r.family_id]["variants"][r.variant].get("general_spec"))
            if cp == 0 or r.politeness_added is True:
                strict.append(0.)
            elif not A.known(cp) or (spec["politeness"] == {"none"} and not A.known(r.politeness)):
                strict.append(np.nan)
            else:
                strict.append(1.)
        frame["strict"] = strict
        cue = frame[frame.cue_in_input.astype(bool)].copy()
        cue = cue[cue.channel.isin(["chip1", "chipall", "full"])]
        n_planned = cue[cue.prompt_id == "P0"].shape[0]
        for arm in ("G1", "G1s", "G1r", "G1t"):
            assert cue[cue.prompt_id == arm].shape[0] == n_planned, (s, arm)
        frame.to_parquet(OUT / f"scored_{s}.parquet", index=False)
        pairs = {}
        for arm in ("G1", "G1s", "G1r", "G1t"):
            b = cue[cue.prompt_id == "P0"].set_index(KEY)
            t = cue[cue.prompt_id == arm].set_index(KEY)
            p = b.join(t, lsuffix="_P0", rsuffix="_arm", validate="one_to_one").reset_index()
            p["cluster_id"] = p.cluster_id_P0
            pairs[arm] = p
            p.drop(columns=[c for c in p.columns if c.startswith(("flags_", "attempts"))]).to_parquet(
                OUT / f"paired_{s}_{arm}.parquet", index=False)
        res = {"n_targets": int(n_planned), "n_families": int(cue.family_id.nunique()),
               "arms": {}, "paired": {}, "contrasts": {}}
        for arm, p in pairs.items():
            res["arms"][arm] = {k: W.metric(cue[cue.prompt_id == arm], cue[cue.prompt_id == arm][c])
                                for k, c in [("joint_pass", "joint"), ("strict_pass", "strict")]}
            res["paired"][arm] = W.pair_metrics(p)
        c0 = cue[cue.prompt_id == "P0"]
        res["arms"]["P0"] = {k: W.metric(c0, c0[c]) for k, c in [("joint_pass", "joint"), ("strict_pass", "strict")]}
        # contrasts: arm X minus arm Y on paired targets (all targets, includes unflagged = zero difference)
        def contrast(x, y, ep):
            px, py = pairs[x].set_index(KEY), pairs[y].set_index(KEY)
            d = (px[ep + "_arm"] - py[ep + "_arm"]).reset_index()
            d["family_id"] = d.family_id
            frame_c = px.reset_index()[KEY + ["cluster_id"]].copy()
            frame_c["d"] = d[0].values if 0 in d else d.iloc[:, -1].values
            r = W.metric(frame_c, frame_c.d)
            only = int((px[ep + "_arm"].eq(1) & py[ep + "_arm"].eq(0)).sum()), int((px[ep + "_arm"].eq(0) & py[ep + "_arm"].eq(1)).sum())
            r.update(x_only_pass=only[0], y_only_pass=only[1])
            return r
        for x, y in [("G1", "G1r"), ("G1t", "G1r"), ("G1", "G1t"), ("G1", "G1s"), ("G1r", "G1s"), ("G1t", "G1s")]:
            res["contrasts"][f"{x}-{y}"] = {ep: contrast(x, y, ep) for ep in ("joint", "strict")}
        # conditional on inputs where the guard fired (P0 flagged)
        fl = {}
        for arm, p in pairs.items():
            q = p[p.flags_initial_P0.map(bool)]
            fl[arm] = dict(n=len(q), joint_pass=float(np.nanmean(q.joint_arm)) if len(q) else None,
                           P0_joint_pass=float(np.nanmean(q.joint_P0)) if len(q) else None)
        res["flagged_targets"] = fl
        # ambiguous-channel politeness (secondary)
        amb = frame[frame.channel.isin(["bare", "noncrit"])]
        res["ambiguous_politeness_added"] = {
            arm: W.metric(amb[amb.prompt_id == arm], pd.to_numeric(amb[amb.prompt_id == arm].politeness_added).astype(float))
            for arm in ("P0", "G1", "G1s", "G1r", "G1t")} if len(amb) else {}
        # request-level cost and trajectory
        uniq = [g for g in gens.values() if g["prompt_id"] in ARMS and g["flags_initial"]]
        c = {}
        for arm in ARMS:
            us = [g for g in uniq if g["prompt_id"] == arm]
            c[arm] = dict(flagged_requests=len(us), logical_calls=sum(g["extra_calls"] for g in us),
                          cached_calls=sum(g.get("cached_calls", 0) for g in us),
                          call_errors=sum(bool(g["guard_errors"]) for g in us),
                          unflagged_after=sum(not g["flags_final"] for g in us),
                          changed=sum(g["changed"] for g in us),
                          first_attempt_unflagged=sum(len(g["attempts"]) > 1 and not g["attempts"][1]["flags"] for g in us),
                          identical_to_original=sum(any(x["text"] == g["attempts"][0]["text"] for x in g["attempts"][1:]) for g in us))
        g1u = [g for g in gens.values() if g["prompt_id"] == "G1" and g["flags_initial"]]
        c["G1"] = dict(flagged_requests=len(g1u), logical_calls=sum(g["extra_calls"] for g in g1u),
                       unflagged_after=sum(not g["flags_final"] for g in g1u), changed=sum(g["changed"] for g in g1u),
                       first_attempt_unflagged=sum(len(g["attempts"]) > 1 and not g["attempts"][1]["flags"] for g in g1u))
        c["G1s"] = dict(flagged_requests=len(g1u), logical_calls=0,
                        unflagged_after=sum(not g["flags_final"] for g in gens.values() if g["prompt_id"] == "G1s" and g["flags_initial"]))
        res["cost"] = c
        res["unresolved_critical_J_units"] = int(frame.crit.isna().sum()) if "crit" in frame else None
        summary[s] = res
    summary["design"] = dict(retry_temperature=RETRY_T, local_seed_base=SEED0, max_retries=MAX_RETRIES,
                             n_boot=W.NBOOT, seed=W.SEED, bootstrap="whole-family percentile, all arms jointly",
                             g1_retry_decoding="T=0, local seed 1000, feedback turn")
    (OUT / "summary.json").write_text(json.dumps(W.clean(summary), indent=2) + "\n")
    # CSVs
    rows = []
    for s, res in summary.items():
        if s == "design":
            continue
        for arm, pm in res["paired"].items():
            for m, r in pm.items():
                if isinstance(r, dict) and "estimate" in r:
                    rows.append(dict(set=s, arm=arm, metric=m, k=r.get("k"), n=r["n"], n_total=r["n_total"],
                                     estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"]))
        for arm, am in res["arms"].items():
            for m, r in am.items():
                rows.append(dict(set=s, arm=arm, metric="level_" + m, k=r.get("k"), n=r["n"], n_total=r["n_total"],
                                 estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"]))
    pd.DataFrame(rows).to_csv(OUT / "arm_metrics.csv", index=False)
    rows = []
    for s, res in summary.items():
        if s == "design":
            continue
        for cn, d in res["contrasts"].items():
            for ep, r in d.items():
                rows.append(dict(set=s, contrast=cn, endpoint=ep, estimate_pp=100 * r["estimate"], ci_low_pp=100 * r["ci_low"],
                                 ci_high_pp=100 * r["ci_high"], n=r["n"], x_only_pass=r["x_only_pass"], y_only_pass=r["y_only_pass"]))
    pd.DataFrame(rows).to_csv(OUT / "contrasts.csv", index=False)
    rows = [dict(set=s, arm=arm, **v) for s, res in summary.items() if s != "design" for arm, v in res["cost"].items()]
    pd.DataFrame(rows).to_csv(OUT / "cost.csv", index=False)
    print("wrote summary.json, arm_metrics.csv, contrasts.csv, cost.csv")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory")
    s = sub.add_parser("gen"); s.add_argument("--set", required=True, choices=SETS); s.add_argument("--model", required=True)
    s.add_argument("--concurrency", type=int, default=4)
    for k in ("assemble", "resolve", "arbview", "arbwrite"):
        s = sub.add_parser(k); s.add_argument("--set", required=True, choices=SETS)
        if k == "arbwrite":
            s.add_argument("--decisions", required=True)
    sub.add_parser("analyze")
    a = ap.parse_args()
    if a.cmd == "gen":
        asyncio.run(gen(a))
    else:
        globals()[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())

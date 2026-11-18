"""Part 28 listener study stimuli. Rules frozen in analysis/listener/PLAN.md (written before this ran).

  python src/make_listener_study.py draw     # seeded draw of 120 intended messages + model assignment -> tmp/listener_draw.json
  python src/make_listener_study.py guard    # G1 (unchanged src/interventions.guard_one) on the 120 bare inputs
  python src/make_listener_study.py build    # analysis/listener/stimuli.jsonl + orchestration/listener_key_private.json
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "analysis/listener"
TMP = ROOT / "tmp"
SEED = 20261117
DIMS = ["polarity", "speech_act", "agent", "time_quantity"]
RANK = {"polarity": ["affirmative", "negated"], "speech_act": ["statement", "question", "request/command"],
        "agent": ["speaker", "addressee", "third party"], "time_quantity": ["now", "past", "later"]}
MODELS = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]
ACTION = {
    "polarity": {"negated": "Treat it as a no: do not go ahead, hold off", "affirmative": "Treat it as a yes: go ahead",
                 "_third": "No reply or action is needed"},
    "speech_act": {"statement": "Take note of it: they are telling you something",
                   "question": "Answer them: they are asking something",
                   "request/command": "Do what they ask: they want you to act"},
    "agent": {"speaker": "Expect the speaker to do it themselves", "addressee": "Expect that you are the one who should do it",
              "third party": "Expect someone else, neither of you, to do it"},
    "time_quantity": {"past": "Treat it as already done", "later": "Plan for it as something still to come",
                      "now": "Treat it as happening right now"},
}
CLARIFY = "Ask them to say it again or confirm what they mean"
SLP_W = {"polarity": 1.0, "speech_act": 0.8, "agent": 0.8, "time_quantity": 0.8}


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def norm(t):
    t = re.sub(r"\s+", " ", (t or "").lower()).strip()
    return re.sub(r"[.!?\s]+$", "", t)


def load_families():
    fams = {}
    for f in ("hw", "hw2"):
        for x in jl(ROOT / f"data/items/{f}.jsonl"):
            x["_file"] = f
            fams[x["family_id"]] = x
    return fams


def default_variant(fam):
    r = RANK[fam["dimension"]]
    vals = {v: fam["variants"][v]["critical_value"] for v in "AB"}
    return min(vals, key=lambda v: r.index(vals[v]))


def draw():
    fams = load_families()
    rng = random.Random(SEED)
    sel = []
    for d in DIMS:
        pool = sorted(f for f, x in fams.items() if x["dimension"] == d and x["human_check"]["n_pass"] >= 2)
        rng.shuffle(pool)
        picks = pool[:30]
        for i, fid in enumerate(picks):
            dv = default_variant(fams[fid])
            nd = "B" if dv == "A" else "A"
            sel.append({"family_id": fid, "dimension": d, "nondefault": i % 2 == 1,
                        "intended": nd if i % 2 == 1 else dv, "default_variant": dv})
    # model assignment: seeded round-robin within dimension x default stratum
    for d in DIMS:
        for nd in (False, True):
            cell = [s for s in sel if s["dimension"] == d and s["nondefault"] == nd]
            rng.shuffle(cell)
            off = rng.randrange(4)
            for i, s in enumerate(cell):
                s["model"] = MODELS[(i + off) % 4]
    sel.sort(key=lambda s: s["family_id"])
    for i, s in enumerate(sel):
        s["item"] = f"L{i + 1:03d}"
    TMP.mkdir(exist_ok=True)
    (TMP / "listener_draw.json").write_text(json.dumps(sel, indent=1))
    print(Counter((s["dimension"], s["nondefault"]) for s in sel), Counter(s["model"] for s in sel))
    return sel


def bare_gens(sel):
    """bare generation rows (full request records) per item, from runs/hw1 / runs/hw2."""
    fams = load_families()
    outs = {}
    for r in ("hw1", "hw2"):
        for o in jl(ROOT / f"runs/{r}/outputs.jsonl"):
            if o["channel"] == "bare":
                outs[(o["family_id"], o["variant"], o["model"])] = o
    gens = {}
    for r in ("hw1", "hw2"):
        for g in jl(ROOT / f"runs/{r}/generations.jsonl"):
            gens[g["request_key"]] = g
    res = {}
    for s in sel:
        o = outs[(s["family_id"], s["intended"], s["model"])]
        res[s["item"]] = gens[o["request_key"]]
    return res, fams


async def guard(sel, models=None):
    import httpx, interventions as I, runio
    bg, fams = bare_gens(sel)
    items = {}
    for cf in ("annotation/written/hw_candidates.jsonl", "annotation/written/hw2/hw_candidates.jsonl"):
        for x in jl(ROOT / cf):
            items[x["family_id"]] = x   # representative family of a shared request may be a dropped candidate (context only)
    items.update(fams)
    # check offline which items need a call (G1 flags only supplied commitments and added politeness)
    caller = I.Caller(conc_local=2, conc_api=4, retries=3)
    out = []
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=8)) as client:
        caller.client = client
        for s in sel:
            if models and s["model"] not in models:
                continue
            g = bg[s["item"]]
            rows = await I.guard_one(caller, g, items, 2, {})
            g1 = [r for r in rows if r["prompt_id"] == "G1"][0]
            out.append({"item": s["item"], "model": s["model"], "bare": (g["suggestions"] or [""])[0],
                        "g1": (g1["suggestions"] or [""])[0], "flags_initial": g1["flags_initial"],
                        "flags_final": g1["flags_final"], "extra_calls": g1["extra_calls"],
                        "errors": g1["guard_errors"], "attempts": g1["attempts"]})
    return out


def need_calls(sel):
    import interventions as I
    bg, _ = bare_gens(sel)
    res = []
    for s in sel:
        g = bg[s["item"]]
        t = (g["suggestions"] or [""])[0]
        fl = I.check(t, I.supplied(g["input_text"])) if t else ["empty"]
        res.append((s["item"], s["model"], fl))
    return res


def build(sel, gres):
    fams = load_families()
    outs = defaultdict(dict)
    for r, chans in (("hw1", ("bare", "chip1")), ("hw2", ("bare", "chip1")), ("hwctl1", ("nlcue",))):
        for o in jl(ROOT / f"runs/{r}/outputs.jsonl"):
            if o["channel"] in chans:
                outs[(o["family_id"], o["variant"], o["model"], o["channel"])] = o
    g1 = {r["item"]: r for r in gres}
    rows, key = [], []
    gap = Counter()
    for s in sel:
        fam = fams[s["family_id"]]
        iv = s["intended"]
        ov = "B" if iv == "A" else "A"
        d = s["dimension"]
        vi, vo = fam["variants"][iv]["critical_value"], fam["variants"][ov]["critical_value"]
        vals = [fam["variants"][v]["critical_value"] for v in "AB"]
        third = [x for x in RANK[d] if x not in vals]
        act = ACTION[d]
        o_third = act[third[0]] if third and third[0] in act else ACTION["polarity"]["_third"]
        r2 = random.Random(f"{SEED}-{s['item']}")
        opts = [{"role": "correct", "text": act[vi]}, {"role": "opposite", "text": act[vo]},
                {"role": "clarify", "text": CLARIFY}, {"role": "other", "text": o_third}]
        r2.shuffle(opts)
        topic = fam.get("topic")
        ctx = f"Topic: {topic}" if topic else None
        readings = {v: f'They are saying: "{fam["variants"][v]["source"]}"' for v in "AB"}
        texts = {}
        texts["bare"] = (outs.get((s["family_id"], iv, s["model"], "bare")) or {}).get("text")
        texts["chip1"] = (outs.get((s["family_id"], iv, s["model"], "chip1")) or {}).get("text")
        nl = outs.get((s["family_id"], iv, s["model"], "nlcue"))
        texts["nlcue"] = nl["text"] if nl else None
        texts["G1"] = g1[s["item"]]["g1"] if s["item"] in g1 else None
        texts["reference"] = fam["variants"][iv]["source"]
        seen = {}
        for c in ["bare", "chip1", "nlcue", "G1", "reference"]:
            t = texts[c]
            if not t:
                gap[c] += 1
                continue
            unit = f"{s['item']}-ref" if c == "reference" else f"{s['item']}-{hashlib.sha1(norm(t).encode()).hexdigest()[:6]}"
            first = seen.get(unit)
            seen.setdefault(unit, c)
            rows.append({"stimulus_id": f"{s['item']}-{c}", "item": s["item"], "condition": c, "judge_unit": unit,
                         "judge_unit_inherits_from": first, "output_text": t, "context": ctx,
                         "intended_reading": iv, "reading_A": readings["A"], "reading_B": readings["B"],
                         "q2_options": opts, "q2_correct": next(i for i, x in enumerate(opts) if x["role"] == "correct"),
                         "q2_opposite": next(i for i, x in enumerate(opts) if x["role"] == "opposite")})
        key.append({"item": s["item"], "family_id": s["family_id"], "variant_intended": iv, "dimension": d,
                    "intended_value": vi, "opposite_value": vo, "nondefault": s["nondefault"], "model": s["model"],
                    "hw_file": fams[s["family_id"]]["_file"], "slp_weight": SLP_W[d],
                    "writer_id": fam.get("writer_id"), "bare_keywords": fam["bare"]})
    OUT.mkdir(exist_ok=True)
    with open(OUT / "stimuli.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    kp = ROOT / "orchestration/listener_key_private.json"
    kp.write_text(json.dumps(key, indent=1))
    cnt = Counter(r["condition"] for r in rows)
    uniq = len({r["judge_unit"] for r in rows})
    print("rows per condition", dict(cnt), "gaps", dict(gap), "unique judge units", uniq)
    return cnt, gap, uniq


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["draw", "needcalls", "guard", "build"])
    ap.add_argument("--models")
    a = ap.parse_args()
    if a.cmd == "draw":
        draw()
    else:
        sel = json.loads((TMP / "listener_draw.json").read_text())
        if a.cmd == "needcalls":
            nc = need_calls(sel)
            print(Counter((m, bool(f)) for _, m, f in nc)); print([x for x in nc if x[2]])
        elif a.cmd == "guard":
            ms = set(a.models.split(",")) if a.models else None
            res = asyncio.run(guard(sel, ms))
            p = TMP / "listener_guard.jsonl"
            with open(p, "a") as f:
                for r in res: f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(len(res), Counter(bool(r["flags_initial"]) for r in res), sum(r["extra_calls"] for r in res), [r for r in res if r["errors"]])
        else:
            gres = [json.loads(l) for l in open(TMP / "listener_guard.jsonl")] if (TMP / "listener_guard.jsonl").exists() else []
            build(sel, gres)

"""Generate draft sets for the coverage pilot (PLAN section 2) with the frozen prompts, then judge every unique draft.
usage: python coverage_gen.py reserve|main [--stages gen,judge,sets]
Writes analysis/coverage/{drafts_<which>.jsonl, judgments_<which>.jsonl, sets_<which>.jsonl, selector_<which>.jsonl}.
Generator/judge ids come from models_used.json. Stored outputs are the data; nothing is regenerated after judging except the single
label-faithfulness regeneration of failed contrast slots (PLAN 2)."""
from __future__ import annotations
import asyncio, json, random, sys
import coverage_lib as L, coverage_judge as J
SEED = 20261117
TPL = {n: L.prompt_text(f"coverage_{n}.txt") for n in ("selector", "diverse", "edit", "event")}
LEG = (L.ROOT / "prompts/chip_legend.txt").read_text().strip()

def clean(t): return L.clean_sentence(t)
def p0(x): return L.P.render("P0", x)
def dims_block(ds): return "\n".join(f"- {d}: {', '.join(o for o in L.OPTIONS[d] if o != 'unclear/mixed')}" for d in ds)
SEL_SCHEMA = lambda ds: L.schema_obj({"ranking": {"type": "array", "items": {"type": "string", "enum": ds}}})
DIV_SCHEMA = L.schema_obj({"sentences": {"type": "array", "items": {"type": "string"}}})
def edit_schema(d):
    o = [x for x in L.OPTIONS[d] if x != "unclear/mixed"]
    return L.schema_obj({"current_value": {"type": "string", "enum": o}, "new_value": {"type": "string", "enum": o}, "sentence": {"type": "string"}})

async def main(which, stages):
    items = [x for x in json.load(open(L.OUT / "items_draw.json"))["items"] if x["reserve"] == (which == "reserve")]
    m = L.resolve_models(); G = m["gen"]
    gen = L.Chat("gen", 4); jch = L.Chat("judge", 3)
    D = {}   # (item_id, cond, kind, key) -> dict(text, meta)
    S = {}   # (item, cond) -> info
    async def per_item(it):
        iid = it["item_id"]; pd_ = it["dimension"]
        r = {}
        # ---- stage G1 / W1
        for cond in ("bare", "chip"):
            r[cond] = {"input": it["inputs"][cond]}
        r["word"] = {"input": it["inputs"]["word"]}
        g1 = await asyncio.gather(*[gen.one(G, p0(r[c]["input"]), temp=0.0, tag="g1", max_tokens=96) for c in ("bare", "chip", "word")])
        for c, t in zip(("bare", "chip", "word"), g1): r[c]["g1"] = clean(t)
        for cond in ("bare", "chip"):
            c = r[cond]; x = c["input"]; g = c["g1"]
            ds = [d for d in L.DIMS if not (cond == "chip" and d == pd_)]
            sel_j = gen.one(G, L.fill(TPL["selector"], input=x, dims=dims_block(ds)), temp=0.0, schema=SEL_SCHEMA(ds), tag="sel", max_tokens=300)
            ev_j = gen.one(G, L.fill(TPL["event"], legend=LEG, input=x, sentence=g, chip_line=("The input chip fixes one aspect of meaning; keep it." if cond == "chip" else "")),
                           temp=0.0, schema=DIV_SCHEMA, tag="event", max_tokens=300)
            dv = [gen.one(G, L.fill(TPL["diverse"], legend=LEG, input=x, first=g, n=n), temp=0.0, schema=DIV_SCHEMA, tag=f"div{n}", max_tokens=300) for n in (2, 4)]
            smp = [gen.one(G, p0(x), temp=1.0, top_p=0.95, draw=i, tag="smp", max_tokens=96) for i in range(4)]
            sel, ev, d2, d4, *sm = await asyncio.gather(sel_j, ev_j, *dv, *smp)
            sm = [clean(t) for t in sm]
            # extra draws only if fewer than 4 distinct non-G1 samples
            seen = {L.norm(g)}; dist = []
            for t in sm:
                if L.norm(t) and L.norm(t) not in seen: seen.add(L.norm(t)); dist.append(t)
            i = 4
            while len(dist) < 4 and i < 12:
                t = clean(await gen.one(G, p0(x), temp=1.0, top_p=0.95, draw=i, tag="smp", max_tokens=96)); i += 1
                if L.norm(t) and L.norm(t) not in seen: seen.add(L.norm(t)); dist.append(t)
            rank = [d for d in (sel or {}).get("ranking", []) if d in ds]
            rank += [d for d in ds if d not in rank]
            rng = random.Random(f"{SEED}|{iid}|{cond}|R3")
            rnd = ds[:]; rng.shuffle(rnd)
            stat = [d for d in L.STATIC_ORDER if d in ds]
            c.update(sel=rank, sel_raw=sel, static=stat, rnd=rnd, event=[clean(s) for s in (ev or {}).get("sentences", [])][:2],
                     div2=[clean(s) for s in (d2 or {}).get("sentences", [])][:2], div4=[clean(s) for s in (d4 or {}).get("sentences", [])][:4], smp=dist, n_draws=i if i > 4 else 4)
            # ---- dimension edits needed
            need = []
            for d in rank[:4] + stat[:2] + rnd[:2]:
                if d not in need: need.append(d)
            c["edits"] = {}
            async def edit(d, avoid=None, draw=0, x=x, g=g, cond=cond):
                tgt = ("Choose a new value different from the current one" + (f" and different from: {', '.join(avoid)}" if avoid else "") + ": the most plausible alternative reading of these keywords.")
                cl = ("The input chip fixes one other aspect of meaning; do not change that aspect." if cond == "chip" else "")
                pr = L.fill(TPL["edit"], input=x, sentence=g, dim=d, defn=L.defn(d), options=", ".join(o for o in L.OPTIONS[d] if o != "unclear/mixed"), target_line=tgt, chip_line=cl)
                o = await gen.one(G, pr, temp=0.0 if draw == 0 else 0.7, schema=edit_schema(d), tag=f"edit{draw}", draw=draw, max_tokens=300)
                return o
            outs = await asyncio.gather(*[edit(d) for d in need])
            for d, o in zip(need, outs): c["edits"][d] = o
            if cond == "bare":   # oracle: pair dimension, two sequential alternatives
                o1 = c["edits"].get(pd_) or await edit(pd_)
                o2 = await edit(pd_, avoid=[o1["new_value"]] if o1 else None)
                c["oracle"] = [o1, o2]
            c["_edit_fn"] = edit
        r["_it"] = it
        # ---- collect drafts of this item
        drafts = {}
        def add(cond, text, kind, dim=None, claimed=None, slot=None):
            if text and L.norm(text):
                drafts.setdefault((iid, text), {"item_id": iid, "text": text, "uses": []})["uses"].append(dict(cond=cond, kind=kind, dim=dim, claimed=claimed, slot=slot))
        add("word", r["word"]["g1"], "g1")
        for cond in ("bare", "chip"):
            c = r[cond]
            add(cond, c["g1"], "g1")
            for t in c["smp"]: add(cond, t, "smp")
            for t in c["div4"]: add(cond, t, "div")
            for t in c["event"]: add(cond, t, "event")
            for d, o in c["edits"].items():
                if o: add(cond, clean(o["sentence"]), "edit", d, o["new_value"])
            for o in c.get("oracle", []):
                if o: add(cond, clean(o["sentence"]), "edit", pd_, o["new_value"])
        async def jd(k, v):
            xs = {u["dim"] for u in v["uses"] if u["kind"] == "edit" and u["dim"] != pd_}
            outs = {}
            for xd in sorted(xs) or [None]:
                outs[xd or ""] = await J.judge(jch, m["judge"], v["text"], it["A"], it["B"], pd_, xd)
            v["judge"] = outs
        await asyncio.gather(*[jd(k, v) for k, v in drafts.items()])
        def ok_edit(cond, d, o, text):
            if not o or not text: return False
            v = drafts.get((iid, text))
            if v is None: return False
            j = v["judge"]; pj = j.get("") or next(iter(j.values()))
            val = pj["value"] if d == pd_ else (j.get(d) or {}).get("extra_value")
            if val != o["new_value"] or o["new_value"] == o.get("current_value"): return False
            if cond == "chip" and pj["value"] != it["intended_value"]: return False
            return True
        regen = [(cond, d) for cond in ("bare", "chip") for d, o in list(r[cond]["edits"].items())
                 if not ok_edit(cond, d, o, clean(o["sentence"]) if o else "")]
        r["n_regen"] = len(regen)
        async def rg(cond, d):
            c = r[cond]
            o = await c["_edit_fn"](d, draw=1); c["edits"][d + "|regen"] = o
            if o:
                t = clean(o["sentence"])
                v = drafts.setdefault((iid, t), {"item_id": iid, "text": t, "uses": []}); v["uses"].append(dict(cond=cond, kind="edit", dim=d, claimed=o["new_value"], slot="regen"))
                if "judge" not in v:
                    xd = d if d != pd_ else None
                    v["judge"] = {(xd or ""): await J.judge(jch, m["judge"], t, it["A"], it["B"], pd_, xd)}
        await asyncio.gather(*[rg(*a_) for a_ in regen])
        r["_drafts"] = drafts
        return iid, r
    if "gen" in stages:
        res = await asyncio.gather(*[per_item(it) for it in items])
        S = dict(res)
        drafts = {}
        for iid, r in S.items(): drafts.update(r["_drafts"])
        print("unique drafts", len(drafts), "faithfulness regenerations:", sum(r["n_regen"] for r in S.values()), flush=True)
        # ---- save
        with (L.OUT / f"drafts_{which}.jsonl").open("w") as fh:
            for (iid, t), v in drafts.items():
                fh.write(json.dumps({**v, "judge": {k: j for k, j in v.get("judge", {}).items()}}, ensure_ascii=False) + "\n")
        with (L.OUT / f"selector_{which}.jsonl").open("w") as fh:
            for iid, r in S.items():
                it = r["_it"]
                fh.write(json.dumps({"item_id": iid, "writer_id": it["writer_id"], "dimension": it["dimension"], "intended": it["intended"],
                                     **{c: {k: r[c][k] for k in ("input", "g1", "sel", "static", "rnd", "event", "div2", "div4", "smp", "n_draws")} | {"edits": {d: o for d, o in r[c]["edits"].items()}, "oracle": r[c].get("oracle")} for c in ("bare", "chip")},
                                     "word": r["word"]}, ensure_ascii=False) + "\n")
        print("saved", gen.n_call, "gen calls", gen.n_err, "gen errors;", jch.n_call, "judge calls", jch.n_err, "judge errors")

if __name__ == "__main__":
    which = sys.argv[1]; st = "gen"
    asyncio.run(main(which, st))

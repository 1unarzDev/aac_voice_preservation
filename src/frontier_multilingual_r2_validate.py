"""E7 detector validation on a fresh sample incl. ambiguous/no-address outputs; arbiters: gpt-6.1-sol (primary) and gpt-6.1-terra (secondary, different prompt). No detector tuning."""
import asyncio, sys, json, re, glob, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
from frontier_multilingual_r2_label import ARB, numbered, pl, batched  # noqa  (module main guarded below)
import httpx
from frontier_multilingual_register import label as det
N = 120
ARB2 = ("For each numbered {lang} sentence say whether the speaker is talking TO a listener using an informal singular form (answer T), a formal form (answer V), "
        "no listener-directed form at all (answer none), or both (answer mixed). Reply with only a JSON array of strings.\n{items}")

def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - hw, c + hw]

async def main():
    used = set()
    for f in ("arbiter_register_items.json",):
        for it in json.load(open(OUT / f)):
            used.add((it["lang"], it["text"]))
    texts = {l: set() for l in LANGS}
    for f in glob.glob(str(RUN2 / "gen_*.jsonl")):
        for r in jl(f):
            if r["kind"] == "REG" and r["lang"] in LANGS and r["text"] and (r["lang"], r["text"]) not in used:
                texts[r["lang"]].add(r["text"])
    sample = {l: sorted(texts[l], key=lambda t: h("ml2val", l, t))[:N] for l in LANGS}
    sem = asyncio.Semaphore(3); res = {}
    async with httpx.AsyncClient() as c:
        for l in LANGS:
            a1 = await batched(c, sem, ARB, L4[l], sample[l])
            out2 = {}
            for i in range(0, N, 15):
                ch = sample[l][i:i + 15]
                for att in range(3):
                    t = await chat2(c, sem, "gpt-6.1-terra", ARB2.format(lang=L4[l], items=numbered(ch)) + " " * att, 600)
                    v = pl(t, len(ch))
                    if v: out2.update(dict(zip(ch, v))); break
            rows = [{"text": t, "det": det(l, t), "arb1": a1.get(t), "arb2": out2.get(t)} for t in sample[l]]
            amb = [r for r in rows if r["det"] == "ambig"]; non = [r for r in rows if r["det"] != "ambig" and r["arb1"]]
            ag = sum(r["det"] == r["arb1"] for r in non)
            nonea = [r for r in non if r["det"] == "none"]; miss = sum(r["arb1"] in ("T", "V", "mixed") for r in nonea)
            both = [r for r in rows if r["arb1"] and r["arb2"]]
            conf = {}
            for r in non:
                conf[f"{r['det']}->{r['arb1']}"] = conf.get(f"{r['det']}->{r['arb1']}", 0) + 1
            res[l] = {"n": len(rows), "n_ambig": len(amb), "n_non_ambig": len(non), "primary_agree": ag / len(non) if non else None, "primary_k": ag, "primary_wilson": wilson(ag, len(non)),
                      "overall_agree_ambig_as_error": ag / len(rows), "none_subset_n": len(nonea), "none_missed_address_forms": miss,
                      "arb1_vs_arb2_agree": sum(r["arb1"] == r["arb2"] for r in both) / len(both) if both else None, "arb_label_dist": {k: sum(r["arb1"] == k for r in rows) for k in ("T", "V", "none", "mixed")},
                      "ambig_arbiter_dist": {k: sum(r["arb1"] == k for r in amb) for k in ("T", "V", "none", "mixed")}, "confusion": conf,
                      "pass": bool(non and ag / len(non) >= 0.95)}
            jdump(OUT / f"r2_validation_items_{l}.jsonl", rows)
    json.dump(res, open(OUT / "r2_detector_validation.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
asyncio.run(main())

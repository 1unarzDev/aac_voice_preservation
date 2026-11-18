"""Part 28 listener study stimuli. Rules frozen in analysis/listener/PLAN.md (written before this ran).

  python src/make_listener_study.py draw     # seeded draw of 120 intended messages + model assignment -> tmp/listener_draw.json
  python src/make_listener_study.py guard    # G1 (unchanged src/interventions.guard_one) on the 120 bare inputs
  python src/make_listener_study.py build    # analysis/listener/stimuli.jsonl + orchestration/listener_key_private.json
  python src/make_listener_study.py package  # Stage 7 packet (Parts 28 and 29): per-person blind files, private keys, balance (frozen; --force redraws)

package writes (rules: annotation/COORDINATOR_STEPS.md section 7, analysis/listener/PLAN.md, analysis/oracle_indep/PLAN.md Amendment 2):
  annotation_package/stage7/<ID>_part28.json, <ID>_part29.json   blind files for annotation_package/rate_items.html
  annotation/listener_key.csv, annotation/oracle_indep_key.csv    PRIVATE keys (+ .sha256 to deposit before sending)
  annotation/assignments/stage7_plan.json                        per-person items and minutes, design record (read by make_assignments.py --stage 7)
Part 28: one listener sees a judge unit (one sentence, merged across conditions with identical text) at most once, and any one intended message in at most
one unit (Latin square over conditions); 2 different listeners per unit; nobody judges a pair they wrote or checked (src/make_frontier_parts.py hw_blocks).
Part 29: 150 mutant/control candidates x 2 annotators, same exclusions on the source family; the two sentences in a seeded order, neutral wording.
"""
from __future__ import annotations
import argparse, asyncio, csv, hashlib, json, random, re, sys
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


ANN = ROOT / "annotation"
PKG7 = ROOT / "annotation_package" / "stage7"
S7_SALT = "s7-20261117"
SEC7 = {"part28": 26.0, "part29": 16.0}        # seconds per judgment, assumptions to be replaced by the pilot timing
N_PRACTICE = 2
IND = ROOT / "analysis/oracle_indep"
TARGET = {"neg_fail_to": "polarity", "neg_refuse_to": "polarity", "neg_hardly": "polarity", "neg_nobody": "polarity",
          "role_passive": "agent", "role_embed": "agent", "q_embed": "speech_act", "time_implied": "time_quantity"}
Q29 = ("Do the two sentences tell the listener the same thing: who does what to whom, whether it is so or not, when it happens, how sure "
       "the speaker is, and whether it is a statement, a question or a request? Small differences in wording or style do not count.")


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


# ----------------------------------------------------------------------------- Stage 7 packet
def opaque(prefix, x):
    return prefix + hashlib.sha1(f"{S7_SALT}|{x}".encode()).hexdigest()[:8]


def id_hash(annotator, check):
    import make_frontier_parts as FP
    return FP.id_hash(annotator, check)


def _opt(v, label):
    return {"v": v, "label": label}


def part28_spec():
    qs = {"q1": {"title": "What is the person saying?", "text": "Choose the message the sentence says. If it fits neither, or you cannot tell, choose the last option.",
                 "options": [_opt("reading 1", "Reading 1"), _opt("reading 2", "Reading 2"), _opt("unclear", "Something else, or I cannot tell")]},
          "q2": {"title": "How would you respond?", "text": "Choose what you would do after hearing the sentence.",
                 "options": [_opt(f"action {i}", f"Response {i}") for i in range(1, 5)]},
          "q3": {"title": "How sure are you?", "text": "How sure are you of what the person is saying?",
                 "options": [_opt("1", "1: not sure"), _opt("2", "2: fairly sure"), _opt("3", "3: sure")]}}
    intro = ["You will see a short topic line and one sentence that a person said to you. Say what you think the person is saying, how you would respond, and how sure you are.",
             "Sentences come from different sources: some were written by a person, some were produced by a program. Do not try to guess the source. Answer only from what the sentence says to you."]
    help_ = [{"term": "What is the person saying?", "text": "Two readings are shown. Choose the one the sentence says to you. If it says neither, or you cannot tell, choose 'Something else, or I cannot tell'."},
             {"term": "How would you respond?", "text": "Choose the response that fits what you understood. 'Ask them to say it again or confirm' is right when you are not sure what they mean."},
             {"term": "How sure are you?", "text": "1 means you are guessing, 3 means you are sure."}]
    def pr(item_id, ctx, sentence, r1, r2, a, exp1, exp2, fb):
        blocks = ([{"label": "Topic", "text": ctx}] if ctx else []) + [{"label": "The sentence", "text": sentence}]
        qo = {"q1": [_opt("reading 1", r1), _opt("reading 2", r2), _opt("unclear", "Something else, or I cannot tell")],
              "q2": [_opt(f"action {i + 1}", t) for i, t in enumerate(a)]}
        return {"item_id": item_id, "blocks": blocks, "qs": ["q1", "q2"], "qopts": qo, "expected": {"q1": exp1, "q2": exp2}, "fb": fb}
    practice = [
        pr("prac-1", "Topic: shopping", "The shop is closed today.", 'They are saying: "The shop is closed today."', 'They are saying: "Is the shop closed today?"',
           ["Answer them: they are asking something", "Take note of it: they are telling you something", "Ask them to say it again or confirm what they mean", "Do what they ask: they want you to act"],
           "reading 1", "action 2", "The sentence tells you something (it is not a question), so Reading 1 and taking note of it."),
        pr("prac-2", "Topic: dinner", "I did not cook the rice.", 'They are saying: "I did not cook the rice."', 'They are saying: "I cooked the rice."',
           ["Treat it as already done", "Treat it as a no: it did not happen", "Ask them to say it again or confirm what they mean", "Plan for it as something still to come"],
           "reading 1", "action 2", "The sentence says the rice was not cooked: Reading 1, and you would treat it as not done. Question 3 (how sure you are) has no right answer; you will see it in the real items.")]
    return {"title": "Listen to a sentence and say what it means", "intro": intro, "help": help_, "questions": qs, "practice": practice}


def part29_spec():
    qs = {"q1": {"title": "Same meaning?", "text": Q29,
                 "options": [_opt("same", "same"), _opt("different", "different"), _opt("unsure", "unsure")]}}
    intro = ["You will see two sentences. Say whether Sentence 2 means the same as Sentence 1.",
             "Answer from the words only. Use 'unsure' if you really cannot decide."]
    help_ = [{"term": "Same or different", "text": "Same if a listener would understand the same thing from both. Different if the listener would understand something else, even if the wording is close."},
             {"term": "Style does not count", "text": "Contractions (I am / I'm), word order that does not change who does what, and similar style differences do not make a difference."}]
    practice = [
        {"item_id": "prac-1", "blocks": [{"label": "Sentence 1", "text": "I will go to the shop."}, {"label": "Sentence 2", "text": "I will not go to the shop."}],
         "qs": ["q1"], "expected": {"q1": "different"}, "fb": "The second sentence says the opposite (not going), so they are different."},
        {"item_id": "prac-2", "blocks": [{"label": "Sentence 1", "text": "It is raining now."}, {"label": "Sentence 2", "text": "It's raining now."}],
         "qs": ["q1"], "expected": {"q1": "same"}, "fb": "Only the contraction differs, so they mean the same."}]
    return {"title": "Do two sentences mean the same?", "intro": intro, "help": help_, "questions": qs, "practice": practice}


def package(out_pkg=PKG7, out_ann=ANN, force=False, write=True):
    import make_frontier_parts as FP
    ids = json.loads((ANN / "assignments" / "plan.json").read_text())["annotators"]
    FP.K.update({"part28": 2, "part29": 2}); FP.SEC.update(SEC7)
    hw = FP.hw_blocks()
    stim = jl(OUT / "stimuli.jsonl")
    key = {k["item"]: k for k in json.loads((ROOT / "orchestration/listener_key_private.json").read_text())}
    # ---- Part 28 units: one per judge_unit
    by_unit = defaultdict(list)
    for r in stim:
        by_unit[r["judge_unit"]].append(r)
    u28 = []
    for unit in sorted(by_unit):
        rs = by_unit[unit]
        first = rs[0]
        k = key[first["item"]]
        assert all(r["output_text"] == first["output_text"] for r in rs)
        u28.append({"item_id": opaque("u", unit), "unit": unit, "item": first["item"], "rows": rs, "key": k,
                    "blocked": set(hw[k["family_id"]]), "group": first["item"]})
    assert all(u["blocked"] for u in u28), "a family without a writer/checker record would silently exclude no one"
    assert len({u["item_id"] for u in u28}) == len(u28)
    # ---- Part 29 units
    cand = {c["id"]: c for c in jl(IND / "candidates.jsonl")}
    ikey = {k["id"]: k for k in jl(IND / "key.private.jsonl")}
    assert set(cand) == set(ikey) and len(cand) == 150
    u29 = []
    for cid in sorted(cand):
        k = ikey[cid]
        flip = random.Random(f"{SEED}|p29|{cid}").random() < 0.5      # True: the mutant/changed text is Sentence 1
        u29.append({"item_id": opaque("m", cid), "cid": cid, "cand": cand[cid], "key": k, "mut_first": flip,
                    "blocked": set(hw[k["family_id"]]), "group": None})
    assert all(u["blocked"] for u in u29), "a family without a writer/checker record would silently exclude no one"
    assert len({u["item_id"] for u in u29}) == len(u29)
    rnd = random.Random(int(hashlib.sha256(S7_SALT.encode()).hexdigest(), 16) % 2**32)
    al = {}
    for p_, us in (("part28", u28), ("part29", u29)):     # each part balanced on its own, so every listener gets about the same share of each part
        al[p_] = FP.Alloc(ids, rnd, base=0)
        al[p_].run({p_: us})
    spec = {"part28": part28_spec(), "part29": part29_spec()}
    per = {a: {} for a in ids}
    key28, key29, files = [], [], {}
    for p, units in (("part28", u28), ("part29", u29)):
        for a in ids:
            mine = [u for u in units if a in al[p].who[(p, u["item_id"])]]
            sec = (len(mine) + N_PRACTICE) * SEC7[p]
            per[a][p] = {"n_items": len(mine), "seconds": round(sec, 1), "minutes": round(sec / 60)}
            items = []
            for u in sorted(mine, key=lambda u: u["item_id"]):
                if p == "part28":
                    r = u["rows"][0]
                    rng = random.Random(f"{SEED}|p28|{a}|{u['unit']}")
                    rd = ["A", "B"]; rng.shuffle(rd)
                    q2 = list(r["q2_options"]); rng.shuffle(q2)
                    blocks = ([{"label": "Topic", "text": r["context"].replace("Topic: ", "", 1)}] if r["context"] else []) + [{"label": "The sentence", "text": r["output_text"]}]
                    qo = {"q1": [_opt("reading 1", r["reading_" + rd[0]]), _opt("reading 2", r["reading_" + rd[1]]), _opt("unclear", "Something else, or I cannot tell")],
                          "q2": [_opt(f"action {i + 1}", o["text"]) for i, o in enumerate(q2)]}
                    items.append({"item_id": u["item_id"], "blocks": blocks, "qs": ["q1", "q2", "q3"], "qopts": qo})
                    k = u["key"]
                    key28.append({"item_id": u["item_id"], "annotator": a, "judge_unit": u["unit"], "item": u["item"],
                                  "conditions": ";".join(x["condition"] for x in u["rows"]), "family_id": k["family_id"],
                                  "dimension": k["dimension"], "nondefault": k["nondefault"], "model": k["model"], "hw_file": k["hw_file"],
                                  "intended_reading": r["intended_reading"], "intended_value": k["intended_value"], "opposite_value": k["opposite_value"],
                                  "slp_weight": k["slp_weight"], "reading1": rd[0], "q2_roles": "|".join(o["role"] for o in q2),
                                  "context": r["context"] or "", "output_text": r["output_text"]})
                else:
                    c = u["cand"]; first, second = (c["mutant"], c["original"]) if u["mut_first"] else (c["original"], c["mutant"])
                    items.append({"item_id": u["item_id"], "blocks": [{"label": "Sentence 1", "text": first}, {"label": "Sentence 2", "text": second}], "qs": ["q1"]})
                    k = u["key"]
                    key29.append({"item_id": u["item_id"], "annotator": a, "cand_id": u["cid"], "kind": k["kind"], "op": k["op"], "expected": k["expected"],
                                  "source_dimension": k["dimension"], "target_dimension": TARGET.get(k["op"], k["dimension"]), "ref_value": k["ref_value"],
                                  "target_ref": "affirmative" if k["op"].startswith("neg_") else k["ref_value"],
                                  "lex_visible": k["lex_visible"], "family_id": k["family_id"], "variant": k["variant"], "mutant_is_sentence": 1 if u["mut_first"] else 2,
                                  "original": c["original"], "mutant": c["mutant"]})
            if mine:
                s = spec[p]
                files[f"{a}_{p}.json"] = {"check_id": p, "tool": "rate_items_v1", "version": 1, "n_items": len(items), "for": id_hash(a, p),
                                          "title": s["title"], "intro": s["intro"], "help": s["help"], "questions": s["questions"],
                                          "practice": s["practice"], "items": items}
    tot = {a: round(sum(v["seconds"] for v in per[a].values()) / 60 + 2 * len(per[a])) for a in ids}    # + 2 min per part to open and download
    plan = {"salt": S7_SALT, "seed": SEED, "seconds_per_judgment": SEC7, "practice_items_per_part": N_PRACTICE, "overhead_min_per_part": 2,
            "n_units": {"part28": len(u28), "part29": len(u29)}, "listeners_per_unit": 2,
            "per_person": per, "total_minutes": tot,
            "note": "minutes per part = round((items + 2 practice) x seconds per judgment / 60); total adds 2 min per part for opening the file and downloading the CSV"}
    if write:
        out_pkg.mkdir(parents=True, exist_ok=True)
        for f in out_pkg.glob("P*_part2[89].json"):
            f.unlink()
        for n, d in files.items():
            (out_pkg / n).write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
        out_ann.mkdir(parents=True, exist_ok=True)
        for name, rows in (("listener_key.csv", key28), ("oracle_indep_key.csv", key29)):
            with open(out_ann / name, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
            (out_ann / name.replace(".csv", ".sha256")).write_text(hashlib.sha256((out_ann / name).read_bytes()).hexdigest() + f"  {name}\n")
        (out_ann / "assignments").mkdir(exist_ok=True)
        (out_ann / "assignments" / "stage7_plan.json").write_text(json.dumps(plan, indent=1) + "\n")
    return {"plan": plan, "key28": key28, "key29": key29, "files": files, "units28": u28, "units29": u29}


# ----------------------------------------------------------------------------- Part 30 listener study v2 (rules: analysis/listener2/PLAN.md)
OUT2 = ROOT / "analysis/listener2"
SEED2 = 20261118
S8_SALT = "s8-20261118"
AUDIO2 = ROOT / "annotation_package/stage8/audio"
TTS_VENV = ROOT / "tmp/tts"
VOICE = "en_US-lessac-medium"


def used_families():
    used = {d["family_id"] for d in json.loads((ROOT / "analysis/listener/draw.json").read_text())["items"]} \
        if isinstance(json.loads((ROOT / "analysis/listener/draw.json").read_text()), dict) else \
        {d["family_id"] for d in json.loads((ROOT / "analysis/listener/draw.json").read_text())}
    used |= {k["family_id"] for k in jl(ROOT / "analysis/oracle_indep/key.private.jsonl")}
    return used


def draw2():
    fams = load_families()
    used = used_families()
    rng = random.Random(SEED2)
    sel, short, elig = [], {}, {}
    for d in DIMS:
        pool = sorted(f for f, x in fams.items() if x["dimension"] == d and x["human_check"]["n_pass"] >= 3 and f not in used)
        elig[d] = len(pool)
        rng.shuffle(pool)
        picks = pool[:30]
        if len(picks) < 30:
            short[d] = len(picks)
        for fid in picks:
            dv = default_variant(fams[fid])
            sel.append({"family_id": fid, "dimension": d, "nondefault": True, "intended": "B" if dv == "A" else "A", "default_variant": dv})
        # reserve attention pool: default-intended, fresh families not drawn
    for d in DIMS:
        cell = [s for s in sel if s["dimension"] == d]
        rng.shuffle(cell)
        off = rng.randrange(4)
        for i, s in enumerate(cell):
            s["model"] = MODELS[(i + off) % 4]
    sel.sort(key=lambda s: s["family_id"])
    for i, s in enumerate(sel):
        s["item"] = f"N{i + 1:03d}"
    chosen = {s["family_id"] for s in sel}
    att_pool = sorted(f for f, x in fams.items() if x["dimension"] in DIMS and x["human_check"]["n_pass"] >= 3 and f not in used and f not in chosen)
    rng.shuffle(att_pool)
    att = [{"family_id": f, "variant": default_variant(fams[f]), "att": f"A{i + 1:02d}"} for i, f in enumerate(att_pool[:30])]
    OUT2.mkdir(exist_ok=True)
    (OUT2 / "draw.json").write_text(json.dumps({"seed": SEED2, "eligible_fresh_per_dim": elig, "shortfall": short, "items": sel, "attention_pool": att}, indent=1))
    print("eligible", elig, "shortfall", short, "N", len(sel), Counter(s["model"] for s in sel), "attention", len(att))
    return sel, att


def build2():
    fams = load_families()
    dr = json.loads((OUT2 / "draw.json").read_text())
    sel, att = dr["items"], dr["attention_pool"]
    outs = {}
    for r in ("hw1", "hw2"):
        for o in jl(ROOT / f"runs/{r}/outputs.jsonl"):
            if o["channel"] in ("bare", "chip1") and o.get("suggestion_idx", 0) == 0:
                outs[(o["family_id"], o["variant"], o["model"], o["channel"])] = o
    rows, key, dropped = [], [], []
    for s in sel:
        fam = fams[s["family_id"]]
        iv = s["intended"]; ov = "B" if iv == "A" else "A"; d = s["dimension"]
        vi, vo = fam["variants"][iv]["critical_value"], fam["variants"][ov]["critical_value"]
        vals = [fam["variants"][v]["critical_value"] for v in "AB"]
        third = [x for x in RANK[d] if x not in vals]
        act = ACTION[d]
        o_third = act[third[0]] if third and third[0] in act else ACTION["polarity"]["_third"]
        r2 = random.Random(f"{SEED2}-{s['item']}")
        opts = [{"role": "correct", "text": act[vi]}, {"role": "opposite", "text": act[vo]},
                {"role": "clarify", "text": CLARIFY}, {"role": "other", "text": o_third}]
        r2.shuffle(opts)
        topic = fam.get("topic")
        ctx = f"Topic: {topic}" if topic else None
        rd = [("A", "B"), ("B", "A")][r2.randrange(2)]   # order of the two readings randomised per item
        t = {c: (outs.get((s["family_id"], iv, s["model"], c)) or {}) for c in ("bare", "chip1")}
        if not all(t[c].get("text") and t[c].get("parse_ok", True) for c in t):
            dropped.append({"item": s["item"], "family_id": s["family_id"], "model": s["model"], "have": {c: bool(t[c].get("text")) for c in t}})
            continue
        ident = norm(t["bare"]["text"]) == norm(t["chip1"]["text"])
        for c in ("bare", "chip1"):
            txt = t[c]["text"]
            unit = f"{s['item']}-same" if ident else f"{s['item']}-{c}"
            rows.append({"stimulus_id": f"{s['item']}-{c}", "item": s["item"], "kind": "study", "condition": c, "judge_unit": unit,
                         "identical_text": ident, "output_text": txt, "context": ctx, "intended_reading": iv,
                         "reading_1": f'They are saying: "{fam["variants"][rd[0]]["source"]}"',
                         "reading_2": f'They are saying: "{fam["variants"][rd[1]]["source"]}"',
                         "reading_order": "".join(rd), "q2_options": opts,
                         "q2_correct": next(i for i, x in enumerate(opts) if x["role"] == "correct"),
                         "q2_opposite": next(i for i, x in enumerate(opts) if x["role"] == "opposite"),
                         "audio": audio_name(txt)})
        key.append({"item": s["item"], "family_id": s["family_id"], "variant_intended": iv, "dimension": d, "intended_value": vi,
                    "opposite_value": vo, "model": s["model"], "hw_file": fam["_file"], "slp_weight": SLP_W[d],
                    "writer_id": fam.get("writer_id"), "identical_text": ident, "bare_keywords": fam["bare"]})
    # attention items: writer's own sentence of the default-intended variant, 30 families
    for a in att:
        fam = fams[a["family_id"]]
        iv = a["variant"]; ov = "B" if iv == "A" else "A"; d = fam["dimension"]
        vi, vo = fam["variants"][iv]["critical_value"], fam["variants"][ov]["critical_value"]
        act = ACTION[d]
        vals = [vi, vo]; third = [x for x in RANK[d] if x not in vals]
        o_third = act[third[0]] if third and third[0] in act else ACTION["polarity"]["_third"]
        r2 = random.Random(f"{SEED2}-{a['att']}")
        opts = [{"role": "correct", "text": act[vi]}, {"role": "opposite", "text": act[vo]},
                {"role": "clarify", "text": CLARIFY}, {"role": "other", "text": o_third}]
        r2.shuffle(opts)
        rd = [("A", "B"), ("B", "A")][r2.randrange(2)]
        txt = fam["variants"][iv]["source"]
        topic = fam.get("topic")
        rows.append({"stimulus_id": a["att"], "item": a["att"], "kind": "attention", "condition": "reference", "judge_unit": a["att"],
                     "identical_text": False, "output_text": txt, "context": f"Topic: {topic}" if topic else None, "intended_reading": iv,
                     "reading_1": f'They are saying: "{fam["variants"][rd[0]]["source"]}"', "reading_2": f'They are saying: "{fam["variants"][rd[1]]["source"]}"',
                     "reading_order": "".join(rd), "q2_options": opts, "q2_correct": 0 if False else next(i for i, x in enumerate(opts) if x["role"] == "correct"),
                     "q2_opposite": next(i for i, x in enumerate(opts) if x["role"] == "opposite"), "audio": audio_name(txt)})
        key.append({"item": a["att"], "family_id": a["family_id"], "kind": "attention", "dimension": d, "writer_id": fam.get("writer_id"), "hw_file": fam["_file"]})
    # practice (2 audio, 2 text share these sentences) and headphone check
    extra = [("prac-1", "The shop is closed today."), ("prac-2", "I did not cook the rice."), ("hp-check", "The number is four, seven, two.")]
    for k, txt in extra:
        rows.append({"stimulus_id": k, "item": k, "kind": "practice" if k.startswith("prac") else "headphone_check", "condition": None, "judge_unit": k,
                     "output_text": txt, "audio": audio_name(txt)})
    with open(OUT2 / "stimuli.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (ROOT / "orchestration/listener2_key_private.json").write_text(json.dumps(key, indent=1))
    kinds = Counter((r["kind"], r["condition"]) for r in rows)
    print("rows", dict(kinds), "dropped", dropped, "identical items", sum(1 for k in key if k.get("identical_text")))
    return rows


def audio_name(text):
    return hashlib.sha1(f"{S8_SALT}|{text}".encode()).hexdigest()[:12] + ".mp3"


def tts():
    """Render unique sentences with Piper (run under the tmp/tts venv), loudness-normalise to -23 LUFS, encode mp3, write manifest."""
    import subprocess, wave, io
    rows = jl(OUT2 / "stimuli.jsonl")
    texts = sorted({(r["audio"], r["output_text"]) for r in rows})
    AUDIO2.mkdir(parents=True, exist_ok=True)
    py = TTS_VENV / "v/bin/python"
    worker = ROOT / "tmp/tts/render.py"
    jobs = [{"name": n, "text": t} for n, t in texts]
    (ROOT / "tmp/tts/jobs.json").write_text(json.dumps(jobs))
    subprocess.run([str(py), str(worker), str(ROOT / "tmp/tts/jobs.json"), str(TTS_VENV / f"{VOICE}.onnx"), str(AUDIO2)], check=True)
    man = {"tts": "piper-tts", "voice": VOICE, "voice_onnx_sha256": hashlib.sha256((TTS_VENV / f"{VOICE}.onnx").read_bytes()).hexdigest(),
           "sample_rate_render": 22050, "loudness_lufs": -23, "format": "mp3 mono 64k", "files": {}}
    for n, t in texts:
        man["files"][n] = {"sha256": hashlib.sha256((AUDIO2 / n).read_bytes()).hexdigest()}
    (AUDIO2.parent / "audio_manifest.json").write_text(json.dumps(man, indent=1))
    print("rendered", len(texts), "files", AUDIO2)


def _main2(cmd):
    {"draw2": draw2, "build2": build2, "tts": tts}[cmd]()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["draw", "needcalls", "guard", "build", "package", "draw2", "build2", "tts"])
    ap.add_argument("--models")
    ap.add_argument("--force", action="store_true", help="package: overwrite the frozen Stage 7 packet")
    a = ap.parse_args()
    if a.cmd in ("draw2", "build2", "tts"):
        _main2(a.cmd); sys.exit(0)
    if a.cmd == "package":
        if (ANN / "assignments" / "stage7_plan.json").exists() and not a.force:
            print("stage7_plan.json exists (frozen); use --force to redraw"); sys.exit(0)
        r = package()
        t = r["plan"]["total_minutes"]
        print("units", r["plan"]["n_units"], "minutes per person min", min(t.values()), "max", max(t.values()), "mean", round(sum(t.values()) / len(t), 1))
        print({k: (min(v[k]["n_items"] for v in r["plan"]["per_person"].values()), max(v[k]["n_items"] for v in r["plan"]["per_person"].values())) for k in ("part28", "part29")})
    elif a.cmd == "draw":
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

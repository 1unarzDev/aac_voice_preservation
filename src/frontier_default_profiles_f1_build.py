"""default_profiles follow-up F1 builder: same-items bare / chip / plain-word generation requests on the EXPOSURE units
(cue in source, dropped from the human keyword set). Rule: analysis/frontier/default_profiles/PLAN.md 'Follow-up F1'.
Writes analysis/frontier/default_profiles/followup/{units.csv,items_f1.jsonl} and runs/frontier_default_profiles_f1_req/f1.jsonl.
The 'bare' arm is the stored elic1 P0 request (same rendered prompt, T=0): it resolves from the request cache, so it equals the stored elic1 output."""
import json, re, sys, collections
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import build_requests as BR, models as M, prompts as P
OUT = ROOT / "analysis/frontier/default_profiles/followup"; OUT.mkdir(exist_ok=True, parents=True)
SEED = 20261103; N_ACT = 120
MODELS = ["gpt-6.1-terra", "qwen2.5-7b", "llama3.1-8b"]
NEG = re.compile(r"\b(?:not|no|never|none|nothing|nobody|nowhere|neither|nor|without|cannot|cant|dont|doesnt|didnt|wont|isnt|arent|wasnt|werent|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt)\b|n't", re.I)
POLR = re.compile(r"\b(?:please|pls|plz|thanks?|thank|sorry|excuse|pardon|appreciate|could|would|may)\b", re.I)
ACT = re.compile(r"\b(?:please|can|could|would|will|shall|let|lets|let's|why|what|where|when|who|whom|how|do|does|did|is|are|am|may|should|want|need)\b|\?", re.I)
CRIT = {"polarity": ("negated", ["negated", "affirmative", "unclear/mixed"]), "politeness": ("polite", ["polite", "plain", "unclear/mixed"]),
        "speech_act": (None, ["statement", "question", "request/command", "refusal", "acceptance", "offer/suggestion", "unclear/mixed"])}
msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv"); rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv")
key = {j["item_id"]: j for j in map(json.loads, open(ROOT / "annotation/elicitation_key.jsonl"))}
fams = {f["family_id"]: f for f in map(json.loads, open(ROOT / "data/items/elic.jsonl"))}
mi = msg.set_index("item_id"); rows = []
for r in rat.itertuples():
    if not isinstance(r.keywords, str) or not r.keywords.strip(): continue
    m = mi.loc[r.item_id]; dl = key[r.item_id]["detector_labels"]; kw = r.keywords.strip(); fam = "elic-" + m.source_id
    lost = r.speech_act_lenient_lost
    for dim in ("polarity", "politeness", "speech_act"):
        if dim == "polarity": exp = dl["polarity"] == "negated" and not NEG.search(kw); chip, word, val = "[NOT]", "not", "negated"
        elif dim == "politeness": exp = dl["politeness"] != "none" and not POLR.search(kw); chip, word, val = "[PLEASE]", "please", "polite"
        else:
            sa = dl["speech_act"]; exp = sa != "statement" and bool(1 if pd.isna(lost) else lost)
            if sa not in ("question", "request/command"): exp = False
            chip, word, val = ("[?]", "question", sa) if sa == "question" else ("[ASK]", "request", sa)
        if exp: rows.append(dict(item_id=r.item_id, fam=fam, channel="human_" + r.annotator, kw=kw, dim=dim, chip=chip, word=word, value=val, source=m.text,
                                 w=1 / m.inclusion_prob, sample=m["sample"], speech_act=dl["speech_act"]))
U = pd.DataFrame(rows)
rng = np.random.default_rng(SEED)
act = U[U.dim == "speech_act"]; keep = set(rng.choice(act.index.to_numpy(), size=min(N_ACT, len(act)), replace=False))
U = U[(U.dim != "speech_act") | U.index.isin(keep)].reset_index(drop=True)
U["uid"] = [f"{r.fam}|{r.dim}|{r.channel}" for r in U.itertuples()]
U.to_csv(OUT / "units.csv", index=False)
print(U.groupby("dim").size().to_dict(), "speech_act exposure total", len(act))
items, reqs = {}, {}
for r in U.itertuples():
    f = fams[r.fam]; fid = f"dpf1-{r.fam}-{r.dim}"
    if fid not in items:
        g = {k: v for k, v in f.items() if k != "custom_channels"}
        v0 = dict(f["variants"]["A"]); v0["critical_value"] = r.value; v0["chips"] = [r.chip]
        g.update(family_id=fid, dimension=r.dim, split="dpf1", critical_options=CRIT[r.dim][1], variants={"A": v0}, base_family_id=r.fam, custom_channels={"A": {}})
        items[fid] = g
    cc = items[fid]["custom_channels"]["A"]
    inp = {"bare": f"Keywords: {r.kw}", "chip": f"Keywords: {r.chip} {r.kw}", "word": f"Keywords: {r.word} {r.kw}"}
    for arm, text in inp.items():
        ch = f"{arm}|{r.channel}"
        cc[ch] = {"input": text, "commitments": [r.chip] if arm == "chip" else []}
        prompt = P.render("P0", text)
        for m_ in MODELS:
            k = BR.request_key(M.get(m_).model, "P0", prompt, 0.0, 0); tgt = {"family_id": fid, "variant": "A", "channel": ch}
            if k in reqs: reqs[k]["targets"].append(tgt); continue
            reqs[k] = {"request_key": k, "model": m_, "prompt_id": "P0", "prompt_sha": P.template_sha("P0"), "temperature": 0.0, "sample_idx": 0, "max_tokens": 96, "n_suggestions": 1,
                       "family_id": fid, "dimension": r.dim, "split": "dpf1", "items_file": "items_f1.jsonl", "input_text": text, "prompt": prompt, "targets": [tgt]}
with (OUT / "items_f1.jsonl").open("w") as fh:
    for g in items.values(): fh.write(json.dumps(g, ensure_ascii=False) + "\n")
rd = ROOT / "runs/frontier_default_profiles_f1_req"
with (rd / "f1.jsonl").open("w") as fh:
    for q in reqs.values(): fh.write(json.dumps(q, ensure_ascii=False) + "\n")
hit = collections.Counter((q["model"], (ROOT / f"runs/cache/{q['request_key']}.json").exists()) for q in reqs.values())
print(len(items), "families;", len(reqs), "unique requests; cached(model,bool):", dict(hit))

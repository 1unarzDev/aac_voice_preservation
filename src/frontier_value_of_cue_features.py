"""value_of_cue round 2: turn raw Stage-1 (local-model) and Stage-2 (external detector) outputs into per-unit feature tables.
Writes analysis/frontier/value_of_cue/round2/features_<model>.parquet and features_S2.parquet. CPU only (L0 labeller on sampled sentences)."""
import json, math, sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frontier_value_of_cue_lib import U, ROOT, OUT
import layer0
LOCAL = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b"]; R2 = OUT / "round2"; R2.mkdir(exist_ok=True); PD3 = ["polarity", "speech_act", "politeness"]
E = {j["family_id"]: j for j in map(json.loads, open(ROOT / "data/items/elic.jsonl"))}
U["input"] = [E[r.fam]["custom_channels"]["A"]["human_" + r.writer]["input"] for r in U.itertuples()]
def H2(p): p = min(max(p, 1e-9), 1 - 1e-9); return -(p * math.log(p) + (1 - p) * math.log(1 - p))
def ent_top(top):
    p = np.array([math.exp(x[1]) for x in top]); rest = max(1 - p.sum(), 0); q = p[p > 0]
    return float(-(q * np.log(q)).sum() + (-rest * math.log(rest) if rest > 1e-9 else 0))
def yes_p(top):
    y = max([x[1] for x in top if x[0].strip().lower() == "yes"], default=-30); nn = max([x[1] for x in top if x[0].strip().lower() == "no"], default=-30)
    return 1 / (1 + math.exp(nn - y))
def build_local(m):
    rows = {}
    for l in open(ROOT / f"runs/frontier_value_of_cue_s1/{m}.jsonl"): r = json.loads(l); rows[r["input"]] = r
    inputs = list(rows); sents = [s for i in inputs for s in rows[i]["samples"]]; lab = layer0.label_many(sents); lab = [lab[k:k + 8] for k in range(0, len(lab), 8)]
    f = {}
    for i, lb in zip(inputs, lab):
        r = rows[i]; tk = r["tokens"]; lp = np.array([t["lp"] for t in tk]) if tk else np.array([0.0]); o = {}
        o["g_ntok"] = len(tk); o["g_meanlp"] = float(lp.mean()); o["g_minlp"] = float(lp.min()); e = [ent_top(t["top"]) for t in tk[:3]] or [0.0]
        o["g_ent1"] = e[0]; o["g_ent3"] = float(np.mean(e)); tp = sorted([x[1] for x in tk[0]["top"]], reverse=True) if tk else [0, -9]; o["g_margin1"] = float(tp[0] - (tp[1] if len(tp) > 1 else -9))
        cue = {"polarity": [x["polarity"] == "negated" for x in lb], "speech_act": [x["speech_act"] != "statement" for x in lb], "politeness": [x["politeness"] != "none" for x in lb]}
        joint = {}
        for k in range(len(lb)): key = (cue["polarity"][k], cue["speech_act"][k], cue["politeness"][k]); joint[key] = joint.get(key, 0) + 1
        pj = np.array(list(joint.values())) / len(lb); o["jH"] = float(-(pj * np.log(pj)).sum())
        for d in PD3:
            fq = float(np.mean(cue[d])); o[f"s_freq_{d}"] = fq; o[f"s_ent_{d}"] = H2(fq); o[f"s_minor_{d}"] = min(fq, 1 - fq)
            pyes = yes_p(r["probe"][d]); o[f"p_yes_{d}"] = pyes; o[f"p_logit_{d}"] = math.log(max(pyes, 1e-6) / max(1 - pyes, 1e-6))
        o["greedy_text"] = r["greedy_text"]; f[i] = o
    gl = layer0.label_many([f[i]["greedy_text"] for i in inputs])
    for i, x in zip(inputs, gl): f[i].update(o_polarity=float(x["polarity"] == "negated"), o_speech_act=float(x["speech_act"] != "statement"), o_politeness=float(x["politeness"] != "none"))
    F = U[["item_id", "writer", "input"]].join(pd.DataFrame([f[i] for i in U.input], index=U.index)); F.to_parquet(R2 / f"features_{m}.parquet"); return F
def build_s2():
    d = {}
    for l in open(ROOT / "runs/frontier_value_of_cue_s2/detector.jsonl"): r = json.loads(l); d[r["input"]] = r
    m = {"polarity": "negation", "speech_act": "question_or_request", "politeness": "polite", "certainty": "hedged_or_emphatic", "agent": "subject_other_than_i"}
    F = U[["item_id", "writer", "input"]].copy()
    for k, v in m.items(): F[f"x_{k}"] = [d[i][v] / 100 for i in U.input]
    F.to_parquet(R2 / "features_S2.parquet"); return F
if __name__ == "__main__":
    for a in sys.argv[1:]:
        print(a); build_s2() if a == "S2" else build_local(a)

"""value_of_cue Stage 0 step A: build the unit table (message x writer) with commit-loss outcomes per model and dimension.
Writes analysis/frontier/value_of_cue/units.parquet and prints the T2 consistency gate. 0 model calls."""
import json, re, sys
import numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/value_of_cue"
DIMS = ["polarity", "speech_act", "politeness", "certainty", "agent"]
MODELS = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]
NEG = re.compile(r"\b(?:not|no|never|none|nothing|nobody|nowhere|neither|nor|without|cannot|cant|dont|doesnt|didnt|wont|isnt|arent|wasnt|werent|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt)\b|n't", re.I)
POL = re.compile(r"\b(?:please|pls|plz|thanks?|thank|sorry|excuse|pardon|appreciate|could|would|may)\b", re.I)
ACT = re.compile(r"\b(?:please|can|could|would|will|shall|let|lets|let's|why|what|where|when|who|whom|how|do|does|did|is|are|am|may|should|want|need)\b|\?", re.I)

def build():
    msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv"); rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv")
    key = {j["item_id"]: j for j in map(json.loads, open(ROOT / "annotation/elicitation_key.jsonl"))}
    msg["w"] = 1 / msg.inclusion_prob; msg["fam"] = "elic-" + msg.source_id; mi = msg.set_index("item_id")
    rows = []
    for r in rat.itertuples():
        m = mi.loc[r.item_id]; k = key[r.item_id]; L = k["detector_labels"]; P = k["present"]
        rows.append(dict(item_id=r.item_id, writer=r.annotator, fam=m.fam, kw=str(r.keywords), w=m.w, sample=m["sample"], stratum=m.stratum, text=m.text,
                         src_pol=L["polarity"], src_act=L["speech_act"], src_pols=L["politeness"], src_cert=L["certainty"], src_agent=L["agent"],
                         pres_polarity=L["polarity"] == "negated", pres_speech_act=L["speech_act"] != "statement", pres_politeness=L["politeness"] != "none",
                         pres_certainty=bool(P["certainty"]), pres_agent=bool(P["agent"]),
                         lost_polarity=r.polarity_lenient_lost, lost_speech_act=r.speech_act_lenient_lost, lost_politeness=r.politeness_lenient_lost,
                         lost_certainty=r.certainty_lenient_lost, lost_agent=r.agent_lenient_lost))
    U = pd.DataFrame(rows)
    U["kw_neg"] = U.kw.str.contains(NEG); U["kw_pol"] = U.kw.str.contains(POL); U["kw_act"] = U.kw.str.contains(ACT)
    # 'no cue in keywords' exactly as src/robust_t2_posterior.py (polarity/politeness: lexicon; speech act: lenient lost flag if cue, else lexicon)
    U["nocue_polarity"] = ~U.kw_neg; U["nocue_politeness"] = ~U.kw_pol
    U["nocue_speech_act"] = np.where(U.pres_speech_act, U.lost_speech_act.fillna(1).astype(bool), ~U.kw_act)
    U["nocue_certainty"] = U.lost_certainty.fillna(1).astype(bool); U["nocue_agent"] = U.lost_agent.fillna(1).astype(bool)
    sc = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); sc = sc[sc.prompt_id.eq("P0") & sc.channel.str.startswith("human_")]
    sc = sc.rename(columns={"family_id": "fam"}); sc["writer"] = sc.channel.str.replace("human_", "", regex=False)
    for mdl in MODELS:
        s = sc[sc.model.eq(mdl)].set_index(["fam", "writer"]); idx = pd.MultiIndex.from_frame(U[["fam", "writer"]])
        o = s.reindex(idx); assert o.polarity.notna().mean() > 0.99, mdl
        o_pol = o.polarity.eq("negated").to_numpy(); o_act = ~o.speech_act.eq("statement").to_numpy(); o_pls = o.politeness.ne("none").to_numpy()
        ok = lambda col: o[col].notna().to_numpy()
        valid = dict(polarity=ok("polarity"), speech_act=ok("speech_act"), politeness=ok("politeness"), certainty=ok("certainty"), agent=ok("agent"))
        ocert = o.certainty.to_numpy(); oagent = o.agent.to_numpy()
        marked = np.isin(ocert, ["hedged/uncertain", "strongly certain/emphatic"])
        r = dict(polarity=U.pres_polarity & U.nocue_polarity & ~o_pol, speech_act=U.pres_speech_act & U.nocue_speech_act & ~o_act,
                 politeness=U.pres_politeness & U.nocue_politeness & ~o_pls,
                 certainty=U.pres_certainty & U.nocue_certainty & (ocert != U.src_cert.to_numpy()),
                 agent=U.pres_agent & U.nocue_agent & (oagent != U.src_agent.to_numpy()))
        s_ = dict(polarity=~U.pres_polarity & o_pol, speech_act=~U.pres_speech_act & o_act, politeness=~U.pres_politeness & o_pls,
                  certainty=~U.pres_certainty & marked, agent=pd.Series(False, index=U.index))   # agent spurious undefined (a subject is always chosen) -> 0
        for d in DIMS:
            U[f"r_{d}_{mdl}"] = np.where(valid[d], np.asarray(r[d], float), np.nan)
            U[f"s_{d}_{mdl}"] = np.where(valid[d], np.asarray(s_[d], float), np.nan)
    for d in DIMS:
        U[f"r_{d}"] = U[[f"r_{d}_{m}" for m in MODELS]].mean(axis=1); U[f"s_{d}"] = U[[f"s_{d}_{m}" for m in MODELS]].mean(axis=1)
        U[f"y_{d}"] = U[f"r_{d}"] + U[f"s_{d}"]
    return U

def slp_weights():
    d = {}
    for f in ["SLP1", "SLP2"]:
        t = pd.read_csv(ROOT / f"expert_package/returns_slp/slp_rating_{f}.csv"); t = t[t.task == 1]
        d[f] = dict(zip(t.item_id, t.severity / 5))
    return d

if __name__ == "__main__":
    U = build(); OUT.mkdir(parents=True, exist_ok=True)
    U.to_parquet(OUT / "units.parquet")
    print("units", len(U), "writers", U.writer.nunique(), "messages", U.item_id.nunique(), "status", pd.read_csv(ROOT/"analysis/elicitation/ratings.csv").status.value_counts().to_dict())
    w = U.w
    for d in DIMS:
        print(d, "reversal/1000 per model:", {m: round(1000 * (U[f"r_{d}_{m}"].fillna(0) * w).sum() / w.sum(), 1) for m in MODELS},
              "mean:", round(1000 * (U[f"r_{d}"] * w).sum() / w.sum(), 1), "spurious/1000:", round(1000 * (U[f"s_{d}"] * w).sum() / w.sum(), 1))
    print(slp_weights())

"""Read-only exploratory checks for hyp.md. Run with the project venv from repo root."""
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
SEED, B = 20261031, 10000
manifest, results, examples = {}, {}, []


def read(path):
    raw = Path(path).read_bytes()
    manifest[path] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return raw


def table(run):
    return pd.read_parquet(io.BytesIO(read(f"runs/{run}/scored.parquet")))


def jl(path):
    return [json.loads(x) for x in read(path).decode().splitlines() if x.strip()]


def rate(d, col):
    """Row-weighted rate, resampling whole families, retaining all models/arms."""
    x = d[["family_id", col]].dropna().copy()
    x[col] = x[col].astype(float)
    c = x.groupby("family_id")[col].agg(["sum", "count"])
    a = c.to_numpy()
    ix = np.random.default_rng(SEED).integers(len(a), size=(B, len(a)))
    boot = a[ix].sum(axis=1)
    z = boot[:, 0] / boot[:, 1]
    return dict(k=float(x[col].sum()), n=len(x), families=len(c), estimate=x[col].mean(),
                lo=float(np.quantile(z, .025)), hi=float(np.quantile(z, .975)))


def paired(d, col, arm, left, right, keys):
    """Left minus right; average repeats before pairing; family-cluster CI."""
    w = d.groupby(keys + [arm])[col].mean().unstack(arm)
    x = (w[left] - w[right]).dropna().rename("delta").reset_index()
    return rate(x, "delta")


def between(d, col, group, left, right):
    """Between disjoint family strata: independently bootstrap each stratum's families."""
    rng = np.random.default_rng(SEED)
    bs, obs = {}, {}
    for g in (left, right):
        x = d[d[group].eq(g)][["family_id", col]].dropna().copy()
        x[col] = x[col].astype(float)
        a = x.groupby("family_id")[col].agg(["sum", "count"]).to_numpy()
        z = a[rng.integers(len(a), size=(B, len(a)))].sum(axis=1)
        bs[g], obs[g] = z[:, 0] / z[:, 1], x[col].mean()
    delta = bs[left] - bs[right]
    return dict(estimate=float(obs[left]-obs[right]), lo=float(np.quantile(delta,.025)),
                hi=float(np.quantile(delta,.975)))


def ratio_contrast(d, col, group, left, right):
    """Correlated groups: bootstrap shared families jointly, then difference row rates."""
    c = d.assign(_n=1).groupby(["family_id", group]).agg(k=(col, "sum"), n=("_n", "sum"))
    fs = sorted(d.family_id.unique())
    a = np.zeros((len(fs), 4))
    for i, f in enumerate(fs):
        for j, g in enumerate((left, right)):
            if (f, g) in c.index:
                a[i, 2*j:2*j+2] = c.loc[(f,g), ["k", "n"]]
    z = a[np.random.default_rng(SEED).integers(len(a), size=(B,len(a)))].sum(axis=1)
    diff = z[:,0]/z[:,1] - z[:,2]/z[:,3]
    tot = a.sum(axis=0)
    return dict(estimate=float(tot[0]/tot[1]-tot[2]/tot[3]),
                lo=float(np.quantile(diff,.025)), hi=float(np.quantile(diff,.975)))


def example(d, label):
    # Declared rule: lexicographic family, model, variant, channel, suggestion index.
    r = d.sort_values(["family_id", "model", "variant", "channel", "suggestion_idx"]).iloc[0]
    path = f"runs/{r['run']}/outputs.jsonl"
    rows = jl(path)
    hit = [z for z in rows if z.get("output_id")==r.output_id and z.get("family_id")==r.family_id
           and z.get("variant")==r.variant and z.get("channel")==r.channel]
    assert hit and hit[0]["text"] == r.text, (label, r.to_dict())
    examples.append(dict(label=label, stored_file=path,
                         **{k:r[k] for k in ["output_id", "request_key", "family_id", "model", "variant", "channel", "input_text", "text"]}))


m, p, g, e, s = (table(r) for r in ["main1", "pilot1", "guard1", "expB1", "span1"])
items = {it["family_id"]: it for it in jl("data/items/test.jsonl")}
quarantine = {f for f,it in items.items() if it["dimension"]=="speech_act" and any(
    v["critical_value"] in {"refusal", "acceptance"} for v in it["variants"].values())}

# H1: changing only the register chip changes the explicitly supplied request act.
for run, d in [("main1",m), ("pilot1",p)]:
    d = d[d.dimension.eq("politeness") & d.channel.eq("chipall")].copy()
    d["request"] = d.speech_act.eq("request/command").astype(float)
    for prompt in ["P0", "P1", "S3", "P2"]:
        x = d[d.prompt_id.eq(prompt)]
        for model in sorted(x.model.unique()):
            z = x[x.model.eq(model)]
            name = f"H1/{run}/{prompt}/{model}"
            results[name] = {v:rate(z[z.variant_value.eq(v)],"request") for v in ["plain","polite"]}
            results[name]["plain_minus_polite"] = paired(z,"request","variant_value","plain","polite",["family_id","model"])
            results[name]["plain_register_match"] = rate(z[z.variant_value.eq("plain")],"critical_match")
            results[name]["plain_joint_match"] = rate(z[z.variant_value.eq("plain")],"constraint_preserving")
    z=d[d.prompt_id.eq("P0")]
    results[f"H1/{run}/P0/pooled_delta"] = paired(z,"request","variant_value","plain","polite",["family_id","model"])
    if run == "main1":
        x=z[z.model.eq("llama3.1-8b") & z.variant_value.eq("plain") & ~z.request.eq(1)].copy()
        x["run"]=run
        example(x,"H1 plain chipall request lost")

# Exp B has four reused families, two greedy repeats, no new family replication.
z=e[e.dimension.eq("politeness") & e.model.eq("llama3.1-8b")].copy()
z["request"] = z.speech_act.eq("request/command").astype(float)
for (channel,prompt),x in z.groupby(["channel","prompt_id"]):
    if channel not in {"i_xy","e_alias","e_nl"}: continue
    results[f"H1/expB/{channel}/{prompt}"]={v:rate(x[x.variant_value.eq(v)],"request") for v in ["plain","polite"]}

# Repaired H1: same paired register comparison, G1 only.
z=g[g.prompt_id.eq("G1") & g.dimension.eq("politeness") & g.channel.eq("chipall") & g.model.eq("llama3.1-8b")].copy()
z["request"]=z.speech_act.eq("request/command").astype(float)
results["H1/G1/llama"]={v:rate(z[z.variant_value.eq(v)],"request") for v in ["plain","polite"]}
results["H1/G1/llama"]["delta"]=paired(z,"request","variant_value","plain","polite",["family_id","model"])

# H2: post-hoc lexical/construction split, exhaustive over the 7 nonquarantined
# question families. This is not a prospectively validated classifier.
state={"act-08","act-12","act-15"}
action={"act-07","act-11","act-13","act-14"}
z=m[m.prompt_id.eq("P0") & m.dimension.eq("speech_act") & m.variant_value.eq("question") & ~m.family_id.isin(quarantine)].copy()
assert set(z.family_id)==state|action
z["construction"]=z.family_id.map(lambda f:"state" if f in state else "action")
z["failure"]=1-z.critical_match.astype(float)
for channel,x in z.groupby("channel"):
    results[f"H2/{channel}"]={v:rate(x[x.construction.eq(v)],"failure") for v in ["action","state"]}
    results[f"H2/{channel}"]["action_minus_state"]=between(x,"failure","construction","action","state")
x=z[z.channel.eq("chip1")]
results["H2/chip1/by_model"]={model:{v:rate(t[t.construction.eq(v)],"failure") for v in ["action","state"]} for model,t in x.groupby("model")}
results["H2/chip1/leave_one_out"]={f:between(x[~x.family_id.eq(f)],"failure","construction","action","state")["estimate"] for f in sorted(x.family_id.unique())}
ex=x[x.failure.eq(1)].copy();ex["run"]="main1";example(ex,"H2 action question chip1 failure")

# H3: compare each rewritten slot to its actual source sentence's stored labels.
# I2 source is the replaced slot; I2t source is the top slot (not replaced slot).
gens=jl("runs/span1/generations.jsonl")
idx=s[s.variant.eq("A")].set_index(["family_id","model","prompt_id","suggestion_idx"])
rewrites=[]
for gen in gens:
    arm=gen["prompt_id"]
    if arm not in {"I2","I2t"}:continue
    for edit in gen.get("span_plan",[]):
        if not edit.get("rewritten"):continue
        f,model=gen["family_id"],gen["model"]
        slot=edit["slot"];source_slot=slot if arm=="I2" else 0
        a=idx.loc[(f,model,"P2",source_slot)];b=idx.loc[(f,model,arm,slot)]
        target=edit["target"]
        label=b[edit["dim"]]
        achieved=label==target if edit["dim"]=="polarity" else (
            label=="hedged/uncertain" if target=="hedged" else label in {"plain assertion","strongly certain/emphatic"})
        agent_known=all(pd.notna(t) and t not in {"unclear/mixed","unspecified"} for t in [a.agent,b.agent])
        rewrites.append(dict(family_id=f,model=model,arm=arm,dim=edit["dim"],slot=slot,source_slot=source_slot,
            quarantine=f in quarantine,verified=edit.get("verified"),achieved=achieved,
            act_change=a.speech_act!=b.speech_act,
            agent_change=(a.agent!=b.agent) if agent_known else None,
            before_act=a.speech_act,after_act=b.speech_act,before_agent=a.agent,after_agent=b.agent,
            before=a.text,after=b.text,output_id=b.output_id,request_key=b.request_key))
r=pd.DataFrame(rewrites)
r.to_csv(OUT/"rewrite_audit.csv",index=False)
# Raw extraction sensitivity: bypass the general-dimension layer0 tiebreak.
sj={(z["text_id"],z["family_id"],z["input_text"]):z for z in jl("runs/span1/judgments.jsonl")}
raw_rows=[]
for rr in rewrites:
    if rr["arm"]!="I2" or rr["quarantine"]:continue
    f,model=rr["family_id"],rr["model"]
    a=idx.loc[(f,model,"P2",rr["source_slot"])];b=idx.loc[(f,model,"I2",rr["slot"])]
    aj=sj[(a.text_id,f,a.input_text)];bj=sj[(b.text_id,f,b.input_text)]
    rec={"family_id":f}
    for judge in ["J1","J2"]:
        rec[judge]=aj[f"{judge}_speech_act"]!=bj[f"{judge}_speech_act"]
    rec["agree_both_ends"]=(aj["J1_speech_act"]==aj["J2_speech_act"] and bj["J1_speech_act"]==bj["J2_speech_act"])
    raw_rows.append(rec)
raw=pd.DataFrame(raw_rows)
results["H3/raw_speech_act"]={judge:rate(raw,judge) for judge in ["J1","J2"]}
results["H3/raw_speech_act"]["agreement_only"]=rate(raw[raw.agree_both_ends],"J1")
results["H3/raw_speech_act"]["n_disagree_either_end"]=int((~raw.agree_both_ends).sum())
# H1 raw agreement audit on all 20 Llama P0 chipall politeness targets.
mj={(z["text_id"],z["family_id"],z["input_text"]):z for z in jl("runs/main1/judgments.jsonl")}
xx=m[m.prompt_id.eq("P0")&m.model.eq("llama3.1-8b")&m.dimension.eq("politeness")&m.channel.eq("chipall")]
results["H1/raw_agreement"]={"n":len(xx),"n_J1_J2_agree":sum(mj[(a.text_id,a.family_id,a.input_text)]["J1_speech_act"]==mj[(a.text_id,a.family_id,a.input_text)]["J2_speech_act"] for _,a in xx.iterrows())}
for arm in ["I2","I2t"]:
    for subset,x in [("all",r[r.arm.eq(arm)]),("nonquarantine",r[r.arm.eq(arm)&~r.quarantine])]:
        name=f"H3/{arm}/{subset}"
        results[name]={"act_change":rate(x,"act_change"),"agent_change_known":rate(x,"agent_change"),"target_achieved":rate(x,"achieved")}
        if arm=="I2":
            results[name]["by_edit"]={dim:rate(t,"act_change") for dim,t in x.groupby("dim")}
            results[name]["certainty_minus_polarity"]=ratio_contrast(x,"act_change","dim","certainty","polarity")
            results[name]["among_achieved"]=rate(x[x.achieved],"act_change")
            results[name]["by_model"]={model:rate(t,"act_change") for model,t in x.groupby("model")}
            results[name]["transitions"]=x.groupby(["before_act","after_act"]).size().to_dict().__str__()
            results[name]["changed_to_statement"]=int((x.act_change&x.after_act.eq("statement")).sum())
            if subset=="nonquarantine":
                for dim in ["certainty","polarity"]:
                    ex=x[x.dim.eq(dim)&x.act_change].sort_values(["family_id","model","slot"])
                    rr=ex.iloc[0]
                    before=s[s.family_id.eq(rr.family_id)&s.model.eq(rr.model)&s.prompt_id.eq("P2")&s.suggestion_idx.eq(rr.source_slot)&s.variant.eq("A")].copy()
                    before["run"]="span1"
                    example(before,f"H3 {dim} edit source")
                    after=s[s.output_id.eq(rr.output_id)&s.variant.eq("A")].copy();after["run"]="span1"
                    example(after,f"H3 {dim} edit act changed")

# Supporting guard residual decomposition (not a new broad guard-efficacy claim).
gg={x["request_key"]:x for x in jl("runs/guard1/generations.jsonl")}
z=g[g.prompt_id.eq("G1") & g.channel.isin(["chip1","chipall","full"]) & ~g.family_id.isin(quarantine)].copy()
z["failure"]=~z.constraint_preserving.eq(True)|z.politeness_added.eq(True)
z["flagged"]=z.request_key.map(lambda k:bool(gg[k].get("flags_final")))
z["any_act_problem"]=z.contra_speech_act.eq(True)|(z.dimension.eq("speech_act")&~z.critical_match.eq(True))
results["guard_nonquarantine"]={"residual_rate":rate(z,"failure"),"residual_act_share":rate(z[z.failure],"any_act_problem"),"residual_flagged_share":rate(z[z.failure],"flagged"),"unflagged_failure_rate":rate(z[~z.flagged],"failure")}

# Candidate screens without a new hypothesis: no monotonic model-size inference;
# full-input plain imperatives are all imperative, so request-form interaction unidentifiable.
results["meta"]={"seed":SEED,"bootstrap_resamples":B,"quarantine_families":sorted(quarantine),"manifest":manifest,
                 "notes":"Exploratory, unadjusted pointwise percentile CIs. Model roster fixed; family resampling is not a population guarantee."}
(OUT/"hyp_checks.json").write_text(json.dumps(results,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
(OUT/"hyp_examples.json").write_text(json.dumps(examples,indent=2)+"\n")
print(json.dumps({k:v for k,v in results.items() if k in ["H1/main1/P0/llama3.1-8b","H1/pilot1/P0/llama3.1-8b","H1/main1/P0/pooled_delta","H1/G1/llama","H2/chip1","H2/chip1/leave_one_out","H3/I2/nonquarantine","guard_nonquarantine"]},indent=2))

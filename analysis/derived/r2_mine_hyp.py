"""CPU-only cycle-2 exploration. Reads frozen evidence; writes only beside this file."""
import hashlib
import io
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
B, SEED = 10000, 20261101
hashes, results, examples = {}, {}, []


def read(p):
    raw = (ROOT / p).read_bytes()
    hashes[p] = hashlib.sha256(raw).hexdigest()
    return raw


def jl(p):
    return [json.loads(x) for x in read(p).decode().splitlines() if x.strip()]


def table(p):
    return pd.read_parquet(io.BytesIO(read(p)))


def rate(d, value, cluster="cluster_id"):
    x = d[[cluster, value]].dropna().copy()
    x[value] = x[value].astype(float)
    a = x.groupby(cluster)[value].agg(["sum", "count"]).to_numpy()
    draws = np.random.default_rng(SEED).multinomial(len(a), np.full(len(a), 1 / len(a)), size=B)
    z = draws @ a
    boot = z[:, 0] / z[:, 1]
    return dict(k=float(x[value].sum()), n=len(x), clusters=len(a),
                estimate=float(x[value].mean()), lo=float(np.quantile(boot, .025)),
                hi=float(np.quantile(boot, .975)))


def difference(d, value, arm, left, right, cluster="cluster_id"):
    # Joint resampling also preserves clusters shared across the compared strata.
    groups = sorted(d[cluster].unique())
    a = np.zeros((len(groups), 4))
    for j, g in enumerate((left, right)):
        s = d[d[arm].eq(g)].groupby(cluster)[value].agg(["sum", "count"]).reindex(groups, fill_value=0)
        a[:, 2*j:2*j+2] = s.to_numpy()
    tot = a.sum(axis=0)
    z = np.random.default_rng(SEED).multinomial(len(a), np.full(len(a), 1/len(a)), size=B) @ a
    ok = (z[:, 1] > 0) & (z[:, 3] > 0)
    boot = z[ok, 0]/z[ok, 1] - z[ok, 2]/z[ok, 3]
    return dict(estimate=float(tot[0]/tot[1]-tot[2]/tot[3]),
                lo=float(np.quantile(boot, .025)), hi=float(np.quantile(boot, .975)),
                clusters=len(groups), n_boot_valid=int(ok.sum()))


def example(r, run, label):
    rows = jl(f"runs/{run}/outputs.jsonl")
    hits = [x for x in rows if x["output_id"] == r.output_id
            and x["family_id"] == r.family_id and x["variant"] == r.variant
            and x["channel"] == r.channel]
    assert hits and hits[0]["text"] == r.text and hits[0]["input_text"] == r.input_text
    examples.append(dict(label=label, stored_file=f"runs/{run}/outputs.jsonl", **hits[0]))


items = {i["family_id"]: i for p in ["data/items/r2_c1.jsonl", "data/items/r2_c2.jsonl"] for i in jl(p)}
c = table("runs/r2c1/scored.parquet")
c = c[~c.family_id.isin(["r2act-078", "r2act-079"])].copy()
c["cluster_id"] = c.family_id.map(lambda f: items[f]["cluster_id"])
c["match"] = c.critical_match.astype("boolean")
c.loc[c.critical_source.eq("J1"), "match"] = pd.NA

# H1: set safety on supplied input, compared with an equal-size S3 set.
keys = ["family_id", "variant", "model", "dimension", "cluster_id", "channel"]
rows = []
for key, x in c[c.channel.isin(["chip1", "chipall", "full"])].groupby(keys+["prompt_id"]):
    *kk, prompt = key
    known = x.match.notna().all()
    expected = 1 if prompt == "P0" else 3
    rows.append(dict(zip(keys, kk), prompt=prompt, n=len(x), known=bool(known),
                     complete=len(x)==expected, any_fail=bool((x.match==False).any()),
                     frac_fail=float((~x.match).mean()) if known else None))
sets = pd.DataFrame(rows)
sets.to_csv(OUT / "supplied_sets.csv", index=False)
for channel in ["chip1", "chipall", "full"]:
    x = sets[sets.channel.eq(channel)].copy()
    eligible = x[x.known & x.complete].groupby(keys).prompt.nunique()
    eligible = eligible[eligible.eq(3)].reset_index()[keys]
    x = x.merge(eligible, on=keys)
    stats = {p: rate(t, "any_fail") for p,t in x.groupby("prompt")}
    stats["P2_minus_S3"] = difference(x, "any_fail", "prompt", "P2", "S3")
    stats["P2_minus_P0"] = difference(x, "any_fail", "prompt", "P2", "P0")
    stats["available_targets"] = int(len(sets[sets.channel.eq(channel)])/3)
    stats["by_dimension"] = {dim: {p:rate(t,"any_fail") for p,t in z.groupby("prompt")}
                             for dim,z in x.groupby("dimension")}
    stats["by_model"] = {model: dict(P2=rate(z[z.prompt.eq("P2")],"any_fail"),
          S3=rate(z[z.prompt.eq("S3")],"any_fail"),
          delta=difference(z,"any_fail","prompt","P2","S3")) for model,z in x.groupby("model")}
    results[f"H1/{channel}"] = stats
    if channel=="full":
        w=x.pivot(index=keys,columns="prompt",values="any_fail").reset_index()
        w["delta"]=w.P2.astype(float)-w.S3.astype(float)
        stats["family_only_delta"]=rate(w,"delta","family_id")
        stats["leave_one_cluster_out_delta_range"]=[float(v) for v in (
            w.groupby("cluster_id").delta.agg(["sum","count"]).apply(
                lambda r:(w.delta.sum()-r["sum"])/(len(w)-r["count"]),axis=1).min(),
            w.groupby("cluster_id").delta.agg(["sum","count"]).apply(
                lambda r:(w.delta.sum()-r["sum"])/(len(w)-r["count"]),axis=1).max())]
        # The same shared eligibility set for the suggestion-position diagnostic.
        slots=c[c.channel.eq("full") & c.prompt_id.eq("P2")].merge(eligible,on=keys)
        slots["fail"]=(~slots.match).astype(float)
        stats["by_slot"]={str(k):rate(t,"fail") for k,t in slots.groupby("suggestion_idx")}
        stats["example_stratum"] = rate(slots[slots.dimension.eq("polarity")],"fail")
        # Bound the contrast on all planned targets by adversarial assignments
        # of unknown labels and incomplete sets; known failures remain failures.
        allsets=sets[sets.channel.eq("full")]
        bounds={}
        for p,z in allsets.groupby("prompt"):
            bounds[p]=(float(z.any_fail.mean()),float((z.any_fail|~z.known|~z.complete).mean()))
        stats["all_target_missingness_bound_P2_minus_S3"]=[bounds["P2"][0]-bounds["S3"][1],
                                                          bounds["P2"][1]-bounds["S3"][0]]
        early={"r2act-007","r2act-029","r2act-030","r2act-032","r2plt-002","r2pol-004"}
        stats["exclude_early_cache_families_delta"]=difference(x[~x.family_id.isin(early)],
                    "any_fail","prompt","P2","S3")

# A conservative, judge-free endpoint distinguishes opposite-source reproductions
# from polarity-labelled paraphrases such as "don't feel sick" for "feel well".
def norm(s):
    return " ".join(re.sub(r"[^a-z0-9\s]", "", s.lower().replace("’", "'")).split())

lex=c[c.dimension.eq("polarity") & c.channel.eq("full")].copy()
lex["copy_partner"]=[norm(r.text)==norm(items[r.family_id]["variants"][
    "B" if r.variant=="A" else "A"]["source"]) for r in lex.itertuples()]
lexsets=lex.groupby(keys+["prompt_id"]).agg(n=("text","size"),copy_partner=("copy_partner","any")).reset_index()
ok=lexsets[lexsets.prompt_id.isin(["P2","S3"]) & lexsets.n.eq(3)].groupby(keys).prompt_id.nunique()
ok=ok[ok.eq(2)].reset_index()[keys]
lexsets=lexsets.merge(ok,on=keys)
results["H1/exact_partner"]={p:rate(z,"copy_partner") for p,z in lexsets.groupby("prompt_id")}
results["H1/exact_partner"]["P2_minus_S3"]=difference(lexsets,"copy_partner","prompt_id","P2","S3")
ex=lex[lex.prompt_id.eq("P2")&lex.copy_partner].merge(ok,on=keys).sort_values(
    ["family_id","model","variant","suggestion_idx"]).iloc[0]
example(ex,"r2c1","H1: first full-P2 exact opposite-source reproduction")
chosen=c[c.family_id.eq(ex.family_id)&c.model.eq(ex.model)&c.variant.eq(ex.variant)&c.channel.eq("full")]
for _,r in chosen.sort_values(["prompt_id","sample_idx","suggestion_idx"]).iterrows():
    example(r,"r2c1","H1 paired full-output inventory")

# H2: localized factorial-cell damage, rather than another generic composition claim.
t = table("analysis/r2d/transitions.parquet")
x = t[t.model.eq("llama3.1-8b") & t.encoding.eq("STATEMENT") & t.dimension.eq("polarity")].copy()
x["cluster_id"] = x.scenario
x["group"] = np.where(x.cell.eq("NOT|YOU"), "NOT|YOU", "other")
results["H2"]={g:rate(z,"damage") for g,z in x.groupby("group")}
results["H2"]["delta"]=difference(x,"damage","group","NOT|YOU","other")
results["H2"]["cell_counts"]=x.groupby("cell").damage.agg(["sum","size"]).to_dict("index")
bad=x[x.damage].copy()
bad["negation_absent"]=~bad.text_b.str.contains(r"\b(?:not|never|no)\b|n['’]t",case=False,regex=True)
bad["nonstatement"]=bad.speech_act_b.ne("statement")
results["H2"]["among_damage"]={v:rate(bad,v) for v in ["negation_absent","nonstatement"]}
results["H2"]["after_acts"]=bad.speech_act_b.value_counts().to_dict()
results["H2"]["damage_scenarios"]=int(bad.scenario.nunique())
results["H2"]["damage_by_draw"]=x[x.cell.eq("NOT|YOU")].groupby("draw").damage.agg(["sum","size"]).to_dict("index")
results["H2"]["raw_judge_agree_at_both_ends"]=int((x.critical_J1_s.eq(x.critical_J2_s)&x.critical_J1_b.eq(x.critical_J2_b)).sum())
wd=table("runs/r2d1/scored.parquet")
ex=bad.sort_values(["scenario","cell","draw"]).iloc[0]
for endpoint in ["s","b"]:
    r=wd[wd.output_id.eq(ex[f"output_id_{endpoint}"]) & wd.family_id.eq(ex.family_id)
         & wd.variant.eq(ex.variant)].iloc[0]
    example(r,"r2d1",f"H2 first damage, endpoint {endpoint}")

# H3: the visible restored cue and the source endpoint must express the same value.
wi={i["family_id"]:i for i in jl("data/items/wb.jsonl")}
wb=table("runs/wb1/scored.parquet")
wb["cluster_id"]=wb.family_id
wb["sample"]=wb.family_id.map(lambda f:wi[f]["sample"])
wb["match"]=wb.critical_match.astype("boolean")
wb.loc[wb.critical_J1.ne(wb.critical_J2),"match"]=pd.NA
wb["cue_conflict"]=wb.family_id.map(lambda f:wi[f]["focal_dim"]=="certainty"
    and wi[f]["variants"]["A"]["critical_value"]=="plain assertion"
    and (wi[f].get("restoration") or {}).get("cue")=="[MAYBE]")
wb["failure"]=(~wb.match).astype("Float64")
cue_values={"[NOT]":{"negated"},"[YES]":{"affirmative"},"[?]":{"question"},
    "[ASK]":{"request/command"},"[TELL]":{"statement"},"[REFUSE]":{"refusal"},
    "[MAYBE]":{"hedged/uncertain"},"[SURE]":{"plain assertion","strongly certain/emphatic"},
    "[I]":{"speaker"},"[YOU]":{"addressee"},"[WE]":{"we/joint"},"[THEY]":{"third party"},
    "[PLEASE]":{"polite"},"[PLAIN]":{"plain"}}
audit=[]
for f,it in wi.items():
    r=it.get("restoration")
    if not r: continue
    val=it["variants"]["A"]["critical_value"]
    status=("word_needs_audit" if r["mode"]!="chip" else
            "unexpressible_reference" if val=="unclear/mixed" else
            "aligned" if val in cue_values[r["cue"]] else "definite_conflict")
    audit.append(dict(family_id=f,sample=it["sample"],dim=it["focal_dim"],source_value=val,
                      actual_cue=r["cue"],mode=r["mode"],status=status,
                      source=it["variants"]["A"]["source"]))
audit=pd.DataFrame(audit)
audit.to_csv(OUT/"cue_source_audit.csv",index=False)
cert=wb[wb.channel.eq("restored") & wb.dimension.eq("certainty") & wb["sample"].eq("enriched")]
results["H3"]={"certainty_source_failure":rate(cert,"failure"),
    "conflict_source_failure":rate(cert[cert.cue_conflict],"failure"),
    "aligned_source_failure":rate(cert[~cert.cue_conflict],"failure")}
results["H3"]["all_restorations_audit"]=audit.status.value_counts().to_dict()
results["H3"]["additional_definite_conflicts"]=audit[audit.status.eq("definite_conflict") & ~audit.dim.eq("certainty")].to_dict("records")
cc=cert[cert.cue_conflict].copy();cc["honours_actual_chip"]=cc.critical.eq("hedged/uncertain")
results["H3"]["conflict_honours_actual_chip"]=rate(cc,"honours_actual_chip")
for sample,z in wb[wb.channel.eq("restored")].groupby("sample"):
    eligible=z[z.match.notna()].copy()
    eligible["failure_after_exclusion"]=eligible.failure.mask(eligible.cue_conflict)
    # Difference of ratios on the SAME resampled message clusters.
    a=eligible.assign(arm="recorded")
    b=eligible[~eligible.cue_conflict].assign(arm="aligned_only")
    results[f"H3/{sample}"]={"recorded":rate(a,"failure"),"aligned_only":rate(b,"failure"),
       "recorded_minus_aligned":difference(pd.concat([a,b]),"failure","arm","recorded","aligned_only")}
# The report's general-label violation endpoint is distinct from focal critical
# match; reproduce its eligibility before measuring the impact on its headline.
long=pd.read_csv(io.BytesIO(read("analysis/wb/long_dims.csv.gz")),compression="gzip")
long["cluster_id"]=long.msg
long["cue_conflict"]=long.msg.map(lambda f:wi[f]["focal_dim"]=="certainty"
    and wi[f]["variants"]["A"]["critical_value"]=="plain assertion"
    and (wi[f].get("restoration") or {}).get("cue")=="[MAYBE]")
for sample,z in long[long.channel.eq("restored") & long.focal & long.expressible].groupby("sample"):
    a=z.assign(arm="recorded")
    b=z[~z.cue_conflict].assign(arm="aligned_only")
    results[f"H3/general/{sample}"]={"recorded":rate(a,"violation"),"aligned_only":rate(b,"violation"),
       "recorded_minus_aligned":difference(pd.concat([a,b]),"violation","arm","recorded","aligned_only")}
cz=long[long.channel.eq("restored")&long.focal&long.expressible&long.dim.eq("certainty")&long["sample"].eq("enriched")]
results["H3"]["general_certainty"]={"recorded":rate(cz,"violation"),
    "aligned_only":rate(cz[~cz.cue_conflict],"violation")}
ex=cc.sort_values(["family_id","model"]).iloc[0]
example(ex,"wb1","H3 first cue-conflict restored output")
results["H3"]["conflict_sources"]=[dict(family_id=f,source=wi[f]["variants"]["A"]["source"],
    source_value=wi[f]["variants"]["A"]["critical_value"],restoration=wi[f]["restoration"])
    for f in sorted(cc.family_id.unique())]

# H4: source-defined syntax, restricted to the 74 frozen explicit-request families.
elig=pd.read_csv(io.BytesIO(read("analysis/r2c/h1_eligibility.csv")))
print("eligibility columns",elig.columns.tolist())
eligible_f=set(elig[elig.eligible.astype(str).str.lower().eq("true")].family_id)
forms={}
for f in eligible_f:
    v=next(v for v in items[f]["variants"].values() if v["critical_value"]=="plain")
    s=v["source"].lower()
    forms[f]="modal" if s.startswith(("can you ","will you ")) else "imperative"
z=c[c.family_id.isin(eligible_f)&c.channel.eq("full")&c.prompt_id.eq("P0")&c.variant_value.eq("plain")].copy()
z["form"]=z.family_id.map(forms)
z["added"]=z.politeness_added.astype(float)
results["H4"]={"family_counts":pd.Series(forms).value_counts().to_dict(),
    "pooled":{f:rate(t,"added") for f,t in z.groupby("form")},
    "pooled_delta":difference(z,"added","form","imperative","modal"),
    "by_model":{m:dict(arms={f:rate(t,"added") for f,t in x.groupby("form")},
          delta=difference(x,"added","form","imperative","modal")) for m,x in z.groupby("model")}}
z["construction"]=z.family_id.map(lambda f:items[f]["construction"])
seeded=z[z.construction.eq("seeded")]
results["H4"]["seeded_only"]={"arms":{f:rate(t,"added") for f,t in seeded.groupby("form")},
    "delta":difference(seeded,"added","form","imperative","modal")}
ex=z[z.model.eq("gemma3-4b")&z.form.eq("imperative")&z.added.eq(1)].sort_values(["family_id"]).iloc[0]
example(ex,"r2c1","H4 first Gemma imperative plain-to-polite failure")
z[["family_id","model","variant","cluster_id","form","added","input_text","text","output_id"]].to_csv(OUT/"request_forms.csv",index=False)

read("annotation/judge_validation_main1.json")
read("analysis/oracle/human_gate.log")
(OUT/"hyp_checks.json").write_text(json.dumps(dict(seed=SEED,n_boot=B,inputs=hashes,results=results),indent=2)+"\n")
(OUT/"hyp_examples.json").write_text(json.dumps(examples,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(results,indent=2))

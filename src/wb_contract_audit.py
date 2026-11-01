"""Offline cycle-2 Action 1: audit the frozen W-B restoration contract.

No generation, judging, relabeling, or historical request reconstruction. Uses
stored extraction labels; its verdicts remain machine-assessed. Run from root:
  .venv/bin/python src/wb_contract_audit.py
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

from labels import CHIP_TO_GENERAL, POLITE_VALUES, critical_match
from wb_items import focal_cue, words_with_cue
from wb_report import honours, NONCOMMIT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/wb"
SEED, B = 20261101, 10000
# Exhaustive review of the eight word inputs, at the existing coarse endpoint.
# These decisions concern the visible words, never the hidden commitments tag.
WORDS = {
    "wb-aactext-train-01531": (None, "unknown_word", "how cheap permits a question or exclamation; the statement source is not fixed by this input"),
    "wb-aactext-test-00375": (None, "unknown_word", "feel sorry can express sympathy; no unambiguous apology or no-politeness instruction, and hidden [PLEASE] is not visible"),
    "wb-aactext-train-00651": (POLITE_VALUES, "aligned", "thanks is visible; already retained in POS-cap4"),
    "wb-aactext-train-03131": (POLITE_VALUES, "aligned", "thank is visible; already retained in POS-cap4"),
    "wb-aactext-train-03837": (POLITE_VALUES, "aligned", "thanks is visible; already retained in POS-cap4"),
    "wb-aactext-train-05007": (POLITE_VALUES, "aligned", "sorry messages short explicitly apologizes for the messages; coarse polite-marker endpoint only"),
    "wb-aactext-test-00467": (POLITE_VALUES, "aligned", "would you is visible in a request construction (CB-2)"),
    "wb-aactext-dev-00292": (POLITE_VALUES, "aligned", "could you is visible in a request construction (CB-2)"),
}


def records(path):
    return [json.loads(line) for line in (ROOT / path).open() if line.strip()]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def clean(v):
    if isinstance(v, np.generic):
        return v.item()
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return v


def boot(frame, col, key):
    # Resample all message clusters in this population, keeping unknown labels
    # as zero denominators, not negative outcomes. Local RNG makes table order
    # immaterial and keeps repeated invocations byte-identical.
    g = frame.groupby("family_id", sort=True)[col].agg(["sum", "count"])
    if g.empty or g["count"].sum() == 0:
        return dict(k=0, n=0, total=len(frame), missing=len(frame), messages=len(g), estimate=None, ci95=None)
    a, n = g["sum"].to_numpy(float), g["count"].to_numpy(float)
    salt = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
    rng = np.random.default_rng([SEED, salt])
    idx = rng.integers(0, len(g), size=(B, len(g)))
    den = n[idx].sum(1)
    val = np.divide(a[idx].sum(1), den, out=np.full(B, np.nan), where=den > 0)
    return dict(k=int(a.sum()), n=int(n.sum()), total=len(frame), missing=int(len(frame)-n.sum()),
                messages=len(g), observed_messages=int((n > 0).sum()),
                estimate=float(a.sum()/n.sum()), ci95=np.nanpercentile(val, [2.5, 97.5]).tolist())


def main():
    start = pd.read_csv(ROOT / "ideas/cycles/c2/cue_source_audit.csv").set_index("family_id")
    items = {r["family_id"]: r for r in records("data/items/wb.jsonl")}
    panel = {r["id"]: r for r in records("annotation/wb_admissibility/panel.jsonl")}
    sample = {r["id"]: r for r in records("data/specs/wb_sample.jsonl")}
    sc = pd.read_parquet(ROOT / "runs/wb1/scored.parquet")
    raw = pd.DataFrame(records("runs/wb1/outputs.jsonl"))
    restored = sc[sc.channel.eq("restored")].copy()
    assert len(items) == 160 and len(restored) == 556
    assert restored.groupby("family_id").size().eq(4).all()
    assert not restored.duplicated(["family_id", "model"]).any()
    assert restored.valid.all() and restored.prompt_id.eq("P0").all()
    keys = ["output_id", "family_id", "model", "channel"]
    joined = restored.merge(raw[keys+["input_text", "text", "request_key"]], on=keys,
                            suffixes=("", "_raw"), validate="one_to_one")
    for col in ("input_text", "text", "request_key"):
        assert joined[col].equals(joined[col+"_raw"]), col
    requests = {r['request_key']:r for r in records('runs/requests/wb1.jsonl')}
    generations = {r['request_key']:r for r in records('runs/wb1/generations.jsonl')}
    legend = (ROOT/'prompts/chip_legend.txt').read_text().strip()
    for r in restored.to_dict('records'):
        req = requests[r['request_key']]; gen = generations[r['request_key']]
        assert req['input_text'] == gen['input_text'] == r['input_text']
        assert req['model'] == gen['model'] == r['model']
        assert req['prompt_sha'] == gen['prompt_sha']
        assert req['prompt'].endswith(r['input_text']) and legend in req['prompt']
        assert gen['suggestions'][r['suggestion_idx']] == r['text']
        assert dict(family_id=r['family_id'],variant=r['variant'],channel=r['channel']) in req['targets']
    # Verify source-order word rendering from the stored carrier ids only.
    # Loading this CPU tokenizer does not call any language model service.
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    inventory, allowed = [], {}
    for fid, group in restored.groupby("family_id", sort=True):
        it = items[fid]; v = it["variants"]["A"]; d = it["focal_dim"]
        p = panel[it["source_id"]]["dims"][d]; r = sample[it["source_id"]]
        chan = it["custom_channels"]["A"]["restored"]
        restoration = it["restoration"]; prior = start.loc[fid]
        assert group.input_text.eq(chan["input"]).all()
        assert v["source"] == r["text"] == prior["source"]
        assert prior["dim"] == d and prior["actual_cue"] == restoration["cue"]
        assert prior["sample"] == it["sample"] and prior["mode"] == restoration["mode"]
        assert prior["source_value"] == v["critical_value"]
        src = p["source_value"]
        expressible = src is not None and src not in NONCOMMIT
        item_src = v["general_spec"][d]
        assert src is None or src == item_src, (fid, src)
        tokens = re.findall(r"\[[^\]]+\]", chan["input"])
        if restoration["mode"] == "chip":
            cue = restoration["cue"]
            assert tokens == [cue] and chan["commitments"] == [cue]
            assert chan["input"] == "Keywords: " + cue + " " + " ".join(r["pos_cap4"])
            dim, vals = CHIP_TO_GENERAL[cue]
            assert dim == d
            # The starting inventory compares to the stored item reference,
            # including detector fallbacks. The aligned sensitivity additionally
            # requires the panel's source consensus, as in original table B.
            mapping_status = ("unknown_reference" if item_src in NONCOMMIT else
                              "aligned" if item_src in vals else "definite_conflict")
            status = "unknown_source_consensus" if src is None else mapping_status
            relation = "unknown_reference" if not expressible else "exact_or_compatible"
            if status == "definite_conflict":
                relation = "disjoint"
            elif d == "certainty" and src == "strongly certain/emphatic":
                relation = "coarsened_SURE_plain_or_emphatic"
            reason = ("source panel disagrees; item reference is a detector fallback, not a consensus" if src is None else
                      "source reference is unclear/unexpressible; actual chip remains auditable" if not expressible else
                      "visible chip contradicts the stored source category" if status == "definite_conflict" else
                      "visible chip is compatible with stored source; [SURE] accepts plain or emphatic" if cue == "[SURE]" else
                      "visible chip maps to the stored focal source category")
            assert mapping_status == {"unexpressible_reference":"unknown_reference"}.get(prior["status"],prior["status"])
        else:
            assert not tokens
            vals, status, reason = WORDS[fid]
            mapping_status = status
            relation = "word_marker_compatible" if vals else "underdetermined"
            c = focal_cue(r,d)
            assert c and words_with_cue(r,c,nlp) == chan["input"].removeprefix("Keywords: ")
        allowed[fid] = sorted(vals) if vals is not None else None
        added = chan["input"] != it["custom_channels"]["A"]["pos_cap4"]["input"]
        inventory.append(dict(family_id=fid, sample=it["sample"], stratum=it["stratum"], dim=d,
            source=v["source"], source_panel_value=src, source_item_value=item_src, source_critical_value=v["critical_value"],
            source_value_origin=it["value_source"][d], source_expressible=expressible,
            source_coder1=p["src_1"], source_coder2=p["src_2"],
            mode=restoration["mode"], actual_cue=restoration["cue"], input_text=chan["input"],
            metadata_commitments=json.dumps(chan["commitments"]),
            visible_accepted_general_values=json.dumps(allowed[fid]),
            input_predicate_identified=vals is not None, status=status, stored_mapping_status=mapping_status, relation=relation,
            aligned_expressible=status=="aligned" and expressible,
            source_predicate_fully_supplied=status=="aligned" and expressible and relation!="coarsened_SURE_plain_or_emphatic",
            changed_visible_input=added, prior_status=prior["status"], reason=reason))
    inv = pd.DataFrame(inventory)
    assert len(inv) == 139 and set(inv.family_id) == set(start.index)
    assert Counter(inv["mode"]) == {"chip":131,"word":8}
    assert Counter(inv.status) == {"aligned":116,"definite_conflict":7,"unknown_reference":9,"unknown_source_consensus":5,"unknown_word":2}
    inv.to_csv(OUT / "contract_audit_inventory.csv", index=False)
    meta = inv.set_index("family_id").to_dict("index")
    diff = []
    for r in restored.sort_values(["family_id", "model"]).to_dict("records"):
        m = meta[r["family_id"]]; d = m["dim"]; vals = allowed[r["family_id"]]
        gen, crit = clean(r[d]), clean(r["critical"])
        # Politeness critical options collapse the polite subtypes.
        cvals = ({"polite" if x in POLITE_VALUES else "plain" if x=="none" else x for x in vals}
                 if vals is not None and d=="politeness" else set(vals) if vals is not None else None)
        source_general_match = honours(d, m["source_panel_value"],gen)
        old_general_eligible = bool(m["source_expressible"])
        actual_general_match = None if vals is None or gen is None else gen in vals
        actual_critical_match = None if cvals is None or crit is None else crit in cvals
        old_violation = None if source_general_match is None or not old_general_eligible else not source_general_match
        new_violation = None if actual_general_match is None else not actual_general_match
        diff.append(dict(family_id=r["family_id"], model=r["model"], output_id=r["output_id"],
            text_id=r["text_id"], request_key=r["request_key"], sample=m["sample"], dim=d,
            channel="restored", input_text=r["input_text"], text=r["text"], mode=m["mode"],
            audit_status=m["status"], relation=m["relation"], source_panel_value=m["source_panel_value"],
            source_critical_value=m["source_critical_value"],
            accepted_general_values=m["visible_accepted_general_values"],
            general_label=gen, critical_J1=clean(r["critical_J1"]), critical_J2=clean(r["critical_J2"]),
            critical_label=crit, critical_source=clean(r["critical_source"]),
            old_source_critical_match=clean(r["critical_match"]), old_source_general_match=source_general_match,
            old_general_eligible=old_general_eligible, old_general_violation=old_violation,
            stored_cue_in_input=bool(r["cue_in_input"]), stored_violation=clean(r["violation"]),
            actual_input_eligible=vals is not None, actual_input_general_match=actual_general_match,
            actual_input_critical_match=actual_critical_match, actual_input_general_violation=new_violation,
            aligned_expressible_eligible=m["aligned_expressible"],
            source_violation_attribution_allowed=m["source_predicate_fully_supplied"],
            attribution_withheld_reason="" if m["source_predicate_fully_supplied"] else m["reason"],
            general_verdict_change=("ineligible_to_known" if old_violation is None and new_violation is not None else
                                    "known_to_unknown" if old_violation is not None and new_violation is None else
                                    "changed" if old_violation != new_violation else "same")))
    df = pd.DataFrame(diff)
    for samp, expected in [('random',(216,232,211,223)),('enriched',(236,318,221,276))]:
        g=df[df['sample'].eq(samp)]
        c=g.old_source_critical_match.dropna()
        h=g.loc[g.old_general_eligible,'old_source_general_match'].dropna()
        assert (int(c.sum()),len(c),int(h.sum()),len(h))==expected
    df.to_csv(OUT / "contract_audit_diff.csv", index=False)
    # Tables at both label granularities, by separate sample, dimension, model.
    estimates = []
    for sample_name, s in df.groupby("sample",sort=True):
        for subset, pop in [("all_restored",s),("aligned_expressible",s[s.aligned_expressible_eligible]),
                            ("chip_only",s[s['mode'].eq('chip')]),
                            ("word_only",s[s['mode'].eq('word')]),
                            ("definite_conflict",s[s.audit_status.eq('definite_conflict')])]:
            for dimension in ["ALL", *sorted(pop.dim.unique())]:
                a = pop if dimension=="ALL" else pop[pop.dim.eq(dimension)]
                for model in ["pooled",*sorted(a.model.unique())]:
                    g = a if model=="pooled" else a[a.model.eq(model)]
                    for metric in ["old_source_critical_match", "old_source_general_match", "actual_input_critical_match", "actual_input_general_match"]:
                        use = g[g.old_general_eligible] if metric=="old_source_general_match" else g
                        if metric.startswith("actual_input"):
                            use = use[use.actual_input_eligible]
                        key = f"{sample_name}/{subset}/{dimension}/{model}/{metric}"
                        estimates.append(dict(sample=sample_name,subset=subset,dim=dimension,model=model,
                                              metric=metric,**boot(use,metric,key)))
    # Retain paired channel gains as changed-population source-fidelity sensitivities.
    wide = sc.pivot(index=["family_id","model"],columns="channel",values="critical_match")
    for sample_name,s in df.groupby("sample",sort=True):
        for subset,g in [("all_restored",s),("aligned_expressible",s[s.aligned_expressible_eligible])]:
            a = g[["family_id","model"]].merge(wide.reset_index(),on=["family_id","model"],validate="one_to_one")
            for metric,left,right in [("paired_restored_minus_pos_cap4","restored","pos_cap4"),
                                      ("paired_full_minus_restored","full","restored")]:
                a[metric] = [None if pd.isna(x) or pd.isna(y) else float(x)-float(y) for x,y in zip(a[left],a[right])]
                estimates.append(dict(sample=sample_name,subset=subset,dim="ALL",model="pooled",metric=metric,
                                      **boot(a,metric,f"{sample_name}/{subset}/{metric}")))
    pd.DataFrame([{**e,"ci_low":e['ci95'][0] if e['ci95'] else None,"ci_high":e['ci95'][1] if e['ci95'] else None}
                  for e in estimates]).drop(columns="ci95").to_csv(OUT / "contract_audit_estimates.csv",index=False)
    # Reproduce the denominator correction without calling wb_report.main().
    polarity=[]
    for samp in ("random","enriched"):
        a=[]
        for r in sc[sc.channel.eq("pos_cap4")].to_dict("records"):
            it=items[r['family_id']]; p=panel[it['source_id']]['dims']['polarity']
            if it['sample']==samp and p['status']=='confirmed_ambiguous' and p['source_value'] is not None:
                a.append(dict(family_id=r['family_id'],src=p['source_value'],out=clean(r['polarity']),
                              honour=honours('polarity',p['source_value'],clean(r['polarity']))))
        a=pd.DataFrame(a)
        for label,mask in [('non_default',a.src.ne('affirmative')),('strict_negated',a.src.eq('negated'))]:
            g=a[mask]; polarity.append(dict(sample=samp,stratum=label,**boot(g,'honour',f"polarity/{samp}/{label}")))
    assert [(p['k'],p['n']) for p in polarity]==[(0,36),(0,32),(2,84),(2,48)]
    h=json.loads((ROOT/'annotation/judge_validation_main1.json').read_text())['human']
    gate={d:{k:t['sampled_test/final'][k] for k in ['n','kappa','kappa_ci']} for d,t in h['judge'].items()}
    wb=json.loads((ROOT/'annotation/wb_audit.json').read_text())
    audit_cells=[e for it in wb['items'] for e in it['dims'].values()]
    filled=sum(v is not None and v!='' for e in audit_cells for k,v in e.items() if k.startswith('HUMAN_'))
    # Freeze a real stored counterexample by the pre-existing H3 selection rule.
    cf=df[df.dim.eq('certainty') & df.audit_status.eq('definite_conflict')].sort_values(['family_id','model'])
    assert len(cf)==20 and cf.actual_input_critical_match.all() and ~cf.old_source_critical_match.any()
    ex=cf.iloc[0].to_dict()
    prior=json.loads((ROOT/'ideas/cycles/c2/hyp_checks.json').read_text())['inputs']
    preserved={name:sha(name)==prior[name] for name in [
        'data/items/wb.jsonl','runs/wb1/scored.parquet','runs/wb1/outputs.jsonl',
        'analysis/wb/long_dims.csv.gz','annotation/judge_validation_main1.json','analysis/oracle/human_gate.log']}
    assert all(preserved.values()), 'Underlying evidence changed since cycle-2 mining'
    result=dict(schema_version=1,action='ideas/cycles/c2/decision.md Action 1',
                generator_calls=0,judge_calls=0,bootstrap=dict(reps=B,seed=SEED,unit='message',
                method='pointwise percentile; endpoint-keyed RNG; samples separate; fixed model roster'),
                inventory=dict(messages=len(inv),outputs=len(df),modes=inv['mode'].value_counts().to_dict(),
                statuses=inv.status.value_counts().to_dict(),
                unchanged_word_inputs=inv[inv['mode'].eq('word') & ~inv.changed_visible_input].family_id.tolist()),
                verdict_changes=df.general_verdict_change.value_counts().to_dict(),
                estimates=estimates,polarity_denominators=polarity,
                human=dict(design=h['design'],gate=gate,
                broader_sampled_final={d:t['sampled/final']['kappa'] for d,t in h['judge'].items()},
                violation=h['verdict']['violation']['primary'],consensus_rule=h['consensus_rule'],
                wb_audit_items=len(wb['items']),wb_human_fields_filled=filled),
                example=dict(selection='first certainty-conflict restored output by family_id then model (c2 H3)',
                phenomenon='source mismatch while honouring visible [MAYBE]',k=20,n=20,message_clusters=5,
                row={k:clean(v) for k,v in ex.items()}),
                prior_c2_hash_verification=preserved,
                input_hashes={p:sha(p) for p in [
                    'ideas/cycles/c2/cue_source_audit.csv','data/items/wb.jsonl','data/specs/wb_sample.jsonl',
                    'annotation/wb_admissibility/panel.jsonl','annotation/wb_audit.json',
                    'annotation/judge_validation_main1.json','runs/wb1/scored.parquet','runs/wb1/outputs.jsonl',
                    'src/wb_items.py','src/labels.py','src/wb_report.py','src/wb_contract_audit.py',
                    'prompts/chip_legend.txt','runs/requests/wb1.jsonl',
                    'runs/wb1/generations.jsonl','runs/wb1/judgments.jsonl','runs/wb1/config.json',
                    'orchestration/SPEC.md']})
    (OUT/'contract_audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['inventory','verdict_changes']},indent=2))
    print('Wrote 139 inventory rows, 556 verdict diffs, estimates and human-status evidence; no model calls.')


if __name__=='__main__':
    main()

"""Read provenance and source specifications only; never read scored labels."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from analyze import load_items, markdown_table
from build_requests import input_text
import pandas as pd
O=ROOT/'analysis/r2c'
if (O/'FREEZE.md').exists():
 raise SystemExit('FREEZE.md already exists; refusing to rewrite the prospective analysis record.')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def utc(p): return datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()
items=load_items(str(ROOT/'data/items/r2_c[12].jsonl'))
paths=['data/items/r2_c1.jsonl','data/items/r2_c2.jsonl','orchestration/PREREG_R2.md','runs/requests/r2c.jsonl','runs/r2c1/config.json']
meta=[dict(path=p,sha256=sha(ROOT/p),mtime_utc=utc(ROOT/p)) for p in paths]
config=json.loads((ROOT/'runs/r2c1/config.json').read_text())
assert sha(ROOT/'runs/requests/r2c.jsonl')==config['requests_sha256']
assert meta[0]['sha256'].startswith('3ca2e1a6') and meta[1]['sha256'].startswith('457eea54')
ts={}; n=0; early=[]
for l in (ROOT/'runs/r2c1/generations.jsonl').open():
 r=json.loads(l); t=r['created_utc']; m=r['model']; n+=1
 if t < max(meta[0]['mtime_utc'],meta[1]['mtime_utc']): early.append({k:r.get(k) for k in ['request_key','model','prompt_id','family_id','input_text','created_utc','cached','targets']})
 if m not in ts: ts[m]=[t,t,0]
 ts[m]=[min(ts[m][0],t),max(ts[m][1],t),ts[m][2]+1]
request_targets=0
for l in (ROOT/'runs/requests/r2c.jsonl').open():
 r=json.loads(l)
 for t in r['targets']:
  assert r['input_text']==input_text(items[t['family_id']],t['variant'],t['channel'])
  request_targets+=1
first=min(v[0] for v in ts.values())
(O/'pre_freeze_cache.json').write_text(json.dumps(early,indent=2)+'\n')
plan='''The three W-C PRIMARY estimands remain exactly PREREG_R2: P1 speech-act chip1 minus noncrit critical match, excluding primary_exclude (r2act-078/079, D-018) and refusal/acceptance; P2 full-input politeness plain→polite addition rate minus polite→plain removal rate; P3 bare polarity affirmative share minus 0.5. All primary outputs use P0 (contrast IDs P1/P2 are not prompt IDs). Fixed 240 approved families, four fixed models, no resizing or extension. Other estimates are descriptive, including per-model and construction breakdowns and discovery-claim replication. Models are fixed; no inference to a population of models.

Resample the recorded cluster_id, retaining all variants/models/channels/suggestions of a seed/construction jointly: 10,000 multinomial cluster resamples, seed 20261031; row-weighted estimates; paired within family/variant/model for P1 and within family/model for P2, with subtraction after joint resampling. P3 deduplicates shared A/B requests and conditions on affirmative/negated readings, with all-output affirmative share sensitivity. Report missingness, families, observed clusters, and Kish effective clusters from observed cluster denominators. Percentile 95% CIs. Holm step-down alpha=.05 across exactly the three pooled primary tests, with expected positive direction. No Holm for descriptive strata.

PREREG specifies bootstrap and expected direction, but not a test-statistic/p-value algorithm, denominator details, or CI type. Operationalization declared here before reading scored outcomes: one-sided null-centered cluster bootstrap p=(1+#(bootstrap_estimate−estimate >= estimate))/(10001), capped at 1; Holm monotone adjusted p; also report two-sided centered-bootstrap p sensitivity. At boundary zero variance, report empirical degeneracy; no zero population-risk inference. Unknown required labels are excluded, never replaced by a favorable label; invalid completion is critical-match failure. P2 directional rates use known critical plain/polite extraction (invalid/unclear are not directional switches), complete paired targets for primary difference, arm-specific rates and missingness also reported. No claim that these implementation choices were specified verbatim in the preregistration.

H1 secondary replication eligibility: politeness pairs only; both source specs must explicitly encode request/command ([ASK]) and an expressible main actor (same explicit [YOU]/[I]/[WE]/[THEY] in both all_chips). Exactly one variant plain and one polite. Freeze family list now, source specs only; do not filter on outcomes. Compare plain−polite request retention on P0 chipall and full, Llama focal, others descriptive. Promotion criterion: difference <= −.20 and upper 95% CI <0; chip-only result is encoding-specific.

H2 secondary construction coding: source-blind to generated outcomes, use bare predicate plus source syntax to label question targets action/event, state/evaluation, or unresolved; preserve all exclusions. No independent second coder is available in this analysis, so the independently-audited construction headline remains unearned; results are descriptive regardless of thresholds. No new generation, judging, or GPU servers.

Secondary: full five-channel P0 ladder by dimension, bare/noncrit P2 versus S3 coverage@3, stance additions, nominal action costs default/nondefault using analyze.py semantics, r2pol-077 exclusion sensitivity and C1–C11/C17 replication scope. C5 requires W-B/S1, C9/C10 encoding manipulations absent here; mark untestable rather than manufacture replication. Deterministic examples use seeded SHA256-ranked eligible stored occurrences with explicit outcome-conditioned rules and stratum rates, not manual selection. Publication figures use make_figs.py with r2c1 and the same cluster/seed/bootstrap/exclusion rules. Flat headline.json exports proportions/differences in unit scale with CI/n/n_clusters; primary.json preserves full inference details.'''
text='# W-C freeze and analysis plan\n\nRecorded UTC: '+datetime.now(timezone.utc).isoformat()+'\n\nThis is a retrospective provenance audit plus a prospective analysis implementation freeze, not a claim that this file existed before generation. No scored outcomes have been loaded by this analyst before writing it.\n\n'+markdown_table(pd.DataFrame(meta))+'\n## Original generation timestamps (not final collection time)\n\n'+markdown_table(pd.DataFrame([dict(model=m,first_created_utc=v[0],last_created_utc=v[1],requests=v[2]) for m,v in sorted(ts.items())]))+f'\n{n:,} generation records; {request_targets:,} request targets were reconstructed against the current source specs with exact input equality. {len(early)} cached generation records predate the final item mtimes; see pre_freeze_cache.json. Thus a blanket freeze-before-generation claim is NOT established. Most requests follow the frozen request file, but earlier cache reuse must remain disclosed. Registered primary estimates keep the fixed sample; sensitivity excludes any family touched by earlier cached requests. Request SHA256 matches config. Item hash prefixes match the independently recorded D-022 freeze. The config created_utc ({config["created_utc"]}) is a final cached collection snapshot and does not date the first generation.\n\nThis establishes recorded ordering for fresh requests but NOT for the reused cache entries (timestamps are not an external trusted timestamp). Primary results are registered contrasts with a cache-provenance qualification, not an unqualified fully fresh confirmation. PREREG title uses November 1 although its actual mtime is October 31 local; ordering uses UTC metadata, not the title. Config lacks item/codebook hashes required by PREREG; source reconstruction and D-022 hashes supply supporting evidence, with that manifest deficiency disclosed.\n\n## Analysis plan unchanged from PREREG\n\n'+plan+'\n'
(O/'FREEZE.md').write_text(text)
# Eligibility written only from item specs; no scored-table read.
rows=[]
for f,i in sorted(items.items()):
 if i['dimension']!='politeness': continue
 vs=i['variants']; regs={v['critical_value']:k for k,v in vs.items()}
 role=[set(v.get('all_chips',[])) & {'[YOU]','[I]','[WE]','[THEY]'} for v in vs.values()]
 ask=all('[ASK]' in v['all_chips'] for v in vs.values())
 eligible=ask and bool(role[0]) and role[0]==role[1] and set(regs)=={'plain','polite'}
 rows.append(dict(family_id=f,eligible=eligible,reason='explicit paired request + same expressible actor' if eligible else 'not two explicit requests' if not ask else 'main actor not explicitly expressible',plain_variant=regs['plain'],polite_variant=regs['polite'],cluster_id=i['cluster_id'],construction=i['construction']))
pd.DataFrame(rows).to_csv(O/'h1_eligibility.csv',index=False)
(O/'freeze_metadata.json').write_text(json.dumps(dict(files=meta,generation_timestamps=ts,pre_freeze_cache_count=len(early),request_targets_reconstructed=request_targets,eligibility_sha256=sha(O/'h1_eligibility.csv')),indent=2)+'\n')
print(text[:500]); print('H1 eligibility:',pd.DataFrame(rows).eligible.value_counts().to_dict())

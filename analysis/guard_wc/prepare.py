"""Action 6 prospective freeze and deterministic monitor replay. No network calls."""
from pathlib import Path
import sys, json, hashlib, shutil, datetime, math
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import runio
import interventions as I
import pandas as pd

OUT = ROOT / 'analysis/guard_wc'
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT / 'FREEZE.md').exists():
        raise SystemExit('Freeze already exists; do not overwrite it.')
    paths = ['orchestration/PREREG_R2.md', 'ideas/cycles/c2/decision.md',
             'analysis/interventions/report.md', 'runs/r2c1/generations.jsonl',
             'runs/r2c1/scored.parquet', 'runs/r2c1/outputs.jsonl',
             'runs/r2c1/judgments.jsonl', 'runs/r2c1/arbiter.jsonl',
             'runs/r2c1/config.json', 'data/items/r2_c1.jsonl', 'data/items/r2_c2.jsonl',
             'annotation/CODEBOOK.md', 'annotation/CB_rules.md',
             'annotation/judge_validation_main1.json', 'analysis/oracle/human_gate.log',
             'prompts/P0.txt', 'prompts/chip_legend.txt', 'models/SHA256SUMS']
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'src').glob('*.py'))]
    paths += ['src/run_interventions.sh', 'src/run_sequential.sh', 'src/serve_local.sh',
              'src/stop_local.sh', 'src/README.md', 'analysis/guard_wc/prepare.py']
    frozen = OUT / 'frozen'
    for p in paths:
        dest = frozen / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / p, dest)
    hashes = {p: sha(frozen/p) for p in paths}
    (OUT/'input_hashes.json').write_text(json.dumps(hashes, indent=2)+'\n')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (OUT/'FREEZE.md').write_text(f'''# W-C guard transfer: prospective Action 6 freeze

Written {stamp}, before any Action 6 retry or judge call. The read-only feasibility
preview used the stored first passes only. D-040 and the user's November 1 instruction
authorize an early launch; the memo's November 11–15 window is superseded for timing.
Core W-B/W-C/W-D evidence and the partial repair endpoint are reviewable. CALE-AI only;
do not change paper/ or the SE4All evidence. No policy tuning, additional arms or items.

## Inventory and policy

W-C r2c1 P0 speech-act families, excluding D-018 r2act-078/079: **78 families × 2 targets
× 4 fixed models × chip1/chipall/full = 1,872 target occurrences** before missing-label
exclusions. All occurrences remain in the planned denominator. Deduplicate generation
by original request_key; clip each request's targets to this inventory, even when its
representative family belongs to another stratum. Re-render and assert the original
request key. Reuse the exact stored first sentence and its raw conversation response.

**UNCHANGED G1** from frozen src/interventions.py: supplied() and check() (layer0 plus
number/time add-on), unsupplied-politeness rule, feedback(), guard_one(), temperature 0,
96 output tokens, seed 1000 for local models (API has no seed), tag I1-guard-v1.
Up to two monitor-triggered regeneration calls. Return the first unflagged candidate,
otherwise fewest flags, earliest on ties (original wins a tie). Empty originals remain
missing/failed without generation. **G1s** uses the unchanged strip_please() rule only
when initial politeness:added and please/pls/plz are present; zero generation calls.
No I2 run. A wrapper may restrict inventory, instrument costs and enforce caps; it
must not alter these functions, prompts, monitor thresholds, or return logic.

## Endpoint and missingness

Primary = **joint supplied-predicate pass**, src/analyze.normalize_table's
constraint_preserving: valid completion, focal match, and no contradicted supplied
general predicate. Known failures dominate missingness; otherwise a needed missing
label yields unknown. Source specifications, not the monitor's source interpretation,
define evaluation. This is a partial contract, not fluency or full semantics. Secondary
strict pass additionally requires no added politeness; this is the previous guard's
repair/changed-correct endpoint. Report both, without switching after outcomes.

Reuse cached J1/J2 evaluation and existing r2c1 arbiter decisions by their production
unit (normalized text, critical question/options, with input where needed). Never
substitute J1. **New critical J1/J2 disagreements are recorded as unresolved**, with
zero new arbiter calls. General labels retain the frozen production agreement/L0
tie-break rule, disclosed with counts and agreement-only sensitivity. No new labels
may replace a frozen baseline label. First-pass baseline retains the completed W-C
arbitration and its chronology qualifications. Preserve missing/error outcomes and
report observed/planned denominators, paired known units and worst/best missingness
bounds. New missing general labels may not silently count as passes.

Compare P0/G1/G1s on identical target occurrences, with paired gains, repair rates,
changed-correct, pass→fail, residual failures and flags, per-model and per-channel.
Primary uncertainty: **10,000 whole-family percentile bootstrap resamples**, seed
20261101, retaining every model/target/channel/arm of a sampled family jointly.
Companion recorded seed/construction-cluster bootstrap (55 clusters) handles shared
W-C templates/seeds; report it alongside the required 78-family bootstrap. Fixed
roster, row-weighted means, pointwise 95% intervals; no population/model inference.

## Audit and examples (selection frozen before retries)

If audit capacity becomes available, select 20 distinct G1 changed texts and 20
unchanged baseline-strict-correct controls by ascending SHA256 of normalized text,
breaking ties by model, family, variant, channel; first collapse exact normalized
texts, retaining all memberships and inclusion counts. Repairs cannot be selected
by judged success. Freeze the resulting sample before any human labels; provide
sentence-only blind completeness and separately paired supplied-constraint review.
No new human time is allocated and no usable-repair claim without new independent
quality evidence. Do not reuse main1 H7 as repair validation.

Examples, if shown: first SHA256(base_request_key, family, variant, channel) in each
predeclared category: strict fail→pass, residual strict failure, correct-text-changed,
pass→fail, G1s fail→pass (one per category, absent categories reported). Quote actual
stored outputs verbatim, output IDs, selection key, and the category's full rate.
These are selected illustrations, never typicality claims.

## Fixed budget, admission, and kill rules

**Across all models: ≤2,000 actual retry-generation HTTP calls; ≤400 actual judge
batch HTTP calls including network/invalid-batch retries; ≤4 h wall clock from the
recorded launch timestamp (including GPU-lock wait).** No automatic HTTP retries
for generation; a failed call consumes its allocated guard attempt and returns the
earliest best available output. Judge transport retries are disabled; any explicit
batch retry consumes the shared cap. Cache hits consume no HTTP calls. Count logical
guard attempts, cache hits, actual requests, failures and latency separately.

Compute F over flagged unique stored first-pass requests with the frozen monitor.
If **2F > 2,000, defer the entire experiment**, without selecting failures/models.
The conservative four-pass judge plan is 4 ceil(2F/25), with actual G1s/cache needs
inventoried before judging and ≤400 enforced for all traffic. If that fixed full
evaluation exceeds budget, report incompleteness; no favorable subset substitution.
Launch long work with setsid nohup. GPU mutex: flock /tmp/aacv_gpu.lock; **one local
server at a time** through src/run_interventions.sh; local 4 slots, CTX 1024, full GPU
layers where available. API concurrency 8 (≤12), judge concurrency 12 (≤12).

Transfer success requires ALL: **≥30% strict failures repaired; ≤10% initially
strict-correct texts changed; positive paired joint-pass gain with lower 95% family
bootstrap bound >0**. Also report joint failure repair and joint-correct edits.
Insufficient evidence/unfinished evaluation cannot earn success. Failure is negative
transfer evidence, never an invitation to tune. Even a pass licenses only scored
predicate transfer; usable-repair requires independent quality evidence on new repairs.

## Hashes and immutable evidence

input_hashes.json records SHA256 for every frozen source/data file, copied byte-for-byte
under frozen/. Its SHA256 is `{sha(OUT/'input_hashes.json')}`.
The machine-readable request/target inventory, monitor replay and admission decision
are written next, before retry launch, and separately hashed in inventory_hashes.json.
An additional launch_manifest.json freezes the completed wrapper/runner/analysis code
before any retries. This file is not regenerated after observing repairs.
''')
    items = runio.load_items([frozen/'data/items/r2_c1.jsonl', frozen/'data/items/r2_c2.jsonl'])
    ids = {k for k,v in items.items() if v['dimension']=='speech_act' and not v.get('primary_exclude')}
    rows = []
    for g in runio.read_jsonl(frozen/'runs/r2c1/generations.jsonl'):
        ts = [t for t in g['targets'] if t['family_id'] in ids and t['channel'] in I.CUE]
        if g['prompt_id'] == 'P0' and ts:
            g = dict(g, targets=ts)
            I.render_checked(g, items)
            rows.append(g)
    assert len(ids)==78 and sum(len(g['targets']) for g in rows)==1872
    assert len({g['request_key'] for g in rows})==len(rows)
    runio.write_jsonl(OUT/'first_passes.jsonl', rows)
    runio.write_jsonl(OUT/'items.jsonl', items.values())
    inventory, replay = [], []
    for g in rows:
        text = g['suggestions'][0] if g['suggestions'] else ''
        spec = I.supplied(g['input_text'])
        flags = I.check(text, spec) if text else ['empty']
        replay.append(dict(request_key=g['request_key'], model=g['model'], input_text=g['input_text'],
                           text=text, flags=flags, flagged=bool(flags), n_targets=len(g['targets']),
                           guard_spec={k:sorted(v) if isinstance(v,(set,frozenset)) else v for k,v in spec.items()}))
        for t in g['targets']:
            inventory.append(dict(**t, model=g['model'], request_key=g['request_key'],
                                  cluster_id=items[t['family_id']]['cluster_id'], input_text=g['input_text']))
    pd.DataFrame(inventory).to_csv(OUT/'inventory.csv', index=False)
    runio.write_jsonl(OUT/'monitor_replay.jsonl', replay)
    base = pd.read_parquet(frozen/'runs/r2c1/scored.parquet')
    base = base[base.prompt_id.eq('P0') & base.family_id.isin(ids) & base.channel.isin(I.CUE)].copy()
    assert len(base)==1872
    base.to_parquet(OUT/'baseline_scored.parquet', index=False)
    flagged = [r for r in replay if r['flagged']]
    F = len(flagged)
    admission = dict(created_utc=stamp, n_families=78, n_targets=1872, n_unique=len(rows), F=F,
                     max_guard_calls=2*F, generation_cap=2000, judge_batch_cap=400, wall_cap_s=14400,
                     formula_judge_batches=4*math.ceil(2*F/25),
                     flags_by_model=dict(Counter(r['model'] for r in flagged)),
                     admitted=2*F<=2000)
    (OUT/'admission.json').write_text(json.dumps(admission,indent=2)+'\n')
    names = ['FREEZE.md','first_passes.jsonl','items.jsonl','inventory.csv','monitor_replay.jsonl',
             'baseline_scored.parquet','admission.json','input_hashes.json']
    (OUT/'inventory_hashes.json').write_text(json.dumps({p:sha(OUT/p) for p in names},indent=2)+'\n')
    print(json.dumps(admission,indent=2))

if __name__=='__main__': main()

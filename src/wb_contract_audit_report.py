"""Render the offline Action-1 report from its machine-readable audit."""
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/wb'


def table(headers, rows):
    def cell(x):
        return str(x).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| '+' | '.join(headers)+' |', '|'+ '---|'*len(headers),
                      *['| '+' | '.join(map(cell,r))+' |' for r in rows]])


def main():
    result=json.loads((OUT/'contract_audit.json').read_text())
    inv=pd.read_csv(OUT/'contract_audit_inventory.csv')
    diff=pd.read_csv(OUT/'contract_audit_diff.csv')
    estimates=result['estimates']
    def get(sample, subset, metric, model='pooled', dim='ALL'):
        return next(r for r in estimates if (r['sample'],r['subset'],r['metric'],r['model'],r['dim'])==
                    (sample,subset,metric,model,dim))
    def fmt(r, paired=False):
        if r['estimate'] is None:
            return 'unknown (0 observed)'
        lo,hi=r['ci95']
        prefix=f"{r['k']}/{r['n']} = " if not paired else ''
        unit=' pp' if paired else '%'
        return f"{prefix}{100*r['estimate']:.2f}{unit} [{100*lo:.2f}, {100*hi:.2f}]; {r['n']}/{r['total']} observed, {r['messages']} messages"
    status=table(['Audit status','Random messages / outputs','Enriched messages / outputs'],
        [(label,*[f"{len(inv[(inv['sample']==s)&(inv.status==label)])} / {len(diff[(diff['sample']==s)&(diff.audit_status==label)])}"
                  for s in ['random','enriched']]) for label in ['aligned','definite_conflict','unknown_reference','unknown_source_consensus','unknown_word']])
    source=table(['Sample','Original focal critical source fidelity (table C)','Original general source fidelity (complement of table B)'],
        [(s,fmt(get(s,'all_restored','old_source_critical_match')),fmt(get(s,'all_restored','old_source_general_match'))) for s in ['random','enriched']])
    actual=table(['Sample','Actual-input critical predicate fidelity','Actual-input general predicate fidelity'],
        [(s,fmt(get(s,'all_restored','actual_input_critical_match')),fmt(get(s,'all_restored','actual_input_general_match'))) for s in ['random','enriched']])
    aligned=table(['Sample','Source critical fidelity','Source general fidelity','Actual-input general fidelity'],
        [(s,*[fmt(get(s,'aligned_expressible',metric)) for metric in ['old_source_critical_match','old_source_general_match','actual_input_general_match']]) for s in ['random','enriched']])
    paired=table(['Sample','Original restored − POS-cap4','Aligned restored − POS-cap4','Aligned full − restored'],
        [(s,fmt(get(s,'all_restored','paired_restored_minus_pos_cap4'),True),
          fmt(get(s,'aligned_expressible','paired_restored_minus_pos_cap4'),True),
          fmt(get(s,'aligned_expressible','paired_full_minus_restored'),True)) for s in ['random','enriched']])
    models=table(['Sample','Model','Original source critical fidelity','Actual-input critical fidelity'],
        [(s,m,fmt(get(s,'all_restored','old_source_critical_match',m)),fmt(get(s,'all_restored','actual_input_critical_match',m)))
         for s in ['random','enriched'] for m in sorted(diff.model.unique())])
    word=table(['Family (wb-aactext- prefix)','Source','Stored visible input','Decision / reason'],
        [(r.family_id.removeprefix('wb-aactext-'),r.source,r.input_text,f'{r.status}: {r.reason}')
         for r in inv[inv['mode'].eq('word')].itertuples(index=False)])
    fallback=table(['Family','Stored fallback reference','Source coder 1 / 2'],
        [(r.family_id,r.source_item_value,f'{r.source_coder1} / {r.source_coder2}')
         for r in inv[inv.status.eq('unknown_source_consensus')].itertuples(index=False)])
    human=result['human']
    gate=table(['Field','Held-out n','κ [95% CI]'],
        [(d,r['n'],f"{r['kappa']:.3f} [{r['kappa_ci'][0]:.3f}, {r['kappa_ci'][1]:.3f}]") for d,r in human['gate'].items()])
    ex=result['example']['row']; source_text=inv.set_index('family_id').loc[ex['family_id'],'source']
    conflict=table(['Family','Stored source category','Actual cue','General source match / actual-cue match (4 outputs each)'],
        [(r.family_id,r.source_panel_value,r.actual_cue,
          f"{int(diff[diff.family_id.eq(r.family_id)].old_source_general_match.sum())}/4 / {int(diff[diff.family_id.eq(r.family_id)].actual_input_general_match.sum())}/4")
         for r in inv[inv.status.eq('definite_conflict')].itertuples(index=False)])
    text=f'''# W-B restoration contract audit — cycle 2, Action 1

Date: **2026-11-01**. **Complete inventory audit: 139 restored messages, 556 stored P0 outputs, four fixed models. 0 generator calls; 0 judge calls; no GPU servers.** This is an audit of stored specifications and machine labels, not new human adjudication or semantic-quality validation.

**Finding:** seven chip/source-category conflicts block a “model ignored the restored source cue” attribution on all 28 associated outputs. Five certainty conflicts account for 20 source failures that all honour the visible `[MAYBE]`. Six word inputs support the existing coarse politeness predicate; two remain unknown. Source-coder disagreement additionally prevents five detector-fallback references from entering the aligned/expressible sensitivity. Original source-fidelity tables remain available; their source-mismatch rates are not automatically supplied-cue violation rates.

## Inventory and verification

Start: `analysis/derived/wb_cue_source_audit.csv`, unchanged. The audit joins every restored scored occurrence to `runs/wb1/outputs.jsonl`, requiring exact equality of output ID, family, model, channel, request key, input and output strings. Every occurrence is also checked against its stored request and generation record: input, model, prompt SHA, target membership, prompt suffix/visible legend and generated suggestion. Every restored input matches `data/items/wb.jsonl`; source strings also match `data/specs/wb_sample.jsonl`. Every visible chip is decoded by the existing `CHIP_TO_GENERAL` mapping and checked against the stored item and panel source reference. The eight word inputs are reconstructed only for verification from stored carrier IDs using the CPU tokenizer, without writing items or requests. All 131 chip mappings and eight word renderings were checked. There is no new corpus sample.

{status}

“Aligned” means compatible with an expressible **panel-consensus** source category at this endpoint, not complete semantic equivalence. The initial CSV had 115 chip mappings aligned to **item** categories, seven conflicts, nine unclear references, and eight words awaiting review. Five of those 115 item references are detector fallbacks without source consensus: after withholding them and admitting six reviewed word inputs, the aligned population is **116 messages / 464 outputs** (55 random, 61 enriched). All nine unclear references remain unknown for source-restoration attribution. Source categories themselves were not relabeled.

The seven definite conflicts (exhaustive census, not selected examples) are:

{conflict}

Five certainty inputs honour their visible chip in **20/20** outputs, while **0/20** match the source. The empirical five-message bootstrap is [100,100]% for visible-chip fidelity; it is not a future-risk bound. Across the two incompatible act inputs, actual-cue general fidelity is **2/8**, while source fidelity is **3/8**. Even when an output fails the actual cue, the original incompatible source predicate was not supplied by that cue. These category disagreements are specification diagnostics against the stored panel labels, not a claim that those labels are linguistic ground truth.

Eight enriched `[SURE]` messages expose a second distinction: D-007 permits **plain or emphatic** output under that chip, whereas their source references demand emphatic. Four of 32 outputs fail the finer source endpoint while honouring `[SURE]`; one fails both. Keep these compatibly aligned messages in the declared sensitivity, but withhold an attribution that the chip supplied the finer distinction. The diff records `source_violation_attribution_allowed=False` on all 32 such occurrences. Actual-input fidelity remains reportable.

The five source-consensus exclusions are:

{fallback}

These five are **not additional definite conflicts**. Their visible chips can be evaluated, but the agreed source endpoint required by original general table B is unavailable.

## Word restoration audit (all eight)

{word}

The six admitted words supply only the existing coarse “any explicit polite marker” predicate. Thanks/apology and softened requests are not exact-subtype preservation endpoints here. `how cheap` lacks the source's exclamatory construction; do not adjudicate it into a fixed statement or question. `feel sorry` retains sympathy/apology ambiguity; a hidden metadata `[PLEASE]` cannot resolve it. Both remain **unknown** for actual-input fidelity and withheld for source-restoration violations, regardless of their scorer labels.

Four word restorations are byte-identical to POS-cap4: `test-00375`, `train-00651`, `train-03131`, `train-03837`. Thus three of the six aligned word cases already carry their marker in the baseline. They remain in the declared population, with `changed_visible_input=False`; a channel name does not establish an added-cue intervention. All seven politeness word records carry metadata `[PLEASE]`, although that literal chip is absent from the rendered words; the audit uses the visible words exclusively.

## (a) Original source fidelity, retained

{source}

Critical fidelity uses the stored focal critical labels and `critical_match` unchanged, including detector/unclear item references in the original table-C population. General fidelity uses panel-consensus expressible references and the original `wb_report.honours` predicate (plain assertion accepts plain/emphatic; polite markers accept any polite marker). Table B's historical restored failure counts are therefore still **12/223 random** and **55/276 enriched**. They measure source mismatch under that eligibility, rather than proving noncompliance with the actual restoration input. `report_tables.md` and the original numeric CSVs are retained byte-for-byte.

## (b) Actual-input predicate fidelity

{actual}

There are **137 messages / 548 occurrences** with an identified visible focal predicate. The two ambiguous word cases account for eight ineligible occurrences, kept in the diff as unknown. Within eligible occurrences, six critical labels and one general-agent label are missing; neither is a failure or a fallback. Thus critical denominators are **228/232 random** and **314/316 enriched**; general denominators are **231/232** and **316/316**. The nine unclear source references and five disputed-source fallbacks remain eligible only for this actual-input endpoint, which does not need a source reference. These rates are category-level preservation, not complete meaning, grammatical completeness, or usefulness.

Critical extraction collapses politeness to polite/plain; general extraction retains subtypes before applying the accepted set. They are distinct views, not interchangeable labels. Existing J1/J2 disagreement handling is retained; general labels include the historical production tiebreak. No new judge labels or single-J1 critical fallback enter this audit.

## (c) Aligned/expressible sensitivity

{aligned}

General source failure becomes **8/219 random** and **26/244 enriched** on this declared population. Actual-input general failure is **8/219** and **22/244**, respectively; the four enriched differences are precisely the `[SURE]` coarsening cases. Critical labels are observed for **218/220 random** and **243/244 enriched** occurrences. This remains machine-assessed, with the two word ambiguities, nine unclear references and five disputed-source references withheld rather than resolved in favour of any model.

Paired channel contrasts use **source critical fidelity** on the indicated population:

{paired}

The new aligned-population gains are changed-population sensitivities. They are not an intervention that improved the historical outputs, nor a replacement for the original restoration estimate.

The earlier **five-certainty-message-only exclusion** is also retained separately (c2 `hyp_checks.json`, `H3/general/enriched`): **55/276 = 19.93% [12.68,27.90] → 35/256 = 13.67% [8.20,19.92]** source failure; original minus restricted ratio **+6.26 pp [1.27,12.10]**. That partial sensitivity still contains the two act conflicts and unresolved word/reference issues; it is neither the comprehensive aligned audit nor a measured intervention gain. Do not pool or average these populations.

### Fixed-model diagnostics

{models}

Per-dimension, model and mode details, exact counts, missingness and CIs are in `contract_audit_estimates.csv` and `contract_audit.json`. Random and enriched samples are always separate; no enriched prevalence claim is licensed.

## Correct the polarity denominators

On primary-panel confirmed-ambiguous POS-cap4 polarity inputs, **0/36 random and 2/84 enriched** are source-honouring counts for **non-default** sources, including mixed/unclear. They were mislabeled as strictly negated in the narrative and ledger. Restricting to panel-consensus **negated** sources gives **0/32 (8 messages)** and **2/48 (12 messages)**. This is a descriptive stratum correction, not changed outputs or evidence that every non-default source is a negation. `contract_audit.json:polarity_denominators` records both definitions.

## Builder defect and future validation requirement

In `src/wb_items.py`, `VALUE_CHIP` maps plain assertion to `[SURE]`, but a special plain-assertion certainty branch overrides it with `vchip=None`. The next condition, `if chip and (vchip is None or chip == vchip)`, treats that absent mapping as permission to copy the detector chip. For these five messages the detector supplies `[MAYBE]`, so the rendered input disagrees with the plain-assertion item/panel endpoint. The same generic fallback admits `[?]` and `[ASK]` for the two offer/suggestion references, whose source category has no mapped chip.

`src/wb_report.py` table B then treats every restored focal dimension as supplied, without decoding the rendered input. This explains its source-mismatch attribution; it is not a changed generation or merely an analysis join error. The historical `scored.parquet` flags and original report-B calculations are separate fields in the diff, because `attribute.py`'s metadata-based `cue_in_input` sometimes already says false.

The new **mandatory future-builder requirement** is the input-builder validation requirement (checked by `src/validate_cue_inputs.py`). Before any new freeze or dispatch, decode visible cues, compare accepted sets with source references, block disjoint mappings, withhold unresolved applicability/consensus, disclose coarse predicates and no-op inputs, and validate word renderings. Missing `vchip` must not authorize an incompatible detector fallback. This audit does **not** modify `wb_items.py`, rebuild/re-key historical requests, or certify that a code fix has been implemented. Historical item/request/output/label files remain unchanged.

## Human validation status (D-031 and actual JSON)

**H7 passed**, with two human annotators, 187 items: 100 double-coded core (76 sampled, 24 challenges), 87 single-coded extras. Gate fields are exactly `human.judge.<field>["sampled_test/final"]`:

{gate}

Held-out κ is **.906–.972**, lowest lower 95% bound **.813**. The broader sampled/final range is **.899–.977**, a different population. Primary Violation agreement is **96/99 [91.5,99.0]%**, κ=.916: 22 both-positive, one judge-only, two human-only, 74 both-negative (judge-positive 23, human-positive 24). Reference labels use plurality with ties/unsure excluded, not adjudicated gold; conversion from another annotation format and missing per-item timing remain disclosed.

Humans correct the machine reading of “can't wait”; both still label “a couple of” as two against the unchanged frozen key (D-033). Passing H7 supports the earlier extraction inventory. It does not certify W-B admissibility, the current word audit, repaired-text quality, or every W-C/W-D boundary. **W-B's 20-message human audit is still absent: {human['wb_human_fields_filled']} completed HUMAN fields in the prepared {human['wb_audit_items']}-message JSON.** Keep W-B machine-assessed; no human-validated ambiguity or transfer-prevalence claim follows.

## Stored counterexample and declared selection

Reuse the c2 H3 rule: among the five certainty-conflict messages' restored outputs, sort **family_id then model**, take the first. Selected output is **{ex['output_id']}**, Gemma, `{ex['family_id']}`, `runs/wb1/outputs.jsonl`. Source (hidden from generator): **{source_text}** Stored source category: plain assertion. Actual generator input and output, verbatim:

```text
{ex['input_text']}
→ {ex['text']}
```

This outcome-conditioned stored counterexample illustrates **20/20 source-mismatch / visible-chip-honouring outputs across five messages**, not typical outputs or ignored `[MAYBE]`. All 556 exact strings, including awkward outputs and unknowns, are available in the diff. No invented or normalized replacement sentence is displayed.

## Artifacts, uncertainty and reproducibility

- `contract_audit_inventory.csv`: all 139 mappings, eight word decisions, source origins/consensus, visible inputs, accepted sets, expressibility, applicability and no-op flags.
- `contract_audit_diff.csv`: all 556 occurrences with exact input/output strings and IDs; original source-critical match, original table-B eligibility/general verdict, historical scored flags, actual-input critical/general verdicts, aligned eligibility and withheld-attribution reasons. General table-B-to-actual changes: **29 changed, 56 ineligible-to-known, eight known-to-unknown, 463 unchanged**; unchanged includes the one missing general outcome.
- `contract_audit_estimates.csv` / `.json`: source/input/aligned rates, paired source contrasts, model/dimension/mode strata, missingness, polarity correction, human-status fields and input SHA-256s.
- `contract_audit_history_20261101.tar.gz`: pre-audit W-B report/narrative/tables/numeric files and shared ledger/captions; no historical snapshot is overwritten.
- `contract_audit_evidence_20261101.tar.gz` and `contract_audit_evidence_manifest.json`: final self-contained hashed evidence snapshot; archive members preserve current inputs, code, outputs and refreshed evidence. This is a **post-hoc evidence snapshot**, not a prospective freeze. See manifest for producing commands and hashes.

New intervals here use **10,000 whole-message percentile resamples, seed 20261101**, separately within each sample/population; fixed model roster and paired arms retained jointly. Endpoint-keyed RNG streams are recorded in the script. Unknown labels leave denominators; messages with zero observed endpoint labels retain their cluster weight. These pointwise intervals do not correct exploratory inspection, source/codebook error or linguistic labeling error. Small/single-message and zero-event intervals can degenerate and do not guarantee future behaviour. Original W-B tables retain their 2,000-resample intervals; the separate earlier c2 five-message sensitivity retains its original joint resampling stream.

Reproduce the derivative analysis without model services:

```bash
setsid nohup bash -c '.venv/bin/python src/wb_contract_audit.py && .venv/bin/python src/wb_contract_audit_report.py' > analysis/wb/contract_audit_run.log 2>&1 < /dev/null &
```

Use the project venv from the repository root. Snapshot verification is separately reproducible with `src/freeze_wb_contract_audit.py --verify`; snapshot creation refuses to overwrite existing evidence.
'''
    (OUT/'contract_audit.md').write_text(text)
    print('Wrote analysis/wb/contract_audit.md')


if __name__=='__main__':
    main()

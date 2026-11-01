# R5 input-builder validator: what it rejects before generation

`src/validate_cue_inputs.py` is a side-effect-free check for the **input-builder boundary** (cycle-3 Action 5, R5).
It decodes only the *rendered* input a model would see, never hidden metadata, and compares the accepted
predicate set with the source requirement the builder claims to restore. Only `compatible` certifies the source.
Tests: `.venv/bin/python -m unittest tests.test_validate_cue_inputs`. Replay (writes only this directory):
`OPENBLAS_NUM_THREADS=1 .venv/bin/python src/validate_cue_inputs.py replay`. **0 generator / 0 judge calls.**

```text
$ .venv/bin/python src/validate_cue_inputs.py check --dimension certainty --requires "plain assertion" \
      --input "Keywords: [MAYBE] extra pillow nice"
verdict: conflicting   accepted: ['hedged/uncertain']   required: ['plain assertion', 'strongly certain/emphatic']
exit status 2 (reject before generation); builder hook: require_valid(...) raises CueContractError
```

## Replay of the frozen W-B restoration inventory

All **139** restored inputs (131 chips + 8 words) from `data/items/wb.jsonl`, each equal to its stored
`runs/wb1` request input, against the claimed source requirement in the item's `general_spec` (basis: panel
consensus or detector fallback). The verdict equals the class implied by the frozen
[contract audit](../wb/contract_audit.md) for **139/139** inputs, and the decoded accepted
set equals the audit's for **139/139**. Input hashes are identical before and
after; no historical request was rebuilt.

| verdict | inputs |
|---|---|
| compatible | 105 |
| compatible_but_coarser | 8 |
| conflicting | 7 |
| unknown | 15 |
| unchanged_noop | 4 |

**Rejected as conflicting: 7/7 known definite conflicts** (none escapes).
In the five `[MAYBE]` cases, stored outputs followed the visible chip and failed the source in
20/20 outputs (5 messages); the validator would have stopped those requests
before generation.

| family | rendered input | claimed source | cue accepts |
|---|---|---|---|
| test-00113 | `Keywords: [MAYBE] extra pillow nice` | plain assertion | ["hedged/uncertain"] |
| test-00508 | `Keywords: [MAYBE] loved go rain kept` | plain assertion | ["hedged/uncertain"] |
| train-00249 | `Keywords: [ASK] let get coffee` | offer/suggestion | ["request/command"] |
| train-01930 | `Keywords: [MAYBE] tell possible` | plain assertion | ["hedged/uncertain"] |
| train-02253 | `Keywords: [MAYBE] wish file compensation claim` | plain assertion | ["hedged/uncertain"] |
| train-03985 | `Keywords: [?] help buddy` | offer/suggestion | ["question"] |
| train-04637 | `Keywords: [MAYBE] wish type` | plain assertion | ["hedged/uncertain"] |

**Compatible but coarser: 8/8 `[SURE]` cases.** D-007 lets `[SURE]` accept plain
*or* emphatic, so the chip cannot supply the emphatic source distinction; 0 are certified.

| family | rendered input | claimed source |
|---|---|---|
| train-00194 | `Keywords: [SURE] bad luck` | strongly certain/emphatic |
| train-01420 | `Keywords: [SURE] life sucks` | strongly certain/emphatic |
| train-02581 | `Keywords: [SURE] cool` | strongly certain/emphatic |
| train-02795 | `Keywords: [SURE] awesome` | strongly certain/emphatic |
| train-03210 | `Keywords: [SURE] feel hot horrible` | strongly certain/emphatic |
| train-03331 | `Keywords: [SURE] time` | strongly certain/emphatic |
| train-04331 | `Keywords: [SURE] waiting` | strongly certain/emphatic |
| train-04463 | `Keywords: [SURE] cold` | strongly certain/emphatic |

**Unknown: 15**, never certified. Unclear references and non-consensus sources stay unknown
even when the chip would map; an uncertain word stays unknown.

| family | rendered input | reason |
|---|---|---|
| test-00070 | `Keywords: [NOT] know buy` | source coders disagree; detector fallback 'negated' |
| train-00093 | `Keywords: [NOT] take care sad` | unclear/mixed source reference |
| train-00355 | `Keywords: [NOT] do long time get` | unclear/mixed source reference |
| train-00734 | `Keywords: [NOT] know have watch` | source coders disagree; detector fallback 'negated' |
| train-00771 | `Keywords: [NOT] please clear table feel` | unclear/mixed source reference |
| train-00858 | `Keywords: [NOT] know check` | unclear/mixed source reference |
| train-01531 | `Keywords: how cheap` | word cue outside supported scope |
| train-02081 | `Keywords: [NOT] fight solve issue` | unclear/mixed source reference |
| train-02212 | `Keywords: [NOT] difficult adjusting` | unclear/mixed source reference |
| train-02265 | `Keywords: [MAYBE] believe minute` | source coders disagree; detector fallback 'hedged/uncertain' |
| train-02277 | `Keywords: [MAYBE] thought ur car good` | source coders disagree; detector fallback 'hedged/uncertain' |
| train-02650 | `Keywords: [NOT] have money` | unclear/mixed source reference |
| train-03284 | `Keywords: [THEY] home` | source coders disagree; detector fallback 'third party' |
| train-04263 | `Keywords: [NOT] delay wait` | unclear/mixed source reference |
| train-04639 | `Keywords: [NOT] go sit sofa dirty` | unclear/mixed source reference |

**Unchanged/no-op: 4** word restorations are byte-identical to their POS-cap4 baseline
(relation shown separately; `feel sorry` is also unknown). Seven word records carry a hidden metadata
`[PLEASE]` that is not visible; the validator warns and ignores it.

| family | rendered input | relation if it had changed |
|---|---|---|
| test-00375 | `Keywords: feel sorry` | unknown |
| train-00651 | `Keywords: thanks get wishes` | compatible |
| train-03131 | `Keywords: thank care love` | compatible |
| train-03837 | `Keywords: thanks saying tat` | compatible |

## Boundary

The supported scope is narrow by design: the `Keywords:` wrapper, every chip in `labels.CHIP_TO_GENERAL`, and
politeness word markers at the coarse polite-marker endpoint. Any other word evidence, full-text input, unsupported chip,
unclear or unexpressible reference, or non-consensus source is `unknown`. This is a requirement check against
machine-assessed W-B source labels, not human-validated ground truth or a semantic-equivalence guarantee.
It is demonstrated on historical inputs; it was not part of the original W-B generation.

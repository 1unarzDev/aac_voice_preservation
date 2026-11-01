"""Reproduce S1: . .venv/bin/activate && python -m src.s1_analyze

--initial writes only initial detector validation predictions; the full run
requires the independently authored manual_labels_compact.txt. All random
choices use seed 20261031. No paid APIs or generation endpoints are used.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys

import pandas as pd

from .s1_cues import (DIMENSIONS, COMPRESSORS, Lexicon, load_nlp, detect_doc,
                      compress_doc, cue_loss, chip_cost)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/s1'
SEED = 20261031


def js(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def wilson(k, n):
    if not n:
        return float('nan'), float('nan')
    z = 1.959963984540054
    p = k / n
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return max(0., center-half), min(1., center+half)


def rate(k, n, **kwargs):
    lo, hi = wilson(k, n)
    return dict(**kwargs, count=int(k), n=int(n), percent=100*k/n if n else None,
                ci_low_percent=100*lo, ci_high_percent=100*hi)


def cell(r):
    if not r['n']:
        return '0/0 (n/a)'
    precision = 2 if r['percent'] < 1 else 1
    return f"{r['count']:,}/{r['n']:,} ({r['percent']:.{precision}f}%; {r['ci_low_percent']:.{precision}f}–{r['ci_high_percent']:.{precision}f})"


def read_data():
    rows = []
    for split in ('train', 'dev', 'test'):
        path = ROOT / f'data/raw/aactext/sent_{split}_aac.txt'
        for i, text in enumerate(path.read_text().splitlines(), 1):
            if text.strip():
                rows.append(dict(id=f'aactext-{split}-{i:05d}', split=split, line=i, text=text.strip()))
    return rows


def manual_labels():
    rows = []
    maps = [dict(a='affirmative', n='negated'),
            dict(s='statement', q='question', r='request/command', f='refusal'),
            dict(i='speaker', w='we/joint', y='addressee', t='third party', u='unspecified'),
            dict(p='plain assertion', h='hedged/uncertain', e='strongly certain/emphatic', x='n/a (question/request)')]
    for line in (OUT / 'manual_labels_compact.txt').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        num, pol, act, agent, cert, time, polite = line.split()
        labels = dict(zip(DIMENSIONS[:4], [m[v] for m, v in zip(maps, [pol, act, agent, cert])]))
        labels['time'] = sorted({'n': 'present', 'p': 'past', 'f': 'future', 'u': 'unspecified'}[x] for x in time if x != '-')
        labels['quantity'] = []
        labels['politeness'] = {'-': 'none', 'p': 'please', 's': 'softened request', 't': 'thanks/apology'}[polite]
        rows.append((int(num), labels))
    assert [i for i, _ in rows] == list(range(1, 151))
    return [labels for _, labels in rows]


def validate(by_id, initial=False):
    selected = random.Random(SEED).sample(read_data(), 150)
    selected = [{k: r[k] for k in ('id', 'split', 'text')} for r in selected]
    (OUT / 'validation_texts.json').write_text(json.dumps(selected, indent=2))
    records = []
    for i, item in enumerate(selected, 1):
        r = by_id[item['id']]
        records.append(dict(row=i, **item, **{f'detector_{d}': js(r['detector']['labels'][d]) for d in DIMENSIONS}))
    if initial:
        pd.DataFrame(records).to_csv(OUT / 'detector_check_initial.csv', index=False)
        for row in records:
            print(row['row'], row['text'], '|', '; '.join(f'{d}={row[f"detector_{d}"]}' for d in DIMENSIONS))
        return
    gold = manual_labels()
    before = pd.read_csv(OUT / 'detector_check_initial.csv').set_index('id')
    agreements, mismatches = [], []
    for item, labels in zip(records, gold):
        for d in DIMENSIONS:
            item[f'llm_{d}'] = js(labels[d])
            item[f'initial_{d}'] = before.loc[item['id'], f'detector_{d}']
            item[f'agree_{d}'] = item[f'detector_{d}'] == item[f'llm_{d}']
            if not item[f'agree_{d}']:
                mismatches.append(dict(id=item['id'], text=item['text'], dimension=d,
                                       llm=item[f'llm_{d}'], detector=item[f'detector_{d}']))
        item['annotator'] = 'executing LLM; source-only first pass; no external human gold'
    for d in DIMENSIONS:
        for version in ('initial', 'detector'):
            k = sum(r[f'{version}_{d}'] == r[f'llm_{d}'] for r in records)
            agreements.append(rate(k, 150, dimension=d, version=version))
    pd.DataFrame(records).to_csv(OUT / 'detector_check.csv', index=False)
    pd.DataFrame(agreements).to_csv(OUT / 'detector_agreement.csv', index=False)
    pd.DataFrame(mismatches).to_csv(OUT / 'detector_disagreements.csv', index=False)
    return agreements


def stratify(rows):
    rng = random.Random(SEED)
    pool = {r['id']: r for r in rows}
    selected, reasons = {}, defaultdict(list)
    predicates = {
        'negation': lambda r: r['detector']['labels']['polarity'] == 'negated',
        'modal_or_hedge': lambda r: bool(r['detector']['hedge_spans']),
        'question': lambda r: r['detector']['labels']['speech_act'] == 'question',
        'second_person': lambda r: r['detector']['labels']['agent'] == 'addressee',
        'please': lambda r: any(c['kind'] == 'please' for c in r['detector']['cues']),
    }
    # Disjoint sequential quota draws: 55 each; fill 125 from the remainder.
    # This is a challenge sample, not prevalence-weighted evaluation data.
    for name, pred in predicates.items():
        candidates = [r for r in pool.values() if pred(r) and r['id'] not in selected]
        for r in rng.sample(candidates, min(55, len(candidates))):
            selected[r['id']] = r
            reasons[r['id']].append(name)
    remaining = [r for r in rows if r['id'] not in selected]
    for r in rng.sample(remaining, 400-len(selected)):
        selected[r['id']] = r
        reasons[r['id']].append('random_fill')
    path = ROOT / 'data/specs/aactext_sample400.jsonl'
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open('w') as f:
        for r in sorted(selected.values(), key=lambda r: r['id']):
            item = dict(id=r['id'], split=r['split'], text=r['text'],
                        detector_labels=r['detector']['labels'],
                        keywords={c: r['keywords'][c]['words'] for c in COMPRESSORS},
                        sampling_stratum=reasons[r['id']][0],
                        detector_version='s1-v1', corpus='AACText fictional crowdsourced messages', license='CC BY 4.0',
                        attribution='Keith Vertanen and Per Ola Kristensson (2011), The Imagination of Crowds',
                        source_url='https://www.aactext.org/imagine/')
            f.write(js(item)+'\n')
    stats = []
    for split in ('all', 'train', 'dev', 'test'):
        full = [r for r in rows if split == 'all' or r['split'] == split]
        sample = [r for r in selected.values() if split == 'all' or r['split'] == split]
        for name, pred in predicates.items():
            stats.append(rate(sum(map(pred, sample)), len(sample), split=split, feature=name, population='sample400'))
            stats.append(rate(sum(map(pred, full)), len(full), split=split, feature=name, population='corpus'))
    pd.DataFrame(stats).to_csv(OUT / 'sample_strata.csv', index=False)
    pd.DataFrame([dict(id=r['id'], split=r['split'], stratum=reasons[r['id']][0]) for r in selected.values()]).to_csv(OUT / 'sample400_manifest.csv', index=False)
    return stats


def analyze(rows, agreements, nlp):
    metrics, prevalence, collision_stats, distributions, cost_stats, diagnostics = [], [], [], [], [], []
    message_rows, collision_examples = [], []
    for split in ('all', 'train', 'dev', 'test'):
        subset = [r for r in rows if split == 'all' or r['split'] == split]
        n = len(subset)
        for d in DIMENSIONS:
            k = sum(any(c['dimension'] == d for c in r['detector']['cues']) for r in subset)
            prevalence.append(rate(k, n, split=split, dimension=d))
        for compressor in COMPRESSORS:
            for name, predicate in {
                'empty_keywords': lambda r: not r['keywords'][compressor]['words'],
                'fewer_than_two_keywords': lambda r: len(r['keywords'][compressor]['words']) < 2,
            }.items():
                diagnostics.append(rate(sum(predicate(r) for r in subset), n, split=split, compressor=compressor, diagnostic=name))
            for d in (*DIMENSIONS, 'any'):
                lost = sum(any(r['loss'][compressor]['lost'].values()) if d == 'any' else r['loss'][compressor]['lost'][d] for r in subset)
                present = n if d == 'any' else sum(r['loss'][compressor]['present'][d] for r in subset)
                metrics.append(dict(rate(lost, n, split=split, compressor=compressor, dimension=d),
                                    cue_present_n=present, conditional_loss_percent=100*lost/present if present else None,
                                    conditional_ci_low_percent=100*wilson(lost, present)[0],
                                    conditional_ci_high_percent=100*wilson(lost, present)[1]))
            groups = defaultdict(list)
            for r in subset:
                groups[' '.join(r['keywords'][compressor]['words'])].append(r)
            colliding = set()
            for keywords, group in groups.items():
                if len({js(r['detector']['labels']) for r in group}) > 1:
                    colliding.update(r['id'] for r in group)
                    if split == 'all':
                        for r in group:
                            collision_examples.append(dict(compressor=compressor, keywords=keywords,
                                                           id=r['id'], split=r['split'], text=r['text'], labels=js(r['detector']['labels'])))
            collision_stats.append(rate(len(colliding), n, split=split, compressor=compressor,
                                        unique_keyword_strings=len(groups), ambiguous_keyword_strings=sum(len({js(r['detector']['labels']) for r in g}) > 1 for g in groups.values())))
            costs = [r['chip_cost'][compressor] for r in subset]
            counts = Counter('unrestorable' if c['min_chips'] is None else str(c['min_chips']) for c in costs)
            for count in sorted(counts, key=lambda c: 999 if c == 'unrestorable' else int(c)):
                distributions.append(rate(counts[count], n, split=split, compressor=compressor, min_chips=count))
            feasible = [r for r in subset if r['chip_cost'][compressor]['fully_restorable']]
            def mean(fn, rr):
                return sum(fn(r) for r in rr)/len(rr) if rr else None
            cost_stats.append(dict(split=split, compressor=compressor, n=n, feasible_n=len(feasible),
                full_chars_mean=mean(lambda r: len(r['text']), subset),
                full_word_selections_mean=mean(lambda r: len(r['text'].split()), subset),
                keyword_chars_mean=mean(lambda r: len(' '.join(r['keywords'][compressor]['words'])), subset),
                keyword_selections_mean=mean(lambda r: len(r['keywords'][compressor]['words']), subset),
                feasible_full_chars_mean=mean(lambda r: len(r['text']), feasible),
                feasible_keyword_chars_mean=mean(lambda r: len(' '.join(r['keywords'][compressor]['words'])), feasible),
                min_chip_selections_mean=mean(lambda r: r['chip_cost'][compressor]['min_chips'], feasible),
                typed_keywords_plus_chips_mean=mean(lambda r: len(' '.join(r['keywords'][compressor]['words'])) + r['chip_cost'][compressor]['min_chips'], feasible),
                predicted_words_plus_chips_mean=mean(lambda r: len(r['keywords'][compressor]['words']) + r['chip_cost'][compressor]['min_chips'], feasible),
                literal_chip_chars_with_separators_mean=mean(lambda r: len(' '.join(r['keywords'][compressor]['words'] + r['chip_cost'][compressor]['chips'])), feasible)))
            if split == 'all':
                for r in subset:
                    cc = r['chip_cost'][compressor]
                    message_rows.append(dict(id=r['id'], split=r['split'], text=r['text'], compressor=compressor,
                        keywords=js(r['keywords'][compressor]['words']), keyword_string=' '.join(r['keywords'][compressor]['words']),
                        labels=js(r['detector']['labels']), present_dimensions=js(r['loss'][compressor]['present']),
                        lost_dimensions=js(r['loss'][compressor]['lost']), any_loss=any(r['loss'][compressor]['lost'].values()),
                        cues=js(r['loss'][compressor]['events']), collision=r['id'] in colliding,
                        chips=js(cc['chips']), min_chips=cc['min_chips'], covered_chip_count=cc['covered_chip_count'], unrestorable=js(cc['unrestorable']),
                        full_chars=len(r['text']), keyword_chars=len(' '.join(r['keywords'][compressor]['words'])),
                        keyword_selections=len(r['keywords'][compressor]['words']),
                        typed_keywords_plus_chips=None if cc['min_chips'] is None else len(' '.join(r['keywords'][compressor]['words']))+cc['min_chips'],
                        predicted_words_plus_chips=None if cc['min_chips'] is None else len(r['keywords'][compressor]['words'])+cc['min_chips']))
    for name, data in [('loss_rates', metrics), ('cue_prevalence', prevalence), ('collision_rates', collision_stats),
                       ('collisions', collision_examples), ('chip_distribution', distributions), ('cost_summary', cost_stats), ('message_metrics', message_rows),
                       ('compressor_diagnostics', diagnostics)]:
        pd.DataFrame(data).to_csv(OUT / f'{name}.csv', index=False)
    with (OUT / 'message_cues.jsonl').open('w') as f:
        for r in rows:
            f.write(js(r)+'\n')
    strata = stratify(rows)
    figure(metrics)
    summary(rows, metrics, prevalence, collision_stats, distributions, cost_stats, agreements, strata, nlp)


def figure(metrics):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    fig, ax = plt.subplots(figsize=(10, 5.5), layout='constrained')
    x = np.arange(len(DIMENSIONS)+1)
    for i, (c, color, label) in enumerate(zip(COMPRESSORS, ['#0072B2', '#E69F00', '#009E73'],
                                                  ['POS cap 4 (+please)', 'POS uncapped', 'Light uncapped (+not/please)'])):
        rr = [next(r for r in metrics if r['split'] == 'all' and r['compressor'] == c and r['dimension'] == d) for d in (*DIMENSIONS, 'any')]
        y = np.array([r['percent'] for r in rr])
        ax.bar(x+(i-1)*.25, y, width=.24, color=color, label=label)
        ax.errorbar(x+(i-1)*.25, y, yerr=[y-np.array([r['ci_low_percent'] for r in rr]), np.array([r['ci_high_percent'] for r in rr])-y], fmt='none', ecolor='#333333', capsize=2, linewidth=.8)
    ax.set_xticks(x, ['Polarity', 'Speech act', 'Agent', 'Certainty', 'Time', 'Quantity', 'Politeness', 'Any dimension'], rotation=20, ha='right')
    ax.set_ylabel('Messages losing ≥1 detected cue (%)')
    ax.set_title(f"AACText: cue-token loss under three keyword compressors (n = {rr[0]['n']:,})")
    ax.set_ylim(0, 105)
    ax.set_yticks(range(0, 101, 20))
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.2)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc='upper left', fontsize=9)
    fig.savefig(OUT / 'fig_loss_by_dimension.png', dpi=180)
    fig.savefig(OUT / 'fig_loss_by_dimension.svg')
    plt.close(fig)


def summary(rows, metrics, prevalence, collisions, dist, costs, agreement, strata, nlp):
    get = lambda c,d,s='all': next(r for r in metrics if r['compressor']==c and r['dimension']==d and r['split']==s)
    old = get('pos_cap4','any')
    old_collision = next(r for r in collisions if r['split']=='all' and r['compressor']=='pos_cap4')
    old_dist = [r for r in dist if r['split']=='all' and r['compressor']=='pos_cap4']
    up_to_two = rate(sum(r['count'] for r in old_dist if r['min_chips'] in {'0','1','2'}), len(rows))
    infeasible = next(r for r in old_dist if r['min_chips']=='unrestorable')
    out = [f"# S1: AACText cue loss and restoration cost\n",
           f"**H1 holds under this detector:** POS-cap4 loses ≥1 detected dimension in **{cell(old)}**; threshold ≥30%. These are cue-token retention estimates, not semantic judgments or AAC-user outcomes.",
           f"Uncapped POS: **{cell(get('pos_uncapped','any'))}**. Light: **{cell(get('light','any'))}**.",
           f"POS-cap4 observed collisions: **{cell(old_collision)}**. At most two SPEC chip selections restore all detected category values in **{cell(up_to_two)}**; **{cell(infeasible)}** have losses the current chip vocabulary cannot express.",
           "## Data and reproducibility\n",
           "AACText: Keith Vertanen and Per Ola Kristensson (2011), *The Imagination of Crowds: Conversational AAC Language Modeling using Crowdsourcing and Large Data Sources*, EMNLP, pp. 700–711. The [official corpus page](https://www.aactext.org/imagine/) was opened successfully during this analysis and verifies this citation, the fictional crowdsourcing protocol, and CC BY 4.0 for these resources (excluding lm_test_switch/lm_test_comm). A snapshot is saved as `corpus_source.html`. Only sent_{train,dev,test}_aac.txt were used. No exclusions for short/empty keyword outputs; nonempty source lines only. No participant or population-style claims.",
           "Run: `. .venv/bin/activate && python -m src.s1_analyze`. Seed 20261031. `--initial` reproduces the frozen pre-fix validation predictions. Inputs and code hashes: `run_manifest.json`. All percentage intervals are Wilson 95% binomial intervals; these are descriptive sensitivity intervals, not worker-cluster sampling intervals. Workers are not identified in these text files.\n",
           '| Split | Messages | Unique exact texts | Sample 400 n |', '|---|---:|---:|---:|']
    sample_ids = set(pd.read_csv(OUT / 'sample400_manifest.csv')['id'])
    for s in ('train','dev','test','all'):
        rr=[r for r in rows if s=='all' or r['split']==s]
        out.append(f"| {s} | {len(rr):,} | {len({r['text'] for r in rr}):,} | {sum(r['id'] in sample_ids for r in rr)} |")
    out += ['\n## Cue prevalence and loss\n',
            'LOSS = count(source cue present AND at least one cue carrier absent)/all messages. A phrase requires all its carrying tokens. Token positions prevent repeated-word false survival. Unmarked defaults have no explicit cue. Time and quantity are separate dimensions. Multiple cues in a dimension use any-cue loss, even when another cue of the same value survives. Conditional loss divides by messages with that dimension present and is provided in `loss_rates.csv`.',
            'Main subject is literal first-clause grammatical subject; imperatives remain unspecified. Request/refusal precedence beats question punctuation. `let\'s` is request/command to follow the requested S1 routing, despite the SPEC offer/suggestion option. Tense is main-predicate/auxiliary morphology plus explicit time words across the message. Full lexicon matches are retained as features; epistemic interpretation excludes obvious physical/ability/directional uses. Certainty is n/a for questions/requests. These heuristics do not resolve negation scope or coordinated-clause roles.\n',
            '| Dimension | Cue present | POS-cap4 loss | Uncapped loss | Light loss |', '|---|---:|---:|---:|---:|']
    for d in DIMENSIONS:
        prev=next(r for r in prevalence if r['split']=='all' and r['dimension']==d)
        out.append('| '+d+' | '+cell(prev)+' | '+' | '.join(cell(get(c,d)) for c in COMPRESSORS)+' |')
    out += ['\nCounts/n (percentage; Wilson 95% CI).\n', '| Split | POS-cap4 any loss | Uncapped any loss | Light any loss |', '|---|---:|---:|---:|']
    for s in ('train','dev','test'):
        out.append('| '+s+' | '+' | '.join(cell(get(c,'any',s)) for c in COMPRESSORS)+' |')
    out += ['\n![Cue loss with Wilson intervals](fig_loss_by_dimension.png)\n',
            'Compressors: (a) old NOUN/PROPN/VERB/ADJ/NUM excluding AUX and aux/auxpass, always keep please, first four tokens; (b) the same content POS filter without cap or please exception; (c) uncapped content POS plus not/n\'t (canonicalized to not) and please. No stopword filter or deduplication. The old minimum-two-keyword exclusion is deliberately not applied. Uncapped POS has more loss than cap4 here because it removes the old please exception: this comparison changes both the cap and the retention rule and is not a pure cap ablation.\n',
            '## Collisions\n',
            'A message counts when its exact ordered, space-joined keyword string is shared by a different source text with a differing detector label in any dimension (including time/quantity). Duplicate identical sources alone do not count. Pooled comparison allows cross-split collisions; split rows compare only within that split. This is a lower bound on possible ambiguity, constrained to attested texts and this codebook.\n',
            '| Split | POS-cap4 | Uncapped | Light |', '|---|---:|---:|---:|']
    for s in ('all','train','dev','test'):
        out.append('| '+s+' | '+' | '.join(cell(next(r for r in collisions if r['split']==s and r['compressor']==c)) for c in COMPRESSORS)+' |')
    out += ['\n## Minimal chip cost and input actions\n',
            'A chip restores its SPEC category value, not exact phrasing, temporal referent, subject identity, or negation scope. Repeated lost events with the same value need one chip; a retained event with that value already makes it available. A distinct lost value needs its matching chip. No default YES/TELL/PLAIN chip is charged because unmarked defaults are not explicit losses. The current SPEC cannot exactly encode lost quantities, thanks/apologies, softened-request forms, or unanchored time. Those cases have **no finite all-cue solution** in this vocabulary; their partial chip count is not presented as complete restoration.\n',
            '| Minimum chips | POS-cap4 | Uncapped | Light |', '|---|---:|---:|---:|']
    bins=sorted({r['min_chips'] for r in dist},key=lambda c:999 if c=='unrestorable' else int(c))
    for b in bins:
        out.append('| '+b+' | '+' | '.join(cell(next((r for r in dist if r['split']=='all' and r['compressor']==c and r['min_chips']==b),rate(0,len(rows)))) for c in COMPRESSORS)+' |')
    out += ['\nCosts below are means; no Wilson intervals apply to means. Character counts include original punctuation/spaces or single keyword separators. One chip selection costs one action. Predicted keywords each cost one selection; typed keywords cost their joined character count. Full-text character cost is a typing reference, not a measured motor/access-time cost. Literal bracketed-chip typing is also available in CSV, distinct from one-selection chips.\n',
            '| Compressor | All n | Full chars, all | Keyword chars, all | Keyword selections, all | Fully restorable n | Chips, feasible | Typed keywords + chip selections, feasible | Predicted words + chips, feasible | Full chars, feasible |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in costs:
        if r['split']=='all':
            out.append(f"| {r['compressor']} | {r['n']} | {r['full_chars_mean']:.2f} | {r['keyword_chars_mean']:.2f} | {r['keyword_selections_mean']:.2f} | {r['feasible_n']} | {r['min_chip_selections_mean']:.2f} | {r['typed_keywords_plus_chips_mean']:.2f} | {r['predicted_words_plus_chips_mean']:.2f} | {r['feasible_full_chars_mean']:.2f} |")
    out += ['\n## Detector validation: 150 source-only LLM labels, one revision\n',
            'A uniform random sample without replacement was drawn before inspecting predictions. The executing LLM read and independently labeled every sampled source in `manual_labels_compact.txt`, then inspected the initial predictions, fixed obvious bugs once, and reran. `detector_check.csv` contains source, initial/final predictions, LLM labels, and agreement flags. This is an unblinded development check by the same LLM that wrote the code, **not independent human validation or a held-out accuracy estimate**. Gold was frozen before prediction inspection and was not edited to improve agreement.\n',
            '| Dimension | Initial agreement | After one revision |', '|---|---:|---:|']
    for d in DIMENSIONS:
        out.append('| '+d+' | '+' | '.join(cell(next(r for r in agreement if r['dimension']==d and r['version']==v)) for v in ('initial','detector'))+' |')
    out += ['\nQuantity has **zero positive cases** in the 150-message uniform sample: its agreement only checks absence, not number recall. Separate executable diagnostics cover numeric examples, contraction normalization, hedge overlap, old-compressor parity, and chip infeasibility. Remaining disagreements are retained in `detector_disagreements.csv`; see `validation_notes.md` for fixes and ambiguous readings. No tuning was done after the single revision.\n',
            '## Stratified sample for later expansion\n',
            '`data/specs/aactext_sample400.jsonl` contains 400 unique source IDs, original splits/text, detector labels, and all three keyword lists. Sequential disjoint quotas draw 55 messages each for negation, modal/hedge match, question, second-person main subject, and please, then a uniform random fill of 125 from remaining messages. Overlapping features can exceed their quotas; exact draw strata are saved. Sampling is without replacement by message ID; duplicate source texts may remain. This challenge sample is not prevalence representative and has no simple inverse-probability weights.\n',
            '| Feature | Corpus | Sample 400 |', '|---|---:|---:|']
    for feature in ('negation','modal_or_hedge','question','second_person','please'):
        out.append('| '+feature+' | '+' | '.join(cell(next(r for r in strata if r['split']=='all' and r['feature']==feature and r['population']==p)) for p in ('corpus','sample400'))+' |')
    out += ['\n## Files and practical limits\n',
            '`message_metrics.csv` has one row per source × compressor and source-indexed cue evidence; `message_cues.jsonl` is the nested reusable form. Aggregate CSVs include all splits and Wilson intervals. `cost_summary.csv` separates feasibility and all-message costs; `collisions.csv` lists every observed collision. `sample_strata.csv` includes split-specific sample counts. `run_manifest.json` records versions and hashes.\n',
            'H1 is supported for this pilot cue detector. The high rate partly reflects omitted grammatical subjects, auxiliary tense, and question forms; retained inflections and imperative roots can count as surviving cues even though word order/scope is gone. Errors in deterministic detection propagate to every endpoint. A source-only human review, worker-aware uncertainty if metadata become available, and scope-aware semantic annotation are needed before stronger claims. The SPEC chip vocabulary needs explicit decisions about exact quantities and mitigation forms before an all-cue Pareto analysis.']
    report = re.sub(r'(?<=\|)\n\n(?=\|)', '\n', '\n\n'.join(out))
    (OUT / 'summary.md').write_text(report+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initial', action='store_true')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    rows=read_data()
    nlp=load_nlp()
    lexicon=Lexicon(nlp)
    for r,doc in zip(rows,nlp.pipe((r['text'] for r in rows),batch_size=64)):
        r['detector']=detect_doc(doc,lexicon,revision=0 if args.initial else 1)
        r['keywords']={c:compress_doc(doc,c) for c in COMPRESSORS}
        r['loss']={c:cue_loss(r['detector'],r['keywords'][c]) for c in COMPRESSORS}
        r['chip_cost']={c:chip_cost(r['loss'][c]) for c in COMPRESSORS}
    agreements=validate({r['id']:r for r in rows},args.initial)
    if args.initial:
        return
    analyze(rows,agreements,nlp)
    import spacy
    paths=list((ROOT/'data/raw/aactext').glob('sent_*_aac.txt'))+[ROOT/'src/s1_cues.py',ROOT/'src/s1_analyze.py',ROOT/'src/s1_verify.py',
        ROOT/'src/s1_hedges.txt',OUT/'manual_labels_compact.txt',OUT/'validation_notes.md',OUT/'corpus_source.html',
        ROOT/'orchestration/BRIEF.md',ROOT/'orchestration/SPEC.md']
    import matplotlib, numpy
    manifest=dict(seed=SEED,n=len(rows),created_utc=datetime.now(timezone.utc).isoformat(),python=sys.version,spacy=spacy.__version__,pandas=pd.__version__,
                  matplotlib=matplotlib.__version__,numpy=numpy.__version__,model=nlp.meta,
                  corpus_source_verified_url='https://www.aactext.org/imagine/',
                  validation_status='same-LLM unblinded development check; one initial-to-final revision; no human gold',
                  sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Analyzed {len(rows)} messages; report: {OUT / "summary.md"}')


if __name__=='__main__':
    main()

"""Targeted S1 diagnostics and whole-corpus output invariants.

Run ``python -m src.s1_verify`` after the analysis. If the read-only legacy
compressor exists, compare every corpus message with that independent reference.
These constructed diagnostics are not validation gold or corpus observations.
"""
import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd

from .s1_cues import Lexicon, load_nlp, detect_doc, compress_doc, cue_loss, chip_cost, COMPRESSORS
from .s1_analyze import OUT, ROOT, read_data, wilson


def main():
    nlp = load_nlp()
    lex = Lexicon(nlp)
    checks = []

    def check(name, ok, detail):
        checks.append(dict(check=name, passed=bool(ok), detail=detail))
        if not ok:
            raise AssertionError(name + ': ' + detail)

    source = "If you don't mind, I think I might want two glasses tomorrow."
    doc = nlp(source)
    det = detect_doc(doc, lex)
    spans = det['hedge_spans']
    check('main_subject_after_conditional', det['labels']['agent'] == 'speaker', str(det['labels']))
    check('longest_match_contracted_hedge', spans[0]['text'] == "If you do n't mind", str(spans))
    indices = [i for s in spans for i in s['token_ids']]
    check('hedge_nonoverlap', len(set(indices)) == len(indices) and len(spans) == 3, str(spans))
    check('number_word', det['labels']['quantity'] == ['two'], str(det['labels']))
    check('light_contraction', 'not' in compress_doc(doc, 'light')['words'], str(compress_doc(doc, 'light')))

    for text, expected in [("I wasn't feeling well.", ['past']),
                           ("I will be waiting.", ['future']),
                           ("Do not go.", [])]:
        got = detect_doc(nlp(text), lex)['labels']['time']
        check('tense:' + text, got == expected, str(got))

    for text, expected in [('Are you hungry?', 'question'),
                           ('When will you call me?', 'question'),
                           ('Could you help me?', 'request/command'),
                           ("I don't want to go.", 'refusal')]:
        got = detect_doc(nlp(text), lex)['labels']['speech_act']
        check('speech:' + text, got == expected, got)

    doc = nlp('Bring red fresh tasty apples and 3 oranges.')
    det = detect_doc(doc, lex)
    check('digit_quantity', det['labels']['quantity'] == ['3'], str(det['labels']))
    lost = cue_loss(det, compress_doc(doc, 'pos_cap4'))
    cost = chip_cost(lost)
    check('quantity_has_no_SPEC_chip', cost['min_chips'] is None and 'quantity:3' in cost['unrestorable'], str(cost))

    # Independent carrier positions, not membership in a string vocabulary.
    repeated = dict(cues=[dict(dimension='polarity', value='negated', carrier_ids=[3], evidence='not', kind='test', chip='[NOT]')])
    check('repeated_surface_not_false_survival', cue_loss(repeated, dict(words=['not'], token_ids=[1]))['lost']['polarity'], 'Only the wrong occurrence was retained.')

    two = dict(events=[dict(dimension='time', value='past', survives=False, chip='[PAST]')]*2)
    check('one_chip_per_category_not_occurrence', chip_cost(two)['min_chips'] == 1, str(chip_cost(two)))
    no_cues = chip_cost(dict(events=[]))
    check('no_explicit_loss_zero_chips', no_cues['min_chips'] == 0, str(no_cues))
    lo,hi=wilson(0,10)
    check('wilson_zero_endpoint', abs(lo) < 1e-12 and abs(hi-.2775328) < 1e-6, f'{lo}, {hi}')

    reference = Path.home() / 'aac-voice-preservation-old/src/compress.py'
    if reference.exists():
        # Avoid writing __pycache__ into the read-only reference project.
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(reference.parent))
        spec = importlib.util.spec_from_file_location('s1_legacy_compress_reference', reference)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        old._NLP = nlp
        mismatches = []
        rows = read_data()
        for r,doc in zip(rows, nlp.pipe((r['text'] for r in rows), batch_size=64)):
            actual = compress_doc(doc, 'pos_cap4')['words']
            expected = old.compress(r['text'], max_keywords=4)
            if actual != expected:
                mismatches.append(r['id'])
        check('legacy_compressor_all_messages', not mismatches, f'n={len(rows)}; mismatches={mismatches[:10]}')

    rows = read_data()
    metrics = pd.read_csv(OUT / 'message_metrics.csv')
    rates = pd.read_csv(OUT / 'loss_rates.csv')
    dist = pd.read_csv(OUT / 'chip_distribution.csv', dtype={'min_chips': str})
    sample = [json.loads(line) for line in (ROOT / 'data/specs/aactext_sample400.jsonl').read_text().splitlines()]
    check('sample400_unique_IDs', len(sample) == len({r['id'] for r in sample}) == 400, f'n={len(sample)}')
    check('all_message_compressor_pairs', len(metrics) == 3*len(rows) and not metrics.duplicated(['id','compressor']).any(), f'rows={len(metrics)}')
    for c in COMPRESSORS:
        subset = metrics[metrics.compressor == c]
        observed = int(subset.any_loss.sum())
        aggregate = int(rates[(rates.split == 'all') & (rates.compressor == c) & (rates.dimension == 'any')]['count'].iloc[0])
        check('aggregate_reconciliation:' + c, observed == aggregate, f'{observed} == {aggregate}')
        check('chip_distribution_reconciliation:' + c, int(dist[(dist.split == 'all') & (dist.compressor == c)]['count'].sum()) == len(rows), f'n={len(rows)}')
    # Verify the final artifacts refer to the exact original source records.
    lookup = {r['id']: r for r in rows}
    check('sample_text_and_split_integrity', all(lookup[r['id']]['text'] == r['text'] and lookup[r['id']]['split'] == r['split'] for r in sample), '400 original IDs/text/splits')
    pd.DataFrame(checks).to_csv(OUT / 'verification_checks.csv', index=False)
    print(f'{len(checks)} diagnostics passed.')


if __name__ == '__main__':
    main()

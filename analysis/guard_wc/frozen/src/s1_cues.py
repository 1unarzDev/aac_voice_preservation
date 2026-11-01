"""Deterministic, auditable AACText cue and keyword extraction (S1 pilot).

Use ``detect(text)`` or reuse a pipeline with ``detect_doc(doc, matcher)``.
No model calls, stochastic sampling, or access to the old project at runtime.
Each cue records its value, source token indices, surface evidence and SPEC chip.
Survival is a *token retention proxy*, not a claim of semantic recoverability:
all carrying tokens must be retained, by source position (not string membership,
which could accidentally credit another occurrence). A dimension is lost when
ANY of its detected cues is lost. Unmarked affirmative/plain/statement defaults
have no carrying token and do not create loss events. Scope is not resolved.

Multiword lexicon matches are longest-first, globally non-overlapping, using
spaCy's own tokenizer, including do/n't. Lexical hedge matches are exposed even
when excluded from epistemic certainty by contextual rules. ``revision=0`` is
the frozen initial detector; revision 1 includes the documented validation fix.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

DIMENSIONS = ('polarity', 'speech_act', 'agent', 'certainty', 'time', 'quantity', 'politeness')
COMPRESSORS = ('pos_cap4', 'pos_uncapped', 'light')
KEEP_POS = {'NOUN', 'PROPN', 'VERB', 'ADJ', 'NUM'}
NEGATION = {"not", "n't", 'never', 'no', 'nothing', 'nobody', 'none', 'neither',
            'nor', 'nowhere', 'without', 'cannot', 'cant', 'dont', 'wont', 'doesnt', 'didnt'}
BOOSTERS = {'definitely', 'really', 'sure', 'certainly', 'absolutely', 'indeed'}
TIME_WORDS = {
    'yesterday': 'past', 'ago': 'past', 'previously': 'past',
    'tomorrow': 'future', 'later': 'future', 'soon': 'future', 'tonight': 'future',
    'now': 'present', 'today': 'present', 'currently': 'present',
    **{w: 'unspecified' for w in ('morning', 'afternoon', 'evening', 'night', 'monday',
       'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'weekend',
       'christmas', 'noon', 'midnight')},
}
SOFT_PHRASES = ('could you', 'would you', 'would you mind', 'do you mind',
                'if possible', "if you don't mind", 'if you do not mind',
                'if you like', 'if you want', 'no rush', 'no pressure', 'excuse me',
                'i would like', "i'd like")


def load_nlp():
    """Load the installed English pipeline, excluding unused named entities."""
    import spacy
    return spacy.load('en_core_web_sm', disable=['ner'])


def norm(text):
    return text.lower().replace('’', "'")


class Lexicon:
    """Tokenized lexicon with deterministic longest-match non-overlap."""
    def __init__(self, nlp, path=None):
        path = Path(path or Path(__file__).with_name('s1_hedges.txt'))
        self.terms = [s.split('#', 1)[0].strip() for s in path.read_text().splitlines()]
        self.terms = [s for s in self.terms if s]
        self.patterns = sorted({tuple(norm(t.text) for t in nlp.make_doc(s))
                                for s in self.terms}, key=lambda p: (-len(p), p))
        self.soft_patterns = sorted({tuple(norm(t.text) for t in nlp.make_doc(s))
                                    for s in SOFT_PHRASES}, key=lambda p: (-len(p), p))

    @staticmethod
    def spans(doc, patterns):
        words = [norm(t.text) for t in doc]
        used, matches = set(), []
        for p in patterns:
            for i in range(len(words) - len(p) + 1):
                ids = tuple(range(i, i + len(p)))
                if not used.intersection(ids) and tuple(words[i:i + len(p)]) == p:
                    matches.append(ids)
                    used.update(ids)
        return sorted(matches)


@dataclass
class Cue:
    dimension: str
    value: str
    carrier_ids: list[int]
    evidence: str
    kind: str
    chip: str | None


def is_content(t):
    return (not t.is_space and not t.is_punct and t.pos_ in KEEP_POS
            and t.pos_ != 'AUX' and t.dep_ not in {'aux', 'auxpass'})


def compress_doc(doc, compressor='pos_cap4'):
    """Return words + source indices; light canonicalizes n't to not, uncapped.

    pos_cap4 exactly reproduces the old default rule, including please before
    truncation and repeated slots. No minimum-keyword exclusion is applied.
    pos_uncapped is strictly content POS. light adds only not/n't and please.
    """
    if compressor not in COMPRESSORS:
        raise ValueError(compressor)
    tokens = [t for t in doc if is_content(t) or
              (compressor != 'pos_uncapped' and norm(t.text) == 'please') or
              (compressor == 'light' and norm(t.text) in {'not', "n't"})]
    if compressor == 'pos_cap4':
        tokens = tokens[:4]
    return {'words': [('not' if compressor == 'light' and norm(t.text) == "n't"
                       else norm(t.text)) for t in tokens],
            'token_ids': [t.i for t in tokens]}


def detect_doc(doc, lexicon, revision=1):
    """Extract labels and explicit cue events; first sentence sets main role/act.

    Questions/requests take certainty=n/a; lexical hedge matches still appear in
    ``hedge_spans`` for sampling. Hedges that are clearly non-epistemic (physical
    feel, directional about/around, ability can, deontic should, habitual often,
    apologies) are not treated as uncertainty. This remains a pilot heuristic.
    Tense comes from the main predicate and its auxiliaries; explicit time words
    anywhere are added. Quantity keeps normalized number surfaces, not magnitudes.
    """
    words = [norm(t.text) for t in doc]
    text = norm(doc.text)
    cues = []

    def add(dim, value, ids, kind, chip):
        ids = sorted(set(ids))
        if ids:
            cues.append(Cue(dim, value, ids, ' '.join(doc[i].text for i in ids), kind, chip))

    if not len(doc):
        raise ValueError('empty message')
    sent = next(doc.sents)
    root = sent.root
    if revision:
        # spaCy sometimes promotes the last paratactic clause to ROOT. Prefer
        # the earliest grammatical subject's predicate, or a preceding explicit
        # imperative. This is source-based, not tied to validation row IDs.
        all_subjects = sorted([t for t in sent if t.dep_ in {'nsubj', 'nsubjpass', 'csubj'} and not any(
            child.dep_ == 'mark' and norm(child.text) in {'if', 'when', 'while', 'because', 'although', 'unless', 'before', 'after'}
            for child in t.head.children)], key=lambda t: t.i)
        if all_subjects:
            first_subject = all_subjects[0]
            root = first_subject.head
            preceding = [t for t in sent if t.i < first_subject.i and t.pos_ == 'VERB' and t.tag_ == 'VB']
            if preceding and norm(preceding[0].text) not in {'let'} and not any(
                    norm(t.text) in {'if', 'when', 'while', 'because', 'although', 'unless', 'before', 'after', 'why', 'how', 'what'}
                    for t in sent if t.i < preceding[0].i):
                root = preceding[0]
        elif root.pos_ == 'INTJ':
            root = next((t for t in sent if t.pos_ in {'VERB', 'AUX'}), root)
    subjects = sorted([t for t in root.children if t.dep_ in {'nsubj', 'nsubjpass', 'csubj'}], key=lambda t: t.i)
    subject = subjects[0] if subjects else None
    typo_future = revision and bool(re.match(r"\s*ill\s+be\b", text))
    typo_its = revision and bool(re.match(r"\s*its\s+(?:really\s+)?\w+ing\b", text))
    wh_copula = revision and bool(re.match(r"\s*(?:where|what|who|how|when)'s\b", text))
    if revision and subject is None and wh_copula and root.pos_ in {'NOUN', 'PROPN', 'PRON'}:
        subject = root
    if revision and subject is None and root.pos_ == 'AUX' and words[0] in {'what', 'which'}:
        subject = next((t for t in root.children if t.dep_ == 'attr'), None)
    if typo_its:
        subject = doc[0]
    lets = bool(re.match(r"\s*let(?:'s|s| us)\b", text))
    person = ('speaker' if typo_future else 'we/joint' if lets else 'speaker' if subject is not None and norm(subject.text) == 'i'
              else 'we/joint' if subject is not None and norm(subject.text) == 'we'
              else 'addressee' if subject is not None and norm(subject.text) == 'you'
              else 'third party' if subject is not None else 'unspecified')
    if lets:
        add('agent', person, [0, 1] if len(doc) > 1 and words[1] in {"'s", 'us'} else [0], 'lets_subject', '[WE]')
    elif subject is not None:
        add('agent', person, [subject.i], 'main_subject',
            {'speaker': '[I]', 'we/joint': '[WE]', 'addressee': '[YOU]', 'third party': '[THEY]'}[person])

    neg = [t for t in doc if t.dep_ == 'neg' or norm(t.text) in NEGATION]
    for t in neg:
        add('polarity', 'negated', [t.i], 'negation', '[NOT]')
    polarity = 'negated' if neg else 'affirmative'

    # Refusal needs volition/declining, not every negative assertion.
    refusal = bool(re.search(r"\bno[ ,]+thanks\b|\bi (?:do not|don't|dont) want\b|\bi (?:will not|won't|wont)\b", text)) or text.strip(' .!') == 'no'
    if revision:
        if re.search(r"\bi (?:won't|wont|will not) (?:be able|let you suffer)\b", text):
            refusal = False
        if re.match(r"\s*no[, ]+i (?:can't|cannot|cant)\b", text):
            refusal = True
    modal_you = re.search(r'\b(can|could|would|will) you\b', text)
    please = [t for t in doc if norm(t.text) == 'please']
    auxiliaries = [t for t in root.children if t.dep_ in {'aux', 'auxpass'}]
    inversion = subject is not None and any(t.i < subject.i for t in auxiliaries)
    if root.pos_ == 'AUX' and subject is not None and root.i < subject.i:
        inversion = True
    wh = next((t for t in sent if not t.is_punct and not t.is_space), root)
    wh_initial = norm(wh.text) in {'what', 'whats', 'who', 'whom', 'whose', 'when', 'where', 'why', 'how', 'which'}
    if revision and not wh_initial:
        clause_wh = next((t for t in root.children if t.tag_ in {'WRB', 'WP', 'WDT'} and t.i < root.i), None)
        if clause_wh is not None:
            wh = clause_wh
            wh_initial = True
    imperative = root.pos_ == 'VERB' and subject is None and root.tag_ == 'VB'
    desire_request = revision and bool(re.search(r"\bi (?:would|'d)\s+(?:(?:really|very much)\s+)?like\b|\bi'd\s+(?:really\s+)?like\b", text))
    if revision:
        # Wh-initial time questions are not requests just because they contain
        # "will you". Greeting formulas are not imperatives; need is ambiguous.
        if wh_initial:
            modal_you = None
            imperative = False
        if subject is None and root.i <= 1 and norm(root.text) in {'read', 'write', 'stop', 'watch', 'call', 'email', 'give', 'go', 'come', 'tell', 'take', 'help'}:
            imperative = True
        if norm(root.text) in {'need', 'thank'} or re.match(r'\s*have (?:a |an )?(?:good|great|nice|lovely)\b', text):
            imperative = False
    act = ('refusal' if refusal else 'request/command' if please or modal_you or lets or imperative
           else 'question' if '?' in text or inversion or wh_initial else 'statement')
    if desire_request:
        act = 'request/command'
    if act == 'refusal':
        add('speech_act', act, [t.i for t in neg[:1]] + [t.i for t in doc if t.lemma_ == 'want'][:1], 'refusal', '[REFUSE]')
    elif act == 'request/command':
        if please:
            ids = [please[0].i]
        elif modal_you:
            ids = [t.i for t in doc if t.idx >= modal_you.start() and t.idx < modal_you.end()]
        elif desire_request:
            ids = [t.i for t in doc if norm(t.text) in {'would', "'d", 'like'}][:2]
        else:
            ids = [root.i]
        add('speech_act', act, ids, 'request_form', '[ASK]')
    elif act == 'question':
        # Alternative question markers each carry the same value. One retained
        # marker suffices (represented as one event with preferred wh carrier).
        ids = [wh.i] if wh_initial else [t.i for t in doc if t.text == '?'][:1]
        if not ids:
            ids = [t.i for t in auxiliaries if subject is not None and t.i < subject.i][:1] or [root.i]
        add('speech_act', act, ids, 'question_form', '[?]')

    hedge_spans = lexicon.spans(doc, lexicon.patterns)
    soft_spans = lexicon.spans(doc, lexicon.soft_patterns)
    if desire_request and not any('like' in [words[i] for i in ids] for ids in soft_spans):
        soft_spans.append(tuple(t.i for t in doc if norm(t.text) in {'i', 'would', "'d", 'like'}))
    epistemic = []
    for ids in hedge_spans:
        phrase = ' '.join(words[i] for i in ids)
        # Retain the full lexicon output as a feature, qualify its interpretation.
        excluded = {'can', 'should', 'sorry', 'about', 'around', 'often', 'sometimes',
                    'usually', 'typically', 'only', 'just', 'merely', 'simply',
                    'barely', 'hardly', 'feel', 'feels', 'a little', 'a bit'}
        if phrase in excluded:
            continue
        if phrase == 'would' and any(w in words for w in {'like', 'love', 'prefer'}):
            continue
        epistemic.append(ids)
    emphatic = [t for t in doc if norm(t.text) in BOOSTERS]
    # A booster inside a longer hedge ("I'm not sure") must not become certainty.
    hedge_ids = {i for ids in hedge_spans if len(ids) > 1 for i in ids}
    emphatic = [t for t in emphatic if t.i not in hedge_ids]
    certainty = ('n/a (question/request)' if act in {'question', 'request/command'}
                 else 'hedged/uncertain' if epistemic else 'strongly certain/emphatic' if emphatic
                 else 'plain assertion')
    if certainty != 'n/a (question/request)':
        for ids in epistemic:
            add('certainty', 'hedged/uncertain', ids, 'hedge', '[MAYBE]')
        for t in emphatic:
            add('certainty', 'strongly certain/emphatic', [t.i], 'booster', '[SURE]')

    for ids in soft_spans:
        add('politeness', 'softened request', ids, 'softener', None)
    for t in please:
        add('politeness', 'please', [t.i], 'please', '[PLEASE]')
    for t in doc:
        if norm(t.text) in {'thank', 'thanks', 'sorry', 'apologies'}:
            add('politeness', 'thanks/apology', [t.i], 'thanks_apology', None)
    politeness_values = {c.value for c in cues if c.dimension == 'politeness'}
    politeness = next((v for v in ('please', 'softened request', 'thanks/apology') if v in politeness_values), 'none')

    predicate = [root] + auxiliaries
    future = [t for t in predicate if norm(t.text) in {'will', "'ll", 'wo', 'shall'}]
    for t in future:
        add('time', 'future', [t.i], 'future_aux', '[LATER]')
    for t in predicate:
        tense = t.morph.get('Tense')
        # Modal could/would are not past events; don't infer past from their tag.
        if t.tag_ == 'MD' or future:
            continue
        if revision and (act == 'request/command' and imperative or
                         'Fin' not in t.morph.get('VerbForm')):
            continue
        if 'Past' in tense:
            add('time', 'past', [t.i], 'morph_tense', '[PAST]')
        elif 'Pres' in tense:
            add('time', 'present', [t.i], 'morph_tense', '[NOW]')
    if typo_future:
        add('time', 'future', [0], 'nonstandard_ill_be', '[LATER]')
    if typo_its:
        add('time', 'present', [0], 'nonstandard_its_progressive', '[NOW]')
    if wh_copula and not any(c.dimension == 'time' for c in cues):
        add('time', 'present', [t.i for t in doc if norm(t.text) == "'s"][:1], 'contracted_wh_copula', '[NOW]')
    for t in doc:
        w = norm(t.text)
        if w in TIME_WORDS:
            value = TIME_WORDS[w]
            prev = words[t.i - 1] if t.i else ''
            if prev == 'last':
                value = 'past'
            elif prev == 'next':
                value = 'future'
            add('time', value, [t.i] + ([t.i - 1] if prev in {'last', 'next'} else []),
                'time_word', {'past': '[PAST]', 'present': '[NOW]', 'future': '[LATER]'}.get(value))
        if t.like_num or t.pos_ == 'NUM':
            add('quantity', w, [t.i], 'number', None)
    labels = dict(polarity=polarity, speech_act=act, agent=person, certainty=certainty,
                  time=sorted({c.value for c in cues if c.dimension == 'time'}),
                  quantity=sorted({c.value for c in cues if c.dimension == 'quantity'}),
                  politeness=politeness)
    return {'labels': labels, 'cues': [asdict(c) for c in cues],
            'hedge_spans': [{'token_ids': list(ids), 'text': ' '.join(doc[i].text for i in ids)} for ids in hedge_spans]}


def cue_loss(detection, keywords):
    """Per-event survival and per-dimension presence/any-loss booleans."""
    kept = set(keywords['token_ids'])
    events = [dict(c, survives=set(c['carrier_ids']).issubset(kept)) for c in detection['cues']]
    return {'events': events,
            'present': {d: any(c['dimension'] == d for c in events) for d in DIMENSIONS},
            'lost': {d: any(c['dimension'] == d and not c['survives'] for c in events) for d in DIMENSIONS}}


def chip_cost(loss):
    """Exact minimum for restorable *category values*, else no finite solution.

    One selection can restore a value shared by multiple lost cue events. A
    retained event with the same dimension/value already restores that category;
    we still report its other token losses in the loss metric. ASK and PLEASE
    encode different dimensions and each needs its own chip. Softened request is
    not exactly synonymous with PLEASE, and quantities have no SPEC chip.
    """
    retained = {(c['dimension'], c['value']) for c in loss['events'] if c['survives']}
    missing = [c for c in loss['events'] if not c['survives'] and
               (c['dimension'], c['value']) not in retained]
    unsupported = sorted({c['dimension'] + ':' + c['value'] for c in missing if c['chip'] is None})
    chips = sorted({c['chip'] for c in missing if c['chip'] is not None})
    return {'chips': chips, 'covered_chip_count': len(chips),
            'min_chips': None if unsupported else len(chips),
            'unrestorable': unsupported, 'fully_restorable': not unsupported}


def detect(text, nlp=None, lexicon=None, revision=1):
    """Convenient single-message interface (batch callers should reuse nlp)."""
    nlp = nlp or load_nlp()
    return detect_doc(nlp(text), lexicon or Lexicon(nlp), revision)

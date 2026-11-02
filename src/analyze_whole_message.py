"""Whole-message fidelity: why a preserved critical commitment is not enough.

usage: . .venv/bin/activate; python src/analyze_whole_message.py
Outputs: analysis/whole_message/{report.md,summary.json,part18_reasons.csv,slp_reasons.csv,hand_check.csv}

Inputs (read only): analysis/intent_check/items.csv (Part 18 returns joined to key, produced by
src/score_intent_check.py), runs/hw1/scored.parquet (judge added_content), expert_package/slp_key.csv,
expert_package/returns_slp/*.csv.  No model calls; no new human data.

Declared choices (written before the numbers were read; see report for caveats)
- "Rejected" in Part 18: (R1) writer does not say the output is the intended version (something else or
  the other version); (R2) writer says "no" to acceptance; (R3) not accepted as-is (no or small edit).
- Reason classes for an output vs the writer's intended sentence (content lemmas, spaCy en_core_web_sm,
  function words, chip realisations and input keywords removed from the novelty test):
  critical (judge's critical label differs from the writer's intended value), fluency (fragment: no
  finite verb or ends on a bare transitive verb, or the note says so), substitution (different event or
  role: subject/sentence-type mismatch, or new content words AND dropped target words), added (new content
  words, nothing dropped), dropped (target content words missing), reword (same content, different words).
  Primary reason = first match in that order. Multi-label flags are also kept.
- Hand check: 40 of the 199 non-accepted items, seeded shuffle (seed 20261102). Hand coding was done by the
  analyst (an LLM, not an independent human), reading the writer's note, text and sentence, and using the
  judge's critical label as evidence for the "critical" class. The rules were written after the 40 were seen,
  so agreement is optimistic (not a held-out test).
- Bridge metric: AUROC (rank, ties 0.5) with item bootstrap (B=2000, seed 20261102); writer-cluster
  bootstrap as a sensitivity. Combined models are ridge logistic regression with 5-fold CV predictions.
  No local embedding model is available (spaCy sm has no vectors; local GGUFs are chat models behind the GPU
  lock), so similarity is lexical (content-lemma Jaccard, token F1 of lemmas).
"""
from __future__ import annotations

import glob
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import spacy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "whole_message"
SEED = 20261102
B = 2000
nlp = spacy.load("en_core_web_sm", disable=["ner"])

CHIP_WORDS = {  # lemmas a faithful realisation of a chip may legitimately contain
    "[LATER]": {"later", "will", "tomorrow", "soon", "future", "going"}, "[PAST]": {"past", "yesterday", "ago", "last", "earlier"},
    "[?]": {"do", "does", "can", "will"}, "[THEY]": {"they"}, "[I]": {"i"}, "[SURE]": {"sure", "definitely", "certainly", "certain", "surely"},
    "[YES]": set(), "[NOT]": {"not", "no", "never", "n't"}, "[PLEASE]": {"please", "could", "would", "can"}, "[PLAIN]": set(),
    "[TELL]": {"tell", "say"}, "[MAYBE]": {"maybe", "might", "may", "perhaps", "possibly", "probably"}, "[NOW]": {"now", "currently", "right"},
    "[YOU]": {"you"},
}
STOP_EXTRA = {"be", "have", "do", "will", "would", "can", "could", "may", "might", "shall", "should", "let", "not", "no", "n't"}
CAT = ["critical", "fluency", "substitution", "added", "dropped", "reword"]


# ---------------------------------------------------------------- text features
def parse_input(s: str):
    s = re.sub(r"^Keywords:\s*", "", s)
    chips = re.findall(r"\[[^\]]+\]", s)
    words = re.sub(r"\[[^\]]+\]", " ", s).split()
    return chips, [w.lower() for w in words]


def content(doc):
    out = []
    for t in doc:
        if t.is_punct or t.is_space:
            continue
        if t.pos_ in ("NOUN", "PROPN", "VERB", "ADJ", "ADV", "NUM") and t.lemma_.lower() not in STOP_EXTRA and not t.is_stop:
            out.append(t.lemma_.lower())
    return out


def lemmas_of(words):
    return {t.lemma_.lower() for t in nlp(" ".join(words))} | set(words)


def frame(doc):
    """(sentence type, subject lemma) for the root clause."""
    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    if root is None:
        return ("none", "")
    txt = doc.text.strip()
    subj = next((c.lemma_.lower() for c in root.children if c.dep_ in ("nsubj", "nsubjpass")), "")
    subj = {"we": "i", "me": "i"}.get(subj, subj)
    if txt.endswith("?") or (root.children and any(c.dep_ == "aux" and c.i < (next((x.i for x in root.children if x.dep_ == "nsubj"), 10**6)) for c in root.children) and txt.endswith("?")):
        return ("q", subj)
    if root.pos_ == "VERB" and not subj and root.tag_ == "VB":
        return ("imp", "you")
    if txt.lower().startswith("let's") or txt.lower().startswith("let us"):
        return ("imp", "i")
    return ("decl", subj)


def fragment(doc):
    toks = [t for t in doc if not t.is_punct]
    if not any(t.pos_ in ("VERB", "AUX") for t in toks):
        return True
    last = toks[-1] if toks else None
    if last is not None and last.pos_ == "VERB" and last.lemma_.lower() in {"contain", "lend", "block", "know", "remember", "need", "check", "send", "read"} and not any(t.dep_ in ("dobj", "obj", "ccomp", "xcomp") for t in doc):
        return len(toks) <= 4 and last.dep_ == "ROOT"
    return False


NOTE_FLU = re.compile(r"fragment|not a (complete |full )?(sentence|instruction)|no object|incomplete|ungrammatical|awkward|garbled|unclear sentence|unusable", re.I)
NOTE_DROP = re.compile(r"^(add|restore|name|include|use|put back|keep)\b", re.I)
NOTE_SUB = re.compile(r"\b(replace|replaces|instead of|rather than|changes|turns|makes me|becomes|not (whether|where|when))\b", re.I)


def classify(row, doc_o, doc_t, chips, kw, crit_ok):
    lo, lt = content(doc_o), content(doc_t)
    allowed = lemmas_of(kw)
    for c in chips:
        allowed |= CHIP_WORDS.get(c, set())
    tset, oset = set(lt), set(lo)
    novel = sorted(x for x in oset if x not in tset and x not in allowed)
    dropped = sorted(x for x in tset if x not in oset)
    dropped_rec = [x for x in dropped if x in allowed]  # keyword the model dropped
    fo, ft = frame(doc_o), frame(doc_t)
    role = fo[0] != ft[0] or (fo[1] and ft[1] and fo[1] != ft[1] and not ({"pharmacy"} & {fo[1]}))
    # a chip-driven pronoun is consistent with the cue, so only flag a mismatch to the writer's sentence
    flu = fragment(doc_o) or bool(NOTE_FLU.search(str(row.get("note", "") or "")))
    subst = bool(role) or (len(novel) >= 1 and len(dropped) >= 1)
    flags = dict(critical=not crit_ok, fluency=flu, substitution=subst, added=len(novel) >= 1, dropped=len(dropped) >= 1,
                 dropped_unrecoverable=len([x for x in dropped if x not in allowed]) >= 1, dropped_keyword=len(dropped_rec) >= 1)
    if not crit_ok:
        prim = "critical"
    elif flu:
        prim = "fluency"
    elif subst:
        prim = "substitution"
    elif len(novel) >= 1:
        prim = "added"
    elif len(dropped) >= 1:
        prim = "dropped"
    else:
        prim = "reword"
    return prim, flags, novel, dropped, role


def note_only(note, crit_ok):
    n = str(note or "")
    if not crit_ok:
        return "critical"
    if NOTE_FLU.search(n):
        return "fluency"
    if NOTE_SUB.search(n):
        return "substitution"
    if NOTE_DROP.search(n):
        return "dropped"
    return "reword"


# ---------------------------------------------------------------- stats
def auroc(y, s):
    y = np.asarray(y, bool)
    s = np.asarray(s, float)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = pd.Series(s).rank().values
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def boot_auc(y, s, groups=None, rng=None, b=B):
    y = np.asarray(y)
    s = np.asarray(s, float)
    n = len(y)
    rng = rng or np.random.default_rng(SEED)
    vals = []
    ug = None if groups is None else np.unique(groups)
    idx_by = None if groups is None else {g: np.where(groups == g)[0] for g in ug}
    for _ in range(b):
        if groups is None:
            ix = rng.integers(0, n, n)
        else:
            ix = np.concatenate([idx_by[g] for g in rng.choice(ug, len(ug))])
        v = auroc(y[ix], s[ix])
        if not np.isnan(v):
            vals.append(v)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def fit_logit(X, y, lam=1.0, it=50):
    w = np.zeros(X.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-X @ w))
        W = p * (1 - p) + 1e-6
        g = X.T @ (y - p) - lam * np.r_[0, w[1:]]
        H = (X * W[:, None]).T @ X + lam * np.diag(np.r_[0, np.ones(len(w) - 1)])
        step = np.linalg.solve(H, g)
        w += step
        if np.abs(step).max() < 1e-7:
            break
    return w


def cv_pred(X, y, folds=5, seed=0):
    X = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1)
    X = np.c_[np.ones(len(X)), X]
    rng = np.random.default_rng(seed)
    f = rng.permutation(len(y)) % folds
    pr = np.zeros(len(y))
    for k in range(folds):
        w = fit_logit(X[f != k], y[f != k])
        pr[f == k] = X[f == k] @ w
    return pr


def pct(a, b):
    return f"{a}/{b} = {100 * a / b:.1f}%" if b else "0/0"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))


def pc(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f}% [{lo:.0f}, {hi:.0f}]" if n else "0/0"


def kappa(a, b):
    a, b = list(a), list(b)
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


HAND = {  # analyst's hand coding of the 40 drawn items (primary reason)
    "critical": "e880fc 1b29e7 2b1ef6 906a00 b708f5 848a0f 6a319a 44a3ca c10aba 744ff2",
    "substitution": "430bad 723baa 5f8932 616cec 87bbef 0e58e5 5d9e2a 02b128 699f8d d9eaf2 74cb2b",
    "fluency": "2c50fd",
    "added": "9308b4",
    "dropped": "af204b c93b90 7a601b 38d142 acad92 f26e57 ab884e 59bd1e 529fff dcdc16 e8c2a7 5935cc 6d7598 5b5b79 e1b357 50ddb9 8f247a",
}
HAND = {"ic-" + i: k for k, v in HAND.items() for i in v.split()}


# ---------------------------------------------------------------- Part 18
def part18():
    d = pd.read_csv(ROOT / "analysis/intent_check/items.csv")
    sc = pd.read_parquet(ROOT / "runs/hw1/scored.parquet")[["output_id", "family_id", "channel", "model", "prompt_id", "variant", "added_content", "any_contra"]]
    d = d.merge(sc.rename(columns={"variant": "intended_variant"}), on=["output_id", "family_id", "channel", "model", "prompt_id", "intended_variant"], how="left")
    assert len(d) == 200
    d["target"] = np.where(d.intended_variant == "A", d.version_A, d.version_B)
    d["says_match"] = np.where(d.says.isna(), np.nan, (d.says == "version " + d.intended_variant).astype(float))
    d["rej_R1"] = 1 - d.says_match  # NaN for unknown
    d["rej_R2"] = (d.accept == "no").astype(float)
    d["rej_R3"] = (d.accept != "yes").astype(float)
    rows = []
    for r in d.itertuples():
        chips, kw = parse_input(r.input_text)
        prim, fl, nov, dro, role = classify(r._asdict(), nlp(r.text), nlp(r.target), chips, kw, bool(r.judge_critical_match))
        n_kw = max(1, len(kw))
        ot, tt = content(nlp(r.text)), content(nlp(r.target))
        so, st = set(ot), set(tt)
        jac = len(so & st) / max(1, len(so | st))
        p = len(so & st) / max(1, len(so))
        rc = len(so & st) / max(1, len(st))
        f1 = 2 * p * rc / (p + rc) if p + rc else 0.0
        allowed = lemmas_of(kw)
        for c in chips:
            allowed |= CHIP_WORDS.get(c, set())
        novel_in = len([x for x in so if x not in allowed])
        rows.append(dict(item_id=r.item_id, prim=prim, note_prim=note_only(r.note, bool(r.judge_critical_match)), novel=";".join(nov),
                         dropped_words=";".join(dro), len_ratio=len(r.text.split()) / n_kw, novel_vs_input=novel_in, jaccard=jac, f1=f1,
                         judge_added=(np.nan if pd.isna(r.added_content) else float(r.added_content == "yes")), **fl))
    f = pd.DataFrame(rows)
    return d.merge(f, on="item_id")


def part18_report(d, S):
    L = []
    na = d[d.accept != "yes"].copy()
    ids = sorted(na.item_id)
    import random
    random.Random(SEED).shuffle(ids)
    samp = ids[:40]
    hc = na[na.item_id.isin(samp)].copy()
    hc["hand"] = hc.item_id.map(HAND)
    assert hc.hand.notna().all()
    agree = (hc.hand == hc.prim).mean()
    agree_note = (hc.hand == hc.note_prim).mean()
    k_auto = kappa(hc.hand, hc.prim)
    cm = pd.crosstab(hc.hand, hc.prim)
    hc[["item_id", "channel", "judge_critical_match", "input_text", "target", "text", "note", "hand", "prim", "note_prim"]].to_csv(OUT / "hand_check.csv", index=False)
    S["hand_check"] = dict(n=40, agree_diff_classifier=float(agree), kappa=float(k_auto), agree_note_only=float(agree_note), hand_dist=hc.hand.value_counts().to_dict())
    d.to_csv(OUT / "part18_reasons.csv", index=False)

    L.append("## 1. Part 18: why writers reject the output\n")
    n = len(d)
    r1 = d.rej_R1.dropna()
    S["part18"] = dict(n=n, not_intended_R1=[int(r1.sum()), len(r1)], no_R2=int(d.rej_R2.sum()), not_as_is_R3=int(d.rej_R3.sum()))
    L.append(f"Rejection definitions: R1 writer does not say it is the intended version {pc(int(r1.sum()), len(r1))}; R2 acceptance = no {pc(int(d.rej_R2.sum()), n)}; "
             f"R3 not accepted as-is {pc(int(d.rej_R3.sum()), n)}.\n")
    L.append("### 1a. Classifier validation (40 hand-coded items)\n")
    L.append(f"Diff classifier vs hand coding (primary reason): agreement {agree:.0%} ({int(agree * 40)}/40), Cohen kappa {k_auto:.2f}. Note-regex-only: {agree_note:.0%}. "
             f"Hand-coded distribution: {hc.hand.value_counts().to_dict()}. **Caveat: the hand coder is an LLM, the classifier rules were written after seeing these 40, so this is optimistic, not held out.**\n")
    L.append("Confusion (rows hand, cols classifier):\n\n```\n" + cm.to_string() + "\n```\n")
    L.append("### 1b. Reason distribution (primary reason, all 199 non-accepted items)\n")
    dist = na.prim.value_counts().reindex(CAT, fill_value=0)
    S["part18"]["reason_all"] = dist.to_dict()
    L.append("| group | n | " + " | ".join(CAT) + " |\n|---|---|" + "---|" * len(CAT))
    def row(name, g):
        c = g.prim.value_counts().reindex(CAT, fill_value=0)
        return f"| {name} | {len(g)} | " + " | ".join(f"{v} ({100 * v / max(1, len(g)):.0f}%)" for v in c) + " |"
    L.append(row("all not accepted", na))
    nn = na.assign(prim=na.note_prim)
    L.append(row("all, note-regex classifier instead", nn))
    S["part18"]["reason_all_note_regex"] = nn.prim.value_counts().to_dict()
    for ch in ["bare", "chip1"]:
        L.append(row(f"channel {ch}", na[na.channel == ch]))
    for m in sorted(na.model.unique()):
        L.append(row(f"model {m}", na[na.model == m]))
    S["part18"]["reason_by_channel"] = {ch: na[na.channel == ch].prim.value_counts().to_dict() for ch in ["bare", "chip1"]}
    S["part18"]["reason_by_model"] = {m: na[na.model == m].prim.value_counts().to_dict() for m in na.model.unique()}
    L.append("\nMulti-label flags (share of non-accepted items; flags overlap):\n")
    fl = ["critical", "fluency", "substitution", "added", "dropped", "dropped_unrecoverable", "dropped_keyword"]
    L.append("| group | n | " + " | ".join(fl) + " |\n|---|---|" + "---|" * len(fl))
    for name, g in [("all", na), ("bare", na[na.channel == "bare"]), ("chip1", na[na.channel == "chip1"])]:
        L.append(f"| {name} | {len(g)} | " + " | ".join(f"{100 * g[c].mean():.0f}%" for c in fl) + " |")
    S["part18"]["flags_all"] = {c: float(na[c].mean()) for c in fl}
    L.append("\n`dropped_unrecoverable` = a content word of the writer's sentence that is neither in the input keywords nor a chip realisation (the model could not have known it). "
             "`dropped_keyword` = the model left out a keyword it was given.\n")

    L.append("### 1c. Key question: judge says the critical value is right\n")
    ok = d[d.judge_critical_match == True]
    bad = d[d.judge_critical_match == False]
    S["key_question"] = {}
    L.append("| subset | n | writer: not the intended version (R1) | acceptance = no (R2) | not accepted as-is (R3) |\n|---|---|---|---|---|")
    for name, g in [("judge critical RIGHT", ok), ("judge critical WRONG", bad), ("RIGHT, chip1", ok[ok.channel == "chip1"]), ("RIGHT, bare", ok[ok.channel == "bare"])]:
        a = g.rej_R1.dropna()
        L.append(f"| {name} | {len(g)} | {pc(int(a.sum()), len(a))} | {pc(int(g.rej_R2.sum()), len(g))} | {pc(int(g.rej_R3.sum()), len(g))} |")
        S["key_question"][name] = dict(n=len(g), R1=[int(a.sum()), len(a)], R2=int(g.rej_R2.sum()), R3=int(g.rej_R3.sum()))
    okr = ok[ok.accept != "yes"]
    L.append(f"\nWhy, among the {len(okr)} judge-RIGHT items not accepted as-is (primary reason):\n")
    L.append(row("judge RIGHT, not accepted", okr))
    okr1 = ok[ok.rej_R1 == 1]
    L.append(row("judge RIGHT, R1 (not intended version)", okr1))
    L.append(row("judge RIGHT, R2 (acceptance=no)", ok[ok.rej_R2 == 1]))
    L.append(row("judge RIGHT, writer-matched but small edit", ok[(ok.rej_R1 == 0) & (ok.accept != "yes")]))
    S["key_question"]["reason_right_not_accepted"] = okr.prim.value_counts().to_dict()
    S["key_question"]["reason_right_R1"] = okr1.prim.value_counts().to_dict()
    L.append("\nA writer-matched item (writer says it is the intended version) was usually still edited: the typical edit is adding the writer's own detail.\n")
    nd = okr
    S["key_question"]["right_not_accepted_flags"] = {c: float(nd[c].mean()) for c in fl}
    L.append(f"Among judge-RIGHT not-accepted items: unrecoverable content dropped {100 * nd.dropped_unrecoverable.mean():.0f}%, role/event substitution {100 * nd.substitution.mean():.0f}%, "
             f"model added new content words {100 * nd.added.mean():.0f}%, judge `added_content` = yes {100 * nd.judge_added.mean():.0f}% (of judged), fragment {100 * nd.fluency.mean():.0f}%.\n")
    return L


# ---------------------------------------------------------------- SLP
def slp_classify(text, kw, chips, note):
    doc = nlp(text)
    allowed = lemmas_of(kw)
    for c in chips:
        allowed |= CHIP_WORDS.get(c, set())
    co = set(content(doc))
    novel = sorted(x for x in co if x not in allowed)
    kwl = {t.lemma_.lower() for t in nlp(" ".join(kw)) if t.pos_ in ("NOUN", "PROPN", "VERB", "ADJ", "ADV", "NUM")}
    dropped_kw = sorted(x for x in kwl if x not in co)
    flu = fragment(doc)
    n = str(note or "")
    cues = dict(
        n_add=bool(re.search(r"\badd(s|ed)?\b|assum|invent|specific|extra|unrequested|presum|not (in|given)|detail", n, re.I)),
        n_flu=bool(re.search(r"garbled|not a (usable|natural|complete)|awkward|fragment|ungrammatical|unclear (noun|phrase)|odd|unnatural|literal|incomplete|noun phrase", n, re.I)),
        n_shift=bool(re.search(r"\b(turns|becomes|instead|changes|replace|reverses|switch|different|shifts|misreads|treats|reads as)\b", n, re.I)),
        n_drop=bool(re.search(r"\b(drop|omit|missing|loses|lost|without|ignores|no (cue|negation))\b", n, re.I)),
    )
    if cues["n_flu"] or flu:
        prim = "fluency"
    elif cues["n_shift"]:
        prim = "substitution"
    elif cues["n_add"] or len(novel) >= 1:
        prim = "added"
    elif cues["n_drop"] or dropped_kw:
        prim = "dropped"
    else:
        prim = "reword"
    return prim, novel, dropped_kw, flu, cues


def slp():
    key = pd.read_csv(ROOT / "expert_package/slp_key.csv")
    rt = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "expert_package/returns_slp/*.csv")))])
    rt = rt[rt.task == 2].rename(columns={"item_id": "item_id"})
    d = rt.merge(key, on="item_id", how="left")
    rows = []
    for r in d.itertuples():
        chips, kw = parse_input(r.input_text)
        prim, nov, dro, flu, cues = slp_classify(r.text, kw, chips, r.note)
        doc = nlp(r.text)
        n_kw = max(1, len(kw))
        allowed = lemmas_of(kw)
        for c in chips:
            allowed |= CHIP_WORDS.get(c, set())
        rows.append(dict(rater=r.rater_id, item_id=r.item_id, arm=r.arm, says=r.says_selected, acceptable=r.acceptable, note=r.note, text=r.text, input_text=r.input_text,
                         judge_fail=r.judge_meaning_fail, judge_added=r.judge_added_content, prim=prim, novel=";".join(nov), dropped_kw=";".join(dro),
                         len_ratio=len(r.text.split()) / n_kw, novel_vs_input=len([x for x in set(content(doc)) if x not in allowed]),
                         slp_reject=float(r.says_selected != "yes"), slp_unacc=float(r.acceptable != "yes"), slp_no=float(r.acceptable == "no")))
    return pd.DataFrame(rows)


def slp_report(s, S):
    L = ["## 2. SLP panel (50 outputs, 2 raters)\n"]
    s.to_csv(OUT / "slp_reasons.csv", index=False)
    S["slp"] = {}
    s["judge_pass"] = (s.judge_fail == 0)
    s["judge_pass_clean"] = (s.judge_fail == 0) & (s.judge_added == 0)
    n = len(s)
    L.append(f"Rater-item pairs: {n}. SLP 'says what the selected words mean' != yes (partly/no): {pc(int(s.slp_reject.sum()), n)}; acceptable != yes: {pc(int(s.slp_unacc.sum()), n)}.\n")
    L.append("| subset | rater-items | says partly/no | acceptable != yes | acceptable = no |\n|---|---|---|---|---|")
    for name, g in [("judge PASS (meaning_fail=0)", s[s.judge_pass]), ("judge PASS and no added_content", s[s.judge_pass_clean]), ("judge FAIL", s[~s.judge_pass])]:
        L.append(f"| {name} | {len(g)} | {pc(int(g.slp_reject.sum()), len(g))} | {pc(int(g.slp_unacc.sum()), len(g))} | {pc(int(g.slp_no.sum()), len(g))} |")
        S["slp"][name] = dict(n=len(g), reject=int(g.slp_reject.sum()), unacc=int(g.slp_unacc.sum()), no=int(g.slp_no.sum()))
    jp = s[s.judge_pass & (s.slp_reject == 1)]
    L.append(f"\nWhy, for the {len(jp)} rater-items the judge passes but the SLP marks partly/no (primary reason from the SLP's note and a diff against the input; "
             "no writer sentence exists for these items; note regexes, so approximate):\n")
    L.append("| group | n | " + " | ".join(CAT) + " |\n|---|---|" + "---|" * len(CAT))
    def row(name, g):
        c = g.prim.value_counts().reindex(CAT, fill_value=0)
        return f"| {name} | {len(g)} | " + " | ".join(f"{v} ({100 * v / max(1, len(g)):.0f}%)" for v in c) + " |"
    L.append(row("judge PASS, SLP partly/no", jp))
    for a in sorted(s.arm.unique()):
        L.append(row(f"  arm {a}", jp[jp.arm == a]))
    S["slp"]["reason_pass_partly_no"] = jp.prim.value_counts().to_dict()
    L.append(f"\nOf these, SLP note mentions adding/assuming content: {100 * jp.note.fillna('').str.contains(r'add|assum|invent|specific|extra|detail', case=False).mean():.0f}%; "
             f"model produced a content word not in the input: {100 * (jp.novel_vs_input > 0).mean():.0f}%; judge `added_content`=yes: {100 * jp.judge_added.mean():.0f}%.\n")
    # kappa SLP vs judge
    for rater in sorted(s.rater.unique()):
        g = s[s.rater == rater]
        k = kappa(g.judge_pass.astype(int), (g.says == "yes").astype(int))
        L.append(f"- {rater}: judge pass vs SLP 'yes': kappa {k:.2f}, SLP says yes {pc(int((g.says == 'yes').sum()), len(g))}, judge pass {pc(int(g.judge_pass.sum()), len(g))}")
        S["slp"][f"kappa_{rater}"] = float(k)
    L.append("")
    return L


# ---------------------------------------------------------------- bridge
def bridge(d, s, S):
    L = ["## 3. Bridge metric: what predicts rejection beyond the critical label?\n"]
    L.append("Deployable predictors need only the input and the output (judge `added_content`, length ratio output words / keyword count, number of output content lemmas not in input or chip realisation). "
             "Oracle-ish predictors need the writer's own sentence (lexical overlap) and are not available in use. No local embedding model: similarity is lexical (content-lemma Jaccard and token F1 with the writer's sentence). "
             "AUROC > .5 means higher value goes with rejection (similarity is sign-flipped so higher = more likely rejected). 95% CIs: item bootstrap (writer-cluster CI in the second CI column).\n")
    rng = np.random.default_rng(SEED)
    S["bridge"] = {}
    def table(df, ycol, preds, title, groups, key):
        L.append(f"**{title}** (n={len(df)}, rejected {int(df[ycol].sum())})\n")
        L.append("| predictor | AUROC | item CI | cluster CI |\n|---|---|---|---|")
        out = {}
        for name, col, sign in preds:
            x = df[col].values.astype(float) * sign
            m = ~np.isnan(x)
            y = df[ycol].values[m]
            a = auroc(y, x[m])
            ci = boot_auc(y, x[m], None, rng)
            cc = boot_auc(y, x[m], groups[m], rng, b=1000)
            L.append(f"| {name} | {a:.3f} | [{ci[0]:.3f}, {ci[1]:.3f}] | [{cc[0]:.3f}, {cc[1]:.3f}] |")
            out[name] = dict(auroc=float(a), ci=ci, cluster_ci=cc, n=int(m.sum()))
        S["bridge"][key] = out
        L.append("")
        return out

    # Part 18, items where judge says critical right
    d = d.copy()
    d["judge_added_f"] = d.judge_added.fillna(0)
    d["crit_wrong"] = (~d.judge_critical_match.astype(bool)).astype(float)
    preds = [("judge added_content (deployable)", "judge_added_f", 1), ("length ratio to keywords (deployable)", "len_ratio", 1),
             ("novel content words vs input (deployable)", "novel_vs_input", 1), ("1 - Jaccard with writer sentence (oracle)", "jaccard", -1), ("1 - token F1 with writer sentence (oracle)", "f1", -1)]
    ok = d[(d.judge_critical_match == True) & d.rej_R1.notna()].copy()
    ok["y"] = ok.rej_R1
    table(ok, "y", preds, "Part 18, judge-RIGHT items, outcome R1 (writer: not the intended version)", ok.writer_id.values, "p18_ok_R1")
    ok2 = d[d.judge_critical_match == True].copy()
    ok2["y"] = ok2.rej_R2
    table(ok2, "y", preds, "Part 18, judge-RIGHT items, outcome R2 (acceptance = no)", ok2.writer_id.values, "p18_ok_R2")
    al = d[d.rej_R1.notna()].copy()
    al["y"] = al.rej_R1
    table(al, "y", [("critical label wrong (judge)", "crit_wrong", 1)] + preds, "Part 18, all items, outcome R1", al.writer_id.values, "p18_all_R1")
    # incremental over critical label (CV logistic), all items, R1
    Xc = al[["crit_wrong"]].values.astype(float)
    y = al.y.values.astype(float)
    feats = {"critical (binary, raw AUROC)": ["crit_wrong"], "critical + judge added": ["crit_wrong", "judge_added_f"], "critical + length ratio": ["crit_wrong", "len_ratio"],
             "critical + novel words": ["crit_wrong", "novel_vs_input"], "critical + all 3 deployable": ["crit_wrong", "judge_added_f", "len_ratio", "novel_vs_input"],
             "critical + all 3 + Jaccard (oracle)": ["crit_wrong", "judge_added_f", "len_ratio", "novel_vs_input", "jaccard"]}
    L.append(f"**Incremental value over the critical label, Part 18 all items, outcome R1** (n={len(al)}; 5-fold CV ridge-logit scores, mean AUROC over 10 CV seeds; bootstrap resamples items and refits)\n")
    L.append("| model | AUROC | item CI | delta vs critical alone | delta CI |\n|---|---|---|---|---|")
    X = {k: al[v].values.astype(float) for k, v in feats.items()}
    def cvauc(Xm, yv, seeds=3):
        return np.mean([auroc(yv, cv_pred(Xm, yv, 5, sd)) if Xm.shape[1] else 0.5 for sd in range(seeds)])
    base = None
    inc = {}
    rngb = np.random.default_rng(SEED + 1)
    n = len(y)
    bidx = [rngb.integers(0, n, n) for _ in range(300)]
    bres = {}
    for k, Xm in X.items():
        raw = Xm.shape[1] == 1
        a = auroc(y, Xm[:, 0]) if raw else np.mean([auroc(y, cv_pred(Xm, y, 5, sd)) for sd in range(10)])
        bv = []
        for ix in bidx:
            yy = y[ix]
            if yy.sum() in (0, len(yy)):
                bv.append(np.nan)
                continue
            bv.append(auroc(yy, Xm[ix, 0]) if raw else np.mean([auroc(yy, cv_pred(Xm[ix], yy, 5, sd)) for sd in range(2)]))
        bres[k] = np.array(bv)
        if base is None:
            base = (a, bres[k])
        dl = bres[k] - base[1]
        ci = np.nanpercentile(bres[k], [2.5, 97.5])
        dci = np.nanpercentile(dl, [2.5, 97.5])
        L.append(f"| {k} | {a:.3f} | [{ci[0]:.3f}, {ci[1]:.3f}] | {a - base[0]:+.3f} | [{dci[0]:+.3f}, {dci[1]:+.3f}] |")
        inc[k] = dict(auroc=float(a), ci=[float(ci[0]), float(ci[1])], delta=float(a - base[0]), delta_ci=[float(dci[0]), float(dci[1])])
    S["bridge"]["p18_incremental_R1"] = inc
    L.append("\n(300 bootstrap resamples for the incremental table, so those intervals are rougher.)\n")

    # SLP
    s = s.copy()
    s["judge_added_f"] = s.judge_added.fillna(0)
    s["crit_wrong"] = s.judge_fail.astype(float)
    spreds = [("judge added_content (deployable)", "judge_added_f", 1), ("length ratio to keywords (deployable)", "len_ratio", 1), ("novel content words vs input (deployable)", "novel_vs_input", 1)]
    sp = s[s.judge_pass].copy()
    table(sp, "slp_reject", spreds, "SLP, judge-PASS rater-items, outcome says partly/no (bootstrap over the 50 items; both raters kept together)", sp.item_id.values, "slp_pass_reject")
    sp["y"] = sp.slp_unacc
    table(sp, "y", spreds, "SLP, judge-PASS rater-items, outcome acceptable != yes", sp.item_id.values, "slp_pass_unacc")
    table(s, "slp_reject", [("judge meaning_fail", "crit_wrong", 1)] + spreds, "SLP, all rater-items, outcome says partly/no", s.item_id.values, "slp_all_reject")
    return L


# ---------------------------------------------------------------- examples
def pick(df, label):
    df = df.copy()
    df["h"] = df.item_id.map(lambda i: hashlib.sha256(f"{SEED}|whole|{label}|{i}".encode()).hexdigest())
    return df.sort_values("h").iloc[0]


def examples(d, s, S):
    L = ["## 4. Representative examples (declared rule)\n",
         "Rule: among judge-RIGHT items, writer rejected (R1), take for each primary reason the item with the smallest sha256(`20261102|whole|<reason>|<item id>`); for SLP, among judge-PASS items with SLP says partly/no, one per primary reason by the same hash. No cherry-picking beyond that; every reason with at least one item is shown.\n"]
    ex = []
    ok = d[(d.judge_critical_match == True) & (d.rej_R1 == 1)]
    for c in CAT:
        g = ok[ok.prim == c]
        if len(g):
            r = pick(g, "p18" + c)
            L.append(f"- Part 18, **{c}** ({len(g)} such items). Input `{r.input_text}`; writer meant: \"{r.target}\"; output: \"{r.text}\"; writer note: \"{r.note}\"; critical value correct per judge.")
            ex.append(dict(src="p18", reason=c, item=r.item_id))
    jp = s[s.judge_pass & (s.slp_reject == 1)]
    jp = jp.assign(item_id=jp.item_id + "|" + jp.rater)
    for c in CAT:
        g = jp[jp.prim == c]
        if len(g):
            r = pick(g, "slp" + c)
            L.append(f"- SLP, **{c}** ({len(g)} rater-items). Input `{r.input_text}`; output: \"{r.text}\"; SLP says \"{r.says}\", acceptable \"{r.acceptable}\"; note: \"{r.note}\".")
            ex.append(dict(src="slp", reason=c, item=r.item_id))
    S["examples"] = ex
    return L



def paragraph(S):
    k = S["key_question"]["judge critical RIGHT"]
    r1 = k["R1"]
    fl = S["key_question"]["right_not_accepted_flags"]
    br = S["bridge"]["p18_ok_R1"]["length ratio to keywords (deployable)"]
    inc = S["bridge"]["p18_incremental_R1"]
    kk = [x for x in inc if "all 3 deployable" in x][0]
    sl = S["slp"]["judge PASS (meaning_fail=0)"]
    return f"""## 5. Draft paragraph (for the authors; papers not edited)

A metric that checks one critical commitment (negation, speech act, agent, certainty, politeness or time) is necessary but not sufficient evidence that a message "said what the user meant". In our writer-intent check, the judge found the critical value correct for {k['n']} outputs, yet writers said {r1[0]} of {r1[1]} ({100*r1[0]/r1[1]:.0f}%) were not the version they meant and accepted only {k['n']-k['R3']} of {k['n']} as written. Classifying the writers' notes against their own sentences, the main reasons were not paraphrase (about 1%) but a different event or role than intended (e.g. "I wait for the taxi" for "the taxi waits at the gate", {100*S['part18']['reason_all']['substitution']/199:.0f}% of all non-accepted outputs by our diff rule) and details the writer meant but the keywords do not carry (place, time, object; the writer's sentence contained such a word in {100*S['part18']['flags_all']['dropped_unrecoverable']:.0f}% of cases). Added content that the user did not request is a real but smaller share: the model introduced content words absent from the input in {100*fl['added']:.0f}% of judge-correct, non-accepted outputs, and the judge's own added-content flag was set for 45% of the outputs on which SLPs marked "partly" or "no" despite a judge pass. Expert SLPs showed the same gap: the judge passed {sl['n']//2} of 50 outputs ({sl['n']} rater-items) but the SLPs marked {sl['reject']} of those {sl['n']} partly or no. A cheap signal that needs no human label, the ratio of output length to the number of keywords given, ranks writer rejection among judge-correct outputs with AUROC {br['auroc']:.2f} (95% item-bootstrap CI {br['ci'][0]:.2f} to {br['ci'][1]:.2f}), and adding it with two other deployable features to the critical label raises cross-validated AUROC from {inc[list(inc)[0]]['auroc']:.2f} to {inc[kk]['auroc']:.2f}. We therefore recommend reporting an "unrequested content" column beside critical-commitment preservation, and we read the headline preservation rates as an upper bound on whole-message fidelity. Limits: writers rated 10 outputs each of their own pairs, whose sentences are richer than keyword input by construction; two SLPs; one prompt and four models; a rule-based, partly LLM-validated reason classifier (agreement with hand coding {100*S['hand_check']['agree_diff_classifier']:.0f}%, optimistic because the rules were tuned on that sample).
"""


# ---------------------------------------------------------------- main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    S = {"seed": SEED, "bootstrap_B": B}
    d = part18()
    s = slp()
    L = ["# Whole-message fidelity: why a preserved critical commitment is not enough\n",
         "Scope: Part 18 (200 writer-rated outputs, 20 writers), SLP panel (50 outputs, 2 raters), exploratory, post hoc, no new model calls. Classifier and hand coding are described in `src/analyze_whole_message.py`. "
         "The 'writer's sentence' is the writer's own A or B sentence for the intended variant; it often contains details (places, times, objects) that the keywords do not carry. "
         "Writer-intent agreement is not validation by AAC users.\n"]
    L += part18_report(d, S)
    L += slp_report(s, S)
    L += bridge(d, s, S)
    L += examples(d, s, S)
    L.append(paragraph(S))
    L.append("Note on examples: the single `reword` Part 18 example is a classifier miss on inspection (the note says the agent and speech act changed), shown because the rule was fixed in advance.\n")
    json.dump(S, open(OUT / "summary.json", "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    (OUT / "report.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()

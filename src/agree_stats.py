"""Small agreement statistics (no sklearn dependency): Cohen's kappa, confusion,
per-label precision/recall. Krippendorff alpha lives in score_gold.py (ported)."""
from __future__ import annotations

from collections import Counter


def cohen_kappa(a: list, b: list) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    if pe >= 1.0:
        return None  # both raters constant on the same label: kappa undefined
    return round((po - pe) / (1 - pe), 3)


def confusion(pred: list, gold: list) -> dict[str, dict[str, int]]:
    labs = sorted(set(pred) | set(gold), key=str)
    m = {g: {p: 0 for p in labs} for g in labs}
    for p, g in zip(pred, gold):
        m[g][p] += 1
    return m  # rows = gold (human), cols = predicted (judge)


def prf(pred: list, gold: list, positive) -> dict:
    tp = sum(p == positive and g == positive for p, g in zip(pred, gold))
    fp = sum(p == positive and g != positive for p, g in zip(pred, gold))
    fn = sum(p != positive and g == positive for p, g in zip(pred, gold))
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": None if prec is None else round(prec, 3),
            "recall": None if rec is None else round(rec, 3)}

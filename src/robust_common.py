"""Shared helpers for the no-new-generation robustness analyses (analysis/robust/<name>/). Stored data only."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261101


def outdir(name: str) -> Path:
    p = ROOT / "analysis/robust" / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path, obj):
    def default(o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
        if isinstance(o, (np.bool_,)): return bool(o)
        if isinstance(o, set): return sorted(o)
        raise TypeError(type(o))
    Path(path).write_text(json.dumps(obj, indent=1, default=default, sort_keys=False) + "\n")


def pct(x, nd=1):
    return "NA" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{100 * x:.{nd}f}"


def ci_str(est, lo, hi, nd=1, unit="%"):
    return f"{pct(est, nd)}{unit} [{pct(lo, nd)}, {pct(hi, nd)}]"


def md_table(df, nd=3):
    """Markdown table without the tabulate dependency."""
    cols = list(df.columns)
    def f(v):
        if isinstance(v, (float, np.floating)):
            return "NA" if np.isnan(v) else f"{v:.{nd}f}"
        return str(v)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(f(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(out)

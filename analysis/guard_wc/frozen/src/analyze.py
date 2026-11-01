"""Turn scored target rows (or pilot layer0 pickle) into reproducible paper artifacts.

    python src/analyze.py --table runs/pilot1/l0.pkl --items 'data/items/*.jsonl' --tag pilot_l0

Only local files are read. No generation, judging, or server processes are started.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from build_requests import input_text
from labels import (EMPH, GENERAL_DIMS, NA_CERTAINTY, PLAIN_A, critical_match,
                    dims_in_chips, general_spec, is_unclear)

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = ["bare", "noncrit", "chip1", "chipall", "full"]
AMBIG = {"bare", "noncrit"}
CUE = {"chip1", "chipall", "full"}
GROUP = ["dimension", "channel", "model", "prompt_id"]
# attribute.py uses these names; callers may add aliases with --column-map JSON.
ALIASES = {"variant_value": "cv", "critical": "crit", "critical_source": "label_source"}
RATE_COLUMNS = ["estimate", "ci_low", "ci_high", "n", "n_total", "n_missing", "n_families",
                "n_families_observed", "n_boot_valid"]


def load_items(pattern: str) -> dict:
    items = {}
    for path in sorted(glob.glob(pattern)):
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            fid = item["family_id"]
            if fid in items and items[fid] != item:
                raise ValueError(f"Conflicting definitions for family {fid}: {path}")
            items[fid] = item
    if not items:
        raise ValueError(f"No items matched {pattern!r}")
    return items


def known(value) -> bool:
    return value is not None and not pd.isna(value)


def normalize_table(raw: pd.DataFrame, items: dict, column_map: dict | None = None) -> pd.DataFrame:
    """Adapt scored.* and layer0 inputs, preserving unknowns instead of calling them failures.

    Layer0 validity is a parse/nonempty proxy, never a grammaticality judgment.
    Supplied deterministic attribution columns are recomputed from labels/specs so
    all input formats have identical denominators and uncertainty handling.
    """
    df = raw.copy()
    if df.empty:
        raise ValueError("The input table has no rows")
    aliases = ALIASES | (column_map or {})
    df = df.rename(columns={a: b for a, b in aliases.items() if a in df and b not in df})
    required = {"family_id", "variant", "channel", "prompt_id", "model", "text", "request_key"}
    if missing := required - set(df):
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if not set(df.channel) <= set(CHANNELS):
        raise ValueError(f"Unknown channels: {set(df.channel) - set(CHANNELS)}")
    for c in ("sample_idx", "suggestion_idx"):
        if c not in df:
            df[c] = 0
    is_l0 = "crit" not in df and "l0_agent" in df
    for d in GENERAL_DIMS:
        if d not in df:
            df[d] = df.get(f"l0_{d}", pd.Series(np.nan, index=df.index))
    if "crit" not in df:
        if not is_l0:
            raise ValueError("Expected crit/critical, or l0_* labels for the pilot adapter")
        def l0_critical(r):
            d = items[r.family_id]["dimension"]
            if d == "time_quantity":
                return np.nan
            value = r[d]
            if d == "certainty" and value in {PLAIN_A, EMPH}:
                return PLAIN_A
            if d == "politeness" and known(value):
                return "plain" if value == "none" else "polite"
            return value
        df["crit"] = df.apply(l0_critical, axis=1)
    if is_l0:
        df["label_source"] = "layer0"
    elif "label_source" not in df:
        df["label_source"] = "unspecified"
    if "added_content" not in df:
        df["added_content"] = np.nan
    df["added_content"] = df.added_content.map(
        lambda v: np.nan if not known(v) else {"yes": True, "no": False}.get(v, v))
    had_validity = "valid" in df
    if not had_validity:
        df["valid"] = df.get("parse_ok", pd.Series(True, index=df.index)).fillna(False).astype(bool)
        df["valid"] &= df.text.fillna("").str.strip().ne("")
    df["validity_source"] = "supplied" if had_validity else "parse/nonempty proxy"
    records = []
    for r in df.to_dict("records"):
        item = items[r["family_id"]]
        var = item["variants"][r["variant"]]
        d, ch = item["dimension"], r["channel"]
        r.update(dimension=d, cv=var["critical_value"], source=var["source"],
                 value_A=item["variants"]["A"]["critical_value"],
                 value_B=item["variants"]["B"]["critical_value"])
        if not known(r.get("input_text")):
            r["input_text"] = input_text(item, r["variant"], ch)
        crit = r["crit"] if known(r["crit"]) else None
        valid = bool(r["valid"]) if known(r["valid"]) else None
        match = critical_match(d, r["cv"], crit)
        r["critical_match"] = False if valid is False else (match if valid else None)
        r["violation"] = (not match if valid and match is not None else None) if ch in CUE else None
        r["commitment"] = (not is_unclear(crit) if valid and crit is not None else
                           False if valid is False else None) if ch in AMBIG else None
        r["chose"] = (None if crit is None or not valid else "unclear" if is_unclear(crit) else
                       "A" if critical_match(d, r["value_A"], crit) else
                       "B" if critical_match(d, r["value_B"], crit) else "other")
        spec = general_spec(var.get("all_chips", []), var.get("general_spec"))
        given = (set(GENERAL_DIMS) if ch == "full" else
                 dims_in_chips(var.get("chips" if ch == "chip1" else "all_chips", []))
                 if ch in {"chip1", "chipall"} else set())
        contradictions = []
        for g in GENERAL_DIMS:
            val, expected = r[g], spec[g]
            comparable = bool(valid and known(val) and expected is not None and not
                              (g == "certainty" and (val == NA_CERTAINTY or NA_CERTAINTY in expected)))
            differs = val not in expected if comparable else None
            r[f"in_input_{g}"] = g in given
            r[f"addition_{g}"] = differs if g not in given else None
            # The critical dimension is already checked by critical_match.
            certainty_na = g == "certainty" and expected is not None and (
                (known(val) and val == NA_CERTAINTY) or NA_CERTAINTY in expected)
            if g in given and g != d and expected is not None and not certainty_na:
                contradictions.append(differs)
        r["politeness_added"] = (r["politeness"] != "none" if valid and known(r["politeness"])
                                 and spec["politeness"] == {"none"} else None)
        cert = r["certainty"]
        r["certainty_raised"] = (cert == EMPH or (cert == PLAIN_A and "hedged/uncertain" in spec["certainty"])
                                 if valid and known(cert) and cert != NA_CERTAINTY
                                 and spec["certainty"] and NA_CERTAINTY not in spec["certainty"] else None)
        if ch not in CUE:
            r["constraint_preserving"] = None
        elif valid is False or match is False or any(x is True for x in contradictions):
            r["constraint_preserving"] = False
        elif not valid or match is None or any(x is None for x in contradictions):
            r["constraint_preserving"] = None
        else:
            r["constraint_preserving"] = True
        # Cost excludes rendering prefixes and treats each chip as one selection.
        chips = var.get("chips" if ch == "chip1" else "all_chips", []) if ch in {"chip1", "chipall"} else []
        words = (var["source"] if ch == "full" else item["bare"] +
                 (" " + item["noncritical"] if ch == "noncrit" else ""))
        r["keyword_count"] = len(words.split())
        r["chip_count"] = len(chips)
        r["input_actions"] = len(words.split()) + len(chips)
        r["input_characters"] = len(words) + len(chips)
        r["repair_chip_cost"] = len(var["chips"])
        records.append(r)
    return pd.DataFrame(records)


def family_bootstrap(frame: pd.DataFrame, value: str, *, n_boot: int = 2000,
                     seed: int = 20261031, transform=None) -> dict:
    """Row-weighted mean, percentile CI from resampling whole families.

    Family sums AND valid-row counts are multiplied by the same multinomial
    multiplicity. This preserves unequal family sizes and within-family pairing.
    Families with only missing outcomes remain in the sampling frame; bootstrap
    replicates with zero observed denominator are excluded and counted.
    """
    if n_boot < 1:
        raise ValueError("n_boot must be positive")
    work = frame[["family_id", value]].copy()
    work[value] = pd.to_numeric(work[value], errors="raise").astype(float)
    agg = work.groupby("family_id", sort=True)[value].agg(["sum", "count"])
    n = int(agg["count"].sum())
    out = dict(estimate=np.nan, ci_low=np.nan, ci_high=np.nan, n=n,
               n_total=len(frame), n_missing=len(frame) - n,
               n_families=len(agg), n_families_observed=int(agg["count"].gt(0).sum()),
               n_boot_valid=0)
    if not n:
        return out
    weights = np.random.default_rng(seed).multinomial(len(agg), np.full(len(agg), 1 / len(agg)), size=n_boot)
    den = weights @ agg["count"].to_numpy(float)
    draws = (weights @ agg["sum"].to_numpy(float))[den > 0] / den[den > 0]
    estimate = float(agg["sum"].sum() / n)
    if transform is not None:
        estimate, draws = transform(estimate), transform(draws)
    lo, hi = np.quantile(draws, [.025, .975])
    out.update(estimate=estimate, ci_low=float(lo), ci_high=float(hi), n_boot_valid=len(draws))
    return out


def summarize(df: pd.DataFrame, groups: list[str], metrics: list[str], n_boot=2000, seed=20261031) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(groups, sort=True, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        for metric in metrics:
            rows.append(dict(zip(groups, key)) | {"metric": metric} |
                        family_bootstrap(g, metric, n_boot=n_boot, seed=seed))
    return pd.DataFrame(rows, columns=groups + ["metric"] + RATE_COLUMNS)


def unique_ambiguous(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.channel.isin(AMBIG)].sort_values(["variant", "sample_idx", "suggestion_idx"]).drop_duplicates(
        ["family_id", "channel", "model", "prompt_id", "request_key", "sample_idx", "suggestion_idx"])


def direction_table(amb: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    rows = []
    for key, g in amb.groupby(GROUP, sort=True):
        g = g.copy()
        for choice in ["A", "B", "other", "unclear"]:
            g[f"share_{choice}_all"] = [float(v == choice) if known(v) else np.nan for v in g.chose]
        g["share_A"] = [float(v == "A") if v in {"A", "B"} else np.nan for v in g.chose]
        g["share_B"] = 1 - g.share_A
        for metric in ["share_A", "share_B", "share_A_all", "share_B_all", "share_other_all", "share_unclear_all", "default_preference_index"]:
            result = family_bootstrap(g, "share_A" if metric == "default_preference_index" else metric,
                                      n_boot=n_boot, seed=seed,
                                      transform=(lambda v: np.abs(v - .5) * 2) if metric == "default_preference_index" else None)
            rows.append(dict(zip(GROUP, key)) | {"metric": metric} | result)
    return pd.DataFrame(rows, columns=GROUP + ["metric"] + RATE_COLUMNS)


def paired_differences(df: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    """Pair channel means within family/variant/model/prompt; suggestions are repeats."""
    keys = ["family_id", "variant", "dimension", "model", "prompt_id"]
    means = df.assign(critical_match=pd.to_numeric(df.critical_match)).groupby(keys + ["channel"])["critical_match"].mean().unstack("channel")
    rows = []
    for high, low in [("chip1", "noncrit"), ("full", "chip1")]:
        if high not in means or low not in means:
            continue
        pairs = means[[high, low]].dropna().copy()
        pairs["critical_match_difference"] = pairs[high] - pairs[low]
        result = summarize(pairs.reset_index(), ["dimension", "model", "prompt_id"],
                           ["critical_match_difference"], n_boot, seed)
        result["comparison"] = f"{high}-minus-{low}"
        rows.append(result)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["dimension", "model", "prompt_id", "metric"] + RATE_COLUMNS + ["comparison"])


def suggestion_sets(df: pd.DataFrame) -> pd.DataFrame:
    """P2: one request's first three; S3: consecutive blocks of three samples.

    Keep variant targets here for reaching costs; deduplicate them for coverage
    summaries. A set with unresolved labels is unknown unless both values are
    already present. Parse failures are observed missing readings, not unknowns.
    """
    x = df[df.prompt_id.isin(["P2", "S3"]) & df.channel.isin(AMBIG)].copy()
    x["set_id"] = [str(r.request_key) if r.prompt_id == "P2" else str(int(r.sample_idx) // 3)
                   for r in x.itertuples()]
    keys = ["family_id", "variant", "dimension", "channel", "model", "prompt_id", "set_id"]
    rows = []
    for key, g in x.groupby(keys, sort=True):
        g = g.sort_values(["sample_idx", "suggestion_idx", "request_key"]).drop_duplicates(
            ["request_key", "sample_idx", "suggestion_idx"]).head(3)
        first = g.iloc[0]
        choices = set(g.chose.dropna())
        unknown = bool((g.valid.fillna(True) & g.crit.isna()).any())
        covered = {"A", "B"} <= choices
        row = dict(zip(keys, key))
        row.update(n_suggestions=len(g), coverage_at_3=True if covered else np.nan if unknown else False,
                   distinct_critical_values=np.nan if unknown else len(choices - {"unclear"}),
                   distinct_variant_values=len(choices & {"A", "B"}),
                   first_choice=first.chose, value_A=first.value_A, value_B=first.value_B,
                   missing_labels=unknown)
        target = row["variant"]
        top = first.chose
        if top == target:
            cost = 0
        elif target in choices:
            cost = 1
        elif unknown:
            cost = np.nan
        else:
            cost = first.repair_chip_cost
        row["extra_actions"] = cost
        row["nondefault_extra_actions"] = cost if top in {"A", "B"} and top != target else np.nan
        row["target_is_nondefault"] = top in {"A", "B"} and top != target
        row["fallback_to_chips"] = False if target in choices else np.nan if unknown else True
        row["repair_chip_cost"] = first.repair_chip_cost
        for col in ["text", "source", "input_text", "request_key", "sample_idx", "suggestion_idx", "label_source"]:
            row[col] = first[col]
        row["outputs"] = json.dumps(g.text.tolist(), ensure_ascii=False)
        rows.append(row)
    return pd.DataFrame(rows, columns=list(dict.fromkeys(keys + ["n_suggestions", "coverage_at_3", "distinct_critical_values",
        "distinct_variant_values", "first_choice", "value_A", "value_B", "missing_labels", "extra_actions",
        "nondefault_extra_actions", "target_is_nondefault", "fallback_to_chips", "repair_chip_cost", "text", "source",
        "input_text", "request_key", "sample_idx", "suggestion_idx", "label_source", "outputs"])))


def pareto_flags(table: pd.DataFrame) -> pd.DataFrame:
    x = table.pivot(index=GROUP, columns="metric", values="estimate").reset_index()
    x["pareto_efficient"] = False
    for _, g in x.groupby(["dimension", "model", "prompt_id"]):
        for i, r in g.iterrows():
            if not known(r.critical_match):
                continue
            dominated = ((g.input_actions <= r.input_actions) & (g.critical_match >= r.critical_match) &
                         ((g.input_actions < r.input_actions) | (g.critical_match > r.critical_match))).any()
            x.loc[i, "pareto_efficient"] = not dominated
    return x


def markdown_table(df: pd.DataFrame) -> str:
    """No optional tabulate dependency; full precision remains in CSV/parquet."""
    def fmt(v):
        if not known(v):
            return "NA"
        if isinstance(v, (float, np.floating)):
            return f"{v:.4f}"
        return str(v).replace("|", "\\|").replace("\n", " ")
    return "| " + " | ".join(df.columns) + " |\n| " + " | ".join(["---"] * len(df.columns)) + " |\n" + "\n".join(
        "| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False, name=None)) + "\n"


def example_miner(df: pd.DataFrame, sets: pd.DataFrame, seed: int) -> str:
    """Select the two smallest seeded SHA256 ranks, distinct families first."""
    def rank(r):
        identity = [str(r.get(k, "")) for k in ["family_id", "variant", "channel", "model", "prompt_id",
                                                "request_key", "sample_idx", "suggestion_idx"]]
        return hashlib.sha256(json.dumps([seed, identity]).encode()).hexdigest()
    sections = ["# Deterministically mined examples\n",
                f"Rule: seed={seed}; sort eligible rows by SHA256(seed, family/variant/channel/model/prompt/request/sample/suggestion); "
                "take two, preferring different families. No manual curation. Missing labels are ineligible. "
                "An assumption-default example expresses the modal A/B choice in that dimension/channel/model/prompt cell "
                "(ties choose A) and mismatches the target variant. Chip repairs pair the same sample/suggestion.\n"]
    amb = unique_ambiguous(df)
    defaults = {}
    for key, g in amb.groupby(GROUP):
        counts = g.chose.value_counts()
        defaults[key] = "A" if counts.get("A", 0) >= counts.get("B", 0) else "B"
    assumption = df[df.channel.isin(AMBIG) & df.critical_match.eq(False)].copy()
    assumption = assumption.loc[pd.Series(
        [r.chose == defaults.get(tuple(getattr(r, k) for k in GROUP)) for r in assumption.itertuples()],
        index=assumption.index, dtype=bool)]
    cue = df[df.channel.isin(CUE) & df.violation.eq(True)]
    pairkeys = ["family_id", "variant", "dimension", "model", "prompt_id", "sample_idx", "suggestion_idx"]
    before = df[df.channel.eq("noncrit") & df.critical_match.eq(False)][pairkeys + ["text", "input_text"]]
    repaired = df[df.channel.eq("chip1") & df.critical_match.eq(True)].merge(before, on=pairkeys, suffixes=("", "_before"))
    missed = sets[sets.coverage_at_3.eq(False) & sets.target_is_nondefault] if len(sets) else sets
    for dim in sorted(df.dimension.unique()):
        sections.append(f"\n## {dim}\n")
        for category, candidates in [("assumption-default", assumption), ("violation-with-cue", cue),
                                     ("chip-repair success", repaired), ("spanning-set miss", missed)]:
            g = candidates[candidates.dimension.eq(dim)].copy()
            # Spanning-set misses concern P2 specifically, not the S3 baseline.
            if category == "spanning-set miss":
                g = g[g.prompt_id.eq("P2")]
            sections.append(f"\n### {category}\n")
            if not len(g):
                sections.append("No eligible examples (missing labels or no qualifying event).\n")
                continue
            g["_rank"] = [rank(r) for r in g.to_dict("records")]
            g = g.sort_values("_rank")
            selected = pd.concat([g.drop_duplicates("family_id"), g]).drop_duplicates("_rank").head(2)
            for r in selected.to_dict("records"):
                output = json.loads(r["outputs"]) if "outputs" in r else r["text"]
                sections.append(f"- `{r['family_id']}/{r['variant']}` · {r['model']} · {r['prompt_id']} · {r['channel']} "
                                f"· label source {r['label_source']}\n"
                                f"  - Source: {json.dumps(r['source'], ensure_ascii=False)}\n"
                                f"  - Visible input: {json.dumps(r['input_text'], ensure_ascii=False)}\n"
                                f"  - Output: {json.dumps(output, ensure_ascii=False)}\n")
                if category == "chip-repair success":
                    sections.append(f"  - Before: {json.dumps(r['input_text_before'])} → {json.dumps(r['text_before'])}\n")
    return "\n".join(sections)


def headline_table(tables: dict) -> pd.DataFrame:
    """Compact human-readable point estimates with uncertainty and denominators."""
    selections = [
        ("critical_match", "critical_match", "P0", "chip1", "chip1 match"),
        ("critical_match", "critical_match", "P0", "full", "full match"),
        ("direction", "share_A", "P0", "bare", "bare share A"),
        ("coverage", "coverage_at_3", "P2", "bare", "P2 coverage"),
        ("coverage", "coverage_at_3", "S3", "bare", "S3 coverage"),
    ]
    parts = []
    for name, metric, prompt, channel, label in selections:
        t = tables[name]
        t = t[t.metric.eq(metric) & t.prompt_id.eq(prompt) & t.channel.eq(channel)].copy()
        if t.empty:
            continue
        t[label] = [f"{r.estimate:.3f} [{r.ci_low:.3f}, {r.ci_high:.3f}]; n={r.n}, f={r.n_families_observed}"
                    if known(r.estimate) else f"NA; n=0, f=0/{r.n_families}" for r in t.itertuples()]
        parts.append(t.set_index(["dimension", "model"])[[label]])
    return pd.concat(parts, axis=1).reset_index() if parts else pd.DataFrame(columns=["dimension", "model"])


def write_report(out: Path, df: pd.DataFrame, tables: dict, args) -> None:
    unknown = int(df.crit.isna().sum())
    report = [f"# Analysis: {args.tag}\n",
              f"Input: `{args.table}`. {df.family_id.nunique()} families; {len(df):,} target rows; "
              f"{df.drop_duplicates(['family_id', 'channel', 'model', 'prompt_id', 'request_key', 'sample_idx', 'suggestion_idx']).shape[0]:,} "
              f"distinct output occurrences within channels; {unknown:,} unresolved critical labels; "
              f"{df.valid.eq(False).sum():,} non-completions.\n",
              f"Label sources: {df.label_source.fillna('unresolved').value_counts().to_dict()}. "
              f"Validity: {df.validity_source.value_counts().to_dict()}.\n",
              "## Selected headline estimates\n",
              "Entries are estimate [95% CI]; n = observed denominator, f = observed families. "
              "Match and direction use P0; coverage uses bare P2/S3. A/B values are defined per family below.\n",
              markdown_table(headline_table(tables)),
              "## Estimands and limitations\n",
              f"95% percentile CIs use {args.n_boot:,} whole-family bootstrap resamples, fixed seed {args.seed}. "
              "Estimates weight observed rows equally; each sampled family's complete cluster gets its sampled multiplicity. "
              "NA outcomes leave rate denominators, and n, n_total, n_missing, n_families and n_families_observed are provided. "
              "No multiple-comparison adjustment. Single-family CIs are degenerate and are not population evidence.\n",
              "Critical match includes invalid completions as failures. Violation excludes non-completions and unknown labels; "
              "constraint-preserving completion (co-primary 1) counts invalid completions as failures and is unknown when a needed "
              "label is missing. A known contradiction is a failure even if other labels are missing. "
              "Without supplied valid labels, parsing and nonempty text are only a provisional validity proxy. "
              "A scored table cannot recover missing generations that were never included as rows.\n",
              "Co-primary 2 commitment, direction and coverage deduplicate shared A/B targets. Commitment is any known label "
              "other than unclear/mixed; invalid outputs count as noncommitment. share_A/share_B condition on A/B choices; "
              "*_all shares use all known choices, including unclear/other. Default preference index = 2|share_A−0.5|, "
              "recomputed within each bootstrap sample (unsigned and upward biased near zero). A/B are family-specific labels; "
              "direction_values.csv lists their meanings.\n",
              "Paired effects subtract channel means within family/variant/model/prompt, after averaging suggestions/samples; "
              "only pairs with both outcomes observed are included. Pair CIs resample families jointly.\n",
              "Stance rates compare every target variant to all_chips-implied general values under bare/noncrit, including the "
              "family's critical dimension when applicable. A/B targets are retained: these are reference-relative rates, "
              "not evidence of the user's intended reading. Silent agent specs and n/a certainty are unscored. "
              "[SURE] accepts plain or emphatic (D-007); certainty_raised separately counts emphatic outputs or plain outputs "
              "against a hedged spec. All emphatic outputs count as raised under this operational rule, even if the source "
              "was emphatic. politeness_added conditions on plain-source specs. Missing added_content stays NA.\n",
              "Suggestion sets: P2 takes the first three suggestion indices per request; S3 takes consecutive blocks of three "
              "samples (0–2, 3–5, …), sorted by sample then suggestion index. Shared targets are counted once for coverage. "
              "Both A/B values must appear. Unknown labels produce NA unless both values are already observed; incomplete "
              "sets with known labels are retained and flagged by n_suggestions. Distinct critical values exclude unclear; "
              "other committed values count. Suggestion additions are also reported by suggestion position.\n",
              "Extra actions to reach each target reading: 0 if top-1 matches, 1 if present among the first three, otherwise "
              "the target's number of critical chips. Nondefault costs condition on top-1 committing to the opposite variant; "
              "ambiguous/other top-1 choices have no identified default. Chip fallback is a nominal input cost and does not "
              "guarantee a successful repair. Single-output prompts use the same rule without a suggestion-selection option.\n",
              "Input actions = whitespace keyword count + chip selections; full = source whitespace word count. "
              "Input characters = number of visible word characters including inter-word spaces + chip selections; "
              "rendering prefixes and chip token spelling are excluded. Pareto flags compare channel means within "
              "dimension/model/prompt and do not test statistical dominance.\n",
              "Figures F1/F2/F3/F5 use P0 when present (otherwise the first available prompt, excluding P1 when possible); "
              "F4 compares P2/S3. P1 is retained as pilot-only sensitivity output per D-010; it is not a recommended paper condition. "
              "All prompt-specific numbers are in the tables below. Main match/assumption analyses include act-01/act-02; "
              "sensitivity_without_act01_act02.csv excludes those frozen pilot speech-act families (D-009). "
              "sensitivity_quarantine_refusal_acceptance.csv reports speech-act estimates with and without the "
              "refusal/acceptance families (column quarantine_refusal_acceptance; PREREG_R2 W-A): the primary speech-act "
              "estimate is primary_excl_quarantine. All headline tables and figures exclude quarantined families "
              "unless --include-quarantine is explicitly supplied for sensitivity. "
              "Pilot layer0 time/quantity labels are unavailable; no time/quantity inference should be made.\n",
              "## Artifacts\n",
              "Normalized input: [scored.parquet](scored.parquet). Set-level audit: [suggestion_sets.csv](suggestion_sets.csv). "
              "Reproduction hashes and settings: [metadata.json](metadata.json). "
              "Deterministically selected triples: [examples.md](examples.md). "
              "Figures: [F1](F1_attribution.pdf), [F2](F2_defaults.pdf), [F3](F3_pareto.pdf), "
              "[F4](F4_coverage.pdf), [F5](F5_stance.pdf), each also PNG.\n"]
    for name, table in tables.items():
        report.append(f"\n## {name.replace('_', ' ')}\n\n[{name}.csv]({name}.csv) · {len(table):,} rows\n\n")
        report.append("<details><summary>All numbers (NA = unobserved / not applicable)</summary>\n\n")
        report.append(markdown_table(table))
        report.append("\n</details>\n")
    (out / "report.md").write_text("\n".join(report))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--items", default="data/items/*.jsonl")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261031)
    ap.add_argument("--column-map", type=Path, help='JSON object of input column -> canonical column')
    ap.add_argument("--include-quarantine", action="store_true", help="quarantine-inclusive sensitivity only")
    args = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.tag) or args.tag in {".", ".."}:
        ap.error("--tag must be a simple directory name")
    if args.n_boot < 1:
        ap.error("--n-boot must be positive")
    items = load_items(args.items)
    raw = pd.read_parquet(args.table) if args.table.suffix in {".parquet", ".pq"} else pd.read_pickle(args.table)
    mapping = json.loads(args.column_map.read_text()) if args.column_map else None
    df = normalize_table(raw, items, mapping)
    all_df = df
    quarantine = df.family_id.map(lambda f: items[f]["dimension"] == "speech_act" and any(
        v["critical_value"] in {"refusal", "acceptance"} for v in items[f]["variants"].values()))
    if not args.include_quarantine:
        df = df[~quarantine].copy()
    out = ROOT / "analysis" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / "scored.parquet", index=False)
    nboot, seed = args.n_boot, args.seed
    amb = unique_ambiguous(df)
    sets = suggestion_sets(df)
    unique_sets = sets.sort_values("variant").drop_duplicates(["family_id", "channel", "model", "prompt_id", "set_id"])
    stance_metrics = [f"addition_{d}" for d in GENERAL_DIMS] + ["politeness_added", "certainty_raised", "added_content"]
    mult = df[df.channel.isin(AMBIG) & df.prompt_id.isin(["P2", "S3"])].copy()
    mult["suggestion_position"] = np.where(mult.prompt_id.eq("S3"), mult.sample_idx % 3 + 1, mult.suggestion_idx + 1)
    # Include P0/P1 top-1 costs alongside the actual 3-suggestion conditions.
    single = df[df.channel.isin(AMBIG) & ~df.prompt_id.isin(["P2", "S3"])].copy()
    single["extra_actions"] = [0 if r.chose == r.variant else r.repair_chip_cost if known(r.chose) or not r.valid else np.nan
                               for r in single.itertuples()]
    single["nondefault_extra_actions"] = [r.extra_actions if r.chose in {"A", "B"} and r.chose != r.variant else np.nan
                                          for r in single.itertuples()]
    costs = pd.concat([sets, single], ignore_index=True)
    tables = {
        "critical_match": summarize(df, GROUP, ["critical_match"], nboot, seed),
        "cue_endpoints": summarize(df[df.channel.isin(CUE)], GROUP, ["violation", "constraint_preserving"], nboot, seed),
        "commitment": summarize(amb, GROUP, ["commitment"], nboot, seed),
        "direction": direction_table(amb, nboot, seed),
        "direction_values": df[["family_id", "dimension", "value_A", "value_B"]].drop_duplicates().sort_values("family_id"),
        "paired_differences": paired_differences(df, nboot, seed),
        "stance_additions": summarize(df[df.channel.isin(AMBIG)], GROUP, stance_metrics, nboot, seed),
        "stance_overall": summarize(df[df.channel.isin(AMBIG)], ["channel", "model", "prompt_id"], stance_metrics, nboot, seed),
        "suggestion_additions": summarize(mult, GROUP + ["suggestion_position"], stance_metrics, nboot, seed),
        "coverage": summarize(unique_sets, GROUP, ["coverage_at_3", "distinct_critical_values", "n_suggestions"], nboot, seed),
        "reaching_cost": summarize(costs, GROUP, ["extra_actions", "nondefault_extra_actions"], nboot, seed),
        "reaching_cost_by_model": summarize(costs, ["dimension", "model", "prompt_id"], ["extra_actions", "nondefault_extra_actions"], nboot, seed),
        "fidelity_cost": summarize(df, GROUP, ["critical_match", "input_actions", "input_characters", "keyword_count", "chip_count"], nboot, seed),
        "label_counts": df.assign(critical_known=df.crit.notna()).groupby(GROUP, dropna=False).agg(
            n_rows=("family_id", "size"), n_families=("family_id", "nunique"), n_known=("critical_known", "sum"), n_valid=("valid", "sum")).reset_index(),
    }
    tables["pareto"] = pareto_flags(tables["fidelity_cost"])
    sensitive = df[~df.family_id.isin(["act-01", "act-02"])]
    tables["sensitivity_without_act01_act02"] = summarize(sensitive, GROUP, ["critical_match", "constraint_preserving"], nboot, seed)
    # PREREG_R2 W-A: refusal/acceptance families are quarantined from primary speech-act estimates.
    quar = quarantine
    sa = all_df[all_df.dimension.eq("speech_act")]
    qmetrics = ["critical_match", "violation", "constraint_preserving"]
    tables["sensitivity_quarantine_refusal_acceptance"] = pd.concat([
        summarize(sa, GROUP, qmetrics, nboot, seed).assign(subset="all_speech_act_families"),
        summarize(sa[~quar[sa.index]], GROUP, qmetrics, nboot, seed).assign(subset="primary_excl_quarantine"),
        summarize(sa[quar[sa.index]], GROUP, qmetrics, nboot, seed).assign(subset="quarantined_only"),
    ], ignore_index=True)
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=False)
    sets.to_csv(out / "suggestion_sets.csv", index=False)
    (out / "examples.md").write_text(example_miner(df, sets, seed))
    metadata = dict(table=str(args.table), items=args.items, n_boot=nboot, seed=seed,
                    n_rows=len(df), n_families=int(df.family_id.nunique()),
                    include_quarantine=args.include_quarantine, n_rows_inclusive=len(all_df),
                    input_sha256=hashlib.sha256(args.table.read_bytes()).hexdigest(),
                    items_sha256={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(glob.glob(args.items))},
                    versions={"pandas": pd.__version__, "numpy": np.__version__})
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    import figs
    figs.make_figures(tables, out)
    write_report(out, df, tables, args)
    print(f"Wrote {out}: {len(df):,} rows, {df.family_id.nunique()} families, {len(tables)} tables, 5 figures (PDF + PNG), report and examples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

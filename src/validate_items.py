#!/usr/bin/env python3
"""Validate hand-authored minimal-pair probe families (SPEC v0.1).

Usage: python src/validate_items.py data/items/pilot.jsonl [more.jsonl ...]
Exit code 1 if any ERROR is found. WARNs are printed but do not fail.
Follow-up records (split expB / expC, D-012) may carry `custom_channels`; their inputs,
commitments, alias/padding tokens and "Meaning:" lines are checked too.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prompts as P  # noqa: E402
from labels import CHIP_TO_GENERAL, general_spec  # noqa: E402

SPLITS = {"pilot", "dev", "test", "expB", "expC"}
ALIAS_TO_CHIP = {v: k for k, v in P.ALIAS.items()}
BRACKET = re.compile(r"\[[^\]]+\]")

VOCAB = {
    "[NOT]", "[YES]", "[?]", "[ASK]", "[REFUSE]", "[TELL]", "[MAYBE]", "[SURE]",
    "[MUST]", "[WANT]", "[I]", "[YOU]", "[WE]", "[THEY]", "[PAST]", "[NOW]",
    "[LATER]", "[PLEASE]", "[PLAIN]",
}
NUM_CHIP = re.compile(r"^\[\d+\]$")  # literal number chips, time_quantity only
DIMENSIONS = {
    "polarity": "pol", "agent": "agt", "certainty": "cer",
    "time_quantity": "tq", "speech_act": "act", "politeness": "pol2",
}
REQUIRED = ["family_id", "dimension", "split", "context", "variants", "bare",
            "noncritical", "critical_options", "notes"]
VARIANT_REQUIRED = ["source", "critical_value", "chips", "all_chips"]
# Words that carry a critical cue and must never appear in `bare`.
CUE_WORDS = {
    "not", "no", "never", "don't", "doesn't", "didn't", "won't", "can't", "isn't",
    "yes", "please", "maybe", "might", "probably", "perhaps", "think", "sure",
    "definitely", "could", "would", "mind", "i", "you", "we", "they", "she", "he",
    "me", "my", "your", "yesterday", "tomorrow", "already", "later", "tonight",
    "today", "now", "last", "next", "soon",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
}
TOKEN = re.compile(r"[a-z0-9']+")
# irregular forms so lemma-form bare words can be traced to inflected sources
IRREG = {"saw": "see", "seen": "see", "got": "get", "paid": "pay", "took": "take",
         "left": "leave", "went": "go", "gone": "go", "ate": "eat", "bought": "buy",
         "brought": "bring", "made": "make", "lost": "lose", "sent": "send", "told": "tell",
         "felt": "feel", "slept": "sleep", "won": "win", "forgot": "forget", "came": "come",
         "met": "meet", "fell": "fall", "broke": "break", "wrote": "write", "gave": "give",
         "spent": "spend", "drove": "drive", "kept": "keep", "found": "find", "heard": "hear",
         "had": "have", "has": "have", "did": "do", "ran": "run", "rode": "ride", "sold": "sell",
         "taught": "teach", "thought": "think", "caught": "catch", "hurt": "hurt"}


def matches(w, t):
    """bare word w matches source token t up to inflection."""
    t2 = IRREG.get(t, t)
    return w == t or w == t2 or t.startswith(w[:3]) or w.startswith(t[:3]) or t2.startswith(w[:3])


def toks(s):
    return TOKEN.findall(s.lower().replace("’", "'"))


def validate_family(fam, where, errs, warns):
    def E(msg):
        errs.append(f"{where} {fam.get('family_id', '?')}: {msg}")

    def W(msg):
        warns.append(f"{where} {fam.get('family_id', '?')}: {msg}")

    for k in REQUIRED:
        if k not in fam:
            E(f"missing field '{k}'")
    if errs and any(f"missing field" in e and where in e for e in errs):
        return
    dim = fam["dimension"]
    if dim not in DIMENSIONS:
        E(f"unknown dimension '{dim}'")
        return
    fid = fam["family_id"]
    if fam["split"] == "expB":
        if not re.fullmatch(rf"xb-{DIMENSIONS[dim]}-\d{{2,3}}", fid):
            E(f"expB family_id must be 'xb-{DIMENSIONS[dim]}-NN'")
    elif fam["split"] == "expC":
        if not re.fullmatch(r"xc-\d{2}-(pol-(i|you)|agt-(yes|not))", fid):
            E("expC family_id must be 'xc-NN-pol-{i,you}' or 'xc-NN-agt-{yes,not}'")
    elif not re.fullmatch(rf"{DIMENSIONS[dim]}-\d{{2,3}}", fid):
        E(f"family_id does not match prefix '{DIMENSIONS[dim]}-NN'")
    if fam["split"] not in SPLITS:
        E(f"bad split '{fam['split']}'")
    ctx = fam["context"]
    if ctx is not None and (not isinstance(ctx, str) or "\n" in ctx or not ctx.strip()):
        E("context must be null or a one-line string")

    bare = fam["bare"]
    if not isinstance(bare, str):
        E("bare must be a string")
        return
    bwords = bare.split()
    if not 2 <= len(bwords) <= 4:
        E(f"bare has {len(bwords)} words (need 2-4)")
    if bare != bare.lower():
        E("bare must be lowercase")
    if "[" in bare or "]" in bare:
        E("bare contains chip/bracket tokens")
    cue_hits = [w for w in bwords if w in CUE_WORDS]
    if cue_hits:
        E(f"bare contains critical cue word(s) {cue_hits}")

    nc = fam["noncritical"]
    if not isinstance(nc, str) or not nc.strip():
        E("noncritical must be a nonempty string")
    elif nc.lower() in bwords:
        E(f"noncritical '{nc}' is in bare")

    opts = fam["critical_options"]
    if not isinstance(opts, list) or "unclear/mixed" not in opts:
        E("critical_options must be a list including 'unclear/mixed'")
        opts = opts if isinstance(opts, list) else []

    variants = fam["variants"]
    if not isinstance(variants, dict) or set(variants) != {"A", "B"}:
        E("variants must have exactly keys A and B")
        return
    vals = []
    for vk in ("A", "B"):
        v = variants[vk]
        for k in VARIANT_REQUIRED:
            if k not in v:
                E(f"variant {vk} missing '{k}'")
        if any(k not in v for k in VARIANT_REQUIRED):
            continue
        if "bare" in v and v["bare"] != bare:
            E(f"variant {vk} bare differs from family bare")
        n = len(toks(v["source"]))
        if not 4 <= n <= 12:
            E(f"variant {vk} source has {n} words (need 4-12)")
        if nc and nc.lower() not in toks(v["source"]):
            E(f"noncritical '{nc}' not in variant {vk} source")
        if v["critical_value"] not in opts:
            E(f"variant {vk} critical_value '{v['critical_value']}' not in critical_options")
        vals.append(v["critical_value"])
        if not v["chips"]:
            E(f"variant {vk} has no chips")
        for field in ("chips", "all_chips"):
            for c in v[field]:
                if c in VOCAB:
                    continue
                if NUM_CHIP.match(c) and dim == "time_quantity":
                    continue
                E(f"variant {vk} {field} has non-vocabulary chip {c}")
        if not set(v["chips"]) <= set(v["all_chips"]):
            E(f"variant {vk} chips not a subset of all_chips")
        if len(set(v["all_chips"])) != len(v["all_chips"]):
            E(f"variant {vk} all_chips has duplicates")
        # soft check: every bare word should be traceable to the source (prefix match handles inflection)
        stoks = toks(v["source"])
        for w in bwords:
            if not any(matches(w, t) for t in stoks if len(t) >= 2):
                W(f"bare word '{w}' not found (even by prefix) in variant {vk} source")
    if "custom_channels" in fam:
        validate_custom(fam, E, W)
    if len(vals) == 2 and vals[0] == vals[1]:
        E("variants A and B have the same critical_value")
    if all(k in variants[x] for x in "AB" for k in ("chips",)):
        if variants["A"]["chips"] == variants["B"]["chips"]:
            E("variants A and B have identical critical chips")
    # words that distinguish A from B must not be in bare
    if all("source" in variants[x] for x in "AB"):
        ta, tb = set(toks(variants["A"]["source"])), set(toks(variants["B"]["source"]))
        for w in bwords:
            if (w in ta) != (w in tb):
                other = tb if w in ta else ta
                if any(matches(w, t) for t in other):
                    if w.endswith(("ing", "ed", "s")):
                        W(f"bare word '{w}' matches one variant's exact form; prefer a lemma")
                else:
                    E(f"bare word '{w}' occurs in only one variant (critical cue leak)")


def validate_custom(fam, E, W):
    """custom_channels: {variant: {channel_id: input | {input, commitments, prompts}}}."""
    cc, variants = fam["custom_channels"], fam["variants"]
    if fam["split"] not in {"expB", "expC"}:
        E("custom_channels only allowed in follow-up splits (expB/expC)")
    if not isinstance(cc, dict) or set(cc) != set(variants):
        E("custom_channels must have exactly one entry per variant")
        return
    if len({frozenset(c) for c in cc.values()}) != 1:
        E("custom_channels: variants must use the same channel ids")
    bwords = fam["bare"].split()
    for vk, chans in cc.items():
        v = variants[vk]
        spec = general_spec(v["all_chips"], v.get("general_spec"))
        for cid, c in chans.items():
            tag = f"custom {vk}/{cid}"
            if isinstance(c, str):
                c = {"input": c}
            text, com = c.get("input"), c.get("commitments")
            if not isinstance(text, str) or not text.startswith("Keywords: "):
                E(f"{tag}: input must be a string starting 'Keywords: '")
                continue
            first = text.split("\n")[0]
            if not first.endswith(" " + fam["bare"]) and first != "Keywords: " + fam["bare"]:
                E(f"{tag}: keyword line must end with the family bare words")
            toks_ = BRACKET.findall(text)
            for t in toks_:
                if t not in VOCAB and t not in ALIAS_TO_CHIP and t != P.PAD:
                    E(f"{tag}: unknown bracket token {t}")
            if any(t in ALIAS_TO_CHIP or t == P.PAD for t in toks_) and (
                    "P0x" not in (c.get("prompts") or [])):
                E(f"{tag}: alias/padding tokens need prompts=['P0x'] (only that legend defines them)")
            if com is None:
                com = [t for t in toks_ if t in VOCAB]
            bad = [x for x in com if x not in VOCAB]
            if bad:
                E(f"{tag}: commitments not in vocabulary {bad}")
                continue
            if "\nMeaning:" in text:
                if toks_:
                    E(f"{tag}: a Meaning: line must not also carry chips")
                if text.split("\n", 1)[1] != P.nl_meaning(com):
                    E(f"{tag}: Meaning line does not encode exactly its commitments")
            else:
                decoded = [ALIAS_TO_CHIP.get(t, t) for t in toks_ if t != P.PAD]
                if sorted(decoded) != sorted(com):
                    E(f"{tag}: chips in input {decoded} != commitments {com}")
            for x in com:   # a channel may only state commitments true of the source
                if x in CHIP_TO_GENERAL:
                    d, ok = CHIP_TO_GENERAL[x]
                    if spec[d] is None:
                        W(f"{tag}: {x} commits {d}, which the variant spec leaves open")
                    elif not (ok & spec[d]):
                        E(f"{tag}: {x} contradicts the variant spec on {d}")
            for pid in c.get("prompts") or []:
                if pid not in P.PROMPTS:
                    E(f"{tag}: unknown prompt {pid}")
            if cid.startswith("e_") and sorted(com) != sorted(v["all_chips"]):
                E(f"{tag}: encoding channel must carry exactly all_chips")


def check_factorial(fams, errs):
    """expC: each factorial family has 4 records whose (cell -> source) maps agree, 4 cells."""
    by = {}
    for where, f in fams:
        if f.get("split") == "expC":
            by.setdefault(f.get("factorial_family"), []).append((where, f))
    for ff, recs in by.items():
        cells = {}
        for where, f in recs:
            for v in f["variants"].values():
                if cells.setdefault(v.get("cell"), v["source"]) != v["source"]:
                    errs.append(f"{where} {f['family_id']}: cell {v.get('cell')} source differs across records")
        if len(recs) != 4 or len(cells) != 4 or len(set(cells.values())) != 4:
            errs.append(f"expC {ff}: need 4 records over 4 distinct cells/sources "
                        f"(got {len(recs)} records, {len(cells)} cells)")


def main(paths):
    errs, warns = [], []
    seen = {}
    all_fams = []
    for p in paths:
        p = Path(p)
        counts = Counter()
        n_ctx = 0
        n = 0
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if not line.strip():
                continue
            where = f"{p.name}:{i}"
            try:
                fam = json.loads(line)
            except json.JSONDecodeError as e:
                errs.append(f"{where}: invalid JSON ({e})")
                continue
            n += 1
            before = len(errs)
            validate_family(fam, where, errs, warns)
            fid = fam.get("family_id")
            if fid in seen:
                errs.append(f"{where} {fid}: duplicate family_id (also {seen[fid]})")
            seen[fid] = where
            all_fams.append((where, fam))
            exp_split = p.stem if p.stem in SPLITS else None
            if exp_split and fam.get("split") != exp_split:
                errs.append(f"{where} {fid}: split '{fam.get('split')}' != file '{exp_split}'")
            counts[fam.get("dimension")] += 1
            n_ctx += fam.get("context") is not None
        dims = ", ".join(f"{d}={counts[d]}" for d in DIMENSIONS)
        print(f"{p}: {n} families ({dims}); with context: {n_ctx}")
    check_factorial(all_fams, errs)
    # cross-file near-duplicate check on bare inputs
    for w in warns:
        print("WARN ", w)
    for e in errs:
        print("ERROR", e)
    print(f"{len(errs)} errors, {len(warns)} warnings")
    return 1 if errs else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))

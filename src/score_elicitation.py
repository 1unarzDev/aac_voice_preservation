"""B2: score human keyword elicitation (annotation_package/keyword_elicitation.html) and build requests.

usage: python src/score_elicitation.py [CSV ...]          (default: annotation/returns_elic/*.csv)
          [--key annotation/elicitation_key.jsonl] [--out analysis/elicitation]
          [--items-out data/items/elic.jsonl] [--requests runs/requests/elic.jsonl]
          [--models qwen2.5-7b,...] [--prompts P0,P2,S3] [--no-baseline] [--no-requests] [--recompute]

Source commitments: the s1_cues (revision 1) cue events of each message, stored in the key by
src/make_elicitation_sets.py (--recompute reruns s1_cues.detect_doc with spaCy; same result).
For every human keyword set and, identically, for the POS-cap4 compressor's words, each cue event is
  strict   retained: all its carrier words occur among the typed words (case-folded; n't = not;
           contractions split as spaCy does: don't -> do + not, let's -> let + 's). This is the
           string analogue of s1_cues.cue_loss (POS-cap4's official token-position metric is also
           reported, from the key, as a check);
  lenient  the typed words carry the same commitment in any form: negation word for negated (s1_cues
           NEGATION), '?' or a question word for a question, please/can/could/would/will for a request,
           a hedge-lexicon term (src/s1_hedges.txt, minus s1_cues' non-epistemic exclusions) or
           s1_cues BOOSTERS for certainty, a polite word for politeness, the pronoun class for agent,
           a time word of the same value for time, the same number for quantity; or strict.
A dimension is LOST in a keyword set when any of its cue events is lost (s1_cues convention); unmarked
defaults (affirmative, statement, plain, no politeness) have no carrier and cannot be lost.
Reported per dimension over messages where the source has the cue: human loss (pooled ratings and
per-message mean), POS-cap4 loss, the paired per-message difference human - POS-cap4 with a
bootstrap 95% CI (2000 resamples over messages, seed 20261101), and the same on the simple-random
half only (an unweighted estimate for the corpus frame; enriched strata are reported separately).
Agreement between people: per message mean pairwise Jaccard of the typed word sets (exact and
4-letter-prefix), share of identical sets, Krippendorff nominal alpha on per-(message, dimension)
lenient loss and on the number of words. Skipped messages and invalid word counts are excluded and
listed.
Requests (no generation is run here): data/items/elic.jsonl holds one single-variant family per
message (split elic, opt-in; critical dimension = enriched stratum, else the first present cue in
W-B's focal priority, else polarity with focal_none) with custom channels human_<ID>
("Keywords: <typed words, lowercased>", commitments []) and, unless --no-baseline, pos_cap4 for a
matched compressor baseline; runs/requests/elic.jsonl is built from it with build_requests.build for
the 4 models under test x P0/P2/S3.
Outputs: <out>/report.md, messages.csv, ratings.csv, summary.json.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import random
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import s1_cues as C  # noqa: E402
from score_gold import alpha_nominal, wilson  # noqa: E402

DIMS = ["polarity", "speech_act", "certainty", "politeness", "agent", "time", "quantity"]
FOCAL_PRIORITY = ["polarity", "certainty", "politeness", "speech_act", "agent"]
CRIT_OPTIONS = {
    "polarity": ["negated", "affirmative", "unclear/mixed"],
    "agent": ["speaker", "addressee", "we/joint", "third party", "unclear/mixed"],
    "certainty": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic", "unclear/mixed"],
    "politeness": ["polite", "plain", "unclear/mixed"],
    "speech_act": ["statement", "question", "request/command", "refusal", "acceptance", "offer/suggestion", "unclear/mixed"],
}
VALUE_CHIP = {
    "polarity": {"negated": "[NOT]", "affirmative": "[YES]"},
    "speech_act": {"question": "[?]", "request/command": "[ASK]", "refusal": "[REFUSE]", "statement": "[TELL]"},
    "agent": {"speaker": "[I]", "addressee": "[YOU]", "we/joint": "[WE]", "third party": "[THEY]"},
    "certainty": {"hedged/uncertain": "[MAYBE]", "strongly certain/emphatic": "[SURE]", "plain assertion": "[SURE]"},
    "politeness": {"please": "[PLEASE]", "none": "[PLAIN]"},
}
# s1_cues.detect_doc treats these lexicon matches as non-epistemic (kept identical here)
NON_EPISTEMIC = {"can", "should", "sorry", "about", "around", "often", "sometimes", "usually", "typically", "only",
                 "just", "merely", "simply", "barely", "hardly", "feel", "feels", "a little", "a bit"}
QWORDS = {"what", "whats", "who", "whom", "whose", "when", "where", "why", "how", "which"}
REQUEST_WORDS = {"please", "can", "could", "would", "will", "pls", "plz"}
POLITE_WORDS = {"please", "pls", "plz", "could", "would", "mind", "excuse", "thank", "thanks", "sorry", "apologies"}
PRONOUN_CLASS = {"speaker": {"i", "me", "my", "myself", "mine"}, "addressee": {"you", "your", "yours", "yourself", "u", "ur"},
                 "we/joint": {"we", "us", "our", "ours", "let", "lets"}}
TIME_VALUE_WORDS = {"past": {"yesterday", "ago", "previously", "last", "already", "was", "were", "did"},
                    "future": {"tomorrow", "later", "soon", "tonight", "will", "next", "gonna"},
                    "present": {"now", "today", "currently"}}
NUMBER_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
                "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "twenty": "20"}
SPLIT = re.compile(r"^(.+?)(n't|'s|'ll|'m|'re|'ve|'d)$")
CANON = {"n't": "not", "wo": "will", "ca": "can", "'ll": "will", "nt": "not"}


def hedge_terms():
    terms = [s.split("#", 1)[0].strip().lower() for s in (ROOT / "src/s1_hedges.txt").read_text().splitlines()]
    terms = [t for t in terms if t and t not in NON_EPISTEMIC]
    return {t for t in terms if " " not in t}, [t for t in terms if " " in t]


HEDGE_1, HEDGE_N = hedge_terms()


def word_set(words: list[str]) -> set[str]:
    """Typed (or compressor) words -> comparable token set (contractions split, n't = not)."""
    out = set()
    for w in words:
        w = C.norm(w).strip()
        w = w.strip(".,;:!\"()[]{}")
        if not w:
            continue
        if "?" in w:
            out.add("?"); w = w.replace("?", "")
            if not w:
                continue
        out.add(w)
        m = SPLIT.match(w)
        if m:
            out.update({m.group(1), m.group(2)})
        if w in {"dont", "doesnt", "didnt", "cant", "wont", "isnt", "arent", "wasnt", "werent", "cannot", "couldnt",
                 "wouldnt", "shouldnt", "havent", "hasnt"}:
            out.update({"not", w[:-2] if w.endswith("nt") else w})
        if w in {"lets"}:
            out.update({"let", "'s"})
    return {CANON.get(t, t) for t in out}


def ev_tokens(ev: str) -> set[str]:
    return {CANON.get(t, t) for t in (C.norm(x).strip() for x in ev.split(" ")) if t}


def survives(cue: dict, ws: set[str], joined: str) -> tuple[bool, bool]:
    strict = ev_tokens(cue["evidence"]) <= ws
    d, v = cue["dimension"], cue["value"]
    len_ = strict
    if d == "polarity":
        len_ = strict or bool(ws & (C.NEGATION | {"not", "no"}))
    elif d == "speech_act":
        if v == "question":
            len_ = strict or "?" in ws or bool(ws & QWORDS)
        elif v == "request/command":
            len_ = strict or bool(ws & REQUEST_WORDS)
        elif v == "refusal":
            len_ = strict or bool(ws & (C.NEGATION | {"not", "no", "refuse"}))
    elif d == "certainty":
        if v == "hedged/uncertain":
            len_ = strict or bool(ws & HEDGE_1) or any(re.search(rf"\b{re.escape(p)}\b", joined) for p in HEDGE_N)
        else:
            len_ = strict or bool(ws & C.BOOSTERS)
    elif d == "politeness":
        len_ = strict or bool(ws & POLITE_WORDS)
    elif d == "agent":
        len_ = strict or bool(ws & PRONOUN_CLASS.get(v, set()))
    elif d == "time":
        len_ = strict or bool(ws & TIME_VALUE_WORDS.get(v, set())) or any(C.TIME_WORDS.get(t) == v for t in ws)
    elif d == "quantity":
        num = NUMBER_WORDS.get(v, v)
        len_ = strict or bool({t for t in ws} & {v, num}) or any(NUMBER_WORDS.get(t) == num for t in ws)
    return strict, len_


def loss_profile(cues: list[dict], words: list[str]) -> dict:
    ws = word_set(words)
    joined = " ".join(C.norm(w) for w in words)
    res = {}
    for d in DIMS:
        cs = [c for c in cues if c["dimension"] == d]
        if not cs:
            res[d] = None
            continue
        sv = [survives(c, ws, joined) for c in cs]
        res[d] = {"strict_lost": not all(s for s, _ in sv), "lenient_lost": not all(l for _, l in sv)}
    return res


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rate(vals):
    known = [v for v in vals if v is not None]
    k, n = sum(known), len(known)
    return {"k": k, "n": n, "p": (k / n) if n else None, "ci": wilson(k, n)}


def fmt(r):
    if not r or not r["n"]:
        return "n/a"
    lo, hi = r["ci"]
    return f"{r['k']}/{r['n']} = {100 * r['p']:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def boot_ci(diffs, n=2000, seed=20261101):
    if not diffs:
        return None
    rnd = random.Random(seed)
    ms = sorted(sum(rnd.choice(diffs) for _ in diffs) / len(diffs) for _ in range(n))
    return [ms[int(0.025 * n)], ms[int(0.975 * n) - 1]]


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else None


def stem4(ws):
    return {w[:4] for w in ws if w not in {"?"}}


def load_returns(paths, key):
    ratings, problems = {}, []
    for p in paths:
        for r in read_csv(p):
            if r.get("practice") == "1" or r["item_id"].startswith("prac-"):
                continue
            if r["item_id"] not in key:
                problems.append(f"{Path(p).name}: unknown item {r['item_id']}"); continue
            a = r["annotator"].strip()
            k = (a, r["item_id"])
            if k in ratings and ratings[k]["exported_at"] > r.get("exported_at", ""):
                continue
            ratings[k] = {"annotator": a, "item_id": r["item_id"], "set_file": r.get("set_file", ""),
                          "keywords": " ".join((r.get("keywords") or "").split()), "skipped": r.get("skipped") == "1",
                          "note": r.get("note", ""), "time_ms": float(r["time_ms"]) if r.get("time_ms") else None,
                          "exported_at": r.get("exported_at", "")}
    valid = {}
    for k, r in ratings.items():
        n = len(r["keywords"].split())
        if r["skipped"]:
            r["status"] = "skipped"
        elif not 2 <= n <= 4:
            r["status"] = "invalid_word_count"; problems.append(f"{k}: {n} words; excluded")
        else:
            r["status"] = "ok"; valid[k] = r
    return ratings, valid, problems


def focal_dim(k):
    if k["stratum"].startswith("enriched_"):
        return k["stratum"][len("enriched_"):], False
    d = next((d for d in FOCAL_PRIORITY if k["present"].get(d)), None)
    return (d, False) if d else ("polarity", True)


def crit_value(dim, v):
    if dim == "politeness":
        return "plain" if v == "none" else "polite"
    return v if v in CRIT_OPTIONS[dim] else "unclear/mixed"


def safe(a):
    return re.sub(r"[^A-Za-z0-9_-]", "_", a)


def build_families(key, valid, baseline):
    fams = []
    by_item = defaultdict(list)
    for r in valid.values():
        by_item[r["item_id"]].append(r)
    for iid, k in sorted(key.items()):
        rs = sorted(by_item.get(iid, []), key=lambda r: r["annotator"])
        if not rs:
            continue
        dim, none = focal_dim(k)
        gen = {d: k["detector_labels"][d] for d in ["polarity", "speech_act", "agent", "certainty", "politeness"]}
        allc = sorted({VALUE_CHIP[d][gen[d]] for d in VALUE_CHIP if gen[d] in VALUE_CHIP[d]})
        import prompts as P
        allc = P.sort_chips(allc)
        chips = [VALUE_CHIP[dim].get(gen[dim])] if VALUE_CHIP[dim].get(gen[dim]) else ["[TELL]" if dim == "speech_act" else "[YES]"]
        if dim == "politeness" and gen[dim] != "none":
            chips = ["[PLEASE]"]
        allc = P.sort_chips(sorted(set(allc) | set(chips)))
        chans = {f"human_{safe(r['annotator'])}": {"input": "Keywords: " + r["keywords"].lower(), "commitments": []} for r in rs}
        if baseline:
            chans["pos_cap4"] = {"input": "Keywords: " + " ".join(k["pos_cap4"]), "commitments": []}
        fams.append({"family_id": f"elic-{k['id']}", "dimension": dim, "split": "elic", "corpus_item": True, "context": None,
                     "source_id": k["id"], "elic_item_id": iid, "sample": k["sample"], "stratum": k["stratum"],
                     "focal_dim": dim, "focal_none": none, "inclusion_prob": k["inclusion_prob"],
                     "value_source": "detector",
                     "variants": {"A": {"source": k["text"], "critical_value": crit_value(dim, gen[dim]), "chips": chips,
                                        "all_chips": allc, "general_spec": gen}},
                     "bare": " ".join(k["pos_cap4"]), "noncritical": None, "critical_options": CRIT_OPTIONS[dim],
                     "notes": "B2 keyword elicitation: human keyword channels (human_<annotator>) + POS-cap4 baseline.",
                     "custom_channels": {"A": chans}})
    return fams


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "elicitation_key.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "elicitation"))
    ap.add_argument("--items-out", default=str(ROOT / "data" / "items" / "elic.jsonl"))
    ap.add_argument("--requests", default=str(ROOT / "runs" / "requests" / "elic.jsonl"))
    ap.add_argument("--models"); ap.add_argument("--prompts", default="P0,P2,S3")
    ap.add_argument("--no-baseline", action="store_true"); ap.add_argument("--no-requests", action="store_true")
    ap.add_argument("--recompute", action="store_true", help="rerun s1_cues on the messages (needs spaCy)")
    a = ap.parse_args(argv)
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / "returns_elic" / "*.csv")))
    if not paths:
        print("no return CSVs found (annotation/returns_elic/*.csv)", file=sys.stderr)
        return 1
    key = {k["item_id"]: k for k in map(json.loads, Path(a.key).open())}
    if a.recompute:
        nlp = C.load_nlp(); lex = C.Lexicon(nlp)
        for k in key.values():
            d = C.detect_doc(nlp(k["text"]), lex)
            k["detector_cues"], k["detector_labels"] = d["cues"], d["labels"]
    ratings, valid, problems = load_returns(paths, key)
    for r in valid.values():
        r["loss"] = loss_profile(key[r["item_id"]]["detector_cues"], r["keywords"].split())
        r["ws"] = word_set(r["keywords"].split())
    by_item = defaultdict(list)
    for r in valid.values():
        by_item[r["item_id"]].append(r)
    msgs = []
    for iid, k in sorted(key.items()):
        rs = by_item.get(iid, [])
        pos = loss_profile(k["detector_cues"], k["pos_cap4"])
        row = {"item_id": iid, "source_id": k["id"], "set": k["set"], "sample": k["sample"], "stratum": k["stratum"],
               "inclusion_prob": k["inclusion_prob"], "text": k["text"], "pos_cap4": " ".join(k["pos_cap4"]),
               "n_ratings": len(rs), "n_skipped": sum(1 for (a, i), r in ratings.items() if i == iid and r["status"] == "skipped"),
               "human_keywords": " | ".join(f"{r['annotator']}: {r['keywords']}" for r in sorted(rs, key=lambda r: r["annotator"]))}
        for d in DIMS:
            present = pos[d] is not None
            row[f"{d}_present"] = present
            for m in ("strict", "lenient"):
                row[f"{d}_{m}_human_loss"] = mean([float(r["loss"][d][f"{m}_lost"]) for r in rs]) if present and rs else None
                row[f"{d}_{m}_pos_loss"] = float(pos[d][f"{m}_lost"]) if present else None
            row[f"{d}_official_pos_loss"] = float(k["lost_pos_cap4"][d]) if present and d in k["lost_pos_cap4"] else None
        pj = [jaccard(x["ws"], y["ws"]) for x, y in combinations(rs, 2)]
        ps = [jaccard(stem4(x["ws"]), stem4(y["ws"])) for x, y in combinations(rs, 2)]
        row["mean_pairwise_jaccard"] = mean(pj)
        row["mean_pairwise_jaccard_stem4"] = mean(ps)
        row["all_identical"] = (len({frozenset(r["ws"]) for r in rs}) == 1) if len(rs) >= 2 else None
        posw = word_set(k["pos_cap4"])
        row["mean_jaccard_with_pos_cap4"] = mean([jaccard(r["ws"], posw) for r in rs])
        row["mean_n_words"] = mean([len(r["keywords"].split()) for r in rs])
        msgs.append(row)
    rated = [m for m in msgs if m["n_ratings"]]
    S = {"returns": [str(p) for p in paths], "n_messages_key": len(key), "n_messages_rated": len(rated),
         "annotators": sorted({r["annotator"] for r in ratings.values()}),
         "n_ratings_valid": len(valid), "status_counts": dict(Counter(r["status"] for r in ratings.values())),
         "problems": problems, "by_dimension": {}, "agreement": {}, "words": {}}
    for d in DIMS:
        ms = [m for m in rated if m[f"{d}_present"]]
        x = {"n_messages_with_cue": len(ms)}
        for meth in ("strict", "lenient"):
            pooled = [r["loss"][d][f"{meth}_lost"] for r in valid.values() if r["loss"][d] is not None]
            diffs = [m[f"{d}_{meth}_human_loss"] - m[f"{d}_{meth}_pos_loss"] for m in ms]
            rand = [m for m in ms if m["sample"] == "random"]
            rdiffs = [m[f"{d}_{meth}_human_loss"] - m[f"{d}_{meth}_pos_loss"] for m in rand]
            x[meth] = {"human_pooled": rate(pooled), "human_message_mean": mean([m[f"{d}_{meth}_human_loss"] for m in ms]),
                       "pos_cap4": rate([bool(m[f"{d}_{meth}_pos_loss"]) for m in ms]),
                       "diff_human_minus_pos": mean(diffs), "diff_ci95": boot_ci(diffs),
                       "majority_humans_keep": rate([m[f"{d}_{meth}_human_loss"] < 0.5 for m in ms]),
                       "random_half": {"n": len(rand), "human_message_mean": mean([m[f"{d}_{meth}_human_loss"] for m in rand]),
                                       "pos_cap4": mean([m[f"{d}_{meth}_pos_loss"] for m in rand]),
                                       "diff_human_minus_pos": mean(rdiffs), "diff_ci95": boot_ci(rdiffs)}}
        x["official_pos_cap4_token_metric"] = rate([bool(m[f"{d}_official_pos_loss"]) for m in ms if m[f"{d}_official_pos_loss"] is not None])
        x["by_stratum"] = {s: {"n": len([m for m in ms if m["stratum"] == s]),
                               "human_lenient": mean([m[f"{d}_lenient_human_loss"] for m in ms if m["stratum"] == s]),
                               "pos_lenient": mean([m[f"{d}_lenient_pos_loss"] for m in ms if m["stratum"] == s])}
                           for s in sorted({m["stratum"] for m in ms})}
        S["by_dimension"][d] = x
    units = defaultdict(list)
    for r in valid.values():
        for d in DIMS:
            if r["loss"][d] is not None:
                units[(r["item_id"], d)].append(int(r["loss"][d]["lenient_lost"]))
    lu = [u for u in units.values() if len(u) >= 2]
    nw = defaultdict(list)
    for r in valid.values():
        nw[r["item_id"]].append(len(r["keywords"].split()))
    nwu = [[n - 2 for n in u] for u in nw.values() if len(u) >= 2]
    S["agreement"] = {"mean_pairwise_jaccard": mean([m["mean_pairwise_jaccard"] for m in rated]),
                      "mean_pairwise_jaccard_stem4": mean([m["mean_pairwise_jaccard_stem4"] for m in rated]),
                      "share_all_identical": rate([m["all_identical"] for m in rated if m["all_identical"] is not None]),
                      "alpha_lenient_loss": alpha_nominal(lu, 2) if lu else None, "alpha_lenient_loss_units": len(lu),
                      "alpha_n_words_nominal": alpha_nominal(nwu, 3) if nwu else None}
    S["words"] = {"human_mean_n_words": mean([len(r["keywords"].split()) for r in valid.values()]),
                  "human_n_words_counts": dict(Counter(len(r["keywords"].split()) for r in valid.values())),
                  "pos_cap4_mean_n_words": mean([len(key[i]["pos_cap4"]) for i in by_item]),
                  "mean_jaccard_human_vs_pos_cap4": mean([m["mean_jaccard_with_pos_cap4"] for m in rated]),
                  "share_human_words_in_message": mean([mean([float(w in word_set(C.norm(key[r["item_id"]]["text"]).split())) for w in r["ws"]])
                                                       for r in valid.values()])}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with open(out / "messages.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(msgs[0])); w.writeheader(); w.writerows(msgs)
    with open(out / "ratings.csv", "w", newline="", encoding="utf-8") as f:
        head = ["annotator", "item_id", "set_file", "status", "keywords", "note", "time_ms"] + \
               [f"{d}_{m}_lost" for d in DIMS for m in ("strict", "lenient")]
        w = csv.writer(f); w.writerow(head)
        for r in sorted(ratings.values(), key=lambda r: (r["item_id"], r["annotator"])):
            lp = r.get("loss") or {}
            w.writerow([r["annotator"], r["item_id"], r["set_file"], r["status"], r["keywords"], r["note"], r["time_ms"]] +
                       [("" if not lp.get(d) else int(lp[d][f"{m}_lost"])) for d in DIMS for m in ("strict", "lenient")])
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")

    def pct(v):
        return "n/a" if v is None else f"{100 * v:.1f}%"

    def ci(c):
        return "" if not c else f" [{100 * c[0]:.1f}, {100 * c[1]:.1f}]"
    L = ["# B2 human keyword elicitation: which commitments survive\n",
         f"Generated by `src/score_elicitation.py`. {len(paths)} return file(s), annotators {', '.join(S['annotators'])}; "
         f"{len(valid)} valid keyword sets on {len(rated)}/{len(key)} messages; status {S['status_counts']}.\n",
         "Loss = the typed words do not carry the source's cue (any cue of that dimension). strict = the cue's own words; "
         "lenient = any word carrying the same commitment. Pooled = over keyword sets; diff = per-message mean human loss "
         "minus POS-cap4 loss, bootstrap 95% CI over messages. Messages are a stratified sample (150 random + 150 cue-enriched); "
         "the random-half column is the unweighted frame estimate.\n",
         "| dimension | messages with cue | human loss, lenient (pooled) | POS-cap4 loss, lenient | diff (all) | diff (random half, n) | human loss, strict | POS-cap4 strict / official |",
         "|---|---|---|---|---|---|---|---|"]
    for d in DIMS:
        x = S["by_dimension"][d]
        if not x["n_messages_with_cue"]:
            continue
        le, st = x["lenient"], x["strict"]
        L.append(f"| {d} | {x['n_messages_with_cue']} | {fmt(le['human_pooled'])} | {fmt(le['pos_cap4'])} | "
                 f"{pct(le['diff_human_minus_pos'])}{ci(le['diff_ci95'])} | {pct(le['random_half']['diff_human_minus_pos'])}"
                 f"{ci(le['random_half']['diff_ci95'])}, {le['random_half']['n']} | {fmt(st['human_pooled'])} | "
                 f"{fmt(st['pos_cap4'])} / {fmt(x['official_pos_cap4_token_metric'])} |")
    ag = S["agreement"]
    L += ["\n## Agreement between people\n",
          f"- mean pairwise Jaccard of typed word sets: {pct(ag['mean_pairwise_jaccard'])} (4-letter prefix: {pct(ag['mean_pairwise_jaccard_stem4'])})",
          f"- all annotators typed the same set: {fmt(ag['share_all_identical'])}",
          f"- Krippendorff alpha on lenient loss per (message, dimension): {ag['alpha_lenient_loss']} ({ag['alpha_lenient_loss_units']} units)",
          f"- Krippendorff alpha on number of words (nominal): {ag['alpha_n_words_nominal']}",
          "\n## Words\n",
          f"- mean words typed: {S['words']['human_mean_n_words']} (counts {S['words']['human_n_words_counts']}); POS-cap4 mean {S['words']['pos_cap4_mean_n_words']}",
          f"- mean Jaccard human vs POS-cap4: {pct(S['words']['mean_jaccard_human_vs_pos_cap4'])}; "
          f"share of typed words found in the message: {pct(S['words']['share_human_words_in_message'])}"]
    if problems:
        L += ["\n## Problems\n"] + [f"- {p}" for p in problems[:100]]
    fams = build_families(key, valid, not a.no_baseline)
    if not a.no_requests:
        Path(a.items_out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.items_out, "w", encoding="utf-8") as f:
            for fam in fams:
                f.write(json.dumps(fam, ensure_ascii=False) + "\n")
        import build_requests as B
        import models as M
        for fam in fams:
            fam["_file"] = Path(a.items_out).name
            B.validate(fam)
        models = [m.strip() for m in a.models.split(",")] if a.models else M.UNDER_TEST
        prompts_ = [p.strip() for p in a.prompts.split(",") if p.strip()]
        reqs = B.build(fams, models, prompts_, [])
        Path(a.requests).parent.mkdir(parents=True, exist_ok=True)
        with open(a.requests, "w", encoding="utf-8") as f:
            for r in reqs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        n_t = sum(len(r["targets"]) for r in reqs)
        L.append(f"\nRequests (not run): {len(fams)} families -> {n_t} (target x sample) cells -> {len(reqs)} unique requests "
                 f"({len(models)} models x {'/'.join(prompts_)}) -> `{a.requests}`; items -> `{a.items_out}`.")
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())

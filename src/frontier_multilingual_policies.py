"""AAC-unit endpoints and policy benchmarks from summary.json / labelled rows. SLP weights read from expert_package/returns_slp."""
import sys, json, csv, glob, collections
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
import frontier_multilingual_register as det

sev = collections.defaultdict(list)
for f in glob.glob(str(ROOT / "expert_package/returns_slp/slp_rating_SLP*.csv")):
    for r in csv.DictReader(open(f)):
        if r["task"] == "1" and r["severity"].strip().isdigit():
            sev[r["item_id"]].append(int(r["severity"]))
W = {k: float(np.mean(v)) / 5 for k, v in sev.items()}
S = json.load(open(OUT / "summary.json"))
rows = []
R = S["register"]; P = S["polarity"]
PI = {"0.5%": 0.005, "2.7%": 0.027, "10%": 0.10}
# polarity policies per language (pooled over the 3 models); weights NEG
for lang in LANGS:
    e = P[f"pooled|{lang}"]
    ab, ar = e["P_aff_given_B_bare"], e["P_aff_given_B_restored"]
    for piname, pi in PI.items():
        base = 1000 * pi * ab
        for pol_, ask, rev in (("always_commit(bare)", 0, base), ("always_ask(chip)", 1, 1000 * pi * ar)):
            rows.append({"domain": "polarity", "lang": lang, "pi": piname, "policy": pol_, "ask_rate": ask, "taps_per_1000": 1000 * ask,
                         "silent_events_per_1000": rev, "slp_weighted_per_1000": rev * W["NEG"], "note": "NEG weight"})
        for p in (0.1, 0.25, 0.5, 0.75):
            rev = 1000 * pi * ((1 - p) * ab + p * ar)
            rows.append({"domain": "polarity", "lang": lang, "pi": piname, "policy": f"random_ask(p={p})", "ask_rate": p, "taps_per_1000": 1000 * p,
                         "silent_events_per_1000": rev, "slp_weighted_per_1000": rev * W["NEG"], "note": "expected value"})
        rows.append({"domain": "polarity", "lang": lang, "pi": piname, "policy": "G1_guard(no_written_cue)", "ask_rate": 0, "taps_per_1000": 0,
                     "silent_events_per_1000": base, "slp_weighted_per_1000": base * W["NEG"], "note": "guard cannot fire without a cue list: equals always_commit (declared in PLAN; not run)"})
# register policies: pooled, grid piV
for lang in LANGS:
    b = R[f"bare|pooled|{lang}"]
    a = b["n_with_address"] / b["n_outputs"]
    tsh = b["T"] / max(1, b["T"] + b["V"]); vsh = 1 - tsh
    cf, ci = R[f"chip_formal|pooled|{lang}"], R[f"chip_informal|pooled|{lang}"]
    eV, eT = 1 - cf["match_among_address"], 1 - ci["match_among_address"]   # chip error when need is V (formal chip) / T
    for piV in (0.1, 0.3, 0.5, 0.7, 0.9):
        mis_bare = a * (piV * tsh + (1 - piV) * vsh)           # model commits T when V needed, or V when T needed
        mis_chip_all = piV * cf["address_rate"] * eV + (1 - piV) * ci["address_rate"] * eT
        mis_trig = a * (piV * eV + (1 - piV) * eT)             # ask only when an address form is produced; tap = 1 per asked message
        for pol_, ask, mis in (("always_commit(bare)", 0, mis_bare), ("always_ask(chip)", 1, mis_chip_all), ("ask_if_address_form", a, mis_trig)):
            rows.append({"domain": "register", "lang": lang, "pi": f"piV={piV}", "policy": pol_, "ask_rate": ask, "taps_per_1000": 1000 * ask,
                         "silent_events_per_1000": 1000 * mis, "slp_weighted_per_1000": 1000 * mis * W["POL"], "note": "POL weight used as approximation; mismatch = address form differs from needed register"})
        for p in (0.25, 0.5):
            mis = (1 - p) * mis_bare + p * mis_chip_all
            rows.append({"domain": "register", "lang": lang, "pi": f"piV={piV}", "policy": f"random_ask(p={p})", "ask_rate": p, "taps_per_1000": 1000 * p,
                         "silent_events_per_1000": 1000 * mis, "slp_weighted_per_1000": 1000 * mis * W["POL"], "note": "expected value"})
with open(OUT / "policies.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
# exploratory: translator's own register on the 'you' source sentences
tr = jl(OUT / "translations.jsonl")
tc = {}
for lang in LANGS:
    c = collections.Counter(det.label(lang, r["t"]["A"]) for r in tr if r["kind"] == "REG" and r["lang"] == lang and r["t"])
    tc[lang] = dict(c)
json.dump({"slp_weights": W, "slp_severities": dict(sev), "translator_register_on_you_sources_exploratory": tc}, open(OUT / "slp_weights_and_translator.json", "w"), indent=1)
print(W, tc)

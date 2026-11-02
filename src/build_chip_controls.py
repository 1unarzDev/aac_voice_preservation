"""E2 (T3 chip-gain controls): items + requests for two control arms on hw1, P0, 4 models.

  irrel : the `noncrit` input plus ONE chip from a different dimension than the critical one (identical for A and B, so the
          input carries no critical information). Chip = first, in PRIORITY order, of the chips that BOTH variants already
          commit to (A.all_chips & B.all_chips) outside the critical dimension, so the chip is true of the source of both
          variants (no input-builder conflicts, SPEC R5 rule).
  nlcue : the critical cue as a plain WORD instead of the chip(s): words replace the chips in the chip1 position
          ("Keywords: not want go party"). Mapping NL below. Legend stays (P0 unchanged).
Declared before any generation (analysis/chip_controls/PLAN.md). Existing hw1 channels noncrit / chip1 are the comparators.
    python src/build_chip_controls.py
"""
import json, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import build_requests as BR, models as M, prompts as P

DIM_OF = {**{c: "polarity" for c in ("[NOT]", "[YES]")}, **{c: "speech_act" for c in ("[TELL]", "[?]", "[ASK]", "[REFUSE]")},
          **{c: "politeness" for c in ("[PLEASE]", "[PLAIN]")}, **{c: "agent" for c in ("[I]", "[YOU]", "[WE]", "[THEY]")},
          **{c: "time_quantity" for c in ("[PAST]", "[NOW]", "[LATER]")}, **{c: "certainty" for c in ("[MAYBE]", "[SURE]")},
          "[WANT]": "desire", "[MUST]": "obligation"}
PRIORITY = ["[I]", "[YOU]", "[WE]", "[THEY]", "[PAST]", "[NOW]", "[LATER]", "[TELL]", "[ASK]", "[?]", "[WANT]", "[MUST]"]
NL = {"[NOT]": "not", "[YES]": "yes", "[?]": "question", "[TELL]": "statement", "[ASK]": "request", "[REFUSE]": "refuse",
      "[I]": "I", "[YOU]": "you", "[THEY]": "they", "[WE]": "we", "[MAYBE]": "maybe", "[SURE]": "sure",
      "[PLEASE]": "please", "[PLAIN]": "plain", "[PAST]": "past", "[NOW]": "now", "[LATER]": "later"}

fams = BR.load_families(str(ROOT / "data/items/hw.jsonl"), "hw")
out, log, nochip = [], [], []
for f in fams:
    A_, B_ = f["variants"]["A"], f["variants"]["B"]
    shared = set(A_["all_chips"]) & set(B_["all_chips"])
    cands = [c for c in PRIORITY if c in shared and DIM_OF[c] != f["dimension"]]
    if not cands: nochip.append(f["family_id"]); continue
    chip = cands[0]
    cc = {}
    for vn, v in f["variants"].items():
        nc = BR.input_text(f, vn, "noncrit")                       # "Keywords: <bare + noncritical word>"
        irrel = nc.replace("Keywords: ", f"Keywords: {chip} ", 1)
        words = " ".join(NL[c] for c in P.sort_chips(v["chips"]))
        nlcue = f"Keywords: {words} {f['bare']}"
        cc[vn] = {"irrel": {"input": irrel, "commitments": [chip], "prompts": ["P0"]},
                  "nlcue": {"input": nlcue, "commitments": list(v["chips"]), "prompts": ["P0"]}}
    g = {k: v for k, v in f.items() if k != "_file"}
    g.update(split="hwctl", custom_channels=cc, irrel_chip=chip, irrel_chip_dim=DIM_OF[chip], base_family_id=f["family_id"])
    out.append(g)
    log.append(dict(family_id=f["family_id"], dimension=f["dimension"], irrel_chip=chip, irrel_dim=DIM_OF[chip],
                    borderline=bool(f["dimension"] == "certainty" and chip == "[TELL]")))
p = ROOT / "data/items_ext/hwctl_items.jsonl"
with p.open("w") as fh:
    for g in out: fh.write(json.dumps(g, ensure_ascii=False) + "\n")
(ROOT / "analysis/chip_controls/mapping.json").write_text(json.dumps(
    {"NL_mapping": NL, "irrelevant_chip_priority": PRIORITY, "dimension_of_chip": DIM_OF, "no_irrelevant_chip_available": nochip,
     "per_family": log, "chip_counts_by_dimension": {d: dict(collections.Counter(l["irrel_chip"] for l in log if l["dimension"] == d))
                                                       for d in sorted({l["dimension"] for l in log})}}, indent=1))
fam2 = BR.load_families(str(p), "hwctl")
reqs = BR.build(fam2, M.UNDER_TEST, ["P0"], BR.CHANNELS)
rp = ROOT / "runs/requests/hwctl.jsonl"
with rp.open("w") as fh:
    for r in reqs: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
hit = sum((ROOT / f"runs/cache/{r['request_key']}.json").exists() for r in reqs)
print(len(fam2), "families;", "no chip:", nochip, ";", len(reqs), "unique requests;", hit, "already cached")
print(collections.Counter(r["targets"][0]["channel"] for r in reqs))

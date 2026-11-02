"""Dry-run of 'add a cue to the harness' without editing the repository.

Monkeypatches ONE table entry (labels.CHIP_TO_GENERAL['[THANKS]']), then
  (1) asks the R5 validator (src/validate_cue_inputs.py) to check a rendered input that uses it,
  (2) re-scores every stored hw1 output with src/attribute.py (no model calls), timed.
Writes paper/se4all/extend_cost.json, read by make_macros.py. Timing varies by machine; re-run to refresh.
"""
import json, pathlib, sys, time, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import labels
labels.CHIP_TO_GENERAL["[THANKS]"] = ("politeness", frozenset({"thanks/apology"}))
import validate_cue_inputs as V
import attribute

ok = V.validate("Keywords: [THANKS] extra pillow", V.Requirement("politeness", "thanks/apology"))
bad = V.validate("Keywords: [THANKS] extra pillow", V.Requirement("politeness", "none"))
t = time.time()
df = attribute.score(ROOT / "runs/hw1", ROOT / "annotation/written/hw_candidates.jsonl")
dt = time.time() - t
loc = lambda p: sum(1 for l in (ROOT / p).read_text().splitlines() if l.strip() and not l.strip().startswith("#"))
n_chips = len(re.findall(r'^\s+"\[[^\]]+\]": \(', (ROOT / "src/labels.py").read_text(), flags=re.M)) - 1  # minus the patched one is not in file
out = dict(new_entry_lines=1, validator_ok=ok.verdict, validator_conflict=bad.verdict,
           rescored_rows=int(len(df)), rescore_seconds=round(dt, 1), model_calls=0,
           loc_attribute=loc("src/attribute.py"), loc_validator=loc("src/validate_cue_inputs.py"),
           loc_labels=loc("src/labels.py"), n_chips=n_chips + 1)
(ROOT / "paper/se4all/extend_cost.json").write_text(json.dumps(out, indent=1))
print(out)

"""R5 input-builder validator: unit cases plus the frozen W-B replay (no model/judge calls)."""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from labels import GENERAL_OPTIONS  # noqa: E402
from validate_cue_inputs import (CueContractError, Requirement, require_valid, replay,  # noqa: E402
                                 requirement_set, validate)

R = Requirement


class UnitCases(unittest.TestCase):
    def test_known_conflict_shapes_rejected(self):
        v = validate("Keywords: [MAYBE] extra pillow night", R("certainty", "plain assertion"))
        self.assertEqual(v.verdict, "conflicting")
        self.assertFalse(v.certifies_source)
        self.assertEqual(validate("Keywords: [?] want help", R("speech_act", "offer/suggestion")).verdict, "conflicting")
        self.assertEqual(validate("Keywords: [ASK] help", R("speech_act", "offer/suggestion")).verdict, "conflicting")

    def test_sure_is_coarser_than_emphatic_and_never_certified(self):
        v = validate("Keywords: [SURE] love it", R("certainty", "strongly certain/emphatic"))
        self.assertEqual(v.verdict, "compatible_but_coarser")
        self.assertEqual(v.accepted, ["plain assertion", "strongly certain/emphatic"])
        self.assertFalse(v.certifies_source)
        with self.assertRaises(CueContractError):
            require_valid("Keywords: [SURE] love it", R("certainty", "strongly certain/emphatic"))
        require_valid("Keywords: [SURE] love it", R("certainty", "strongly certain/emphatic"), allow_coarser=True)
        self.assertEqual(validate("Keywords: [SURE] love it", R("certainty", "plain assertion")).verdict, "compatible")

    def test_supported_chips_compatible(self):
        cases = [("[NOT]", "polarity", "negated"), ("[?]", "speech_act", "question"),
                 ("[ASK]", "speech_act", "request/command"), ("[MAYBE]", "certainty", "hedged/uncertain"),
                 ("[I]", "agent", "speaker"), ("[YOU]", "agent", "addressee"), ("[THEY]", "agent", "third party"),
                 ("[PLEASE]", "politeness", "please"), ("[PLEASE]", "politeness", "thanks/apology")]
        for chip, d, val in cases:
            v = require_valid(f"Keywords: {chip} go home", R(d, val), baseline="Keywords: go home")
            self.assertEqual(v.verdict, "compatible", (chip, d, val))

    def test_word_markers_narrow_scope(self):
        self.assertEqual(validate("Keywords: could you make call", R("politeness", "softened request (could you/would you mind)")).verdict, "compatible")
        self.assertEqual(validate("Keywords: sorry messages short", R("politeness", "thanks/apology")).verdict, "compatible")
        v = validate("Keywords: feel sorry", R("politeness", "none"))
        self.assertEqual(v.verdict, "unknown")
        self.assertIn("feel sorry", " ".join(v.reasons))
        self.assertEqual(validate("Keywords: how cheap", R("speech_act", "statement")).verdict, "unknown")
        self.assertEqual(validate("Keywords: not go", R("polarity", "negated")).verdict, "unknown")  # words: out of scope

    def test_noop_and_precedence(self):
        v = validate("Keywords: thanks get wishes", R("politeness", "thanks/apology"), baseline="Keywords: thanks get wishes")
        self.assertEqual((v.verdict, v.relation), ("unchanged_noop", "compatible"))
        v = validate("Keywords: feel sorry", R("politeness", "none"), baseline="Keywords: feel sorry")
        self.assertEqual((v.verdict, v.relation), ("unchanged_noop", "unknown"))
        v = validate("Keywords: [MAYBE] go", R("certainty", "plain assertion"), baseline="Keywords: [MAYBE] go")
        self.assertEqual(v.verdict, "conflicting")

    def test_unknowns(self):
        self.assertEqual(validate("Keywords: [NOT] go", R("polarity", "mixed/unclear")).verdict, "unknown")
        self.assertEqual(validate("Keywords: [NOT] go", R("polarity", None)).verdict, "unknown")
        self.assertEqual(validate("Keywords: [MUST] go", R("speech_act", "request/command")).verdict, "unknown")
        self.assertEqual(validate("The user typed: I won't go.", R("polarity", "negated")).verdict, "unknown")
        v = validate("Keywords: [THEY] go", R("agent", "third party", "detector_fallback"))
        self.assertEqual((v.verdict, v.relation), ("unknown", "compatible"))
        self.assertEqual(validate("Keywords: [NOT] [YES] go", R("polarity", "negated")).verdict, "conflicting")

    def test_hidden_metadata_is_warned_not_used(self):
        v = validate("Keywords: thanks saying tat", R("politeness", "thanks/apology"), None, ["[PLEASE]"])
        self.assertEqual(v.evidence, ["thanks"])
        self.assertTrue(v.warnings)

    def test_requirement_set_mirrors_wb_report_honours(self):
        from wb_report import honours
        for d, opts in GENERAL_OPTIONS.items():
            for src, out in itertools.product(opts, opts):
                req = requirement_set(d, src)
                if req is not None:
                    self.assertEqual(out in req, bool(honours(d, src, out)), (d, src, out))


class FrozenWBReplay(unittest.TestCase):
    def test_replay_matches_frozen_audit_without_changing_inputs(self):
        inv = list(csv.DictReader((ROOT / "analysis/wb/contract_audit_inventory.csv").read_text().splitlines()))
        hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                  for p in ["data/items/wb.jsonl", "runs/requests/wb1.jsonl", "runs/wb1/outputs.jsonl"]}
        with tempfile.TemporaryDirectory() as tmp:
            s = replay(Path(tmp))
            rows = list(csv.DictReader((Path(tmp) / "replay.csv").read_text().splitlines()))
        self.assertEqual(s["n"], 139)
        self.assertEqual(s["agrees_with_audit"], 139)
        self.assertEqual((s["known_conflicts_rejected"], s["sure_granularity_flagged"], s["coarse_certified"]), (7, 8, 0))
        by = {r["family_id"]: r for r in rows}
        conflicts = [r["family_id"] for r in inv if r["status"] == "definite_conflict"]
        self.assertEqual(len(conflicts), 7)
        self.assertTrue(all(by[f]["verdict"] == "conflicting" for f in conflicts))
        words = [r for r in rows if r["mode"] == "word"]
        self.assertEqual(len(words), 8)
        self.assertEqual(sorted(r["verdict"] for r in words),
                         ["compatible"] * 3 + ["unchanged_noop"] * 4 + ["unknown"])
        for r in inv:  # unresolved references/words never certify
            if r["status"] in {"unknown_reference", "unknown_source_consensus", "unknown_word"}:
                self.assertEqual(by[r["family_id"]]["certifies_source"], "False")
        self.assertEqual(hashes, {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in hashes})
        self.assertEqual(json.loads(json.dumps(s["input_sha256"]))["data/items/wb.jsonl"], hashes["data/items/wb.jsonl"])


if __name__ == "__main__":
    unittest.main()

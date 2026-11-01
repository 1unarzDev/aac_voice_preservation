"""Offline regressions for cross-run arbitration and explicit unresolved labels."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import attribute
import resolve_labels
import runio
from test_analyze import ITEM


class ResolutionTests(unittest.TestCase):
    def test_arbiter_overrides_agreement_across_families_and_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            common = dict(text_id="same", input_text="Keywords: water", dimension="polarity", family_id="one")
            runio.write_jsonl(root / "runs/main/judgments.jsonl", [
                common | dict(J1_critical="affirmative", J2_critical="affirmative"),
                common | dict(dimension="agent", J1_critical="speaker", J2_critical="speaker")])
            runio.write_jsonl(root / "runs/span/arbiter.jsonl", [
                common | dict(family_id="other", critical="negated")])
            with patch.object(runio, "ROOT", root):
                rows = resolve_labels.build(["main", "span"])
            bydim = {r["dimension"]: r for r in rows}
            self.assertEqual(bydim["polarity"]["critical"], "negated")
            self.assertEqual(bydim["polarity"]["critical_source"], "arbiter")
            self.assertEqual(bydim["agent"]["critical"], "speaker")

    def test_conflicting_agreements_are_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            common = dict(text_id="same", input_text="x", dimension="polarity", family_id="one")
            for run, value in [("a", "affirmative"), ("b", "negated")]:
                runio.write_jsonl(root / f"runs/{run}/judgments.jsonl", [
                    common | dict(J1_critical=value, J2_critical=value)])
            with patch.object(runio, "ROOT", root):
                rows = resolve_labels.build(["a", "b"])
            self.assertIsNone(rows[0]["critical"])
            self.assertTrue(rows[0]["conflict"])

    def test_resolution_overrides_fallback_including_unknown_and_absent_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            items = directory / "items.jsonl"
            runio.write_jsonl(items, [ITEM])
            occurrence = dict(text_id="text", output_id="output", text="I want water.",
                              family_id="toy", variant="A", channel="chip1", input_text="water [NOT]",
                              request_key="request", model="toy", prompt_id="P0", valid=True)
            runio.write_jsonl(directory / "outputs.jsonl", [occurrence])
            runio.write_jsonl(directory / "judgments.jsonl", [occurrence | dict(
                J1_critical="affirmative", J2_critical="unclear/mixed", critical=None, certainty="plain assertion")])
            resolution = directory / "resolution.jsonl"
            with patch.object(attribute.layer0, "label_many", side_effect=lambda ss: [{"certainty": "plain assertion"}] * len(ss)):
                self.assertEqual(attribute.score(directory, items, "J1").critical.iloc[0], "affirmative")
                for label, source in [("negated", "arbiter"), (None, None)]:
                    runio.write_jsonl(resolution, [dict(text_id="text", input_text="water [NOT]",
                                                       dimension="polarity", critical=label, critical_source=source)])
                    scored = attribute.score(directory, items, "J1", resolution)
                    self.assertEqual(scored.critical.iloc[0], label)
                resolution.write_text("")
                self.assertIsNone(attribute.score(directory, items, "J1", resolution).critical.iloc[0])


if __name__ == "__main__":
    unittest.main()

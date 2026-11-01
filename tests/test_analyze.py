"""Run without extra dependencies: .venv/bin/python tests/test_analyze.py."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyze import (direction_table, example_miner, family_bootstrap, normalize_table,
                     paired_differences, suggestion_sets, unique_ambiguous)


ITEM = {"family_id": "toy", "dimension": "polarity", "bare": "want water", "noncritical": "now",
        "variants": {
            "A": {"source": "I do not want water now.", "critical_value": "negated",
                  "chips": ["[NOT]"], "all_chips": ["[NOT]", "[I]", "[TELL]", "[PLAIN]"]},
            "B": {"source": "I want water now.", "critical_value": "affirmative",
                  "chips": ["[YES]"], "all_chips": ["[YES]", "[I]", "[TELL]", "[PLAIN]"]}}}


def row(**kwargs):
    return dict(family_id="toy", variant="A", channel="bare", prompt_id="P2", model="toy-model",
                text="I want water.", request_key="request", sample_idx=0, suggestion_idx=0,
                critical="affirmative", critical_source="agree", polarity="affirmative", agent="speaker",
                certainty="plain assertion", speech_act="statement", politeness="none", valid=True) | kwargs


class BootstrapTests(unittest.TestCase):
    def test_constant_cluster_and_missing(self):
        x = pd.DataFrame({"family_id": ["a", "a", "b", "b"], "value": [1, np.nan, 1, 1]})
        result = family_bootstrap(x, "value")
        self.assertEqual((result["estimate"], result["ci_low"], result["ci_high"]), (1, 1, 1))
        self.assertEqual((result["n"], result["n_missing"], result["n_families"]), (3, 1, 2))

    def test_whole_family_unequal_sizes_known_distribution(self):
        # Whole-family bootstrap can only yield 0, 1/4, or 1. A row bootstrap
        # admits many other draws; equal weighting family means gives 1/2.
        x = pd.DataFrame({"family_id": ["a", "a", "a", "b"], "value": [0, 0, 0, 1]})
        result = family_bootstrap(x, "value", n_boot=2000, seed=12)
        self.assertEqual(result["estimate"], .25)
        self.assertEqual((result["ci_low"], result["ci_high"]), (0, 1))
        self.assertEqual(result, family_bootstrap(x.sample(frac=1, random_state=2), "value", seed=12))

    def test_cluster_dependence_changes_ci(self):
        # Exact distribution: two homogeneous 0-families + two homogeneous
        # 1-families => Binomial(4,.5)/4; central 95% interval is [0,1].
        x = pd.DataFrame({"family_id": np.repeat(["a", "b", "c", "d"], 100),
                          "value": np.repeat([0, 0, 1, 1], 100)})
        result = family_bootstrap(x, "value", seed=7)
        self.assertEqual(result["estimate"], .5)
        self.assertEqual((result["ci_low"], result["ci_high"]), (0, 1))

    def test_all_missing(self):
        result = family_bootstrap(pd.DataFrame({"family_id": ["a"], "v": [None]}), "v")
        self.assertTrue(np.isnan(result["estimate"]))
        self.assertEqual((result["n"], result["n_families"], result["n_boot_valid"]), (0, 1, 0))

    def test_pairing_preserves_perfect_delta(self):
        rows = []
        for fid, base in [("a", 0), ("b", .4), ("c", .7)]:
            for channel, value in [("noncrit", base), ("chip1", base + .2), ("full", base + .3)]:
                rows.append(dict(family_id=fid, variant="A", dimension="polarity", model="m", prompt_id="P0",
                                 channel=channel, critical_match=value))
        x = paired_differences(pd.DataFrame(rows), 2000, 4).set_index("comparison")
        for comparison, expected in [("chip1-minus-noncrit", .2), ("full-minus-chip1", .1)]:
            for column in ["estimate", "ci_low", "ci_high"]:
                self.assertAlmostEqual(x.loc[comparison, column], expected)
            self.assertEqual(x.loc[comparison, "n"], 3)


class ScoringTests(unittest.TestCase):
    def test_shared_targets_and_set_coverage(self):
        rows = [row(variant=v, suggestion_idx=i, critical=label)
                for v in ["A", "B"] for i, label in enumerate(["affirmative", "negated", "affirmative"])]
        x = normalize_table(pd.DataFrame(rows), {"toy": ITEM})
        self.assertEqual(len(unique_ambiguous(x)), 3)
        sets = suggestion_sets(x).set_index("variant")
        self.assertTrue(sets.coverage_at_3.all())
        self.assertEqual(sets.loc["A", "extra_actions"], 1)
        self.assertEqual(sets.loc["B", "extra_actions"], 0)
        self.assertEqual(sets.loc["A", "nondefault_extra_actions"], 1)
        self.assertTrue(np.isnan(sets.loc["B", "nondefault_extra_actions"]))

    def test_sampled_baseline_groups_requests(self):
        rows = [row(prompt_id="S3", sample_idx=i, request_key=f"request{i}", critical=label)
                for i, label in enumerate(["affirmative", "negated", "affirmative"])]
        sets = suggestion_sets(normalize_table(pd.DataFrame(rows), {"toy": ITEM}))
        self.assertEqual(len(sets), 1)
        self.assertEqual(sets.iloc[0].n_suggestions, 3)
        self.assertTrue(sets.iloc[0].coverage_at_3)

    def test_missing_and_noncompletion_denominators(self):
        x = normalize_table(pd.DataFrame([row(channel="full", critical=None),
                                         row(channel="full", critical=None, valid=False, text="")]), {"toy": ITEM})
        self.assertTrue(pd.isna(x.iloc[0].critical_match))
        self.assertTrue(pd.isna(x.iloc[0].constraint_preserving))
        self.assertEqual(x.iloc[1].critical_match, False)
        self.assertEqual(x.iloc[1].constraint_preserving, False)
        self.assertTrue(x.violation.isna().all())

    def test_unknown_general_label_does_not_certify_completion(self):
        x = normalize_table(pd.DataFrame([row(channel="full", critical="negated", agent=None)]), {"toy": ITEM})
        self.assertTrue(x.iloc[0].critical_match)
        self.assertTrue(pd.isna(x.iloc[0].constraint_preserving))

    def test_not_applicable_certainty_does_not_make_completion_unknown(self):
        x = normalize_table(pd.DataFrame([row(channel="full", critical="negated", polarity="negated",
                                             certainty="n/a (question/request)")]), {"toy": ITEM})
        self.assertTrue(x.iloc[0].constraint_preserving)

    def test_all_unknown_set_is_not_zero_coverage(self):
        x = normalize_table(pd.DataFrame([row(critical=None)]), {"toy": ITEM})
        s = suggestion_sets(x).iloc[0]
        self.assertTrue(pd.isna(s.coverage_at_3))
        self.assertTrue(pd.isna(s.extra_actions))

    def test_layer0_mapping_and_cost(self):
        r = row(channel="chipall", valid=True)
        for key in ["critical", "critical_source"]:
            r.pop(key)
        r.update({f"l0_{d}": r.pop(d) for d in ["polarity", "agent", "certainty", "speech_act", "politeness"]})
        x = normalize_table(pd.DataFrame([r]), {"toy": ITEM}).iloc[0]
        self.assertEqual(x.crit, "affirmative")
        self.assertEqual(x.label_source, "layer0")
        self.assertEqual(x.input_actions, 6)
        self.assertEqual(x.input_characters, len("want water") + 4)

    def test_cue_only_input_has_empty_ambiguous_artifacts(self):
        x = normalize_table(pd.DataFrame([row(channel="full")]), {"toy": ITEM})
        sets = suggestion_sets(x)
        direction = direction_table(unique_ambiguous(x), 2000, 4)
        self.assertTrue(direction.empty)
        self.assertIn("estimate", direction)
        examples = example_miner(x, sets, 4)
        self.assertIn("violation-with-cue", examples)
        self.assertIn("No eligible examples", examples)


if __name__ == "__main__":
    unittest.main()

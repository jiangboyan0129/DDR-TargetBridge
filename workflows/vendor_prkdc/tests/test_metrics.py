"""Hand-derived synthetic tests; no real DDR scores are imported or accessed."""
import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from metrics import (basic_effects, deletion_ranges, matched_diagnostic,
                     numeric, rank_fraction, separation, specificity,
                     summarize_records, validate_rows)


def row(gene, called=False, rho=0.0, coord=0.2):
    return dict(gene=gene, gemini_sensitive=-1.0 if called else 0.0,
                source_called=called, source_generic_fragility=coord,
                rho_R2=rho, gamma_R2=-coord, rho_R3_min=rho,
                rho_R3_median=rho, rho_R3_max=rho, gamma_R3_median=-coord,
                rho_ATMi_R2=0.0, rho_ATRi_R2=0.0, rho_WEE1i_R2=0.0)


class SyntheticMetricTests(unittest.TestCase):
    def test_midranks_hand_derived(self):
        self.assertEqual(rank_fraction([1, 1, 3, 2]), [0.25, 0.25, 0.875, 0.625])
        self.assertEqual(rank_fraction([4, 4, 4]), [0.5, 0.5, 0.5])

    def test_exact_tie_half_credit(self):
        self.assertEqual(separation([1], [1]), 0.5)
        self.assertEqual(separation([0, 1], [0, 2]), 0.375)

    def test_opposite_direction_is_opposite_result(self):
        rows = [row("P", True, -2), row("C", False, 2)]
        self.assertEqual(basic_effects(rows)["A_R2"], 1)
        rows[0]["rho_R2"], rows[1]["rho_R2"] = 2, -2
        self.assertEqual(basic_effects(rows)["A_R2"], 0)

    def test_records_paired_completeness_no_imputation(self):
        records = [dict(record_id="a", transcript="G_P1", rho=-9, gamma=None),
                   dict(record_id="b", transcript="G_P1", rho=-2, gamma=3)]
        result = summarize_records(records)
        self.assertEqual(result["rho_R3_median"], -2)
        self.assertEqual(result["gamma_R3_median"], 3)
        self.assertEqual(result["r3_n_records"], 2)
        self.assertEqual(result["r3_n_complete"], 1)
        self.assertTrue(result["r3_any_missing"])
        self.assertFalse(result["r3_single_original_paired_complete"])
        self.assertEqual(result["records"], records)
        self.assertEqual(result["paired_complete"], [False, True])

    def test_record_components_use_same_eligible_set_but_separate_medians(self):
        result = summarize_records([
            dict(record_id="x", rho=-4, gamma=2),
            dict(record_id="y", rho=4, gamma=-6),
            dict(record_id="z", rho=1, gamma=8)])
        self.assertEqual(result["rho_R3_median"], 1)
        self.assertEqual(result["gamma_R3_median"], 2)
        self.assertTrue(result["r3_sign_discordance"])
        self.assertTrue(result["r3_all_original_paired_complete"])
        self.assertFalse(result["r3_single_original_paired_complete"])

    def test_missing_records_never_become_zero(self):
        result = summarize_records([dict(record_id="x", rho="NaN", gamma=1)])
        self.assertIsNone(result["rho_R3_median"])
        self.assertIsNone(result["gamma_R3_median"])
        self.assertIsNone(result["r3_all_observed_rho_negative"])
        self.assertEqual(result["r3_n_complete"], 0)

    def test_zero_boundary_is_an_explicit_sign_category(self):
        for values, signs, discordance in (([-1, 0], [-1, 0], True),
                                          ([0, 1], [0, 1], True),
                                          ([0, 0], [0], False)):
            records = [dict(record_id=i, rho=v, gamma=0) for i, v in enumerate(values)]
            result = summarize_records(records)
            self.assertEqual(result["r3_rho_sign_set"], signs)
            self.assertEqual(result["r3_sign_discordance"], discordance)

    def test_duplicate_ids_rejected_distinct_records_with_same_label_preserved(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            summarize_records([dict(record_id=1, rho=1, gamma=1)] * 2)
        records = [dict(record_id=i, transcript="G_P1", rho=i, gamma=i) for i in (1, 2)]
        self.assertEqual(summarize_records(records)["r3_n_records"], 2)

    def test_envelope_hand_derived_monotonic_bounds(self):
        rows = [row("P", True, -1), row("C", False, 0)]
        rows[0].update(rho_R3_min=-3, rho_R3_max=2)
        effects = basic_effects(rows)
        self.assertEqual(effects["A_R3_observed_record_lower"], 0)
        self.assertEqual(effects["A_R3_median"], 1)
        self.assertEqual(effects["A_R3_observed_record_upper"], 1)

    def test_duplicate_genes_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate gene"):
            validate_rows([row("A"), row("A")])

    def test_nonfinite_and_boolean_rejected(self):
        for value in (float("nan"), float("inf"), True, "unknown"):
            with self.assertRaises(ValueError):
                numeric(value)

    def test_source_threshold_inclusive_and_frozen_class_checked(self):
        effects = basic_effects([row("P", True), row("C")])
        self.assertEqual(effects["source_called_N"], 1)
        bad = row("P", True)
        bad["source_called"] = False
        with self.assertRaisesRegex(ValueError, "frozen source class"):
            basic_effects([bad, row("C")])

    def test_matching_exact_caliper_boundary(self):
        # P G5 has q=.55; G3 q=.35 is EXACTLY .20 away, despite
        # float(.55)-float(.35) > .2. G2 q=.25 is outside the caliper.
        rows = [row(f"G{i}", i == 5, coord=i/10) for i in range(10)]
        summary, pairs = matched_diagnostic(rows)
        chosen = {p["control_gene"] for p in pairs}
        self.assertEqual(chosen, {"G3", "G4", "G6", "G7"})
        self.assertEqual(summary["matched_source_called_N"], 1)
        self.assertTrue(all(p["degree_rank_gap"] <= .2 for p in pairs))

    def test_matching_lex_ties_reuse_distinct_controls_and_no_case_matches(self):
        rows = [row("P1", True, -1), row("P2", True, -1)]
        rows += [row(f"C{i}") for i in (6, 2, 5, 3, 1, 0, 4)]
        summary, pairs = matched_diagnostic(rows)
        for case in ("P1", "P2"):
            selected = [p for p in pairs if p["source_called_gene"] == case]
            self.assertEqual([p["control_gene"] for p in selected], [f"C{i}" for i in range(5)])
            self.assertAlmostEqual(sum(p["within_case_weight"] for p in selected), 1)
        self.assertEqual(summary["unique_controls"], 5)
        self.assertEqual(summary["controls_reused_across_cases_N"], 5)
        self.assertEqual(summary["matched_pair_N"], 10)
        self.assertAlmostEqual(summary["effective_comparator_N_kish"], 5)

    def test_equal_case_weight_with_unequal_control_counts(self):
        rows = [row(f"G{i}", i in (0, 5), coord=i/10) for i in range(10)]
        rows[0]["rho_R2"] = -100
        rows[5]["rho_R2"] = 100
        summary, pairs = matched_diagnostic(rows)
        self.assertEqual(sum(p["source_called_gene"] == "G0" for p in pairs), 2)
        self.assertEqual(sum(p["source_called_gene"] == "G5" for p in pairs), 4)
        self.assertEqual(summary["A_R2_matched"], .5)

    def test_unmatched_case_retained_and_diagnostic_unavailable(self):
        rows = [row("P", True, coord=0), row("C", coord=1)]
        summary, pairs = matched_diagnostic(rows)
        self.assertEqual(summary["unmatched_source_called_genes"], ["P"])
        self.assertIsNone(summary["A_R2_matched"])
        self.assertEqual(pairs, [])
        self.assertEqual(basic_effects(rows)["N"], 2)

    def test_locked_parameters(self):
        with self.assertRaisesRegex(ValueError, "locked"):
            matched_diagnostic([row("P", True), row("C")], caliper=.3)

    def test_specificity_hand_derived_and_not_raw_scale_comparison(self):
        rows = [row("P", True, -10), row("C", False, 10)]
        summary, records = specificity(rows)
        self.assertEqual(summary["median_S_source_called"], .25)
        self.assertEqual(summary["median_S_source_not_called"], -.25)
        self.assertEqual(summary["difference_of_class_medians"], .5)
        rows[0]["rho_R2"], rows[1]["rho_R2"] = -1, 1
        self.assertEqual(specificity(rows)[0], summary)

    def test_delete_one_known_results_recomputed(self):
        rows = [row("P_high", True, -3), row("P_low", True, -1),
                row("C_high", False, -2), row("C_low", False, 0)]
        result = deletion_ranges(rows)
        self.assertEqual(result["full"]["A_R2"], .75)
        actual = {d["deleted_gene"]: d["A_R2"] for d in result["deletions"]}
        self.assertEqual(actual, {"P_high": .5, "P_low": 1, "C_high": 1, "C_low": .5})
        self.assertEqual(result["all_genes"]["A_R2"], [.5, 1])
        self.assertEqual(result["source_called_only"]["A_R2"], [.5, 1])

    def test_deletion_empty_class_is_labelled(self):
        result = deletion_ranges([row("P", True), row("C1"), row("C2")])
        dropped = next(d for d in result["deletions"] if d["deleted_gene"] == "P")
        self.assertEqual(dropped["status"], "NO_SOURCE_CLASS_CONTRAST")

    def test_row_order_invariance(self):
        rows = [row("Z", True, -1), row("A"), row("B")]
        self.assertEqual(basic_effects(rows), basic_effects(rows[::-1]))
        self.assertEqual(matched_diagnostic(rows), matched_diagnostic(rows[::-1]))
        self.assertEqual(specificity(rows), specificity(rows[::-1]))

    def test_no_source_class_never_substitutes_threshold(self):
        with self.assertRaisesRegex(ValueError, "NO_SOURCE_CLASS_CONTRAST"):
            basic_effects([row("C1"), row("C2")])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticMetricTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {"scope": "Synthetic fixtures only; no biological validation or real outcome access",
               "tests_run": result.testsRun, "failures": len(result.failures),
               "errors": len(result.errors), "successful": result.wasSuccessful(),
               "test_names": sorted(n for n in dir(SyntheticMetricTests) if n.startswith("test_"))}
    Path(__file__).with_name("synthetic_test_results.json").write_text(json.dumps(receipt, indent=2) + "\n")
    sys.exit(not result.wasSuccessful())

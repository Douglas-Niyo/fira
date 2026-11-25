import math
import unittest

from fira.benchmark import fsr, tier_outcomes


class SeverityMetricsTests(unittest.TestCase):
    def test_caps_do_not_shift_to_urgent_types(self):
        # Cap both types at two. Two of six urgent + one of two duplicates.
        present, found = {"T04": 6, "T01": 2}, {"T04": 2, "T01": 1}
        self.assertAlmostEqual(fsr(present, found, 4), .75)
        outcome = tier_outcomes(present, found, 4)
        self.assertAlmostEqual(outcome["tier_weighted_fsr"], 5/6)
        self.assertEqual((outcome["tier1_schemes_found"], outcome["tier1_schemes_present"]), (2, 6))

    def test_finding_lower_priority_type_has_less_weight(self):
        present = {"T05": 1, "T02": 1}
        self.assertAlmostEqual(tier_outcomes(present, {"T02": 1}, 120)["tier_weighted_fsr"], 1/3)

    def test_clean_year_and_absent_tiers(self):
        clean = tier_outcomes({}, {}, 120)
        self.assertTrue(math.isnan(clean["tier_weighted_fsr"]))
        self.assertEqual((clean["tier1_schemes_found"], clean["tier1_schemes_present"]), (0, 0))
        self.assertEqual(tier_outcomes({"T09": 2}, {"T09": 1}, 120)["tier_weighted_fsr"], .5)

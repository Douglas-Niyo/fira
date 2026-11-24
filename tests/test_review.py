"""Checks on the monthly review pack."""
import unittest

from fira.review import build
from tests import test_rules


class TestReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_rules.TestRules.setUpClass()
        cls.labels = test_rules.TestRules.labels
        cls.alerts = test_rules.TestRules.alerts
        cls.items, cls.summary, cls.detail = build(cls.alerts)

    def test_pack_is_much_shorter(self):
        self.assertLess(len(self.items), 0.3 * len(self.alerts))

    def test_every_scheme_still_in_pack(self):
        recs = {r for x in self.items.records for r in x.split(";")}
        found = self.labels.assign(f=self.labels.record_id.isin(recs)).groupby("scheme_id").f.any()
        self.assertTrue(found.all(), list(found[~found].index))

    def test_tiered_primary_ids_are_in_review_items(self):
        from fira.review import TIER
        expected = set(self.alerts[self.alerts.rule.isin(TIER)].record_id)
        in_items = {r for group in self.items.records for r in group.split(";")}
        self.assertEqual(in_items, expected)
        # Typed source links, standalone context and related records are tested
        # against the exported monthly pack in tests/test_monthly.py.

    def test_self_approval_not_listed_as_items(self):
        self.assertFalse(self.items.rules.str.contains("R07").any())
        self.assertGreater(len(self.summary), 0)


if __name__ == "__main__":
    unittest.main()

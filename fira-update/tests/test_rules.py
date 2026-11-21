"""Checks on the FIRA control rules (runs with unittest or pytest)."""
import unittest

import pandas as pd

from fira.generator import Config, Generator
from fira.rules import Rules, _norm_number


class TestRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t = Generator(Config(seed=11)).run()
        cls.labels = t.pop("labels")
        for name, cols in {"Invoices_Received": ["Invoice_Amount_Local"],
                           "Payments_Made": ["Payment_Amount_Local"],
                           "AP_Cash_Application": ["AP_Application_Amount"]}.items():
            for c in cols:
                t[name][c] = pd.to_numeric(t[name][c])
        cls.t = {k: v.fillna("").astype({c: str for c in v.columns
                                        if v[c].dtype == object}) for k, v in t.items()}
        cls.alerts = Rules(cls.t).run()

    def test_number_normalisation(self):
        self.assertEqual(_norm_number("INV-00123"), "123")
        self.assertEqual(_norm_number("12-345 "), "12345")

    def test_every_planted_scheme_is_flagged(self):
        flagged = set(zip(self.alerts.table, self.alerts.record_id))
        lab = self.labels.assign(found=[(a, b) in flagged for a, b in zip(self.labels.table, self.labels.record_id)])
        missed = lab.groupby("scheme_id").found.any()
        self.assertTrue(missed.all(), f"missed schemes: {list(missed[~missed].index)}")

    def test_every_alert_has_a_reason_and_control(self):
        self.assertTrue((self.alerts.reason.str.len() > 10).all())
        self.assertTrue((self.alerts.control.str.len() > 10).all())

    def test_no_alert_says_fraud(self):
        self.assertFalse(self.alerts.reason.str.contains("fraud", case=False).any())


if __name__ == "__main__":
    unittest.main()

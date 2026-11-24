"""Basic checks on the synthetic data generator (runs with unittest or pytest)."""
import unittest

from fira.generator import Config, Generator


class TestGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = Generator(Config(seed=7)).run()

    def test_same_seed_same_data(self):
        again = Generator(Config(seed=7)).run()
        for name in ["Invoices_Received", "Payments_Made", "labels"]:
            self.assertTrue(self.t[name].equals(again[name]), name)

    def test_different_seed_different_data(self):
        other = Generator(Config(seed=8)).run()
        self.assertFalse(self.t["Invoices_Received"].equals(other["Invoices_Received"]))

    def test_keys_link_up(self):
        sup = set(self.t["Supplier_Listing"].Supplier_Account_ID)
        self.assertTrue(set(self.t["Invoices_Received"].Supplier_Account_ID) <= sup)
        self.assertTrue(set(self.t["Payments_Made"].Supplier_Account_ID) <= sup)
        app = self.t["AP_Cash_Application"]
        self.assertTrue(set(app.Payment_ID) <= set(self.t["Payments_Made"].Payment_ID))
        self.assertTrue(set(app.Invoice_ID) <= set(self.t["Invoices_Received"].Invoice_ID))

    def test_ids_unique(self):
        self.assertTrue(self.t["Invoices_Received"].Invoice_ID.is_unique)
        self.assertTrue(self.t["Payments_Made"].Payment_ID.is_unique)

    def test_every_injected_type_present(self):
        types = set(self.t["labels"].type)
        self.assertEqual(types, {"T01", "T02", "T04", "T05", "T06", "T09", "T15"})

    def test_labeled_records_exist(self):
        lab = self.t["labels"]
        for table, key in [("Invoices_Received", "Invoice_ID"), ("Payments_Made", "Payment_ID")]:
            ids = set(lab[lab.table == table].record_id)
            self.assertTrue(ids <= set(self.t[table][key]), table)

    def test_prevalence_is_low(self):
        lab = self.t["labels"]
        share = (lab.table == "Payments_Made").sum() / len(self.t["Payments_Made"])
        self.assertLess(share, 0.05)

    def test_ids_do_not_reveal_planted_records(self):
        """Planted records must not cluster at the end of the ID or check-number sequence."""
        lab = self.t["labels"]
        pay = self.t["Payments_Made"].reset_index(drop=True)
        planted = pay.Payment_ID.isin(lab[lab.table == "Payments_Made"].record_id)
        # mean position of planted payments should not sit in the last tenth of the file
        self.assertLess(planted[planted].index.to_series().mean() / len(pay), 0.9)
        # the fictitious supplier must not always be the last supplier ID
        positions = []
        for seed in range(5):
            t = Generator(Config(seed=seed)).run()
            sup, lb = t["Supplier_Listing"].reset_index(drop=True), t["labels"]
            fake = sup.index[sup.Supplier_Account_ID.isin(lb[lb.table == "Supplier_Listing"].record_id)]
            positions.extend(list(fake))
        self.assertTrue(any(p_ < len(sup) - 1 for p_ in positions))

    def test_ids_follow_dates(self):
        inv = self.t["Invoices_Received"]
        self.assertTrue(inv.Entered_Date.is_monotonic_increasing)
        pay = self.t["Payments_Made"]
        self.assertTrue(pay.Payment_Date.is_monotonic_increasing)

    def test_no_plain_tax_ids(self):
        self.assertNotIn("Supplier_TIN", self.t["Supplier_Listing"].columns)


if __name__ == "__main__":
    unittest.main()

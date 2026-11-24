import unittest,json
from pathlib import Path
import pandas as pd
from fira.rules import load, Rules
from fira.monthly import *
from fira.benchmark import fsr,jobs,DEV

class MonthlyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    root=Path(__file__).resolve().parents[1]/"data/small_seed42"
    cls.profile=json.loads((root/"profile.json").read_text())
    cls.t=contract(load(root),cls.profile)
    cls.pack=monthly(cls.t,cls.profile["start"])
 def test_no_future_information(self):
    t={k:(v[v[DATE[k]]<="2025-09-30"].copy() if k in DATE else v.copy()) for k,v in self.t.items()}
    early=monthly(t,self.profile["start"])
    for name,field in [("review_items","month"),("raw_alerts","observed_month"),("self_approval_summary","month"),("alert_links","month")]:
        for_test=lambda pack:pack[name].loc[pack[name][field]<="2025-09"].reset_index(drop=True)
        pd.testing.assert_frame_equal(for_test(early),for_test(self.pack),check_dtype=False)
 def test_overpayments_enter_expected_month(self):
    r=self.pack["raw_alerts"].query("rule=='R04'");self.assertEqual(set(r.observed_month),{"2025-11","2026-05"})
    self.assertEqual(set(self.pack["review_items"].query("rules.str.contains('R04')").month),set(r.observed_month))
 def test_zero_alerts_and_twelve_months(self):
    t={k:v.iloc[:0] for k,v in self.t.items()};p=monthly(t,self.profile["start"])
    self.assertEqual(len(p["monthly_load"]),12);self.assertEqual(p["monthly_load"].lines.sum(),0)
    self.assertIn("alert_id",p["raw_alerts"]);self.assertIn("item_id",p["review_items"])
 def test_trace_resolves(self):
    a=self.pack["raw_alerts"]; links=self.pack["alert_links"]
    keys={**{k:set(self.t[k][v]) for k,v in KEY.items()},C:set(self.t[C].Supplier_Account_ID+"@"+self.t[C].Changed_Date)}
    groups={k:set(zip(g.table,g.record_id)) for k,g in links.groupby("alert_id")}
    dests=set(self.pack["review_items"].item_id)|{f"summary:{r.month}:{r.user}" for r in self.pack["self_approval_summary"].itertuples()}
    for r in a.itertuples():self.assertIn((r.table,r.record_id),groups[r.alert_id])
    for r in links.itertuples():
        self.assertIn(r.record_id,keys[r.table]);self.assertTrue(r.destination in dests or r.destination=="context:"+r.alert_id)
 def test_nonstandard_user(self):
    a=self.pack["raw_alerts"].copy();a.loc[a.rule=="R07","user_id"]="clerk@example.org"
    _,s,d=build(a)
    self.assertEqual(set(s.user),{"clerk@example.org"});self.assertEqual(len(d),s.invoices_count.sum()+s.payments_count.sum())
 def test_allocations_and_rejections(self):
    t=dict(self.t); row=t[I].iloc[[0]].copy(); row["Invoice_Amount_Local"]=25.;t[I]=pd.concat([row.assign(Purchase_Order_ID="1"),row.assign(Purchase_Order_ID="2")])
    t[A]=t[A].iloc[:0]
    mapped=contract(t,{**self.profile,"invoice_rows":"allocated_by_purchase_order"})
    self.assertEqual(list(mapped[I].Invoice_Amount_Local),[50]);r=Rules(mapped);r.duplicates();self.assertFalse(r.alerts)
    with self.assertRaises(ValueError):contract(t,self.profile)
    with self.assertRaises(ValueError):contract(self.t,{**self.profile,"currency":"EUR"})
    with self.assertRaisesRegex(ValueError,"Not tested"):contract({**self.t,I:self.t[I].drop(columns="Approved_By")},self.profile)
 def test_chronology(self):
    d=self.t[A].merge(self.t[P],on="Payment_ID").merge(self.t[I],on="Invoice_ID",suffixes=("_p","_i"))
    self.assertTrue((d.Payment_Date>=d.Entered_Date_i).all())
 def test_seeds_and_scheme_metric(self):
    seeds=[j[0] for j in jobs()];self.assertEqual(len(seeds),570);self.assertEqual(len(set(seeds)),570);self.assertFalse(DEV.intersection(seeds))
    self.assertAlmostEqual(fsr({"a":1,"b":4},{"b":1},2),.5)
 def test_real_duplicate_survives_allocation_mapping(self):
    t=dict(self.t);row=t[I].iloc[[0]].copy(); row["Invoice_Amount_Local"]=25
    t[I]=pd.concat([row.assign(Purchase_Order_ID="po1"),row.assign(Purchase_Order_ID="po2"),
                   row.assign(Invoice_ID="another-invoice",Purchase_Order_ID="po3",Invoice_Amount_Local=50)])
    t[A]=t[A].iloc[:0]
    r=Rules(contract(t,{**self.profile,"invoice_rows":"allocated_by_purchase_order"})); r.duplicates()
    self.assertEqual(len(r.alerts),1);self.assertNotEqual(r.alerts[0]["record_id"],r.alerts[0]["related_records"])
 def test_context_only_reachable(self):
    t={k:v.iloc[:0].copy() for k,v in self.t.items()}
    t[I]=self.t[I].iloc[[0]].copy();t[I]["Entered_Time"]="23:00:00";t[I]["Approved_By"]="independent"
    t[S]=self.t[S][self.t[S].Supplier_Account_ID.isin(t[I].Supplier_Account_ID)]
    p=monthly(t,self.profile["start"]);self.assertTrue(p["review_items"].empty)
    self.assertTrue(any(p["alert_links"].destination.str.startswith("context:")))

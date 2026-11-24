import unittest
import numpy as np
import pandas as pd
from fira.ranking import family, order, relative_features
from fira.benchmark import scores

class RankingTests(unittest.TestCase):
    def test_all_comparators_charge_summaries_last(self):
        p=[("m","low",4,10),("m","summary:m:user",6,999),("m","urgent",2,50)]
        for method in ("B1","B2","B3","B3_min","B4"):
            args=({"urgent":0,"low":1},{"urgent":"bank change","low":"duplicate"},{})
            self.assertEqual(set(v[1] for v in order(p,method,2,*args)),{"urgent","low"})
            self.assertEqual(order(p,method,3,*args)[-1][1],"summary:m:user")
    def test_families_share_capacity_without_repeating_items(self):
        p=[("m","a",2,100),("m","b",2,90),("m","c",4,30),("m","d",4,20)]
        f={"a":"bank change","b":"bank change","c":"duplicate","d":"split"}
        ids=lambda pool:[v[1] for v in order(pool,"B4",3,{},f,{})]
        self.assertEqual(ids(p),["a","c","d"]);self.assertEqual(ids(p[::-1]),ids(p))
        self.assertEqual(family({"R01","R09"}),"duplicate")
    def test_supplier_baselines_exclude_entire_current_and_later_months(self):
        f=pd.DataFrame({"Payment_Date":["2025-01-02"]*6+["2025-02-10","2025-02-11","2025-02-10","2025-03-01"],
                        "Supplier_Account_ID":["a"]*3+["b"]*3+["a","a","b","a"],
                        "Payment_Amount_Local":[100]*3+[200]*3+[200,900,200,9999],
                        "Payment_Type":["CHECK"]*3+["ACH"]*3+["ACH","CHECK","ACH","ACH"]})
        x=relative_features(f)
        np.testing.assert_allclose(x[:6],0)
        np.testing.assert_allclose(x[6],[np.log(201/101),.75]);np.testing.assert_allclose(x[8],[0,0])
        np.testing.assert_array_equal(relative_features(f.iloc[:7]),x[:7])
    def test_cold_start_is_neutral_for_sparse_supplier(self):
        f=pd.DataFrame({"Payment_Date":["2025-01-01","2025-01-02","2025-02-02"],
                        "Supplier_Account_ID":["v"]*3,"Payment_Amount_Local":[1,2,100000],"Payment_Type":["CHECK","CHECK","ACH"]})
        np.testing.assert_array_equal(relative_features(f),np.zeros((3,2)))

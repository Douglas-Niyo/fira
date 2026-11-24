"""FIRA transparent control rules, v0.1.

Each rule returns alerts with a plain-English reason, the irregularity type it targets
(see docs/irregularity-typology-v0.1.md) and a control reference. An alert means
"review this", never "fraud".

Duplicate matching follows Dubinsky & Warner (2008): compare invoice numbers after
stripping zeros, letters and punctuation; dates within 13 days; amounts within 3%.

Usage:
    python -m fira.rules --data data/small_seed42 --out alerts.csv
"""
from __future__ import annotations

import argparse
import re
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

SEGREGATION = "GAO Green Book / COSO Principle 10: segregation of duties"
APPROVAL = "GAO Green Book / COSO Principle 10: authorization and approval"
MASTER = "GAO Green Book / COSO Principle 10: vendor master file controls"
DISBURSE = "GAO Green Book / COSO Principle 10: disbursement controls"

DEFAULTS = dict(
    duplicate_window_days=13,
    amount_tolerance=0.03,
    approval_threshold=5000.0,
    split_window_days=7,
    bank_change_window_days=30,
    business_start="07:00:00",
    business_end="19:00:00",
    min_consecutive_invoices=4,
)

TABLES = ["Supplier_Listing", "Invoices_Received", "Payments_Made", "AP_Cash_Application",
          "FIRA_Supplier_Change_Log", "User_Listing"]


def load(folder: str | Path) -> dict[str, pd.DataFrame]:
    folder = Path(folder)
    out = {}
    for t in TABLES:
        f = folder / f"{t}.csv"
        out[t] = pd.read_csv(f, dtype=str, keep_default_na=False) if f.exists() else pd.DataFrame()
    for t, cols in {"Invoices_Received": ["Invoice_Amount_Local"],
                    "Payments_Made": ["Payment_Amount_Local"],
                    "AP_Cash_Application": ["AP_Application_Amount"]}.items():
        for c in cols:
            if c in out[t]:
                out[t][c] = pd.to_numeric(out[t][c])
    return out


def _norm_number(x: str) -> str:
    """Keep digits only and drop leading zeros (Dubinsky & Warner 2008)."""
    d = re.sub(r"\D", "", str(x)).lstrip("0")
    return d


def _money(x: float) -> str:
    return f"${x:,.2f}"


class Rules:
    def __init__(self, t: dict[str, pd.DataFrame], **settings):
        self.t = t
        self.s = {**DEFAULTS, **settings}
        self.alerts: list[dict] = []
        sup = t["Supplier_Listing"]
        self.sup_name = dict(zip(sup.Supplier_Account_ID, sup.Supplier_Account_Name)) if len(sup) else {}

    def _add(self, rule, typ, table, record_id, supplier, amount, when, reason, control, related="", user_id="", application_ids="", invoice_id=""):
        self.alerts.append(dict(rule=rule, type=typ, table=table, record_id=record_id,
                                supplier_id=supplier, supplier_name=self.sup_name.get(supplier, ""),
                                amount=amount, date=when, reason=reason, control=control,
                                related_records=related,user_id=user_id,application_ids=application_ids,invoice_id=invoice_id))

    # ---------------- duplicates ----------------
    def duplicates(self):
        inv = self.t["Invoices_Received"].copy()
        if inv.empty:
            return
        inv["d"] = pd.to_datetime(inv.Invoice_Date)
        inv["n"] = inv.Invoice_Number.map(_norm_number)
        win, tol = self.s["duplicate_window_days"], self.s["amount_tolerance"]
        for sid, g in inv.sort_values(["d", "Invoice_ID"]).groupby("Supplier_Account_ID"):
            rows = g.to_dict("records")
            for i, a in enumerate(rows):
                for b in rows[:i]:
                    if a["Invoice_ID"] == b["Invoice_ID"]: continue
                    same_amt = abs(a["Invoice_Amount_Local"] - b["Invoice_Amount_Local"]) <= tol * max(
                        abs(b["Invoice_Amount_Local"]), 0.01)
                    exact_amt = a["Invoice_Amount_Local"] == b["Invoice_Amount_Local"]
                    close = abs((a["d"] - b["d"]).days) <= win
                    if a["Invoice_Number"] == b["Invoice_Number"] and exact_amt:
                        self._add("R01", "T01", "Invoices_Received", a["Invoice_ID"], sid,
                                  a["Invoice_Amount_Local"], a["Entered_Date"],
                                  f"Same supplier, invoice number {a['Invoice_Number']} and amount "
                                  f"{_money(a['Invoice_Amount_Local'])} as invoice {b['Invoice_ID']}.",
                                  DISBURSE, b["Invoice_ID"])
                        break
                    if close and a["n"] and a["n"] == b["n"] and same_amt:
                        self._add("R02", "T02", "Invoices_Received", a["Invoice_ID"], sid,
                                  a["Invoice_Amount_Local"], a["Entered_Date"],
                                  f"This may be a duplicate bill: invoice number '{a['Invoice_Number']}' looks like "
                                  f"'{b['Invoice_Number']}' once formatting differences are removed, and the amounts "
                                  f"differ by no more than 3%.",
                                  DISBURSE, b["Invoice_ID"])
                        break
                    if exact_amt and close:
                        self._add("R03", "T03", "Invoices_Received", a["Invoice_ID"], sid,
                                  a["Invoice_Amount_Local"], a["Entered_Date"],
                                  f"Same supplier and same amount {_money(a['Invoice_Amount_Local'])} as "
                                  f"invoice {b['Invoice_ID']}, {abs((a['d'] - b['d']).days)} days apart, "
                                  f"different invoice numbers.", DISBURSE, b["Invoice_ID"])
                        break

    def paid_more_than_billed(self):
        app, inv = self.t["AP_Cash_Application"], self.t["Invoices_Received"]
        if app.empty:
            return
        lookup=inv.set_index("Invoice_ID")
        for iid,g in app.sort_values(["AP_Application_Date","AP_Application_ID"]).groupby("Invoice_ID"):
            if iid not in lookup.index: continue
            bill=lookup.loc[iid]
            total=0; pays=[]; apps=[]
            for r in g.itertuples():
                total+=int(round(100*r.AP_Application_Amount)); pays.append(r.Payment_ID); apps.append(r.AP_Application_ID)
                if total>int(round(100*bill.Invoice_Amount_Local))+1:
                    self._add("R04","T04","Payments_Made",r.Payment_ID,bill.Supplier_Account_ID,total/100,
                              max(r.AP_Application_Date,bill.Entered_Date),
                              f"Payments applied to invoice {iid} total {_money(total/100)} against a bill of {_money(bill.Invoice_Amount_Local)}. Check whether both amounts cleared and whether a credit is due.",
                              DISBURSE,";".join(dict.fromkeys(pays)),application_ids=";".join(apps),invoice_id=iid)
                    break

    # ---------------- vendor master ----------------
    def bank_change_then_payment(self):
        chg, pay = self.t["FIRA_Supplier_Change_Log"], self.t["Payments_Made"]
        if chg.empty:
            return
        chg = chg[chg.Changed_Field == "bank_account"]
        pay = pay.assign(d=pd.to_datetime(pay.Payment_Date))
        w = self.s["bank_change_window_days"]
        for _, c in chg.iterrows():
            cd = pd.Timestamp(c.Changed_Date)
            hits = pay[(pay.Supplier_Account_ID == c.Supplier_Account_ID) & (pay.d >= cd) &
                       (pay.d <= cd + pd.Timedelta(days=w))]
            for _, p in hits.iterrows():
                self._add("R05", "T05", "Payments_Made", p.Payment_ID, p.Supplier_Account_ID,
                          p.Payment_Amount_Local, p.Payment_Date,
                          f"Paid {(p.d - cd).days} days after this supplier's bank details were changed "
                          f"(by {c.Changed_By} on {c.Changed_Date} at {c.Changed_Time}). Confirm the change "
                          f"by phoning the supplier at a known number.", MASTER,
                          f"{c.Supplier_Account_ID}@{c.Changed_Date}")

    def supplier_created_and_paid_by_same_user(self):
        sup, pay = self.t["Supplier_Listing"], self.t["Payments_Made"]
        creator = dict(zip(sup.Supplier_Account_ID, sup.Entered_By))
        sup_approver = dict(zip(sup.Supplier_Account_ID, sup.Approved_By))
        new_from = dict(zip(sup.Supplier_Account_ID, sup.Entered_Date))
        for _, p in pay.iterrows():
            c = creator.get(p.Supplier_Account_ID)
            if not c:
                continue
            # only suppliers created in the review period and self-approved at set-up
            if sup_approver.get(p.Supplier_Account_ID) == c and p.Approved_By == c and p.Entered_By == c:
                self._add("R06", "T06", "Payments_Made", p.Payment_ID, p.Supplier_Account_ID,
                          p.Payment_Amount_Local, p.Payment_Date,
                          f"The same user ({c}) created and approved this supplier on {new_from.get(p.Supplier_Account_ID)}, "
                          f"then entered and approved this payment. Check whether someone else independently "
                          f"reviewed it.", SEGREGATION)

    def supplier_master_quality(self):
        sup = self.t["Supplier_Listing"]
        for _, s in sup.iterrows():
            why = []
            if not s.get("Supplier_TIN_Hash", ""):
                why.append("no tax ID on file")
            if re.match(r"\s*p\.?\s*o\.?\s*box", str(s.Supplier_Physical_Street_Address1), re.I):
                why.append("physical address is a P.O. box")
            if why:
                self._add("R10", "T10", "Supplier_Listing", s.Supplier_Account_ID, s.Supplier_Account_ID,
                          None, s.Entered_Date, "Supplier record: " + " and ".join(why) + ".", MASTER)
        # possible duplicate suppliers
        rows = sup.to_dict("records")
        for i, a in enumerate(rows):
            for b in rows[:i]:
                same_tin = a.get("Supplier_TIN_Hash") and a.get("Supplier_TIN_Hash") == b.get("Supplier_TIN_Hash")
                sim = SequenceMatcher(None, a["Supplier_Account_Name"].lower(),
                                      b["Supplier_Account_Name"].lower()).ratio()
                same_addr = (a["Supplier_Physical_Street_Address1"].lower() ==
                             b["Supplier_Physical_Street_Address1"].lower())
                if same_tin or sim >= 0.92 or (same_addr and a["Supplier_Physical_Street_Address1"].strip()):
                    self._add("R11", "T11", "Supplier_Listing", a["Supplier_Account_ID"],
                              a["Supplier_Account_ID"], None, a["Entered_Date"],
                              f"May duplicate supplier {b['Supplier_Account_ID']} "
                              f"({'same tax ID' if same_tin else 'same address' if same_addr else 'very similar name'}).",
                              MASTER, b["Supplier_Account_ID"])

    # ---------------- approvals ----------------
    def approvals(self):
        thr = self.s["approval_threshold"]
        for table, amt, key, d in [("Invoices_Received", "Invoice_Amount_Local", "Invoice_ID", "Entered_Date"),
                                   ("Payments_Made", "Payment_Amount_Local", "Payment_ID", "Payment_Date")]:
            df = self.t[table]
            for _, r in df.iterrows():
                if r.Approved_By and r.Approved_By == r.Entered_By:
                    self._add("R07", "T07", table, r[key], r.Supplier_Account_ID, r[amt], r[d],
                              f"The same user ({r.Entered_By}) entered and approved this "
                              f"{'invoice' if table == 'Invoices_Received' else 'payment'}. Check for a separate, "
                              f"documented review.", SEGREGATION, user_id=r.Entered_By)
                elif not r.Approved_By and r[amt] >= thr:
                    self._add("R08", "T08", table, r[key], r.Supplier_Account_ID, r[amt], r[d],
                              f"No approval recorded for {_money(r[amt])}, above the {_money(thr)} threshold.",
                              APPROVAL)

    def split_purchases(self):
        inv = self.t["Invoices_Received"].copy()
        thr, win = self.s["approval_threshold"], self.s["split_window_days"]
        inv["d"] = pd.to_datetime(inv.Invoice_Date)
        below = inv[(inv.Invoice_Amount_Local < thr) & (inv.Invoice_Amount_Local >= 0.5 * thr)]
        for sid, g in below.sort_values("d").groupby("Supplier_Account_ID"):
            rows = g.to_dict("records")
            consumed=set()
            for i, a in enumerate(rows):
                if a["Invoice_ID"] in consumed: continue
                group = [b for b in rows if b["Invoice_ID"] not in consumed and 0 <= (b["d"] - a["d"]).days <= win]
                total = sum(b["Invoice_Amount_Local"] for b in group)
                if len(group) >= 2 and total >= thr:
                    for b in group:
                        self._add("R09", "T09", "Invoices_Received", b["Invoice_ID"], sid,
                                  b["Invoice_Amount_Local"], b["Entered_Date"],
                                  f"{len(group)} invoices from this supplier within {win} days fall below the "
                                  f"{_money(thr)} approval threshold but together total {_money(total)}. Check whether "
                                  f"they relate to one purchase requiring higher approval.", APPROVAL,
                                  ";".join(x["Invoice_ID"] for x in group))
                    consumed.update(x["Invoice_ID"] for x in group)

    # ---------------- timing and patterns ----------------
    def timing(self):
        pay, app, sup = self.t["Payments_Made"], self.t["AP_Cash_Application"], self.t["Supplier_Listing"]
        inv = self.t["Invoices_Received"].set_index("Invoice_ID")
        inactive = {r.Supplier_Account_ID: r.Inactive_Date for _, r in sup.iterrows() if r.Inactive_Date}
        linked = set(app.Payment_ID)
        linked_inv = app.groupby("Payment_ID").Invoice_ID.apply(list).to_dict()
        for _, p in pay.iterrows():
            why = []
            if p.Payment_ID not in linked:
                why.append("has no linked invoice")
            ia = inactive.get(p.Supplier_Account_ID)
            if ia and p.Payment_Date >= ia:
                why.append(f"went to a supplier already marked inactive on {ia}")
            ids = linked_inv.get(p.Payment_ID, [])
            if any(iid in inv.index and p.Payment_Date < inv.loc[iid, "Invoice_Date"] for iid in ids):
                why.append("is dated before its invoice")
            if why:
                self._add("R15", "T15", "Payments_Made", p.Payment_ID, p.Supplier_Account_ID,
                          p.Payment_Amount_Local, p.Payment_Date,
                          "This payment " + ", and ".join(why) + ". Check the supporting documents and "
                          "payment authorization.", DISBURSE)

    def consecutive_invoice_numbers(self):
        inv = self.t["Invoices_Received"].copy()
        inv["n"] = pd.to_numeric(inv.Invoice_Number.map(_norm_number), errors="coerce")
        k = self.s["min_consecutive_invoices"]
        for sid, g in inv.dropna(subset=["n"]).sort_values("Invoice_Date").groupby("Supplier_Account_ID"):
            if len(g) < k:
                continue
            steps = g.n.diff().dropna()
            if (steps.between(1, 2)).mean() >= 0.8:
                for _, r in g.iterrows():
                    self._add("R14", "T14", "Invoices_Received", r.Invoice_ID, sid, r.Invoice_Amount_Local,
                              r.Entered_Date,
                              f"{len(g)} invoices from this supplier have consecutive or nearly consecutive numbers "
                              f"({int(g.n.min())} to {int(g.n.max())}). This can be legitimate; review alongside "
                              f"other supplier concerns.", MASTER, ";".join(g.Invoice_ID))

    def after_hours(self):
        st, en = self.s["business_start"], self.s["business_end"]
        inv = self.t["Invoices_Received"]
        for _, r in inv.iterrows():
            wd = pd.Timestamp(r.Entered_Date).weekday()
            if r.Entered_Time and (r.Entered_Time < st or r.Entered_Time > en or wd >= 5):
                self._add("R13", "T13", "Invoices_Received", r.Invoice_ID, r.Supplier_Account_ID,
                          r.Invoice_Amount_Local, r.Entered_Date,
                          f"Entered outside business hours ({r.Entered_Date} at {r.Entered_Time}).", SEGREGATION)

    def run(self) -> pd.DataFrame:
        self.alerts=[]
        for f in [self.duplicates, self.paid_more_than_billed, self.bank_change_then_payment,
                  self.supplier_created_and_paid_by_same_user, self.supplier_master_quality,
                  self.approvals, self.split_purchases, self.timing,
                  self.consecutive_invoice_numbers, self.after_hours]:
            f()
        df = pd.DataFrame(self.alerts, columns="rule type table record_id supplier_id supplier_name amount date reason control related_records user_id application_ids invoice_id".split())
        df.insert(0, "alert_id", [f"A{i + 1:05d}" for i in range(len(df))])
        return df


def main(argv=None):
    p = argparse.ArgumentParser(description="Run FIRA control rules")
    p.add_argument("--data", default="data/small_seed42")
    p.add_argument("--out", default="alerts.csv")
    a = p.parse_args(argv)
    import json
    from .monthly import monthly,contract
    folder=Path(a.data)
    if (folder/"AP_Adjustments.csv").exists(): raise ValueError("Unsupported adjustments")
    profile=json.loads((folder/"profile.json").read_text())
    alerts=monthly(contract(load(folder),profile),profile["start"])["raw_alerts"]
    alerts.to_csv(a.out, index=False)
    print(f"{len(alerts)} alerts written to {a.out}")
    if len(alerts):
        print(alerts.groupby(["rule", "type"]).size().to_string())


if __name__ == "__main__":
    main()

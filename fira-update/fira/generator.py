"""Synthetic accounts-payable data for a small U.S. local government.

FIRA v0.1 benchmark generator. Produces AICPA Audit Data Standards (Procure to Pay)
style tables plus FIRA extensions, with labeled, injected irregularities.

Design notes
------------
* The entity is small: one clerk-treasurer enters almost everything, and a part-time
  treasurer or mayor approves most payments. Some self-approval is *normal* here,
  which is exactly why simple segregation rules overflag in small entities.
* Payments are made in batches on council meeting dates (twice a month).
* Suppliers number their invoices in their own sequences with jumps, because they
  have other customers. A fictitious supplier tends to number consecutively.
* Every injected irregularity is recorded in labels.csv with a scheme_id, so one
  scheme that touches several records counts once.

Usage
-----
    python -m fira.generator --out data/small_seed42 --seed 42
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

GENERATOR_VERSION = "0.1.1"


@dataclass
class Config:
    seed: int = 42
    start: str = "2025-07-01"          # fiscal year start
    days: int = 365
    n_suppliers: int = 60
    approval_threshold: float = 5000.0
    bank_change_window_days: int = 30
    # number of injected schemes of each type
    n_exact_duplicates: int = 3
    n_near_duplicates: int = 3
    n_overpayments: int = 2
    n_bank_redirects: int = 2
    n_fictitious_suppliers: int = 1
    n_split_purchases: int = 2
    n_inactive_payments: int = 2
    # normal-life noise that should *not* be labeled
    n_legit_bank_changes: int = 4
    normal_self_approval_rate: float = 0.12


USERS = [
    ("U01", "Clerk-Treasurer", "clerk"),
    ("U02", "Deputy Clerk", "clerk"),
    ("U03", "Mayor", "approver"),
    ("U04", "Council Treasurer", "approver"),
]

CATEGORIES = {
    # name: (median amount, sigma, invoices per year)
    "Electric utility": (1800, 0.25, 12),
    "Water treatment chemicals": (2400, 0.35, 8),
    "Fuel": (900, 0.40, 24),
    "Office supplies": (180, 0.60, 10),
    "Engineering services": (6500, 0.50, 4),
    "Legal services": (2200, 0.50, 5),
    "Road materials": (4200, 0.55, 5),
    "Equipment repair": (1300, 0.70, 6),
    "Insurance": (9500, 0.20, 2),
    "IT services": (750, 0.30, 12),
    "Janitorial": (650, 0.20, 12),
    "Telephone and internet": (420, 0.15, 12),
}

STREETS = ["Main St", "Oak Ave", "Industrial Way", "Commerce Dr", "Mill Rd",
           "Lakeview Blvd", "Pine St", "Station Rd", "Market St", "River Rd"]
CITIES = [("Spokane", "WA", "992"), ("Colville", "WA", "991"), ("Kettle Falls", "WA", "991"),
          ("Chewelah", "WA", "991"), ("Deer Park", "WA", "990")]
NAME_A = ["Northern", "Valley", "Summit", "Pioneer", "Cascade", "Evergreen", "Ridge",
          "Inland", "Columbia", "Frontier", "Tri-County", "Granite", "Pinecrest", "Riverside"]
NAME_B = {"Electric utility": "Power", "Water treatment chemicals": "Chemical Supply",
          "Fuel": "Fuel & Oil", "Office supplies": "Office Supply", "Engineering services": "Engineering",
          "Legal services": "Law Group", "Road materials": "Aggregates", "Equipment repair": "Equipment Repair",
          "Insurance": "Insurance Pool", "IT services": "IT Solutions", "Janitorial": "Cleaning Services",
          "Telephone and internet": "Telecom"}


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


class Generator:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)
        self.start = date.fromisoformat(cfg.start)
        self.end = self.start + timedelta(days=cfg.days - 1)
        self.labels: list[dict] = []
        self._ids = {"INV": 0, "PAY": 0, "APP": 0, "SUP": 0}
        self.check_no = 10000

    # ---------- helpers ----------
    def _next(self, prefix: str) -> str:
        self._ids[prefix] += 1
        return f"{prefix}{self._ids[prefix]:06d}"

    def _business_time(self) -> time:
        h = int(self.rng.integers(8, 17))
        return time(h, int(self.rng.integers(0, 60)))

    def _meeting_dates(self) -> list[date]:
        # 2nd and 4th Tuesday of each month
        out, d = [], self.start
        while d <= self.end:
            if d.weekday() == 1 and ((d.day - 1) // 7) in (1, 3):
                out.append(d)
            d += timedelta(days=1)
        return out

    def _label(self, scheme_id: str, typ: str, table: str, record_id: str, note: str = ""):
        self.labels.append(dict(scheme_id=scheme_id, type=typ, table=table,
                                record_id=record_id, note=note))

    # ---------- normal life ----------
    def build_suppliers(self) -> pd.DataFrame:
        rows, cats = [], list(CATEGORIES)
        used = set()
        for i in range(self.cfg.n_suppliers):
            cat = cats[i % len(cats)]
            while True:
                name = f"{self.rng.choice(NAME_A)} {NAME_B[cat]}"
                if name not in used:
                    used.add(name)
                    break
            city, st, zip3 = CITIES[int(self.rng.integers(len(CITIES)))]
            sid = self._next("SUP")
            entered = self.start - timedelta(days=int(self.rng.integers(100, 2000)))
            rows.append(dict(
                Supplier_Account_ID=sid, Supplier_Account_Name=name, Supplier_Group=cat,
                Supplier_Physical_Street_Address1=f"{int(self.rng.integers(10, 9999))} {self.rng.choice(STREETS)}",
                Supplier_Physical_City=city, Supplier_Physical_State_Province=st,
                Supplier_Physical_ZipPostalCode=f"{zip3}{int(self.rng.integers(10, 99))}",
                Supplier_TIN_Hash=_hash(f"TIN-{sid}"),
                Active_Date=entered.isoformat(), Inactive_Date="",
                Entered_By="U01", Entered_Date=entered.isoformat(),
                Approved_By="U03", Last_Modified_By="U01", Last_Modified_Date=entered.isoformat(),
                _median=CATEGORIES[cat][0] * float(self.rng.uniform(0.6, 1.6)),
                _sigma=CATEGORIES[cat][1], _per_year=CATEGORIES[cat][2],
                _inv_seq=int(self.rng.integers(1000, 90000)),
            ))
        return pd.DataFrame(rows)

    def build_invoices(self, sup: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, s in sup.iterrows():
            n = max(1, int(self.rng.poisson(s._per_year * self.cfg.days / 365)))
            days = np.sort(self.rng.integers(0, self.cfg.days, n))
            seq = s._inv_seq
            for d in days:
                seq += int(self.rng.integers(3, 400))       # supplier has other customers
                amt = round(float(self.rng.lognormal(np.log(s._median), s._sigma)), 2)
                inv_date = self.start + timedelta(days=int(d))
                entered = inv_date + timedelta(days=int(self.rng.integers(1, 6)))
                while entered.weekday() >= 5:          # office closed at weekends
                    entered += timedelta(days=1)
                rows.append(dict(
                    Invoice_ID=self._next("INV"), Invoice_Number=f"{seq}",
                    Invoice_Date=inv_date.isoformat(),
                    Invoice_Due_Date=(inv_date + timedelta(days=30)).isoformat(),
                    Supplier_Account_ID=s.Supplier_Account_ID, Business_Unit_Code="GEN",
                    Entered_By="U01" if self.rng.random() < 0.85 else "U02",
                    Entered_Date=entered.isoformat(), Entered_Time=self._business_time().isoformat(),
                    Approved_By="", Invoice_Amount_Local=amt,
                ))
        df = pd.DataFrame(rows)
        # approvals: approver signs most; the clerk sometimes self-approves (normal weakness)
        self_ok = self.rng.random(len(df)) < self.cfg.normal_self_approval_rate
        df["Approved_By"] = np.where(self_ok, df["Entered_By"],
                                     self.rng.choice(["U03", "U04"], len(df)))
        return df

    def pay_invoices(self, inv: pd.DataFrame):
        meetings = self._meeting_dates()
        pays, apps = [], []
        for _, r in inv.iterrows():
            due = date.fromisoformat(r.Entered_Date)
            pay_date = next((m for m in meetings if m >= due), self.end)
            pid, aid = self._new_payment(r.Supplier_Account_ID, pay_date, r.Invoice_Amount_Local,
                                         r.Entered_By, r.Approved_By, r.Invoice_ID, pays, apps)
        return pays, apps

    def _new_payment(self, sup_id, pay_date, amount, entered_by, approved_by, invoice_id, pays, apps,
                     ptype=None):
        self.check_no += 1
        ptype = ptype or ("CHECK" if self.rng.random() < 0.7 else "ACH")
        pid = self._next("PAY")
        pays.append(dict(
            Payment_ID=pid, Supplier_Account_ID=sup_id, Business_Unit_Code="GEN",
            Payment_Date=pay_date.isoformat(), Reference_Number=str(self.check_no),
            Amount_Credit_Debit_Indicator="D", Payment_Type=ptype,
            Payment_Amount_Local=round(float(amount), 2),
            Entered_By=entered_by, Entered_Date=pay_date.isoformat(),
            Entered_Time=self._business_time().isoformat(), Approved_By=approved_by,
        ))
        aid = None
        if invoice_id is not None:
            aid = self._next("APP")
            apps.append(dict(AP_Application_ID=aid, AP_Application_Date=pay_date.isoformat(),
                             Supplier_Account_ID=sup_id, Payment_ID=pid, Invoice_ID=invoice_id,
                             AP_Application_Amount=round(float(amount), 2), Entered_By=entered_by))
        return pid, aid

    def _rand_day(self, lo=30, hi=None) -> date:
        hi = hi or self.cfg.days - 30
        return self.start + timedelta(days=int(self.rng.integers(lo, hi)))

    def _next_meeting(self, d: date) -> date:
        return next((m for m in self._meeting_dates() if m >= d), self.end)

    # ---------- injected irregularities ----------
    def inject(self, sup, inv, pays, apps, chg):
        k = 0
        inv_rows = inv.to_dict("records")

        def pick_invoice():
            return inv_rows[int(self.rng.integers(len(inv_rows)))]

        # T01 exact duplicate invoice, paid twice
        for _ in range(self.cfg.n_exact_duplicates):
            k += 1; sid = f"S{k:03d}"
            o = pick_invoice()
            d = date.fromisoformat(o["Entered_Date"]) + timedelta(days=int(self.rng.integers(10, 40)))
            new = dict(o, Invoice_ID=self._next("INV"), Entered_Date=d.isoformat())
            inv_rows.append(new)
            pid, _ = self._new_payment(o["Supplier_Account_ID"], self._next_meeting(d),
                                       o["Invoice_Amount_Local"], new["Entered_By"], new["Approved_By"],
                                       new["Invoice_ID"], pays, apps)
            self._label(sid, "T01", "Invoices_Received", new["Invoice_ID"], f"duplicate of {o['Invoice_ID']}")
            self._label(sid, "T01", "Payments_Made", pid)

        # T02 near-duplicate (reformatted number), paid
        for _ in range(self.cfg.n_near_duplicates):
            k += 1; sid = f"S{k:03d}"
            o = pick_invoice()
            num = str(o["Invoice_Number"])
            fmt = self.rng.choice([f"INV-{num}", f"0{num}", f"{num[:2]}-{num[2:]}", f"{num} "])
            d = date.fromisoformat(o["Entered_Date"]) + timedelta(days=int(self.rng.integers(5, 25)))
            new = dict(o, Invoice_ID=self._next("INV"), Invoice_Number=str(fmt), Entered_Date=d.isoformat())
            inv_rows.append(new)
            pid, _ = self._new_payment(o["Supplier_Account_ID"], self._next_meeting(d),
                                       o["Invoice_Amount_Local"], new["Entered_By"], new["Approved_By"],
                                       new["Invoice_ID"], pays, apps)
            self._label(sid, "T02", "Invoices_Received", new["Invoice_ID"], f"near-duplicate of {o['Invoice_ID']}")
            self._label(sid, "T02", "Payments_Made", pid)

        # T04 one invoice paid twice (second payment applied to the same invoice)
        for _ in range(self.cfg.n_overpayments):
            k += 1; sid = f"S{k:03d}"
            o = pick_invoice()
            d = self._next_meeting(date.fromisoformat(o["Entered_Date"]) + timedelta(days=20))
            pid, aid = self._new_payment(o["Supplier_Account_ID"], d, o["Invoice_Amount_Local"],
                                         "U01", "U01", o["Invoice_ID"], pays, apps)
            self._label(sid, "T04", "Payments_Made", pid, f"second payment of {o['Invoice_ID']}")

        # legitimate bank changes (NOT labeled) - realistic false-positive bait
        for _ in range(self.cfg.n_legit_bank_changes):
            s = sup.iloc[int(self.rng.integers(len(sup)))]
            d = self._rand_day()
            chg.append(dict(Supplier_Account_ID=s.Supplier_Account_ID, Changed_Field="bank_account",
                            Old_Value_Hash=_hash(f"old{d}{s.Supplier_Account_ID}"),
                            New_Value_Hash=_hash(f"new{d}{s.Supplier_Account_ID}"),
                            Changed_By="U01", Changed_Date=d.isoformat(),
                            Changed_Time=self._business_time().isoformat()))

        # T05 bank redirect: change, then a large payment within the window
        for _ in range(self.cfg.n_bank_redirects):
            k += 1; sid = f"S{k:03d}"
            s = sup[sup._median > 1500].sample(1, random_state=int(self.rng.integers(1e9))).iloc[0]
            d = self._rand_day()
            chg.append(dict(Supplier_Account_ID=s.Supplier_Account_ID, Changed_Field="bank_account",
                            Old_Value_Hash=_hash(f"o{sid}"), New_Value_Hash=_hash(f"n{sid}"),
                            Changed_By="U02", Changed_Date=d.isoformat(), Changed_Time="18:42:00"))
            amt = round(float(s._median) * float(self.rng.uniform(2.0, 4.0)), 2)
            inv_d = d + timedelta(days=int(self.rng.integers(1, 6)))
            iid = self._next("INV")
            inv_rows.append(dict(Invoice_ID=iid, Invoice_Number=f"{int(s._inv_seq) + 99999}",
                                 Invoice_Date=inv_d.isoformat(), Invoice_Due_Date=(inv_d + timedelta(days=10)).isoformat(),
                                 Supplier_Account_ID=s.Supplier_Account_ID, Business_Unit_Code="GEN",
                                 Entered_By="U02", Entered_Date=inv_d.isoformat(), Entered_Time="17:55:00",
                                 Approved_By="U03", Invoice_Amount_Local=amt))
            pid, _ = self._new_payment(s.Supplier_Account_ID, self._next_meeting(inv_d), amt, "U02", "U03",
                                       iid, pays, apps, ptype="ACH")
            self._label(sid, "T05", "FIRA_Supplier_Change_Log", f"{s.Supplier_Account_ID}@{d.isoformat()}")
            self._label(sid, "T05", "Invoices_Received", iid)
            self._label(sid, "T05", "Payments_Made", pid)

        # T06/T10/T12/T14 fictitious supplier created and paid by the clerk
        new_sup = []
        for _ in range(self.cfg.n_fictitious_suppliers):
            k += 1; sid = f"S{k:03d}"
            fid = self._next("SUP")
            created = self._rand_day(30, 120)
            new_sup.append(dict(
                Supplier_Account_ID=fid, Supplier_Account_Name="Valley Maintenance Services",
                Supplier_Group="Equipment repair", Supplier_Physical_Street_Address1="PO Box 412",
                Supplier_Physical_City="Colville", Supplier_Physical_State_Province="WA",
                Supplier_Physical_ZipPostalCode="99114", Supplier_TIN_Hash="",
                Active_Date=created.isoformat(), Inactive_Date="", Entered_By="U01",
                Entered_Date=created.isoformat(), Approved_By="U01", Last_Modified_By="U01",
                Last_Modified_Date=created.isoformat(), _median=0, _sigma=0, _per_year=0, _inv_seq=0))
            self._label(sid, "T06", "Supplier_Listing", fid, "fictitious supplier")
            n_bills = int(self.rng.integers(6, 10))
            for j in range(n_bills):
                d = created + timedelta(days=14 + 30 * j + int(self.rng.integers(0, 6)))
                if d > self.end:
                    break
                amt = float(self.rng.choice([1500, 2000, 2400, 2500, 3000]))
                iid = self._next("INV")
                inv_rows.append(dict(Invoice_ID=iid, Invoice_Number=f"{1001 + j}",
                                     Invoice_Date=d.isoformat(), Invoice_Due_Date=(d + timedelta(days=30)).isoformat(),
                                     Supplier_Account_ID=fid, Business_Unit_Code="GEN", Entered_By="U01",
                                     Entered_Date=d.isoformat(), Entered_Time=self._business_time().isoformat(),
                                     Approved_By="U01", Invoice_Amount_Local=amt))
                pid, _ = self._new_payment(fid, self._next_meeting(d), amt, "U01", "U01", iid, pays, apps,
                                           ptype="CHECK")
                self._label(sid, "T06", "Invoices_Received", iid)
                self._label(sid, "T06", "Payments_Made", pid)

        # T09 split purchases just under the approval threshold
        for _ in range(self.cfg.n_split_purchases):
            k += 1; sid = f"S{k:03d}"
            s = sup.sample(1, random_state=int(self.rng.integers(1e9))).iloc[0]
            d = self._rand_day()
            parts = int(self.rng.integers(2, 4))
            seq = int(s._inv_seq) + 50000
            for j in range(parts):
                amt = round(self.cfg.approval_threshold * float(self.rng.uniform(0.85, 0.99)), 2)
                dd = d + timedelta(days=j)
                iid = self._next("INV")
                inv_rows.append(dict(Invoice_ID=iid, Invoice_Number=f"{seq + j * 7}",
                                     Invoice_Date=dd.isoformat(), Invoice_Due_Date=(dd + timedelta(days=30)).isoformat(),
                                     Supplier_Account_ID=s.Supplier_Account_ID, Business_Unit_Code="GEN",
                                     Entered_By="U01", Entered_Date=dd.isoformat(),
                                     Entered_Time=self._business_time().isoformat(), Approved_By="U01",
                                     Invoice_Amount_Local=amt))
                pid, _ = self._new_payment(s.Supplier_Account_ID, self._next_meeting(dd), amt, "U01", "U01",
                                           iid, pays, apps)
                self._label(sid, "T09", "Invoices_Received", iid)
                self._label(sid, "T09", "Payments_Made", pid)

        # T15 payment to an inactive supplier (no invoice), after its last normal payment
        sup = sup.copy()
        last_paid = {}
        for p_ in pays:
            last_paid[p_["Supplier_Account_ID"]] = max(last_paid.get(p_["Supplier_Account_ID"], ""), p_["Payment_Date"])
        used = set()
        for _ in range(self.cfg.n_inactive_payments):
            k += 1; sid = f"S{k:03d}"
            for _try in range(200):
                idx = int(self.rng.integers(len(sup)))
                sup_id = sup.iloc[idx].Supplier_Account_ID
                lp = last_paid.get(sup_id)
                if sup_id in used or not lp:
                    continue
                inactive_from = date.fromisoformat(lp) + timedelta(days=int(self.rng.integers(5, 20)))
                if inactive_from + timedelta(days=45) < self.end:
                    break
            else:
                raise RuntimeError("no supplier available for T15 injection")
            used.add(sup_id)
            sup.loc[sup.index[idx], "Inactive_Date"] = inactive_from.isoformat()
            d = self._next_meeting(inactive_from + timedelta(days=int(self.rng.integers(10, 40))))
            pid, _ = self._new_payment(sup_id, d, round(float(self.rng.uniform(800, 4000)), 2), "U01", "U01",
                                       None, pays, apps)
            self._label(sid, "T15", "Payments_Made", pid, "payment to inactive supplier, no invoice")

        sup = pd.concat([sup, pd.DataFrame(new_sup)], ignore_index=True) if new_sup else sup
        return sup, pd.DataFrame(inv_rows)

    # ---------- run ----------
    def run(self) -> dict[str, pd.DataFrame]:
        sup = self.build_suppliers()
        inv = self.build_invoices(sup)
        pays, apps = self.pay_invoices(inv)
        chg: list[dict] = []
        sup, inv = self.inject(sup, inv, pays, apps, chg)
        # suppliers whose invoices were all made up later are still fine; drop helper columns
        sup = sup[[c for c in sup.columns if not c.startswith("_")]]
        users = pd.DataFrame([dict(User_ID=u, User_Name=n, Role=r) for u, n, r in USERS])
        return {
            "Supplier_Listing": sup,
            "Invoices_Received": inv.sort_values("Invoice_ID").reset_index(drop=True),
            "Payments_Made": pd.DataFrame(pays).sort_values("Payment_ID").reset_index(drop=True),
            "AP_Cash_Application": pd.DataFrame(apps).sort_values("AP_Application_ID").reset_index(drop=True),
            "FIRA_Supplier_Change_Log": pd.DataFrame(chg),
            "User_Listing": users,
            "labels": pd.DataFrame(self.labels),
        }


def write(tables: dict[str, pd.DataFrame], out: Path, cfg: Config) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
    labels = tables["labels"]
    card = {
        "generator_version": GENERATOR_VERSION,
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "config": asdict(cfg),
        "row_counts": {k: int(len(v)) for k, v in tables.items()},
        "injected_schemes": int(labels["scheme_id"].nunique()) if len(labels) else 0,
        "labeled_payments": int((labels["table"] == "Payments_Made").sum()) if len(labels) else 0,
        "payment_prevalence": round(float((labels["table"] == "Payments_Made").sum())
                                    / max(1, len(tables["Payments_Made"])), 4),
        "synthetic": True,
        "note": "Synthetic data. No real persons, suppliers or governments.",
    }
    (out / "data_card.json").write_text(json.dumps(card, indent=2))


def main(argv=None):
    p = argparse.ArgumentParser(description="Generate FIRA synthetic AP data")
    p.add_argument("--out", default="data/small_seed42")
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args(argv)
    cfg = Config(seed=a.seed)
    write(Generator(cfg).run(), Path(a.out), cfg)
    print(f"Wrote synthetic data to {a.out}")


if __name__ == "__main__":
    main()

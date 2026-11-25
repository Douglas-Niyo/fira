"""Monthly review pack for the independent reviewer (rules-only baseline, v0.1).

Turns raw rule alerts into what a board member can act on. Design reviewed and
approved by D. Niyonsingiza (2026-11-20):

* Tier 1 (check first): bank-change payments (R05), supplier created and paid by one
  user (R06), invoices paid more than once (R04), payments without invoices or to
  inactive suppliers (R15).
* Tier 2 (check next): duplicates (R01-R03), split purchases (R09), missing approvals
  (R08), supplier-record problems (R10, R11).
* Context only: out-of-hours entry (R13) and consecutive invoice numbers (R14) are not
  listed on their own; they are attached to a supplier that already has a Tier 1 or 2 item.
* Self-approval (R07) is reported as a monthly summary per user, with invoices and
  payments counted separately, instead of one alert per transaction.

Within a tier, items are ordered by amount (largest first). Several alerts about the
same supplier and tier in a month are grouped into one review item.

Usage:
    python -m fira.review --data data/small_seed42 --out review
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .rules import Rules, load

TIER = {"R05": 1, "R06": 1, "R04": 1, "R15": 1,
        "R01": 2, "R02": 2, "R03": 2, "R09": 2, "R08": 2, "R10": 2, "R11": 2}
CONTEXT = {"R13", "R14"}


def _month(d: str) -> str:
    return str(d)[:7] if d else ""


def build(alerts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    a = alerts.copy()
    a["amount"] = pd.to_numeric(a["amount"], errors="coerce")
    a["month"] = a["date"].map(_month)
    # supplier-level month for master-file alerts without a date in the period
    a.loc[a.month == "", "month"] = "standing"

    tiered = a[a.rule.isin(TIER)].copy()
    tiered["tier"] = tiered.rule.map(TIER)
    flagged_suppliers = set(tiered.supplier_id)
    ctx = a[a.rule.isin(CONTEXT) & a.supplier_id.isin(flagged_suppliers)]
    ctx_by_sup = ctx.groupby(["supplier_id","month"]).reason.apply(lambda s: " | ".join(sorted(set(s))))

    items = (tiered.groupby(["month", "tier", "supplier_id"], dropna=False)
             .agg(supplier_name=("supplier_name", "first"),
                  rules=("rule", lambda s: ",".join(sorted(set(s)))),
                  records=("record_id", lambda s: ";".join(s)),

                  largest_amount=("amount", "max"),
                  reasons=("reason", lambda s: " | ".join(dict.fromkeys(s))))
             .reset_index())
    items["context"] = [ctx_by_sup.get((r.supplier_id,r.month),"") for r in items.itertuples()]
    items = items.sort_values(["month", "tier", "largest_amount"], ascending=[True, True, False])
    items.insert(0, "item_id", [f"I{i + 1:04d}" for i in range(len(items))])

    sa = a[a.rule == "R07"].copy()
    sa["user"] = sa["user_id"]
    sa["kind"] = sa.table.map({"Invoices_Received": "invoices", "Payments_Made": "payments"})
    summary = (sa.groupby(["month", "user", "kind"])
               .agg(count=("record_id", "count"), dollars=("amount", "sum"))
               .unstack("kind", fill_value=0))
    summary.columns = [f"{k}_{m}" for m, k in summary.columns]
    summary = summary.reset_index()
    summary=summary.reindex(columns=["month","user","invoices_count","payments_count","invoices_dollars","payments_dollars"],fill_value=0)
    # drill-down: every self-approved record stays reachable behind its summary line
    detail = sa[["month", "user", "kind", "record_id", "supplier_name", "amount", "date"]]
    detail = detail.sort_values(["month", "user", "kind", "amount"], ascending=[True, True, True, False])
    return items, summary, detail


def main(argv=None):
    p = argparse.ArgumentParser(description="Build the monthly review pack")
    p.add_argument("--data", default="data/small_seed42")
    p.add_argument("--out", default="review")
    a = p.parse_args(argv)
    from .monthly import export
    export(a.data,a.out)


if __name__ == "__main__":
    main()

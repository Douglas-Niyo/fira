# Data card: FIRA synthetic AP benchmark, v0.1.1 (November 1, 2026)

## What it is

Synthetic accounts-payable data for one fictional small U.S. local government over one
fiscal year (July 2025 to June 2026), with labeled, injected irregularities.
**No real people, suppliers or governments are represented.**

Generate it with:

```
pip install -r requirements.txt
python -m fira.generator --out data/small_seed42 --seed 42
python -m unittest -v
```

## Files

| File | Contents |
| --- | --- |
| Supplier_Listing.csv | About 60 suppliers in 12 categories (utilities, fuel, engineering, legal and others) |
| Invoices_Received.csv | About 590 invoices |
| Payments_Made.csv | About 590 payments (checks and ACH) |
| AP_Cash_Application.csv | Which payment paid which invoice |
| FIRA_Supplier_Change_Log.csv | Bank-detail changes (some legitimate, some injected) |
| User_Listing.csv | Four users: two clerks, the mayor and the council treasurer |
| labels.csv | Every injected record, with scheme_id and type |
| data_card.json | Settings, row counts and prevalence for this run |

## How "normal" is modeled

- Each supplier has its own typical amount (log-normal) and billing frequency.
- One clerk-treasurer enters about 85% of invoices; a deputy enters the rest.
- About 12% of invoices are self-approved. In a small entity this is a normal weakness,
  not fraud, so these are **not** labeled. A good method must not drown the reviewer in them.
- Invoices are entered on weekdays only; the office is closed at weekends.
- Payments go out on council meeting dates (2nd and 4th Tuesday).
- Suppliers' invoice numbers jump between bills, because they have other customers.
- Four legitimate bank-detail changes are included and **not** labeled, so the T05
  check meets realistic false alarms.

## Injected irregularities (default settings)

| Type | Schemes | What is injected |
| --- | --- | --- |
| T01 Exact duplicate | 3 | A copied invoice, paid again |
| T02 Near-duplicate | 3 | A copied invoice with a reformatted number, paid again |
| T04 Paid twice | 2 | A second payment applied to an already-paid invoice |
| T05 Bank redirect | 2 | A bank change after hours by the deputy, then a larger-than-usual ACH payment |
| T06 Fictitious supplier | 1 | A P.O.-box supplier with no tax ID, created, billed and approved by the clerk: consecutive invoice numbers and round amounts |
| T09 Split purchase | 2 | Two or three invoices just under the $5,000 approval threshold on consecutive days |
| T15 Inactive supplier | 2 | A payment with no invoice to a supplier marked inactive |

With seed 42, about 24 of 590 payments (about 4%) are labeled. That is higher than real life on
purpose, so that the smallest file still contains every type. The Week 8 experiments
will vary prevalence (0.1%, 0.5% and 1%) and entity size.

## Known limitations

- The amounts, timing and roles are plausible but **not yet calibrated** to real data.
  Calibration against open-checkbook data is planned.
- One entity, one year, one fund. No grants, purchase orders or goods receipts yet.
- The fraud patterns are the ones we chose to inject. A method that finds them has
  only shown it can find these patterns, not real fraud in general.

## Change history

| Version | Date | Change | Why |
| --- | --- | --- | --- |
| 0.1.0 | 2026-10-30 | First version | |
| 0.1.1 | 2026-11-01 | Normal invoices no longer entered at weekends | First rules run flagged 186 normal weekend entries; unrealistic for a small office |
| 0.1.1 | 2026-11-01 | T15: supplier is made inactive only after its last normal payment | Normal payments were landing after the inactive date and looked like unlabeled irregularities |

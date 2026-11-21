# FIRA irregularity typology, v0.1 (draft, October 30, 2026)

This is the list of payment irregularities FIRA v1 will look for. FIRA does not invent
new tests. Each type is grounded in published auditor guidance, the ACFE Fraud Tree,
or documented public-sector cases. Field names refer to [schema-v0.1.md](schema-v0.1.md).

**An alert means "review this", never "fraud".** Many alerts will have innocent
explanations: data-entry errors, legitimate repeat purchases, or system quirks.

Control reference for all types: GAO *Standards for Internal Control in the Federal
Government* (Green Book), Principle 10 (design control activities, including
segregation of duties), and COSO 2013 Principle 10. Where segregation of duties is not
possible, these checks are designed to act as compensating controls.

## Types in version 1 (accounts payable and vendor master)

| ID | Irregularity | What it looks like in the data | Why it matters | Fields needed | Method | Grounding |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | Exact duplicate invoice | Same supplier, invoice number and amount entered twice | Paying the same bill twice, by error or on purpose | Invoices_Received | Rule | AZ Auditor General duplicate test; Ohio and NY duplicate-payment results |
| T02 | Near-duplicate invoice | Same supplier and amount; invoice numbers differ only by punctuation, spaces or leading zeros (e.g., INV-0012 vs INV12); dates within the duplicate window | Hides a duplicate from an exact-match check | Invoices_Received | Rule (normalized match) | AZ guidance on removing hyphens and slashes; KNIME duplicate-invoice workflow |
| T03 | Same amount, different invoice numbers | Same supplier and identical amount, different invoice numbers, within the window | Possible re-billing of one service | Invoices_Received | Rule + ranking | KNIME duplicate-invoice workflow |
| T04 | Invoice paid more than once, or overpaid | Applied payments for one invoice exceed its amount | Direct loss | AP_Cash_Application, Invoices_Received | Rule | Ohio and NY duplicate-payment recoveries |
| T05 | Payment soon after a bank-detail change | Supplier bank details changed, then a payment within the bank-change window | Payment redirection (business email compromise) | FIRA_Supplier_Change_Log, Payments_Made | Rule | FBI IC3 business email compromise reports |
| T06 | Supplier created and paid by the same person | Entered_By on the supplier matches Entered_By or Approved_By on its payments | One person controls both set-up and payment: the core segregation failure | Supplier_Listing, Payments_Made | Rule | ACFE Fraud Tree: billing schemes (shell company) |
| T07 | Self-approved invoice or payment | Entered_By equals Approved_By | No independent approval | Invoices_Received, Payments_Made | Rule | Green Book segregation of duties |
| T08 | Missing approval above threshold | Approved_By blank and amount at or above the approval threshold | Control bypassed | Invoices_Received, Payments_Made, FIRA_Settings | Rule | Entity approval policy |
| T09 | Split purchases | Several invoices from one supplier within a few days, each under the threshold, together above it | Avoiding approval or bidding rules | Invoices_Received, FIRA_Settings | Rule | ACFE Fraud Tree: purchasing schemes |
| T10 | Supplier with missing tax ID or P.O.-box-only address | Supplier_TIN blank, or physical address is a P.O. box | Common sign of a fictitious supplier | Supplier_Listing | Rule | AZ Auditor General vendor-master analysis |
| T11 | Possible duplicate suppliers | Same TIN, or very similar names or addresses | Duplicate payments; hiding activity across two records | Supplier_Listing | Rule (fuzzy match) | AZ vendor-master analysis; commercial duplicate-vendor tests |
| T12 | Round-dollar amounts | Invoice amounts evenly divisible by 100 or 1,000 | Weak signal of estimates or invented bills; used only to rank, never alone | Invoices_Received | Score feature | AZ even-dollar test |
| T13 | Entered outside business hours | Entry on weekends, holidays or late at night | Activity when no one else is present | Entered_Date, Entered_Time | Score feature | AZ day-of-week test |
| T14 | Unusual invoice-number patterns | One supplier's invoices numbered consecutively over months, or gaps in the entity's own check sequence. Can be legitimate; used as context alongside other flags | Fictitious supplier; removed records | Invoices_Received, Payments_Made | Rule + score | ACFE Fraud Tree: shell company; AZ gap and sequence test |
| T15 | Timing anomalies | Payment before the invoice date; payment to an inactive supplier; payment with no linked invoice | Payment without a valid obligation | Payments_Made, AP_Cash_Application, Supplier_Listing | Rule | Auditor guidance |
| T16 | Unusual new or reactivated supplier | New or long-dormant supplier receives payments far above its peers early on | Shell company or account takeover | Supplier_Listing, Payments_Made | Model score | Peer-group anomaly scoring |

## Planned for later versions

| ID | Irregularity | Version | Note |
| --- | --- | --- | --- |
| T17 | Grant charge outside award period or allowed categories | v2 | Needs FIRA_Fund_Coding |
| T18 | Personal purchases on entity debit or credit cards | v1.1 (planned) | Common in documented small-town cases (WA State Auditor; NY Comptroller) |
| T19 | Receipts collected but not deposited | v1.1 (planned) | Needs bank-statement data |
| T20 | Payroll overpayments to oneself | v2 | Needs payroll data |

## Added from practitioner review (D. Niyonsingiza, November 20, 2026)

Reviewing the first alert list as a council treasurer would, Douglas identified checks
that a government finance office makes routinely and that FIRA v1 does not yet cover.
They need data FIRA v1 does not read (fund coding, purchase orders, goods receipts,
budgets, bank statements, review sign-offs), so they are planned for later versions.

| ID | Check | Data needed | Version |
| --- | --- | --- | --- |
| T21 | Spending charged to the wrong fund, department, grant or accounting period | GL coding on invoice lines; fund and period tables | v2 |
| T22 | Amount not authorized by a contract or purchase order, or goods and services not received (three-way match) | Purchase_Orders, Goods_Received (AICPA P2P) | v2 |
| T23 | Grant-funded cost outside the award's purpose, dates or documentation rules (extends T17) | FIRA_Fund_Coding; award terms | v2 |
| T24 | Payments that do not agree with bank activity and the ledger, including voids, credits and reversals | Bank statements; AP_Adjustments | v1.1 |
| T25 | Cumulative spending above a budget line or contract limit | Budget and contract tables | v2 |
| T26 | Independent review recorded as done but not actually documented | Review sign-off log | v1.1 |

Douglas also set the review priorities used by `fira/review.py`: bank-change payments,
supplier set-up and payment by one user, invoices paid more than once, and unsupported
payments first; duplicates and split purchases next; out-of-hours entry and consecutive
invoice numbers only as context alongside stronger flags; self-approval as a monthly
summary per user with invoices and payments counted separately.

## Open questions

1. The ACFE's interactive tool lists 117 anti-fraud data analytics tests. Each type above
   should cite the specific ACFE test it matches. *Status: not yet mapped test by test.*
2. *Decided October 30, 2026:* documented small-town losses (Washington State Auditor;
   NY Comptroller) mostly involve cards, cash and payroll rather than vendor invoices.
   Version 1 stays limited to accounts payable and the vendor master, because that data
   is standardized and testable. Bank-statement and card checks (T18, T19) follow
   immediately as version 1.1.

## Sources

- Arizona Auditor General, *Fraud Prevention Alert: Data Analytics, Part 2* (Report 18-406, October 2018).
- ACFE, *Anti-Fraud Data Analytics Tests* (Fraud Risk Management Guide resources).
- InnovateOhio and Ohio OBM, duplicate-payment analytics results (March 31, 2023).
- Office of the New York State Comptroller, *Enterprise Fraud, Waste and Abuse Prevention and Detection* (September 2025).
- Washington State Auditor's Office, small-government fraud reports (2025–2026).
- FBI Internet Crime Complaint Center, 2025 annual report (business email compromise).
- GAO, *Standards for Internal Control in the Federal Government* (Green Book).

# Supported input for development release 0.2.0

The executable contract is in fira/monthly.py (COL, KEY, DATE, contract). The included sample is entirely synthetic. The only supported data are synthetic CSV tables following that contract plus profile.json. The CLI explicitly rejects unsupported currencies, missing required columns, raw supplier TINs, ambiguous invoice keys, credit disbursements and an adjustments CSV. An absent column stops the run with a message; it is not a passed check. Empty approval values in an available approval column have a different meaning. This release has no production ERP connector, de-identification service, multicurrency conversion, full ADS conformance claim or grant allowability test.

## Sources and meaning

Selected table and field names reference AICPA, Procure to Pay Subledger Standard (July 2015), §§2.5 and 2.8–2.10, 2.14. AICPA describes a voluntary extraction convention; the user listing and supplier-change log here are project-specific. The Base Standard user mapping is unverified. Do not upload third-party standards with this project.

The standard permits a flat invoice export with one row per invoice and purchase order (PDF p. 27). Set invoice_rows to one_per_invoice or, only when amounts are known to be allocated, allocated_by_purchase_order. Allocations must have a nonempty distinct PO per invoice, consistent header metadata and reconciled source totals. The adapter sums allocations and stores invoice_source_rows.csv. An exporter that repeats invoice totals per PO is unsupported. A file alone cannot establish its accounting semantics.

Use one documented USD basis for invoice, payment and application amounts. In ADS the application amount and local invoice amount are not necessarily in the same currency (pp. 31, 54). The synthetic profile explicitly declares one USD basis. C/D alone does not identify a reversal. Unreversed synthetic payments have a positive amount and D; other cases require a separate mapped workflow. Applications have independent IDs. A payment can have several applications. The check compares accumulated applications against the invoiced amount with one cent of tolerance.

## Time and identity

Fiscal start must be the first day of a month. The release evaluates twelve month ends. Normal settlements may occur after year end at the next meeting and remain in the generated table for reconciliation, but cannot enter that year's review. Approval is assumed available at entry; supplier name, address, and identity are static synthetic attributes; inactivation is effective on its date. Arbitrary overwritten real supplier masters or delayed approval histories are unsupported. No payroll or banking data are needed.

The review drill-down uses (table, record ID) throughout. A supplier change uses supplier ID and change date; multiple changes for one supplier on a single date need a more granular key and are rejected. Each displayed item is a review question; amounts on overlapping alerts must not be added to infer loss.

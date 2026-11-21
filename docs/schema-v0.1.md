# FIRA data layout, v0.1 (draft, October 30, 2026)

FIRA reads ordinary accounts-payable exports and maps them to one canonical layout.
The layout follows the table and field names of the **AICPA Audit Data Standards:
Procure to Pay Subledger Standard (July 2015)**, so that data already prepared for
auditors can be reused, and so that FIRA can work across different ERP systems.

> Field names below are taken from the AICPA standard for interoperability. Descriptions
> are FIRA's own. The standard itself is copyrighted by the AICPA and is not reproduced
> here; obtain it from aicpa-cima.com.

Level 1 = required by FIRA v1. Level 2 = used when available; checks that need a
missing field are skipped and reported as "not tested", never as "passed".

## 1. Tables used from the AICPA P2P standard

### Supplier_Listing (vendor master)

| Field | FIRA level | Used for |
| --- | --- | --- |
| Supplier_Account_ID | 1 | Key that links all tables |
| Supplier_Account_Name | 1 | Duplicate-supplier checks (name similarity) |
| Supplier_Physical_Street_Address1, _City, _State_Province, _ZipPostalCode | 1 | Duplicate suppliers; P.O.-box-only suppliers |
| Supplier_Billing_Address1, _City, _State_Province, _ZipPostalCode | 2 | Address differences |
| Supplier_TIN | 1 | Missing or shared tax IDs (stored hashed) |
| Active_Date, Inactive_Date | 2 | Payments to inactive suppliers; new-supplier checks |
| Entered_By, Entered_Date | 1 | Who created the supplier, and when |
| Approved_By | 2 | Supplier set-up approval |
| Last_Modified_By, Last_Modified_Date | 2 | Recent changes to the supplier record |

### Invoices_Received (invoice headers)

| Field | FIRA level | Used for |
| --- | --- | --- |
| Invoice_ID | 1 | Key |
| Invoice_Number | 1 | Duplicate and sequence checks (as the supplier wrote it) |
| Invoice_Date, Invoice_Due_Date | 1 | Timing checks |
| Supplier_Account_ID | 1 | Link to supplier |
| Purchase_Order_ID | 2 | Invoices without a purchase order |
| Business_Unit_Code | 2 | Department or fund grouping |
| Entered_By, Entered_Date, Entered_Time | 1 / 2 / 2 | Who entered it; after-hours entry |
| Approved_By, Approved_By_Date | 2 | Self-approval; missing approval |
| Invoice_Amount_Local | 1 | Amount checks |

### Payments_Made (disbursements)

| Field | FIRA level | Used for |
| --- | --- | --- |
| Payment_ID | 1 | Key |
| Supplier_Account_ID | 1 | Link to supplier |
| Payment_Date | 1 | Timing checks |
| Reference_Number | 1 | Check or transfer number; sequence gaps |
| Payment_Type | 1 | Check, ACH, wire, card |
| Payment_Amount_Local | 1 | Amount checks |
| Amount_Credit_Debit_Indicator | 1 | Separates payments from reversals |
| Entered_By, Approved_By | 1 / 2 | Segregation checks |

### AP_Cash_Application (which payment paid which invoice)

| Field | FIRA level | Used for |
| --- | --- | --- |
| Payment_ID, Invoice_ID, Supplier_Account_ID | 1 | Link payments to invoices |
| AP_Application_Amount | 1 | Over-payment and duplicate-payment checks |
| AP_Application_Date | 1 | Payment before invoice date |

### AP_Adjustments (credits, voids, write-offs) — optional in v1

Adjustment_ID, Adjustment_Type, Invoice_ID, Supplier_Account_ID, Adjustment_Date,
Entered_By, Approved_By, Adjustment_Amount_Local.

### User_Listing (from the AICPA *Base* Standard)

User_ID, user name, role or title, active dates. Needed to tell who did what.
*Status: the Base Standard has not yet been reviewed; field names to be confirmed.*

## 2. FIRA extensions (not in the AICPA P2P standard)

The AICPA standard allows user-defined fields to be added. FIRA needs three
extensions, because the standard has no field for supplier bank details and no
history of changes to the supplier record.

### FIRA_Supplier_Change_Log

| Field | Description |
| --- | --- |
| Supplier_Account_ID | Supplier whose record changed |
| Changed_Field | Which field changed (for example, bank account, address, TIN) |
| Old_Value_Hash, New_Value_Hash | One-way hashes, so bank numbers are never stored in plain text |
| Changed_By | User_ID of the person who made the change |
| Changed_Date, Changed_Time | When the change was made |

### FIRA_Fund_Coding (version 2)

Fund_Code, Grant_ID, award start and end dates, and allowed cost categories, for
grant-period and allowability checks.

### FIRA_Settings

| Setting | Example | Why |
| --- | --- | --- |
| Approval_Threshold | 5,000 | Split-purchase checks |
| Duplicate_Window_Days | 30 | How close two invoices must be to compare |
| Bank_Change_Window_Days | 30 | Payment soon after a bank-detail change |
| Business_Hours | 07:00–19:00, Mon–Fri | After-hours checks |
| Weekly_Review_Capacity | 25 | Number of alerts the reviewer can handle (k) |

## 3. Data protection rules

- Supplier TINs and bank details are hashed on import; plain values are never written to disk by FIRA.
- Employee data is limited to User_ID and role.
- All processing runs on the user's own machine.

## Credit

Field names follow *Audit Data Standards: Procure to Pay Subledger Standard*,
July 2015, AICPA Assurance Services Executive Committee. Copyright 2015 by the
American Institute of Certified Public Accountants, Inc.

# Literature review, v0.2 (November 1, 2026)

Scope: 23 papers found through the Maharishi International University library and
Google Scholar (October 30 to November 1, 2026), plus about 25 government, professional
and web sources from the Week 2 scan. This version summarizes what each strong source
establishes and what it changes in FIRA.

## 1. What the evidence establishes

### Small local governments have weak oversight of disbursements

- **Huefner (2011a, *The CPA Journal*; 2011b, *Journal of Forensic & Investigative
  Accounting*)** reviewed all 307 New York State Comptroller audits of towns and villages
  from 2003 to 2009. Of 259 control audits, only 24 were clean. Across 234 reports,
  auditors cited 1,587 specific deficiencies. Cash receipts and disbursements problems
  appeared in 108 audits (46%), and procurement and claims processing problems in 73
  (31%). **The most frequently cited deficiency (92 cases) was lack of oversight of
  fiscal activity by the town or village board.** Where duties could not be segregated,
  auditors looked for compensating controls such as extended board review. The
  Comptroller audits only about 3% of towns and villages each year. Of the sampled
  units, 55% had fewer than 3,000 residents.
  *Caveat: data from 2003–2009, one state.*
- **Modlin (2012, *Journal of Public Budgeting, Accounting & Financial Management*)**
  studied auditor findings for North Carolina counties (fiscal 2009; 63% responded).
  59% received a letter citing reporting problems. Smaller governments were more likely
  to have multiple problems, partly because they cannot employ more accounting staff.
- **Modlin and Stewart (2014, *Public Administration Quarterly*)** and **Matkin (2010,
  *JPBAFM*)** describe the audit and audit-committee context in U.S. local government.

### Independent review is the main compensating control when duties cannot be split

- **Gramling, Hermanson, Hermanson and Ye (2010, *The CPA Journal*)** analyzed 116
  smaller companies reporting segregation-of-duties material weaknesses. The
  compensating controls most often cited were management, board or other independent
  review and reconciliation, and third-party review.
- **Barra (2010, *Journal of Information Systems*)** shows analytically that the
  effectiveness of separating duties depends on the detective controls in the system.
  This is theoretical support for strong detective checks where separation is weak.

**Implication for FIRA.** Huefner's top finding (no board oversight) and Gramling's
top compensating control (independent review) point to the same user: the board
member or official who is supposed to review the books. This confirms the
"independent reviewer" focus chosen in Week 2.

### Machine learning for audit anomalies: methods and, above all, evaluation

- **Gronewald, Scherer and Mehdiyev (2026, arXiv:2610.06133, preprint, not yet peer
  reviewed)** is the most important paper in this set. They evaluated nine unsupervised
  detectors on four real client ledgers and one public synthetic ledger under a fixed
  review budget. Their finding: **high hit rates can hide blind spots.** On the largest
  ledger, three detectors placed about 98 anomalies in the first 100 entries, but at
  least 95.8 of those belonged to a single type. They propose *type-aware* measures:
  per-type recall, fair-share type recall (FSR@k), type coverage and first-hit rank.
  They also found that reviewer feedback raised hits per 100 reviews from 40.0 to 68.3
  but barely widened coverage (2.7 to 3.0 types).
- The same group released a **public synthetic general-ledger benchmark** (DIB General
  Ledger Data, Zenodo, 2026, doi:10.5281/zenodo.22014653).
- **Duan, Vasarhelyi and Codesso (2025, *Journal of Information Systems*)** combine
  process mining, rule-based variant analysis, control-risk assessment and ML anomaly
  detection on a real procurement process. This supports FIRA's hybrid of rules and
  scoring, and its mapping of each alert to a control.
- **Singh and Best (2016, *Managerial Auditing Journal*)** built visual analytics for
  anomalous accounts-payable transactions in SAP and found that continuous monitoring
  often produces long reports that need painstaking follow-up. This supports FIRA's
  short, explained review list.
- **Anwar and Akeel (2026, *Accounting and Auditing*, systematic review of 100
  articles)** find a gap in comparative evaluation of AI methods and stress
  human-in-the-loop controls.
- **Das (2026, "PayGuard AI", Research Square preprint, posted October 22, 2026; not
  peer reviewed)** is the closest prior work found. It combines business rules, Isolation
  Forest and logistic regression on 5,600 synthetic corporate supplier payments with a 5%
  anomaly rate across seven categories, including duplicates, overpayments and recent
  bank-account changes. The hybrid had slightly lower ROC-AUC than rules alone (0.982 vs
  0.989) but higher average precision (0.770 vs 0.680), and it **detected exact and near
  duplicates poorly**. Data and code are in its supplementary files. Its setting is a
  large corporate payer (aircraft components, ground services), not a small public entity.
- **Dubinsky and Warner (2008, *Business Credit*; first published in ACFE's *Fraud*
  magazine, 2006)** give nine practical duplicate-payment matching patterns built from
  four fields (supplier, invoice number, date, amount), plus fuzzy rules: compare invoice
  numbers after stripping zeros, letters and punctuation; treat dates within 13 days as
  similar, to avoid flagging legitimate monthly bills; and treat amounts as similar if
  within 3%, exactly double, or sharing the first four digits.
- **Dai (2021, *Journal of Emerging Technologies in Accounting*, editorial)** argues for
  continuous, data-driven government accountability.

## 2. What this changes in FIRA

1. **Evaluation (RQ1).** FIRA will report Gronewald et al.'s type-aware measures
   (per-type recall, FSR@k, type coverage, first-hit rank) alongside precision@k. For a
   board reviewer, a list that finds ten duplicates but misses the fake supplier is a
   failure, even with high precision. FIRA's injected types (T01–T15) make this possible.
2. **Originality, stated precisely.** A public synthetic *general ledger* benchmark now
   exists. FIRA's contribution is narrower: a benchmark and method for *accounts payable
   and vendor master* data in *small public entities*, built around the independent
   reviewer. For version 2 (journal entries), FIRA should use the DIB ledger rather than
   build its own.
3. **Design.** Show the reviewer which irregularity *types* each month's list covers, not
   just a ranked list, so that blind spots are visible.
4. **Duplicates belong to rules, not models.** PayGuard's models missed duplicates, which
   are a matching problem, not an outlier problem. FIRA's T01–T03 rules will implement
   Dubinsky and Warner's fuzzy-matching patterns, and the rules-versus-hybrid comparison
   will be reported per type.
5. **Differentiation from PayGuard, stated plainly.** The hybrid idea itself is not new.
   FIRA differs in setting (small public entities with one or two finance staff), user
   (the independent board reviewer), data standard (AICPA Procure to Pay), evaluation
   (type-aware, at a fixed weekly review capacity) and the realistic "innocent noise" in
   its benchmark (normal self-approvals and legitimate bank changes).

## 3. Sources to keep out of formal work

These were reviewed but are weak as evidence: either the venue has limited quality
control, the setting is unrelated, or the paper is promotional or conceptual. Citing
them in a paper or petition would weaken credibility.

| Source | Reason |
| --- | --- |
| Navandar (2022), "SMART: Security Model Adversarial Risk-based Tool", *IJRAI* | Low-quality venue; keywords do not match content |
| Onyenahazi (2025), *IJARPR* | Low-quality venue; general overview |
| Olasoji et al. (2023), *SHISRRJ* | Low-quality venue; conceptual, no results |
| Brickley and Thakur (2021), *IJCSDF* | Low-quality venue; access-control overview |
| Aladejebi (2017), Walden University DBA study | Nigerian private SMEs; interview study; little relevance |
| Nuswantara, Maulidi and Pujiono (2017), *Management & Marketing* | Indonesian case study; context only |
| Hardiman et al. (1980s), *The CPA Journal* | Historical (Federal Managers' Financial Integrity Act); background only |
| Li, Yen and Wang (2024), *IEEE Access* | Sound venue, but about financial-statement fraud at listed companies, not payment controls; background only |

## 4. Still needed

- Full text of **Hudáková Stasová (2026), "Assessment of the Performance of Control
  Activities in Small Municipalities: Evidence from the Slovak Republic,"** *Croatian and
  Comparative Public Administration* 26(1). Only the table of contents was downloaded.
- Recent U.S. studies (2018 or later) on fraud or control weaknesses in small local
  governments or nonprofits.
- Studies of how non-accountant board members review financial reports.

## References (reviewed)

- Anwar, A., & Akeel, M. O. (2026). Integrating artificial intelligence in audit workflow: Opportunities, architecture, and challenges: A systematic review. *Accounting and Auditing*, 2, 4.
- Barra, R. A. (2010). The impact of internal controls and penalties on fraud. *Journal of Information Systems*, 24(1), 1–21. https://doi.org/10.2308/jis.2010.24.1.1
- Dai, J. (2021). The transformation of government accountability and reporting. *Journal of Emerging Technologies in Accounting*, 18(2), 1–21. https://doi.org/10.2308/jeta-10780
- Das, T. (2026). PayGuard AI: An explainable hybrid framework for corporate payment-anomaly detection and working-capital decision support [Preprint]. Research Square. https://doi.org/10.21203/rs.3.rs-11144714/v1
- Dubinsky, B., & Warner, C. (2008). Uncovering accounts payable fraud using "fuzzy matching logic": Part 1. *Business Credit*, March 2008, 6–9.
- Duan, H. K., Vasarhelyi, M. A., & Codesso, M. (2025). Integrating process mining and machine learning for advanced internal control evaluation in auditing. *Journal of Information Systems*, 39(1), 55–75. https://doi.org/10.2308/ISYS-2022-028
- Gramling, A. A., Hermanson, D. R., Hermanson, H. M., & Ye, Z. (2010). Addressing problems with the segregation of duties in smaller companies. *The CPA Journal*, 80(7), 30–34.
- Gronewald, J., Scherer, M., & Mehdiyev, N. (2026). Machine learning for journal entry testing: A type-aware evaluation of anomaly detectors under a review budget. arXiv:2610.06133.
- Gronewald, J., Stephan, S., Rombach, A., & Fettke, P. (2026). DIB General Ledger Data [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.22014653
- Huefner, R. J. (2011a). Internal control weaknesses in local government: Evidence from town and village audits. *The CPA Journal*, July 2011, 20–27.
- Huefner, R. J. (2011b). Fraud risks in local government: An analysis of audit findings. *Journal of Forensic & Investigative Accounting*, 3(3), 111–125.
- Matkin, D. S. T. (2010). In the shadow of corporate scandal: The use of audit committees in U.S. local governments. *Journal of Public Budgeting, Accounting & Financial Management*, 22(2), 206–226.
- Modlin, S. (2012). County government finance practices: What independent auditors are finding and what makes local government susceptible. *Journal of Public Budgeting, Accounting & Financial Management*, 24(4), 558–578.
- Modlin, S., & Stewart, L. (2014). Local government staff involvement in the external audit process. *Public Administration Quarterly*, Summer 2014, 247–274.
- Singh, K., & Best, P. (2016). Interactive visual analysis of anomalous accounts payable transactions in SAP enterprise systems. *Managerial Auditing Journal*, 31(1), 35–63. https://doi.org/10.1108/MAJ-10-2014-1117

*Page ranges for some items were taken from the PDFs and should be checked before formal citation.*

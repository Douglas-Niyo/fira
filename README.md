# FIRA — Financial Integrity and Risk Analytics

**Status: early research (started October 2026). Nothing here is production software.**

FIRA is an open research project that asks a practical question:

> Can small U.S. local governments and nonprofits, offices where one or two people
> often handle vendors, invoices, payments and reconciliations, use transparent,
> explainable checks on their ordinary ERP exports to catch payment irregularities
> earlier, with an alert workload they can actually review?

## Why this matters

Segregation of duties is a basic internal control, but in a town or nonprofit with a
one- or two-person finance office it is often not possible. FIRA studies automated,
explainable checks that can act as *compensating controls* in that setting.

## Planned scope (version 1)

- Accounts payable and vendor master data only (invoices, payments, vendor changes).
- Transparent control rules, each with a reason code and a control reference.
- Simple unsupervised scoring (e.g., Isolation Forest, peer-group z-scores).
- A ranked review queue in which every alert is explained in plain accounting terms.
- An open benchmark: synthetic data with labeled, injected irregularities, plus the evaluation code.
- Runs locally. No financial data is uploaded anywhere.

## What FIRA is not

- It does not decide whether fraud occurred. It flags items for human review.
- Results on synthetic data do not prove real-world effectiveness.
- It uses no confidential employer, client, donor or government data.

## Research questions

See [docs/research-questions.md](docs/research-questions.md).

## Author

Douglas Niyonsingiza: accountant (government and nonprofit), MS in Information Technology.
ORCID: [0009-0000-1094-9269](https://orcid.org/0009-0000-1094-9269)


## License

Apache License 2.0 (see `LICENSE`).

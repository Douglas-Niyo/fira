# Development notes

Exploratory runs made while building FIRA. These are **not** evaluation results.
The formal evaluation will follow a plan published before it is run, on seeds
not used during development (seed 42 is the development seed).

## 2026-11-01: first rules-only run (rules v0.1, generator v0.1.1, seed 42)

- 239 alerts on about 590 invoices and 590 payments.
- All 15 planted schemes (7 types) had at least one record flagged.
- 192 of the 239 alerts (80%) are R07 "entered and approved by the same person".
  In a two-person office this is routine, so a rules-only list buries the real
  problems. This is the main reason FIRA needs ranking, and a case for reporting
  segregation gaps once as a summary rather than one alert per transaction.
- R05 (payment after bank change) raised 8 alerts, 2 on planted cases; the others
  came from the 4 legitimate bank changes. This is expected; the reviewer's step is a
  phone call to the supplier at a known number.
- The first run (generator v0.1.0) produced 444 alerts, 186 of them weekend entries.
  This exposed an unrealistic generator setting, fixed in v0.1.1.

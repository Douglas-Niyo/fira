# Development comparison | same seed, corrected process

The supplied handover is the old baseline. Its seven input CSVs and five outputs were reproduced before changes. The new column uses regenerated seed 42 and twelve independent month-end snapshots. It is one enriched synthetic example, not a formal benchmark or a human usability study.

| Measure | Handover | 0.2.0 |
| --- | ---: | ---: |
| Raw alerts | 239 | 238 |
| Review items + self-approval summaries | 28 + 19 | 28 + 19 |
| Top-level displayed lines | 47 | 47 |
| Fewer displayed lines than raw alerts | 80.33% | 80.25% |
| Planted schemes with a primary record in dated review items | 13 of 15 | 15 of 15 |
| Dated monthly item for each overpayment | 0 of 2 | 2 of 2 |
| Payments dated before their invoice was entered | 7 | 0 |

The old year-end fallback could pay late-entered invoices on June 30. The new generator lets settlement take place at the next meeting: 19 generated payments settle after the window. The net raw-alert difference is one fewer R07 self-approval; other rule counts happen to agree. The previous monthly calendar omitted empty item months and the two undated overpayments. In the new calendar the maximum is six displayed lines, including summaries. All 15 planted schemes are represented at a ten-line budget in this example; the example cannot establish superior ranking at ten because the budget never binds.

Columbia Office Supply first crosses the threshold in November 2025; Evergreen Power crosses in May 2026. Both can now be checked in the month observed. Adding later transactions must not rewrite an earlier pack. The regression suite compares September output both with and without later records.

A separate development example with one invoice spread across two purchase orders previously triggered a self-duplicate. The corrected input contract checks the declared layout; an explicit allocation mapping can combine allocated rows while retaining their source lines. Ambiguous totals are unsupported. Current tests do not establish performance across real ERP exports.

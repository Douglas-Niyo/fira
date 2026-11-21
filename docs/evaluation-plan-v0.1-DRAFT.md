# FIRA evaluation plan, v0.1 — DRAFT, not yet frozen (November 20, 2026)

> **Status: draft for author approval.** This plan becomes binding when it is committed
> to the public repository with the heading changed to "FROZEN" and the date of freezing.
> Any later change will be listed under "Deviations" with the reason. No evaluation seed
> may be run before freezing.

## 1. Question

**RQ1.** For a small U.S. local government, does a hybrid ranking (transparent rules
plus simple anomaly scoring) put more *kinds* of payment irregularity in front of an
independent reviewer than rules alone, when the reviewer can only look at a fixed
number of items each month?

## 2. Hypotheses

- **H1 (main).** At the primary review budget, the hybrid ranking has higher fair-share
  type recall (FSR@k) than the rules-only ranking.
- **H2.** At the primary review budget, the hybrid ranking covers more irregularity types
  (type coverage) than the rules-only ranking.
- **H3 (workload).** Reporting self-approval as a monthly summary (review pack) instead
  of one alert per transaction cuts the number of items a reviewer must read by at least
  70%, while still listing at least one record from every planted scheme.

A result against a hypothesis will be reported as fully as a result for it.

## 3. Data

- Generator: `fira/generator.py`, version frozen at the commit that freezes this plan.
- **Development seed (already used):** 42. Results on seed 42 are exploratory and are
  excluded from the evaluation.
- **Evaluation seeds:** 1001 to 1030 (30 synthetic entity-years), not run before freezing.
- **Entity sizes:** small (about 600 invoices a year), medium (about 3,000), large
  (about 12,000).
- **Prevalence:** share of payments belonging to planted schemes: 0.5% (primary),
  0.1% and 1% (sensitivity).
- *Before freezing:* the generator needs size and prevalence settings, which it does not
  have yet (see Section 9).

## 4. Unit of analysis

A **scheme** is one planted irregularity, which may involve several records (for
example, a fictitious supplier, its invoices and its payments). A scheme counts as
**found** when any of its records appears in a review item within the budget.
Record-level results are reported as secondary.

## 5. Review budget

A small-town board member reviews monthly. The budget *k* is the number of review items
read per month:

- **Primary: k = 10 items per month** (about one hour of review).
- Sensitivity: k = 5 and k = 20.
- Self-approval summary lines (H3) are counted separately and do not use up *k*.

## 6. Methods compared

| ID | Method | How items are ordered |
| --- | --- | --- |
| B0 | ERP-style exact duplicate check | R01 only, by amount |
| B1 | Rules only (review pack) | Douglas's tiers (Tier 1, then Tier 2), then amount; context flags attached, not ranked |
| B2 | Model only | Anomaly score from Isolation Forest and HBOS on payment features, highest first |
| B3 | Hybrid | Tier first; within a tier, by anomaly score; items scoring very high with no rule hit enter after Tier 2 |

The anomaly features and model settings for B2 and B3 will be fixed in a short appendix
before freezing. No settings may be tuned on evaluation seeds.

## 7. Measures

| Measure | Meaning for the reviewer |
| --- | --- |
| **FSR@k (primary)** | Fair-share type recall (Gronewald, Scherer & Mehdiyev, 2026): each type's credit is capped at its share of the budget, so one flood of a single type cannot hide missed types. *Exact formula to be checked against Section 3.2 of the paper before freezing.* |
| Type coverage@k | How many of the planted types appear at least once |
| Per-type recall@k | Share of schemes of each type found |
| Scheme recall@k | Share of all schemes found |
| Precision@k | Share of review items that involve a planted scheme |
| First-hit rank | Position of the first item for each type |
| Dollars found@k | Planted dollars appearing within the budget |
| Items per month | Workload (H3) |

## 8. Analysis

- Each measure is computed per seed, size and prevalence, then averaged over the
  30 seeds with a 95% bootstrap confidence interval.
- **H1 is supported** if the mean paired difference in FSR@10 (B3 minus B1) at 0.5%
  prevalence is above zero and its 95% interval excludes zero; a Wilcoxon signed-rank
  test on the 30 paired seeds is reported as well.
- H2 uses the same rule for type coverage@10.
- H3 is supported if items read fall by at least 70% from raw alerts to the review pack
  and every scheme still has a record in the pack, on all 30 seeds.
- All runs are made from one command and the outputs committed to the repository.

## 9. To do before freezing

1. Add size and prevalence settings to the generator; add tests.
2. Confirm the FSR@k formula against the paper (Douglas, Day 5 reading).
3. Fix B2/B3 features and settings in an appendix.
4. Douglas approves the plan; it is committed with "FROZEN" and the date.

## 10. Limits stated in advance

- Synthetic data: the result shows how well each method finds *these planted patterns*,
  not real fraud.
- The tiers come from one practitioner's judgment and may not suit every entity.
- The planted types and the rules were designed by the same team, which favors rules.
  This bias works *against* H1, so a positive result is more convincing than a negative
  one is damning.

## Credits

Review priorities, alert wording and the self-approval summary design come from
Douglas Niyonsingiza's practitioner review of the development alerts (November 20, 2026).

## Deviations

*None yet.*

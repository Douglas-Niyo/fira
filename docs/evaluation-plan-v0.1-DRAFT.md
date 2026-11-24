> Historical plan v0.3. See evaluation-v0.4.md for current implementation and decisions awaiting sign-off. Historical counts below are not results for this release.

# FIRA evaluation plan, v0.3 — DRAFT, not yet frozen (November 21, 2026)

> **Status: draft.** The plan becomes binding when it is committed with the heading
> changed to "FROZEN" and the date. Any later change will be listed under "Deviations"
> with the reason. No evaluation seed may be run before freezing.

## 0. What this evaluation can and cannot show

This is a test on synthetic data. It can show how well each method surfaces *the planted
patterns* under a fixed review budget. It cannot show performance on real fraud,
usability for a board member, or effectiveness in a real organization. Those need the
separate reviewer study (`docs/review-protocol-v0.1.md`) and, later, authorized pilots.

FIRA's value does not depend on machine learning helping. If the hybrid adds little over
clear rules and a well-designed review pack, that result will be reported as plainly as a
positive one.

## 1. Question

**RQ1.** For a small U.S. local government, does a hybrid ranking (transparent rules
plus simple anomaly scoring) put more *kinds* of payment irregularity in front of an
independent reviewer than rules alone, when the reviewer can only look at a fixed
number of items each month?

## 2. Hypotheses

- **H1.** Where the monthly budget is binding (Section 5), the hybrid ranking (B3) has
  higher fair-share type recall (FSR) than the rules-only review pack (B1).
- **H2.** Under the same conditions, B3 has higher type coverage than B1.
- **H3 (reading load).** The review pack needs at least 70% fewer lines to read than the
  raw alert list, counting review items **and** self-approval summary lines, while
  (a) every planted scheme still has a record in the pack and (b) every flagged record
  stays reachable. Line counts are not review time; time is measured in the reviewer study.

## 3. Data

### 3.1 Units and denominators

- In the generator, each normal invoice is paid by one payment, so invoices and payments
  are close to one-to-one. Planted schemes can add payments without an invoice, or a
  second payment for one invoice. Every result reports **both** invoice and payment counts.
- **Prevalence** is the share of *payments* that belong to a planted scheme. It is a
  testing assumption, not a claim about real fraud rates.

| Size | Invoices a year (about) | Payments a year (about) | Expected affected payments at 0.1% / 0.5% / 1% |
| --- | --- | --- | --- |
| Small | 600 (50 a month) | 600 | 0.6 / 3 / 6 |
| Medium | 3,000 (250 a month) | 3,000 | 3 / 15 / 30 |
| Large | 12,000 (1,000 a month) | 12,000 | 12 / 60 / 120 |

### 3.2 Two families of experiments, kept apart

**A. Realistic-prevalence experiments.** The number of planted schemes in a year is drawn
at random so that, on average, the stated share of payments is affected. Types are drawn
at random. Years with **no** planted scheme are allowed and kept, because a small entity
at 0.1% or 0.5% will often have a clean year. Primary prevalence: 0.5%; sensitivity: 0.1% and 1%.

**B. Enriched type-coverage tests.** Every year contains at least one scheme of every type,
so methods can be compared across all types. These runs are **labeled "enriched"**, their
actual prevalence is reported, and they are never described as realistic.

### 3.3 Seeds

- Development seed (already used): 42. Excluded.
- Seeds by family and size, fixed at freezing. Planned: realistic, small 100 runs per
  prevalence level; medium and large 30 each; enriched, 30 runs per size.
- **Unfamiliar variations.** Besides new seeds, the evaluation includes variants of each
  type not used during development (for example, other invoice-number formats, splits
  spread over 10 to 14 days, bank changes made during business hours by the main clerk).
  The variants are written down at freezing.

## 4. Unit of analysis

A **scheme** is one planted irregularity, which may involve several records. A scheme
counts as **found** when any of its records appears in a review item within the budget.
Record-level results are secondary.

## 5. Review budget

- The budget *k* is the number of review items read per month: **10 primary**, 5 and 20 as
  variations. The reviewed set for a year is the union of each month's top *k* items.
- These are **initial reviews**, not full investigations. Ten initial reviews and ten
  investigations are different workloads.
- **Budget pressure is reported for every run:** candidate items per month and the share
  of months in which candidates exceed *k*. Where the budget is never exceeded, every
  method shows the reviewer the same items and the comparison is uninformative; those
  cells are reported as "no ranking pressure", not as evidence for or against H1.
- H1 and H2 are tested in the enriched family and in the realistic cells where candidates
  exceed *k* in at least 25% of months. Which cells qualify is reported before results.

## 6. Methods compared

| ID | Method | How items are ordered |
| --- | --- | --- |
| B0 | ERP-style exact duplicate check | R01 only, by amount |
| B1 | Rules only (review pack) | Tier 1, then Tier 2, then amount |
| B2 | Model only | Anomaly score (Isolation Forest and HBOS on payment features), highest first |
| B3 | Hybrid | Tier first; within a tier, anomaly score; very high scores with no rule hit enter after Tier 2 |

**Same presentation for all methods.** B1, B2 and B3 use the same grouping rules, the same
supporting information and the same review format. Only the **order** differs, and any
extra item a model adds counts against the same budget. Gains can then come only from
ranking, not from summarizing or presentation.

**Fixed before freezing:** features, model settings, ranking logic, tie handling
(amount, then date, then ID) and every measurement rule. No setting is tuned on
evaluation seeds.

**No leakage:**
- Models never see labels, record IDs, invoice or check numbers as numbers, or anything
  derived from them.
- Generator v0.1.2 assigns IDs and check numbers so that they do not reveal planted records.
- Scoring respects time: items for month *m* are scored using data up to the end of month
  *m* only.

## 7. Measures

The type-aware measures below are an **existing method** published by Gronewald, Scherer
and Mehdiyev (2026, arXiv preprint; also listed by DFKI). FIRA applies them to its own
setting, with schemes as the unit. For one year: *T* is the set of types with at least one
planted scheme in that run; *n_t* is the number of schemes of type *t*; *f_t* is the number
found within the reviewed set; *K = 12k*.

| Measure | Definition |
| --- | --- |
| **FSR (primary)** | Caps by water-filling: *c_t = min(n_t, s\*)*, where *s\** is the smallest level for which the caps sum to *min(K, Σ n_t)*. *FSR = Σ_t w_t · min(f_t, c_t) / c_t*, equal weights *w_t = 1/|T|* |
| Type coverage | Types in *T* with *f_t ≥ 1*, divided by *|T|* |
| Per-type recall | *f_t / n_t*, pooled over runs |
| Scheme recall | *Σ f_t / Σ n_t* |
| Precision | Share of reviewed items that involve a planted scheme |
| First-hit month | Month in which each type first appears |
| Dollars found | Planted dollars within the reviewed set |
| Reading load (H3) | Raw alert lines versus review items plus summary lines |
| Clean-year load | In years with no planted scheme: items shown to the reviewer |

- **Absent types:** types with no planted scheme in a run are left out of *T* for that run.
- **Clean years:** FSR and type coverage are undefined when no scheme is planted. Such years
  are excluded from those averages; their number and their clean-year load are reported.
- **Estimand:** FSR and type coverage are computed per run, then averaged (Gronewald et al.,
  2026, Section 3.5).
- **Weights:** equal weights are primary. Sensitivity: Tier 1 types weighted twice.

## 8. Analysis

- Measures are averaged within each family, size and prevalence, with 95% bootstrap
  confidence intervals over runs.
- **H1 is supported** if, in qualifying cells (Section 5), the mean paired difference in FSR
  (B3 minus B1) at k = 10 is above zero and its 95% interval excludes zero. A Wilcoxon
  signed-rank test on paired runs is reported as well. H2 uses the same rule for type coverage.
- **H3** is supported if the pack needs at least 70% fewer lines than the raw list on every
  run, with (a) and (b) in Section 2 met. On the development seed the figure is 80.3%
  (47 lines from 239), or 88.3% counting review items only; the evaluation reports the
  first figure as primary.
- All runs come from one command, and outputs are committed to the repository.

## 9. To do before freezing

1. Generator: realistic-prevalence sampling (clean years allowed), enriched mode, three
   sizes, held-out variants; tests for each.
2. B2/B3 features and settings fixed in an appendix; time-respecting scoring.
3. Final list of qualifying cells and seeds.
4. Author approves; committed as "FROZEN" with the date.

## 10. Limits stated in advance

- Synthetic data and planted patterns; prevalence levels are assumptions.
- No review time, understanding or real-world effectiveness measured here.
- One set of tier priorities; other entities may rank differently.
- The planted types and the rules were designed by the same team, which favors rules (B1).

## Decisions

Decisions in this plan were reviewed and approved by the author, Douglas Niyonsingiza
(November 20–21, 2026).

## References

Gronewald, J., Scherer, M., & Mehdiyev, N. (2026). Machine learning for journal entry
testing: A type-aware evaluation of anomaly detectors under a review budget [Preprint].
arXiv:2610.06133.

## Deviations

*None yet.*

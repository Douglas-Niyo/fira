# Development review: where the ten slots went

**Question:** Did the large development year miss duplicates because they never entered the pack, or because they were ranked too low? All twelve planted duplicate schemes were already represented in the full actionable pack. The failure was selection. The pack still omitted one of four split-purchase schemes; ranking cannot recover it.

**Reproduction:** Parent 3498aa0, same generator, rules, development seeds and monthly packs. Compare archived v0.4 scale-12000.csv with seed-11.csv here, selecting k=10. Pool months July 2025–June 2026. The test measures grouped review items; scheme counts are not counts of monthly queue slots. These are known development inputs.

| Policy | Schemes / 44 | Exact / 8 | Near / 4 | Unsupported / 11 | Split / 4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Archived B1, summaries between tiers | 30 | 0 | 0 | 11 | 2 |
| B1, summaries last, amount within tier | 32 | 1 | 0 | 11 | 3 |
| B3_min, four-feature hybrid, summaries last | 33 | 2 | 0 | 11 | 3 |
| B3, six-feature hybrid, summaries last | 33 | 2 | 0 | 11 | 3 |
| B4, rules only, spread slots across families | 41 | 8 | 4 | 10 | 2 |

In all twelve months the total candidate list exceeded ten. In **zero** months did grouped Tier 1 items alone reach ten. B1 used 43 of 120 slots on Tier 1 and 77 on Tier 2; moving the summaries alone still left 11 duplicates unselected. B4 used 42 Tier 1 and 78 Tier 2 slots but changed which families got reviewed. Its duplicate coverage came with one fewer unsupported-payment scheme and one fewer split than revised B1. This is a decision about risk coverage, not a uniform improvement.

All 24 monthly user summaries in the large year remained accessible in the full pack, but none received one of the ten slots under the revised B1–B4 policies. Do not report these summaries as reviewed. For deployment, a board wanting mandatory segregation oversight should explicitly assign time and responsibility; a future one-slot reservation would displace actionable items and should be evaluated under the same total cap.

In the medium stress year, revised B1, B2, B3, B3_min and B4 each surfaced the same 15 of 17 schemes at ten slots. The other two did not appear in the full actionable pack. In the large year, the extra supplier features did not change aggregate scheme recall or type-aware recall versus B3_min at ten. This does not imply identical item ordering or a general null effect. New features are retained as a specified comparison, not a proven performance improvement.

No bank-alert false-positive rate is inferred from the number of planted bank-change schemes. No rule or disclosed stress variant was widened or relabeled as unseen. The primary held-out comparison remains B3 versus B1; B4 and feature comparisons are secondary. No held-out years, outside users or real payment data are part of these results.


## November 25 severity and workload check

Large stress development year (seed 11), ten slots per month. The denominator for Tier 1 is the number of distinct planted Tier 1 schemes in scope. The weighted score averages capped credit by type, so it can rise even when a high-priority scheme is missed.

| Method | All schemes found / present | Tier 1 schemes found / present | Equal-weight FSR | Tier-weighted FSR | User summaries deferred |
| --- | ---: | ---: | ---: | ---: | ---: |
| B1 | 32 / 44 | 28 / 28 | 0.6964 | 0.8068 | 24 / 24 |
| B3 | 33 / 44 | 28 / 28 | 0.7143 | 0.8182 | 24 / 24 |
| B4 | 41 / 44 | 27 / 28 | 0.9156 | 0.9380 | 24 / 24 |

No independent sign-offs are simulated. The operating protocol assigns deferred summaries outside the ten slots. In these outputs, “read” means selected for display.

**Development verification.** The four known years produced 72 method/budget rows. All prior output values matched the earlier development CSV after decoding JSON dictionaries. Python 3.12.14, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0 and scikit-learn 1.8.0. A second process ran the enriched seed 42 case with PYTHONHASHSEED=887; the two seed-42.csv files had the same SHA-256: `f26c6a04095bb2ec059d65827691996b6a59cfc25748bce72c65940aa9124e9c`. This check applies to this environment and file only.

# DRAFT — evaluation protocol v0.5 for author review

Draft following inspection of disclosed development results. No formal evaluation cases have been run. This is a pre-freeze amendment, not an already registered protocol. Record author review and publish the freeze commit before the held-out seed run.

## Study design

| Decision | Specification |
| --- | --- |
| Unit and window | One generated government fiscal year, July 2025–June 2026. Count each scheme once if any labeled source record is observable by year end. Post-period settlements stay in source data. Standing issues first observable at opening enter the first snapshot. |
| Scale | About 600, 3,000 or 12,000 invoices; 60 regular suppliers. Vary transaction density, not staffing or procurement structure. At high volume the generator may add a retired supplier for the inactive-payment injection. |
| Realistic years | Target prevalence of 0.1%, 0.5% or 1%. For each prevalence, generate 100 small, 30 medium and 30 large years. Retain clean years. Report observed invoice and payment counts, planted scheme counts, and realized prevalence: distinct affected in-period payments divided by in-period payments. The target is a simulation parameter, not a real fraud rate. |
| Counts | Independent Poisson scheme counts per type. Expected count = target payments × target prevalence / (7 × expected affected payments per scheme). Working sizes in type order T01/T02/T04/T05/T06/T09/T15: 1/1/1/1/7.5/2.5/1. Overlap, year-end cutoffs and varying scheme sizes affect realized rates. |
| Enriched years | 30 per size with one of each type; report separately. Total across both designs: 570 paired years. |
| Seeds and stress | Start at 700001 in `jobs()` order. Exclude development seeds 0, 1, 2, 3, 4, 7, 8, 11 and 42. Alternate stress within cells: prefix/suffix reformatting, 12-day split spans, daytime clerk bank changes. Other types retain ordinary variation. These are disclosed stress patterns. |

## What counts toward ten

The benchmark selects up to ten lines each month (sensitivity: five and twenty). Empty months count. Shared-candidate methods rank actionable items first. A selected monthly summary for one user costs one slot and earns no scheme credit; none is reserved. Report available, selected and deferred summaries. A selected line measures exposure, not completion of a control.

In actual use, assign every deferred summary to a reviewer independent of those transactions. Record completion, time and follow-up outside the ten slots; if nobody can review it, carry it as outstanding. Do not add that work or its findings to benchmark detections. The [operating protocol](review-protocol-v0.1.md) defines the sign-off and separate time record.

## Ranking methods

| Method | How the next actionable item is chosen | What it tests |
| --- | --- | --- |
| B0 | Exact-duplicate flagged items only; credit only those exact records. | Narrow baseline. |
| B1 | Tier first; largest amount within tier. | Rules-only reference. |
| B2 | Six-feature model score, without tier priority. | Score ordering on rule-generated items. |
| B3 | Tier first; six-feature model score within tier. | Hybrid ranking; primary comparison with B1. |
| B3_min | Tier first; original four-feature score within tier; same summaries policy. | Contribution of the two supplier features. |
| B4 | Select the least-represented available rule family each slot. Break equal counts by the best remaining item: tier, largest amount, then ID. Reset monthly. | Whether diversity improves coverage at a cost to high-priority items. |

B1 through B4, including B3_min, share candidates. No method adds model-only candidates. No labels enter ranking. For B4, assign each group to the **first** matching family: unsupported (R15), overpayment (R04), bank change (R05), supplier control (R06), duplicate (R01–03), split (R09), approval (R08), supplier record (R10–11). The first slot goes to the highest-priority item; later slots may displace Tier 1. Further ties use amount descending then stable destination ID ascending. Summary amounts are invoice plus payment activity, not losses.

## Model specification

Features: log(1+payment amount), weekday, same entering/approving user, ACH indicator. B2/B3 additionally use (i) log(1+amount) minus log(1+supplier median amount) and (ii) payment-method rarity, 1−(previous same-method count+1)/(previous payment count+1). Use only prior completed months relative to each row, including training rows. Below three prior supplier payments set both features to zero. The rarity statistic is a descriptive index, not a calibrated probability. These features may describe unusual transfers but cannot establish bank redirection; ordinary-amount duplicates may have no unusual model score. Fit to earlier months only. At least 20 historical payments required; otherwise scores are zero. Isolation Forest: 64 trees, up to 256 observations, fixed seed 117. HBOS: ten equal-width bins per feature, add-one smoothing, clamp outside observations to end bins. Average both empirical score percentiles against training samples. For an item take the maximum score among its primary current payments or current payments applied to its primary invoices by month end; absent scores are zero. No labels, record numbers or transaction identifiers used as numeric features.
## Outcomes and interpretation

| Status | Comparison or measure | Decision rule |
| --- | --- | --- |
| Sole primary | B3 minus B1, equal-weight FSR, 10 slots, 12,000 invoices, 0.5% prevalence. | Evaluate only if at least 25% of months across all runs in that cell exceed ten candidates. On eligible nonclean years take paired yearly differences; 95% percentile bootstrap, 2,000 draws, seed 2301. A positive lower bound favors B3. Report insufficient pressure or an interval including zero; do not substitute another test. |
| Secondary, descriptive | B4 minus B1 (queue design), B3 minus B4 (hybrid vs. family diversity), B3 minus B3_min (supplier features). | Report paired differences at ten slots. Always show B4's results, including any displaced Tier 1 schemes. No second primary test. |
| Severity sensitivity, descriptive | Tier-weighted FSR uses the same caps and detections as primary FSR. | Double Tier 1 type weights, normalize over types present, and report raw Tier 1 schemes found / present beside the score. Weights affect reporting only. |
| Supporting measures | Scheme recall, type coverage, tier counts, summary deferral, per-type recall, distinct selected labeled payment dollars. | Aggregate per-year rates after computing them. Linked dollars are neither total scheme value nor losses prevented. Other cells, budgets, stress subgroups, type counts and signed-rank tests are descriptive. |

**Scoring.** Credit each distinct scheme ID once if its primary record occurs in a selected nonsummary item. Blanket context links earn no credit; a grouped item can surface multiple schemes. For each type present, cap its count at the common water-filling level so the caps sum to the smaller of 12 × monthly budget and total schemes. Type credit is found count (limited to its cap) divided by that cap. Equal-weight FSR is the mean credit over types present. For the sensitivity, multiply each type credit by its fixed weight below, sum, and divide by the sum of weights for present types. Classify by the planted scheme type, even if a different alert surfaced it. Clean years have undefined FSR (both versions), recall and type coverage; report load and 0 found / 0 present, not a zero detection rate.

| Severity | Planted types | Descriptive weight per present type |
| --- | --- | ---: |
| Tier 1 | T04 overpayment; T05 bank redirection; T06 fictitious supplier; T15 inactive/unsupported payment | 2 |
| Tier 2 | T01 exact duplicate; T02 near duplicate; T09 split purchase | 1 |

`tier1_schemes_found` and `tier1_schemes_present` count distinct schemes. `tier1_read` counts selected review items; these units are different.

## H3: reduction in lines

Requirement: for every nonempty raw alert year, require >=70% fewer top-level lines AND representation of all observable planted schemes in nonsummary items AND traceability from all emitted alerts; retain and report even a single alert with no compression. Zero-alert years have undefined percentage; separately report load, retention failures and count. Line counts do not estimate time. Runtime source-link validation and release regression tests supplement the benchmark’s coverage indicator.
## Reproduction and freeze

Retain all run rows and failed runs; do not reroll a failing seed. Archive the tagged source, exact environment, outputs and deviations. Sort JSON dictionary keys for stable serialization. Check repeat-run file hashes under recorded versions; do not assume byte equality across versions. There are no multiple-cell confirmatory claims. Identical-format reviewer materials and independent reproduction are separate evidence. No nonprofit effectiveness or adoption claim follows from this generator.

Freeze sequence: review this exact draft and code, resolve changes, then change the heading to “# FROZEN” followed by date and version, commit the tracked code and protocol, tag that commit FIRA-eval-freeze and publish it before running the held-out grid. Commands are in README. Any subsequent change needs a dated deviation and separate release.

Source for the adapted FSR metric: Gronewald, Scherer and Mehdiyev (2026), Machine Learning for Journal Entry Testing: A Type-Aware Evaluation of Anomaly Detectors under a Review Budget, arXiv:2610.06133, §§3.2, 3.5. The grouped-scheme adaptation and monthly review assumptions are FIRA design choices.

## Pre-freeze change record | 2026-11-24
These changes were motivated by known development outcomes, especially seed 11. No detection windows, generator distributions, labels, candidate-generation rules or disclosed stress variants were changed. The seven-day split rule still faces 12-day spans. New seeds test replication under known patterns, not unseen mechanisms. If a rule is changed in response, retain these cases as regression tests, document the trigger and before/after results, and have an independent reviewer design and privately seal a fresh challenge set before freezing. Record its hash, authorship and unblinding date. No such independently sealed set exists in this release. A null primary result is reportable.

## Pre-freeze change record | 2026-11-25

Retained one primary contrast; restored the original 2:1 severity sensitivity with explicit type mapping and raw Tier 1 counts. Clarified responsibility for deferred summaries and sorted benchmark JSON keys. The ten-slot accounting, ranking, generator, model, formal seeds and H3 criteria are unchanged. This document remains a draft.

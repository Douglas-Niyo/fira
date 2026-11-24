# Development checks and unfavorable findings
These are four known development years, not independent evaluation. Neither the primary hypothesis nor a filing claim can be evaluated from these examples.

| Example | In-period invoices | Schemes | Raw / displayed lines | All schemes in full nonsummary items? | Months over 10 |
| --- | ---: | ---: | ---: | --- | ---: |
| Small enriched, seed 42 (one per type) | 572 | 7 | 209 / 36 | Yes | 0/12 |
| Small low prevalence, seed 7 | 564 | 0 | 118 / 22 | No schemes present | 0/12 |
| Medium stress, seed 8 | 2,753 | 17 | 837 / 98 | **No** | 1/12 |
| Large stress, seed 11 | 10,976 | 44 | 3,827 / 294 | **No** | 12/12 |

All four examples retain trace destinations for the alerts that were emitted. Alert traceability does not mean that the rules recognized every planted scheme. The full pack missed at least one observable scheme in each larger stress example, before pruning to ten items. Less reading did not guarantee full detection, so the combined H3 criterion failed in these two development runs. Under the ten-line budget the large rules-only ranking surfaced 30 of 44 schemes and the hybrid surfaced 32 of 44; this one development year cannot establish superiority.

The 15-scheme handover demonstration is a different configuration even though it also uses seed 42. The 7-scheme enriched check here is the benchmark's one-per-type configuration.

To reproduce the scale checks in addition to the two default smoke runs, from the source root:
```python
from fira.benchmark import one
import pandas as pd
for seed, size in [(8,3000),(11,12000)]:
    pd.DataFrame(one(seed,size,.005,False,True)).to_csv(f"scale-{size}.csv", index=False)
```

# FIRA | monthly payment review
Development release 0.2.0 • synthetic accounts payable • Douglas Niyonsingiza

FIRA gives an independent reviewer at a small local government a short monthly list of payments and invoices to check, with explanations and access to supporting records. The reviewer investigates and documents the outcome. A flag is not a finding of wrongdoing. Nonprofit recipients of federal funds are a second intended population; this release does not establish that the method works for them.

**Start with [the before-and-after example](examples/BEFORE-AFTER.md), then [the November pack](examples/November-review.md).** Source data are entirely synthetic. No institutional affiliation or endorsement is implied.

## Reproduce locally
Tested with Python 3.12.14. From this folder (macOS/Linux):
```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
python -m fira.generator --seed 42 --out reproduced/data
python -m fira.review --data reproduced/data --out reproduced/pack
python -m fira.benchmark --out reproduced/benchmark-development
```
Choose a new output folder for each benchmark. Development mode exercises two configurations; its enriched seed 42 plants one of each type and is distinct from the 15-scheme example. Running the generator and review commands with the default configuration reproduces the demonstration. Compare CSV outputs; the data-card creation timestamp is intentionally variable.

## Files
- `examples/corrected/`: all twelve months, raw alerts, summary and detail rows, record links and an invoice-source-row map. Context-only alerts remain searchable even when they do not receive a top-level line.
- `docs/schema-v0.1.md`: current supported subset and limitations (legacy filename). No production imports or real confidential records.
- `docs/evaluation-v0.4.md`: current protocol awaiting author approval. The older draft is historical.
- `examples/development-benchmark/`: development-only results, never evidence from a frozen experiment.
- `docs/review-protocol-v0.1.md`: independent reviewer duties and the proposed human study.

## Formal benchmark (after public protocol freeze only)
Publish the reviewed freeze commit and tag per the protocol. In a clean checkout of that tag, use `python -m fira.benchmark --formal --out ../FIRA-formal-results`. Keep output outside the source tree. The runner checks the local tag and tracked files; it cannot verify that the protocol was published. Preserve partial outputs and report failures. Do not replace development evidence with claims of measured time saved, avoided losses or verified real-world detection.

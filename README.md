# Rakshasutra | SurakshaNet

**Research engineering workspace for Rakshasutra (SurakshaNet), a proposed cognitive-assistive wearable and BLE-to-LoRaWAN pilgrim-safety network.** The current reading copy contains the author's supplied 10-page PDF followed by a repository-prepared, one-page arithmetic erratum. The untouched source PDF is archived alongside it.

> **Evidence status:** The manuscript presents an architecture and analytical estimates. No raw field dataset, hardware logs, deployment record, or experimental protocol was supplied. Table 5's collision-loss entries are recomputed in the erratum from its displayed offered-load values. All numbers remain analytical claims, not field results. The traffic-event simulation and several non-Table-5 audit outputs are separate illustrative or historical analyses; none validates the proposed deployment.

![Concept architecture](figures/concept_architecture.svg)

**Start here:** [corrected reading copy](paper/rakshasutra_open.pdf) · [untouched author-supplied PDF](paper/rakshasutra_double_column_tables_fixed_source.pdf) · [erratum details](docs/errata.md) · [version and evidence notes](docs/version-notes.md) · [reproduction guide](docs/reproduction.md) · [generated results](results/)

## What this project contains

- `paper/rakshasutra_open.pdf` — 11-page reading copy: the supplied 10-page PDF plus a clearly labeled repository-prepared erratum; its SHA-256 is recorded in `paper/SHA256SUMS.txt`.
- `paper/rakshasutra_double_column_tables_fixed_source.pdf` — byte-for-byte copy of the supplied 10-page source PDF.
- `simulation/audit.py` — standard-library Python calculations for LoRa airtime, pure-ALOHA collision probability, Bloom-filter false positives, BLE single-hit capture assumptions, pseudonym collision probability, and idealized battery arithmetic.
- `simulation/traffic_simulation.py` — a fixed-seed, explicitly synthetic single-cell Poisson traffic comparison.
- `configs/traffic_scenario.json` — its editable scenario inputs and all traffic-model assumptions.
- `configs/claims.json` — Table 5 offered-load inputs from the supplied manuscript and selected other claims; derived loss values are regenerated from the displayed G values.
- `results/` — generated CSV tables from the audit script.
- `figures/` — generated SVG plots and a conceptual system diagram.
- `docs/claim-audit.md` — historical audit notes for claims that are outside the Table 5 correction; its scope limits remain in force.
- `docs/reproduction.md` — exact commands and model definitions for the included historical/synthetic calculations.
- `docs/errata.md` — the Table 5/Table 8 arithmetic correction and derivation.

## Quick start

Requires Python 3.10 or later; the audit uses only the Python standard library.

```bash
python simulation/audit.py
python simulation/traffic_simulation.py
```

The first command rewrites arithmetic-check CSVs in `results/` and analytical SVGs in `figures/`, including the corrected Table 5 loss pairs. The second writes the fixed-seed illustrative traffic CSV and figure. Neither simulates a validated shrine deployment: one is deterministic arithmetic and the other uses only the explicit synthetic workload in `configs/traffic_scenario.json`. To rebuild the reading-copy PDF, install `pypdf` and `reportlab`, then run `python simulation/build_erratum_pdf.py`.

## Headline checks

- Revised Table 5 losses are recomputed as `1 - exp(-2G)` from the displayed offered loads. At 3,000 tags, 60-pole explicit departures (`G=17.11%`) yield 28.98%; implicit departures (`G=11.98%`) yield 21.31%; the 40-pole fiber-offload case (`G=7.99%`) yields 14.77%.
- Table 8's 15.8% / 8.6% pair is a stale value from an earlier draft. The appended erratum names the corrected cases and values.
- Other airtime, battery, Bloom-filter, pseudonym, and BLE calculations in `results/` are arithmetic or assumptions-based checks. Consult the historical claim audit for their version limits; none are field validation.
- The separate synthetic workload uses the assumptions in `configs/traffic_scenario.json`; it is not calibrated to the manuscript and is not a deployment estimate.

![Illustrative traffic simulation](figures/traffic_simulation.svg)

In this synthetic workload, periodic batch flushes cluster the transmissions. The event simulation therefore produces a much higher loss than the pure-ALOHA estimate from mean offered load alone. This is a schedule-sensitivity warning under the stated assumptions, not evidence of actual shrine-network performance.

See the audit notes before quoting any number from this repository.

## Safety, privacy, and intended use

This is a research prototype and calculation set. It is not a validated child-tracking product, medical device, emergency-response system, or safety-certified design. Do not deploy it for real-world safeguarding without institutional review, privacy/legal review, security testing, RF and battery testing, and operational trials. The uploaded source contains implementation proposals that need independent technical and regulatory review.

## Citation

Jha, Raj. *Rakshasutra (SurakshaNet): A Zero-UI Cognitive-Assistive Wearable and Edge-Filtered BLE–LoRaWAN Architecture for Spatial Disorientation and Crowd Localization in Cellular-Denied Mountain Pilgrimages*. Author-supplied revised manuscript, October 2026, 10 pages. Repository reading copy adds a clearly labeled one-page arithmetic erratum; the untouched 10-page source is preserved separately. The correction checks arithmetic only and does not certify the manuscript's analytical model or performance.

No license is included. All rights in the manuscript remain with its author unless a license is added explicitly.

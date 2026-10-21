# Rakshasutra | SurakshaNet

**Research engineering workspace for Rakshasutra (SurakshaNet), a proposed cognitive-assistive wearable and BLE-to-LoRaWAN pilgrim-safety network.** The current paper is the author's revised, 10-page, double-column-table-fixed PDF supplied on 21 October 2026. It supersedes the earlier nine-page PDF in this repository.

> **Evidence status:** The manuscript presents an architecture and analytical estimates. No raw field dataset, hardware logs, deployment record, or experimental protocol was supplied with the revised PDF. Its numbers are *author-reported analytical claims*, not independent field results. The repository's existing audit/configuration/results were prepared for the earlier nine-page manuscript; they are retained for provenance but are not a complete audit or validation of the revised version.

![Concept architecture](figures/concept_architecture.svg)

**Start here:** [current supplied paper](paper/rakshasutra_open.pdf) · [version and evidence notes](docs/version-notes.md) · [historical claim audit](docs/claim-audit.md) · [reproduction guide](docs/reproduction.md) · [generated results](results/)

## What this project contains

- `paper/rakshasutra_open.pdf` — exact copy of the latest supplied 10-page PDF (`rakshasutra_double_column_tables_fixed.pdf`); its SHA-256 is recorded in `paper/SHA256SUMS.txt`.
- `simulation/audit.py` — standard-library Python calculations for LoRa airtime, pure-ALOHA collision probability, Bloom-filter false positives, BLE single-hit capture assumptions, pseudonym collision probability, and idealized battery arithmetic.
- `simulation/traffic_simulation.py` — a fixed-seed, explicitly synthetic single-cell Poisson traffic comparison.
- `configs/traffic_scenario.json` — its editable scenario inputs and all traffic-model assumptions.
- `configs/claims.json` — inputs transcribed from the earlier nine-page manuscript, with provenance and evidence status; do not assume they represent the revised manuscript.
- `results/` — generated CSV tables from the audit script.
- `figures/` — generated SVG plots and a conceptual system diagram.
- `docs/claim-audit.md` — historical audit of selected claims in the earlier nine-page version. It needs a fresh pass against the current PDF.
- `docs/reproduction.md` — exact commands and model definitions for the included historical/synthetic calculations.

## Quick start

Requires Python 3.10 or later; the audit uses only the Python standard library.

```bash
python simulation/audit.py
python simulation/traffic_simulation.py
```

The first command rewrites arithmetic-check CSVs in `results/` and analytical SVGs in `figures/`. The second writes the fixed-seed illustrative traffic CSV and figure. Neither simulates a validated shrine deployment: one is deterministic arithmetic and the other uses only the explicit synthetic workload in `configs/traffic_scenario.json`.

## Headline checks

- The paper's SF7 airtime values for 28 B, 77 B, and 213 B PHY payloads can be reproduced from the standard LoRa symbol-time equation (under the paper's stated SF7/125 kHz assumptions).
- The packet-loss values in its comparison table are consistent with the pure-ALOHA relation `P_loss = 1 - exp(-2G)` when the listed offered load `G` is used. This checks the formula, not whether the offered load is derived from a realistic event trace.
- A 512-bit Bloom filter with three hashes has density-dependent false positives; it cannot provide a universal guarantee of exact tag identity or zero false reports.
- The stated average current of 29.74 µA implies ideal capacity/current lifetimes that differ from the paper's stated month figures. Real life must be established with a complete load profile and cold-temperature hardware tests.
- A claim such as 99.4% EV capture cannot be derived from “five opportunities” alone; the per-advertisement packet reception probability must be measured or otherwise justified.
- The 3000-tag comparison table's offered-load values imply a 77.9% drop from 39.0% to 8.6%; the abstract separately states an 82.4% airtime reduction, which needs reconciliation.
- The separate synthetic workload does not tune itself to the paper's 15.8% loss result; it uses the assumptions listed in `configs/traffic_scenario.json` and reports its own seeded outcome.

![Illustrative traffic simulation](figures/traffic_simulation.svg)

In this synthetic workload, periodic batch flushes cluster the transmissions. The event simulation therefore produces a much higher loss than the pure-ALOHA estimate from mean offered load alone. This is a schedule-sensitivity warning under the stated assumptions, not evidence of actual shrine-network performance.

See the audit notes before quoting any number from this repository.

## Safety, privacy, and intended use

This is a research prototype and calculation set. It is not a validated child-tracking product, medical device, emergency-response system, or safety-certified design. Do not deploy it for real-world safeguarding without institutional review, privacy/legal review, security testing, RF and battery testing, and operational trials. The uploaded source contains implementation proposals that need independent technical and regulatory review.

## Citation

Jha, Raj. *Rakshasutra (SurakshaNet): A Zero-UI Cognitive-Assistive Wearable and Edge-Filtered BLE–LoRaWAN Architecture for Spatial Disorientation and Crowd Localization in Cellular-Denied Mountain Pilgrimages*. Author-supplied revised manuscript, October 2026, 10 pages. This repository preserves the supplied PDF. Existing simulations and audits are based on an earlier version and do not certify the revised manuscript's evaluations.

No license is included. All rights in the manuscript remain with its author unless a license is added explicitly.

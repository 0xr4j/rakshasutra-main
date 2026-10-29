<div align="center">
  <img src="figures/hero.svg" alt="Rakshasutra concept: a BLE wristband is heard by a smart pole, relayed through a gateway, and used for an authorized last-heard checkpoint lookup" width="100%">
  <h1>Rakshasutra · SurakshaNet</h1>
  <p><strong>The last pole that heard the band.</strong><br>
  A BLE and LoRaWAN checkpoint proposal for pilgrim routes.</p>
  <p>
    <a href="https://0xr4j.github.io/rakshasutra-main/">Open the project site</a> ·
    <a href="paper/rakshasutra_research_draft.pdf">Read the research draft</a> ·
    <a href="paper/rakshasutra_open.pdf">View the original supplied PDF</a> ·
    <a href="docs/claim-audit.md">Claim-by-claim audit</a> ·
    <a href="docs/reproduction.md">Reproduce calculations</a> ·
    <a href="results/paper_reconciliation.csv">Paper-number reconciliation</a>
  </p>
</div>

**Project:** Rakshasutra (SurakshaNet) is a proposal for BLE wristbands and fixed receivers at selected points along pilgrim routes. This repository contains the supplied paper, calculation scripts, and a traffic simulation with synthetic inputs. It has no field data or deployment records.

The reader copy at [`paper/rakshasutra_research_draft.pdf`](paper/rakshasutra_research_draft.pdf) replaces the IEEE journal masthead with “Rakshasutra | Research Draft.” The original supplied PDF remains unchanged.

## How it could work

A wristband broadcasts a short BLE identifier. A nearby pole may receive it and store the time. A gateway can forward the record to a server for an authorized lookup. The paper also proposes rotating identifiers, filtering records at the poles, and sending compact presence messages.

The result would be the latest pole that heard the band, not a live GPS position. If no pole receives it, or there is a long gap between poles, the record may be missing or out of date. This repository checks selected paper calculations and uses synthetic traffic; it does not show that the system works at a shrine.

> [!IMPORTANT]
> No raw field dataset, hardware logs, or deployment record were supplied. The simulation uses stated synthetic inputs. These materials do not establish field performance, safety, or readiness for deployment.

## Start here

| If you want to… | Open |
|---|---|
| Read the public-facing manuscript copy | [Research draft PDF](paper/rakshasutra_research_draft.pdf) |
| Compare with the original supplied file | [Original PDF](paper/rakshasutra_open.pdf) |
| Read the claim audit | [Selected claim audit](docs/claim-audit.md) |
| Rerun the calculations | [Reproduction guide](docs/reproduction.md) |
| Inspect the chosen synthetic workload | [Scenario inputs](configs/traffic_scenario.json) |
| See paper values beside recalculations | [Reconciliation CSV](results/paper_reconciliation.csv) |
| Inspect schedule-jitter sensitivity | [Benchmark CSV](results/jitter_sensitivity.csv) · [Plot](figures/jitter_sensitivity.svg) |
| Run the software checks | [Unit tests](tests/) |
| See the full calculation inputs | [Claim inputs](configs/claims.json) |
| Browse every output | [Results](results/) · [Figures](figures/) |

The [project site](https://0xr4j.github.io/rakshasutra-main/) is published from `docs/` with GitHub Pages. Changes to `main` trigger deployment through GitHub Actions.

## What is in this repository

- `paper/rakshasutra_research_draft.pdf` — nine-page reader copy with the unsupported IEEE journal masthead removed; article content preserved.
- `paper/rakshasutra_open.pdf` — original supplied nine-page PDF, preserved unchanged as the source under review.
- `simulation/audit.py` — standard-library Python calculations for LoRa airtime, pure-ALOHA loss, Bloom-filter false positives, BLE capture assumptions, pseudonym collisions, and idealized battery arithmetic.
- `simulation/traffic_simulation.py` — a separate single-cell synthetic packet-overlap simulation with deterministic seeds.
- `configs/` — transcribed paper values and explicit simulation assumptions.
- `results/` — generated CSV outputs, including the paper-number reconciliation and synthetic benchmark records.
- `tests/` — deterministic arithmetic/reproducibility tests and labeled synthetic fixtures.
- `figures/` — concept architecture and analytical or synthetic SVG plots.
- `docs/claim-audit.md` — claim-by-claim findings and questions that remain open.
- `docs/reproduction.md` — model definitions, exact commands, and output interpretation.

## Run the checks

Requires Python 3.10 or later. The scripts use only the Python standard library.

```bash
python -m unittest discover -s tests -v
python simulation/audit.py
python simulation/traffic_simulation.py
python simulation/sensitivity.py
```

The audit script rewrites selected CSVs in `results/` and analytical plots in `figures/`. The traffic script runs the scenario described in `configs/traffic_scenario.json` and writes its summary, run-level CSV, and plot. The sensitivity script repeats that synthetic workload across four batch-jitter settings. GitHub Actions runs the unit tests and regenerates all outputs before deploying the Pages site. These commands do **not** reproduce a shrine deployment or the manuscript’s raw experiment traces.

## Paper values and simulation results

### The manuscript's 3,000-tag ALOHA table

The manuscript lists offered load values of 0.390 for “single-event + raw heartbeat” and 0.086 for “25-tag chunk + 64 B Bloom.” Applying its stated pure-ALOHA equation, (P_{loss}=1-e^{-2G}), gives 54.2% and 15.8% packet loss, respectively.

Those two offered-load entries imply a **77.9% reduction in offered load**. The abstract separately says 82.4%; that difference needs reconciliation. The repository recomputes the formula from the paper’s (G) values; it does not independently derive or validate those offered loads.

### The repository's separate synthetic schedule

The event simulation uses a separate synthetic workload:

| One-hour, 3,000-tag scenario | Mean simulated packet loss |
|---|---:|
| Single arrivals + raw per-pole heartbeat | 56.7% |
| 15-second batch windows + 64-byte heartbeat | 72.8% |

The batched case sends fewer packets, but this schedule emits them in narrow periodic windows. In this synthetic model, clustering increases overlaps. The 2.5th–97.5th percentiles describe run-to-run variation across 40 deterministic seeds, **not** uncertainty in the assumptions or measured shrine traffic. This is a schedule-sensitivity illustration, not a prediction of field performance.

### Other checks and limits

- **BLE vehicle capture:** five opportunities require at least 64.1% independent reception probability per advertisement to reach the paper’s 99.4% aggregate claim. That per-ad probability is not measured in the supplied evidence.
- **Rotating identifier:** the 32-bit birthday estimate for 3,000 tags is about 0.105% chance of at least one collision in one set under a uniform-random model. That estimate is not a complete privacy or linkability analysis.
- **Battery arithmetic:** using the paper’s stated 620/434 mAh capacities and the stated 17.5983 µA weighted current gives 48.23/33.76 ideal months, while the manuscript reports 14.2/11.1. This mismatch needs a corrected derivation; neither result validates runtime under cold conditions, pulse loads, regulator losses, cutoff behavior, aging, or a real device duty cycle.
- **Capacitor pulse check:** an ideal 100 µF capacitor alone would drop 32 V while supplying 32 mA for 100 ms. The complete battery-plus-capacitor circuit needs a bench test.
- **Radio range:** a link-budget calculation is not an RF range test. Site geometry, body loss, antennas, crowding, interference, and equipment need measurement.

The [claim audit](docs/claim-audit.md) lists the assumptions and limitations behind these results.

## Repository map

```text
configs/       transcribed manuscript inputs and explicit scenario assumptions
docs/          project guide, claim audit, and reproduction instructions
figures/       concept architecture and generated plots
paper/         supplied PDF and checksum
results/       generated CSV outputs and per-run simulation data
simulation/    reproducible arithmetic audit and synthetic event simulation
```

## Safety, privacy, and intended use

This is an early research concept and calculation set. It is not a validated child-tracking product, medical device, emergency-response system, or safety-certified design. Do not rely on it for real-world safeguarding.

Any prototype or deployment requires informed consent and access-control design, privacy/legal review, security testing, RF and battery tests, venue approval, and supervised operational trials. Rotating identifiers alone do not establish anonymity, unlinkability, or compliance with privacy law.

## Citation

Jha, Raj. *Rakshasutra: A Privacy-Preserving, Edge-Filtered Hybrid BLE–LoRaWAN Architecture for Real-Time Crowd Localization in Cellular-Denied Mountain Pilgrimages*. Author-supplied manuscript, October 2026, 9 pages.

This repository preserves the supplied PDF and audits selected calculations; it does not certify the manuscript’s reported evaluations. No open-source license is included. All rights in the manuscript remain with its author unless a license is added explicitly.

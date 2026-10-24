# Reproduction guide

## Environment

Python 3.10+; standard library only.

## Run

From the repository root:

```bash
python simulation/audit.py
```

The script reads `configs/claims.json`, then writes deterministic CSVs to `results/` and SVGs to `figures/`.

Run the separate event-driven scenario:

```bash
python simulation/traffic_simulation.py
```

This simulation interprets the paper's 3,000 tags, 60 poles, and 55-second passage assumption as one Poisson arrival stream per cell, evenly spread across poles. It compares single-event uplinks plus raw per-pole ID heartbeats with 15-second, at-most-25-record chunks plus fixed 64-byte per-pole heartbeats. This is a chosen synthetic workload, **not** the paper's traffic derivation and not a reconstruction of shrine operations. The default runs 40 independent deterministic seeds and writes both a summary (`results/illustrative_traffic_simulation.csv`) and per-run records (`results/illustrative_traffic_replications.csv`). The summary includes the mean, standard deviation, and 2.5th–97.5th percentiles of run-level loss. These percentiles describe stochastic run-to-run variation under the configured assumptions; they do not measure uncertainty in the assumptions or field performance. Because the proposed batches are emitted in a narrow 200–1500 ms jitter window every 15 seconds, transmissions cluster. The simulator reports both event-driven loss and the pure-ALOHA estimate from mean load to expose how the Poisson-arrival approximation can fail for scheduled bursts.

## Tests and sensitivity benchmark

Run the deterministic unit tests:

```bash
python -m unittest discover -s tests -v
```

The tests check selected arithmetic, fixture behavior, and reproducibility. They are software checks, not hardware, RF, security, or field validation.

Run the batch-schedule sensitivity benchmark:

```bash
python simulation/sensitivity.py
```

It runs 40 deterministic seeds at each configured maximum jitter (1.5, 3.75, 7.5, and 15 seconds) and writes `results/jitter_sensitivity.csv` plus `figures/jitter_sensitivity.svg`. These are synthetic event-simulation outputs. The schedule sweep is not calibrated to measured radio reception or shrine traffic.

## Model definitions

- **LoRa airtime:** Semtech-style symbol-time and payload-symbol calculation for the explicitly stated SF7/125 kHz/CR 4/5 scenario. PHY payload lengths are transcribed assumptions.
- **Pure ALOHA:** `P_loss = 1 - exp(-2G)`, where the offered load `G` values are copied from the paper's comparison table. This reproduces the table's arithmetic only; it does not independently derive G.
- **Bloom false-positive rate:** `(1 - exp(-k n / m))^k`, with `m=512` bits and `k=3` hashes. This is an asymptotic approximation for independent uniform hashes.
- **BLE capture:** for five independent advertising opportunities, `P_capture = 1-(1-p)^5`. The script calculates the per-opportunity probability needed to obtain the manuscript's claimed aggregate value; it does not estimate p from measurements.
- **32-bit pseudonym collisions:** birthday approximation `1-exp(-N(N-1)/(2·2^b))` for independent uniform values. AES-CMAC outputs are not observed values here; this is a random-space estimate.
- **Battery arithmetic:** capacity divided by current, plus weighted active/sleep average. This is an idealized arithmetic ceiling, not a battery model. Pulse droop uses the ideal capacitor estimate `ΔV=I·t/C` and is explicitly not a circuit simulation.

## Output interpretation

CSV values include a `status` or `note` column to preserve their provenance. Generated SVGs include captions stating that the curves are analytical or assumption-based. Do not relabel them as field results.

The traffic-model figure shows mean loss across seeds with whiskers spanning the empirical 2.5th–97.5th percentiles. This is a run-level spread summary, not a confidence interval for an unknown deployment loss and not a parameter-uncertainty analysis.

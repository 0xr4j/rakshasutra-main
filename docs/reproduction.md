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

The model treats the paper's 3,000 tags, 60 poles, and 55-second passage time as one Poisson arrival stream spread evenly across the poles. It compares single-event uplinks and raw-ID heartbeats with 15-second batches of up to 25 records and fixed 64-byte heartbeats. This workload is synthetic; it does not reproduce the paper's traffic calculation or shrine operations.

By default, the script runs 40 deterministic seeds. It writes a summary to `results/illustrative_traffic_simulation.csv` and per-run records to `results/illustrative_traffic_replications.csv`. The summary reports the mean, standard deviation, and 2.5th–97.5th percentiles of run-level packet loss. Those percentiles describe variation across runs under the chosen inputs, not uncertainty in the inputs or expected field performance.

Batched transmissions use a shared 15-second schedule with 200–1500 ms of jitter, so they can cluster. The script reports both simulated collisions and the pure-ALOHA estimate from average load to show how timing can change the result.

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

# Reproduction guide

## Environment

Python 3.10+; standard library only.

## Run

From the repository root:

```bash
python simulation/audit.py
```

The script reads `configs/claims.json`, then writes deterministic CSVs to `results/` and SVGs to `figures/`.

## Model definitions

- **LoRa airtime:** Semtech-style symbol-time and payload-symbol calculation for the explicitly stated SF7/125 kHz/CR 4/5 scenario. PHY payload lengths are transcribed assumptions.
- **Pure ALOHA:** `P_loss = 1 - exp(-2G)`, where the offered load `G` values are copied from the paper's comparison table. This reproduces the table's arithmetic only; it does not independently derive G.
- **Bloom false-positive rate:** `(1 - exp(-k n / m))^k`, with `m=512` bits and `k=3` hashes. This is an asymptotic approximation for independent uniform hashes.
- **BLE capture:** for five independent advertising opportunities, `P_capture = 1-(1-p)^5`. The script calculates the per-opportunity probability needed to obtain the manuscript's claimed aggregate value; it does not estimate p from measurements.
- **32-bit pseudonym collisions:** birthday approximation `1-exp(-N(N-1)/(2·2^b))` for independent uniform values. AES-CMAC outputs are not observed values here; this is a random-space estimate.
- **Battery arithmetic:** capacity divided by current, plus weighted active/sleep average. This is an idealized arithmetic ceiling, not a battery model. Pulse droop uses the ideal capacitor estimate `ΔV=I·t/C` and is explicitly not a circuit simulation.

## Output interpretation

CSV values include a `status` or `note` column to preserve their provenance. Generated SVGs include captions stating that the curves are analytical or assumption-based. Do not relabel them as field results.

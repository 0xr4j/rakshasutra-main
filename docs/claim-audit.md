# Selected claim audit

This is a first-pass engineering consistency audit of the author-supplied manuscript. It is not a peer review, field validation, regulatory opinion, or complete security analysis. “Reproduced” below means only that a stated equation reproduces a stated number under listed inputs.

| Manuscript statement | What can be checked here | Evidence status / issue |
|---|---|---|
| SF7 airtime: 66.82 ms, 138.50 ms, 338.18 ms | Recomputed for 28 B, 77 B, 213 B PHY payloads at SF7, BW=125 kHz, CR 4/5, explicit header, CRC enabled, eight preamble symbols | Arithmetic reproduces the values under these assumptions. This does not verify the chosen payloads, regional legality, or deployment traffic. |
| 3,000-tag cell loss falls from 54.2% to 15.8% | The table's stated G values 0.390 and 0.086 yield those values under P=1-exp(-2G) | Formula consistent; the paper does not include raw traces or a derivation sufficient to validate offered load G. Pure-ALOHA is a simplifying model. |
| 82.4% airtime-load reduction | Compare the table's 3,000-tag offered loads, 0.390 and 0.086 | Those values imply a 77.9% reduction. The abstract's 82.4% needs a separate definition or corrected arithmetic. |
| 64-byte Bloom heartbeat guarantees bounded airtime | A fixed payload does bound heartbeat bytes per transmission | It does not guarantee exact set recovery. A Bloom filter has false positives whose rate increases with the number of inserted IDs; missing query procedure, hash specification, and population limits matter. |
| 99.4% EV capture from five BLE opportunities | With five opportunities, compute required per-advertisement reception probability | At least 64.1% independent reception probability per opportunity is needed for 99.4% aggregate capture. Independence and reception probability require empirical evidence. |
| 32-bit rotating pseudonym is unlinkable | Estimate birthday collision probability for 3,000 simultaneous pseudonyms | Approx. 0.105% probability of at least one collision in a single 3,000-tag set under a uniform-random model. This is not a complete privacy analysis; metadata and timing may still link observations. |
| 14.2 months ambient / 11.1 months cold battery life | Recompute with the paper's 620 mAh / 434 mAh capacities and the stated 17.5983 µA weighted active/sleep current | Arithmetic gives 48.23 months ambient and 33.76 months cold, not 14.2 / 11.1. This is an arithmetic inconsistency, not evidence that the longer values are achievable. The calculation omits pulse behavior, CR2450 discharge curves, cold capacity under load, cutoff, regulator efficiency, aging, and self-discharge; obtain the exact manuscript duty-cycle derivation and bench-test the device before revising the claim. |
| 100 µF capacitor buffers 32 mA, 100 ms burst | Charge-balance estimate ΔV=I·t/C | An ideal 100 µF capacitor alone would droop 32 V at 32 mA for 100 ms. The battery may supply part of the load, but the cited capacitor value alone does not prove brownout protection. Test the complete circuit at temperature. |
| BLE Coded PHY 50–92 m detection | No RF measurements or propagation dataset supplied | Link-budget calculations are not a range test. Using the paper's stated +8 dBm, 40.2 dB at 1 m, exponent 2.15, 14 dB body loss, and −103 dBm sensitivity gives about 20.3 dB median margin at 50 m, not the separately stated 28.6 dB. Antenna gains, receiver implementation, body loss, and GI-shed geometry need measurements. |
| Latency claims | Compare abstract (<4 s), system section (2.5–5.0 s), and conclusion (<5 s) | The manuscript gives inconsistent bounds. Define start/end events, radio/network conditions, percentile, and measurement method, then report raw latency trials. |
| “Empirical” field results | No raw records, site protocol, dates, device logs, or instrumentation files supplied in the provided PDF | Not independently verifiable from the supplied material. Do not describe these outcomes as reproduced or measured by this repository. |

## Additional design questions before a preprint

1. Specify the precise BLE advertisement format, assigned Company Identifier, byte order, bit-level cryptographic inputs, MAC-address type, and standard-compliant advertising behavior. A lab identifier must not be presented as a Bluetooth SIG-assigned identifier.
2. Publish the exact LoRaWAN payload accounting, regional channel plan, EIRP/duty-cycle constraints, retry behavior, gateway demodulation assumptions, and a derivation of every offered-load row.
3. Define how an on-premise server resolves Bloom-filter membership without creating unacceptable false positives or a large per-heartbeat query workload.
4. Replace the “100% Class C”/latency statements with a tested downlink budget, gateway scheduling assumptions, RF coexistence analysis, and fallback behavior. A Class C label alone does not imply guaranteed delivery.
5. Reconcile component specifications, current profile, battery capacity versus temperature, capacitor placement/ESR, pulse duration, and safe battery enclosure. Perform bench tests before asserting runtime or brownout behavior.
6. Add references and primary-source support for site-specific route lengths, footfall, roof coverage/attenuation, pole counts, device BOM, and local operational procedures.
7. Conduct a threat-model review that includes key provisioning/revocation, replay windows, 32-bit tag/MIC collision/forgery risks, stolen devices, side channels, and child privacy. The 24-bit wake-token forgery bound in the paper is especially sensitive to repeated attempts and rate limits.
8. Reconcile the 82.4% reduction in the abstract with the 77.9% reduction implied by the 3,000-tag offered-load figures in Table IV.

## What this audit does not establish

It does not establish that the system was built, deployed, tested at SMVD, accepted by shrine authorities, compliant with Indian radio rules, safe for children, or effective in locating pilgrims. It does not verify the manuscript's citations or external site-specific factual claims. Those require primary-source checks and/or measurements.

## Synthetic schedule sensitivity

`simulation/traffic_simulation.py` adds a separate one-hour fixed-seed workload using the assumptions in `configs/traffic_scenario.json`. Under that scenario, batching lowers the number of packets and average airtime load, but the narrow periodic flush jitter creates transmission bursts. The event-driven collision model reports substantially more loss than `1-exp(-2G)` calculated from mean load. In a 40-seed parameter sweep, mean event-driven loss was 72.8% at a maximum 1.5 s jitter, 49.5% at 3.75 s, 32.4% at 7.5 s, and 21.0% at 15 s; the mean offered load stayed the same. This illustrates sensitivity to a synthetic scheduling assumption, not actual SMVD packet loss. It is a design warning that average offered load alone is insufficient when packet starts are synchronized; field-like event traces and schedule/jitter experiments are still needed.

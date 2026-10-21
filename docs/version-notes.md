# Current manuscript and repository evidence

## Current paper

`paper/rakshasutra_double_column_tables_fixed_source.pdf` is an exact copy of the author's file `rakshasutra_double_column_tables_fixed.pdf`, supplied on 21 October 2026. It is a 10-page revised manuscript titled *Rakshasutra (SurakshaNet): A Zero-UI Cognitive-Assistive Wearable and Edge-Filtered BLE–LoRaWAN Architecture for Spatial Disorientation and Crowd Localization in Cellular-Denied Mountain Pilgrimages*. `paper/rakshasutra_open.pdf` is the same manuscript followed by a clearly labeled, one-page repository-prepared arithmetic erratum; the source pages are preserved unchanged.

SHA-256 checksums for both PDFs are listed in [`paper/SHA256SUMS.txt`](../paper/SHA256SUMS.txt).

## Relationship to repository code and results

The Table 5 inputs in `configs/claims.json` and the generated `aloha_claim_check.csv` are now aligned with the revised manuscript's displayed `G` values; loss is independently recomputed from `1 - exp(-2G)`. Other audit outputs and the synthetic traffic event simulation do not reproduce all current manuscript claims and must not be presented as validating the revised paper. The prior claim audit is retained for traceability.

The updated paper itself describes analytical models and estimates. No raw field dataset, instrument logs, deployment record, or hardware measurements were included with the supplied PDF. Do not label its analytical results as field measurements or independently verified performance.

## Corrected internal mismatch

The source Table 5's displayed offered loads and losses are not fully consistent with `P_loss = 1 - exp(-2G)`. Using the displayed `G`, the 3,000-tag 60-pole explicit-departure case is 17.11% / **28.98%**, and the implicit-departure case is 11.98% / **21.31%**. Table 8 also retains a prior-draft 8.6% / 15.8% result. A visible correction sheet is appended to the reading copy, and [`docs/errata.md`](errata.md) gives the derivation. The original 10-page PDF is kept unchanged.

## Provenance

- Source filename: `rakshasutra_double_column_tables_fixed.pdf`
- Repository filename: `paper/rakshasutra_open.pdf` (stable path retained for existing links)
- Source page count: 10
- Reading-copy page count: 11 (source plus erratum)
- Source SHA-256: `FB0D3484ECDFDD96FFAC97A9542F1388A5713DAC87DC00F91F66B462B702735C`
- Reading-copy SHA-256: `02449FEF77E4AA625E77F7A4CD6F1429AAF3ADDFF7AAB1E430EB8875C09B64BD`

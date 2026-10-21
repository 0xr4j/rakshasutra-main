# Table 5 and Table 8 arithmetic erratum

The PDF supplied on 21 October 2026 reports the pure-ALOHA loss relation `P_loss = 1 - exp(-2G)`. Recalculation from the displayed Table 5 offered loads corrects two 3,000-tag loss entries:

| 3,000-tag case | Displayed offered load `G` | Loss printed in source | Recomputed loss |
|---|---:|---:|---:|
| 60 poles, explicit departures | 17.11% | 28.99% | **28.98%** |
| 60 poles, implicit departures | 11.98% | 21.35% | **21.31%** |
| 40 LoRa poles + fiber hubs | 7.99% | 14.77% | 14.77% |

The corrected reading copy appends this erratum after the untouched source PDF. It also identifies Table 8's “15.8% loss (`G = 8.6%`) at 60 poles” as a superseded value from an earlier draft. For the revised Table 5 cases, use 28.98% (explicit departures) and 21.31% (implicit departures), when recomputing from the displayed loads.

These values only check the stated formula against the displayed `G`; they do not validate the offered-load model or represent field measurements. The exact manuscript TeX source was not supplied, so the correction is attached visibly rather than applied invisibly to the original PDF pages. To make a clean publication master, update the source and regenerate from unrounded model outputs.

Rebuild the reading copy from the preserved source with `python simulation/build_erratum_pdf.py`. This optional PDF-building script requires `pypdf` and `reportlab`; the arithmetic audit and simulations remain standard-library Python.

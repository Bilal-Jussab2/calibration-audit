# Jev results (BANKING77 and CLINC150)

Raw data and reviews behind [Does Jev's confidence mean what it says?](https://audit.korbant.co.uk/jev.html). The method was committed before any scored call: [pre-registration](../../preregistration/jev-preregistration.md).

| File | What it is |
|---|---|
| `jev_banking77_raw.jsonl.gz` | Every Jev response for the 3,080 BANKING77 test items (model `jev-1.13.0`, 22 Sep 2026) |
| `jev_clinc_oos_raw.jsonl.gz` | Every Jev response for the 1,000 CLINC150 out of scope items |

The two raw files are gzip compressed (`gunzip` restores the original JSON lines).
| `report.json` | All scored figures, produced by `jevcal` from the raw files |
| `review_156.csv` / `.json` | Hand review of all 156 wrong answers at confidence 0.90 or above, with a reason for each |
| `low_sample_40.json` | The random sample of 40 wrong answers below 0.88 (seed 20260925) |
| `review_low_40.csv` / `.json` | Hand review of that sample (extra analysis, not in the plan) |
| `reliability_*.png` | Reliability diagrams for both signals |

Reproduce: see [`jevcal`](../../jevcal). The first pass of both reviews was AI assisted and then checked by hand; every verdict is listed so anyone can disagree with a single call.

Datasets: BANKING77 (Casanueva et al. 2020, PolyAI, CC BY 4.0) and CLINC150 (Larson et al. 2019, CC BY 3.0), used unmodified. The raw files store item IDs, labels and Jev's outputs; the review lists also quote each utterance so every verdict can be checked, as the licences allow with attribution.

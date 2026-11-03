## Paired significance: v2 vs v3

| metric | v2 | v3 | delta | 95% CI (paired bootstrap) | P(v3 > v2) |
|---|---|---|---|---|---|
| mAP@0.5 | 51.7% | 54.2% | +2.5% | [-6.9%, +12.4%] | 0.714 |
| recall | 64.3% | 74.2% | +9.9% | [+4.5%, +15.8%] | 1.000 |
| tooth (end-to-end) | 63.7% | 72.5% | +8.8% | [+3.8%, +14.0%] | 0.999 |
| joint (end-to-end) | 56.0% | 65.9% | +9.9% | [+3.8%, +16.2%] | 1.000 |

### McNemar exact test (per-lesion, paired)

| metric | v3-only correct | v2-only correct | p (two-sided) |
|---|---|---|---|
| detection | 26 | 8 | 2.94e-03 |
| tooth | 22 | 6 | 3.72e-03 |
| joint | 26 | 8 | 2.94e-03 |

### Per-class AP@0.5

| class | v2 | v3 | delta | 95% CI | P(v3 > v2) |
|---|---|---|---|---|---|
| Impacted | 76.7% | 75.0% | -1.7% | [-11.7%, +5.4%] | 0.322 |
| Caries | 33.3% | 35.3% | +2.0% | [-3.3%, +7.3%] | 0.764 |
| Periapical Lesion | 37.5% | 55.6% | +18.1% | [-15.7%, +51.9%] | 0.863 |
| Deep Caries | 59.3% | 51.1% | -8.1% | [-23.8%, +7.5%] | 0.132 |

Bootstrap: 2000 replicates, images resampled with replacement.

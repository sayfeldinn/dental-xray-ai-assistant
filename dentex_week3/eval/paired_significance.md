## Paired significance: v1 vs v2

| metric | v1 | v2 | delta | 95% CI (paired bootstrap) | P(v2 > v1) |
|---|---|---|---|---|---|
| mAP@0.5 | 49.8% | 51.7% | +2.0% | [-11.4%, +11.1%] | 0.603 |
| recall | 63.7% | 71.4% | +7.7% | [-0.5%, +16.1%] | 0.964 |
| tooth (end-to-end) | 48.4% | 63.7% | +15.4% | [+4.8%, +26.8%] | 0.997 |
| joint (end-to-end) | 42.3% | 56.0% | +13.7% | [+4.0%, +23.9%] | 0.997 |

### McNemar exact test (per-lesion, paired)

| metric | v2-only correct | v1-only correct | p (two-sided) |
|---|---|---|---|
| detection | 30 | 16 | 5.41e-02 |
| tooth | 48 | 20 | 9.14e-04 |
| joint | 44 | 19 | 2.23e-03 |

### Per-class AP@0.5

| class | v1 | v2 | delta | 95% CI | P(v2 > v1) |
|---|---|---|---|---|---|
| Impacted | 75.0% | 76.7% | +1.7% | [-8.1%, +14.1%] | 0.629 |
| Caries | 28.2% | 33.3% | +5.1% | [-2.0%, +12.1%] | 0.926 |
| Periapical Lesion | 42.9% | 37.5% | -5.4% | [-60.0%, +20.5%] | 0.275 |
| Deep Caries | 52.9% | 59.3% | +6.3% | [-8.5%, +22.4%] | 0.789 |

Bootstrap: 2000 replicates, images resampled with replacement.

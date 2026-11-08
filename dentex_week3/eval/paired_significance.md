## Paired significance: v1 vs v2

| metric | v1 | v2 | delta | 95% CI (paired bootstrap) | P(v2 > v1) |
|---|---|---|---|---|---|
| mAP@0.5 | 49.8% | 51.7% | +2.0% | [-11.4%, +11.1%] | 0.603 |
| recall | 56.6% | 64.3% | +7.7% | [+0.0%, +15.4%] | 0.970 |
| tooth (end-to-end) | 48.4% | 65.4% | +17.0% | [+7.0%, +28.3%] | 1.000 |
| joint (end-to-end) | 42.3% | 57.1% | +14.8% | [+5.4%, +24.7%] | 0.999 |

### McNemar exact test (per-lesion, paired)

| metric | v2-only correct | v1-only correct | p (two-sided) |
|---|---|---|---|
| detection | 33 | 19 | 7.04e-02 |
| tooth | 49 | 18 | 1.94e-04 |
| joint | 45 | 18 | 8.98e-04 |

### Per-class AP@0.5

| class | v1 | v2 | delta | 95% CI | P(v2 > v1) |
|---|---|---|---|---|---|
| Impacted | 75.0% | 76.7% | +1.7% | [-8.1%, +14.1%] | 0.629 |
| Caries | 28.2% | 33.3% | +5.1% | [-2.0%, +12.1%] | 0.926 |
| Periapical Lesion | 42.9% | 37.5% | -5.4% | [-60.0%, +20.5%] | 0.275 |
| Deep Caries | 52.9% | 59.3% | +6.3% | [-8.5%, +22.4%] | 0.789 |

Bootstrap: 2000 replicates, images resampled with replacement.

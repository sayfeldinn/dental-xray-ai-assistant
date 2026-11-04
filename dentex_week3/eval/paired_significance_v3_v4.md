## Paired significance: v3 vs v4

| metric | v3 | v4 | delta | 95% CI (paired bootstrap) | P(v4 > v3) |
|---|---|---|---|---|---|
| mAP@0.5 | 54.2% | 55.1% | +0.8% | [-6.0%, +6.1%] | 0.643 |
| recall | 74.2% | 71.4% | -2.7% | [-8.6%, +3.4%] | 0.159 |
| tooth (end-to-end) | 73.1% | 70.3% | -2.7% | [-7.7%, +2.6%] | 0.130 |
| joint (end-to-end) | 65.9% | 60.4% | -5.5% | [-11.3%, +0.6%] | 0.029 |

### McNemar exact test (per-lesion, paired)

| metric | v4-only correct | v3-only correct | p (two-sided) |
|---|---|---|---|
| detection | 9 | 14 | 4.05e-01 |
| tooth | 6 | 11 | 3.32e-01 |
| joint | 8 | 18 | 7.55e-02 |

### Per-class AP@0.5

| class | v3 | v4 | delta | 95% CI | P(v4 > v3) |
|---|---|---|---|---|---|
| Impacted | 75.0% | 72.5% | -2.5% | [-8.0%, +1.0%] | 0.102 |
| Caries | 35.3% | 34.2% | -1.1% | [-5.9%, +3.2%] | 0.321 |
| Periapical Lesion | 55.6% | 50.0% | -5.6% | [-30.0%, +12.5%] | 0.251 |
| Deep Caries | 51.1% | 63.6% | +12.5% | [+1.5%, +23.4%] | 0.987 |

Bootstrap: 2000 replicates, images resampled with replacement.

# Level 3 out-of-time evaluation, 2016-2025 (prompt 07, Step 4)

Pre-registered in `reports/eval_plan.md` (amendment and addendum of 2026-10-12, both committed before any result existed). **This is an out-of-time generalization test of the frozen method (profiles, V4 selected on 1995-2015, z-score statistics frozen from the 1995-2015 matrix), not a forecast:** the concept profiles come from the current LoC description text, which is not limited to papers before 2016. Nothing on this page selects, tunes or changes anything.

## Read this first

- **Candidate-only AUC is the more informative number.** Positives are almost entirely candidate-pool papers (see the per-theory 'positives by corpus part' lines), while most negatives are background or random papers; the all-negatives AUC therefore rewards any variant that prefers theory-flavoured neuroscience/consciousness text. Candidate-only restricts negatives to the candidate pool.
- **Exclusive positives are single-theory papers.** A large share of GWT and IIT papers name both theories (306 of 519 GWT and 333 of 462 IIT direct-mention papers in this window) and are not positives. Positives are therefore not a random sample of each theory's literature.
- **Positives come from the capped candidate pool** (random sample of at most 400 papers per theory from the Europe PMC phrase hits), so the silver sets for GWT, IIT and PP are samples; panpsychism and Champagne were taken whole.
- **The random background sample is week-clustered** (random weekly FIRST_PDATE slices per year, 100 per year), not a uniform draw over each year.
- **Champagne's primary subset is only 8 papers** (title/abstract mention or >= 3 mentions); the other 17 of its 25 exclusive positives have no title/abstract mention and fewer than 3 strong-term mentions. Its numbers are quantitative by the n >= 20 rule but fragile.
- **BM25 statistics** (IDF, per-claim max normalisation) come from the 2016-2025 chunk set; z-scores for V4/V5 use the frozen 1995-2015 statistics.
- **Negatives are unlabeled**, so every metric is a lower bound. 1995-2015 rows below are copied from `reports/level3_eval_test.md` (GWT and PP: test halves, n = 77 and 99; the others: all positives, n = 3, 17, 7). The 1995-2015 and 2016-2025 negative pools differ in size and composition, so differences are indicative, not exact.
- CIs: 2,000 bootstrap resamples of the positives (seed 20261011), negatives fixed.

## Summary (candidate-only AUC, V4; 1995-2015 -> 2016-2025)

| theory | n (1995-2015 -> 2016-2025) | V4 | V5 | BM25 | V4 minus BM25 in 2016-2025 |
|---|---|---|---|---|---|
| Champagne | 3 -> 25 | 0.915 -> 0.732 | 0.966 -> 0.844 | 0.705 -> 0.695 | +0.037 (CIs overlap) |
| GWT | 77 -> 213 | 0.809 -> 0.744 | 0.711 -> 0.736 | 0.673 -> 0.690 | +0.054 (CIs overlap narrowly) |
| IIT | 17 -> 129 | 0.893 -> 0.764 | 0.899 -> 0.755 | 0.858 -> 0.738 | +0.026 (CIs overlap) |
| Panpsychism | 7 -> 61 | 0.973 -> 0.832 | 0.970 -> 0.866 | 0.861 -> 0.705 | +0.127 (CIs barely overlap or separate) |
| PP | 99 -> 151 | 0.760 -> 0.678 | 0.874 -> 0.835 | 0.660 -> 0.720 | **-0.042 (BM25 ahead, CIs overlap)** |

**Plain reading.** Performance **dropped, but stayed well above chance (0.5) for every theory and variant**. V4's candidate-only AUC fell by 0.06-0.18 for all five theories. With all years the drop is statistically clear (non-overlapping CIs) for Champagne, IIT and panpsychism and overlaps for GWT and PP; with 2020-2022 excluded it is clear for IIT, panpsychism and PP and overlaps for Champagne (n = 18, exploratory) and GWT. BM25 also dropped for IIT, panpsychism and Champagne (point estimates), so part of the fall is shared by all methods and is not specific to the profiles. We did not test why; possible contributors are the 1995-2015 numbers resting on very few positives for Champagne, IIT and panpsychism (n = 3, 17, 7) and differences in the negative pools between windows. V4's advantage over BM25 on candidate-only AUC is positive for four theories but within overlapping CIs for most (panpsychism's CIs overlap only slightly), and **BM25 is ahead of V4 on predictive processing** (0.720 vs 0.678, CIs overlap). V5 (the contrast variant) fell less than V4 for Champagne, panpsychism and PP and is level elsewhere on candidate-only AUC, but its all-negatives AUC is still poor for GWT (0.626), as in 1995-2015. Excluding 2020-2022 changes no conclusion. This is reported as found; V4 remains the selected variant and nothing was re-selected on these data.

**Discriminability (`reports/level3_discriminability_late.md`).** For both V4 and V5, with all negatives and with candidate-pool negatives only, and with and without 2020-2022, the diagonal is the column maximum in 5/5 columns: each theory's profile retrieves its own masked positives better than the other four profiles do.

# ALL YEARS 2016-2025

## Champagne: n positives = 25, negatives = 5403, candidate-pool negatives = 1448

Positives by corpus part: {'candidate': 25}. 1995-2015 test n = 3.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.891 [0.844, 0.930] | **0.732 [0.636, 0.815]** | 0.200 [0.079, 0.360] | 0.240 [0.080, 0.400] | 0.360 [0.200, 0.521] | 0.14 |
| 1995-2015 | V4 | 0.981 [0.960, 0.997] | **0.915 [0.823, 0.987]** | 0.333 | 0.333 | 0.667 | - |
| 2016-2025 | V5 | 0.835 [0.736, 0.918] | **0.844 [0.757, 0.917]** | 0.280 [0.120, 0.480] | 0.360 [0.160, 0.560] | 0.440 [0.240, 0.640] | 0.00 |
| 1995-2015 | V5 | 0.977 [0.944, 1.000] | **0.966 [0.927, 0.998]** | 0.333 | 0.667 | 0.667 | - |
| 2016-2025 | BM25 | 0.789 [0.690, 0.876] | **0.695 [0.580, 0.799]** | 0.200 [0.040, 0.360] | 0.200 [0.040, 0.360] | 0.280 [0.120, 0.440] | 0.08 |
| 1995-2015 | BM25 | 0.838 [0.706, 0.983] | **0.705 [0.491, 0.948]** | 0.000 | 0.000 | 0.333 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.009 | 0.019 | 0.037 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.183; CIs do NOT overlap); V5 dropped (-0.122; CIs do NOT overlap); BM25 held (-0.010; CIs overlap).

## GWT: n positives = 213, negatives = 4913, candidate-pool negatives = 958

Positives by corpus part: {'candidate': 213}. 1995-2015 test n = 77.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.878 [0.857, 0.897] | **0.744 [0.709, 0.779]** | 0.146 [0.099, 0.197] | 0.254 [0.197, 0.315] | 0.399 [0.333, 0.465] | 0.00 |
| 1995-2015 | V4 | 0.912 [0.888, 0.937] | **0.809 [0.758, 0.861]** | 0.208 | 0.286 | 0.455 | - |
| 2016-2025 | V5 | 0.626 [0.586, 0.665] | **0.736 [0.704, 0.769]** | 0.014 [0.000, 0.033] | 0.038 [0.014, 0.066] | 0.103 [0.066, 0.146] | 0.00 |
| 1995-2015 | V5 | 0.592 [0.520, 0.662] | **0.711 [0.646, 0.775]** | 0.013 | 0.013 | 0.039 | - |
| 2016-2025 | BM25 | 0.765 [0.731, 0.796] | **0.690 [0.651, 0.727]** | 0.047 [0.019, 0.075] | 0.127 [0.085, 0.169] | 0.207 [0.155, 0.263] | 0.02 |
| 1995-2015 | BM25 | 0.779 [0.731, 0.825] | **0.673 [0.610, 0.736]** | 0.091 | 0.117 | 0.156 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.010 | 0.020 | 0.041 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.065; CIs overlap); V5 rose (+0.025; CIs overlap); BM25 held (+0.017; CIs overlap).

## IIT: n positives = 129, negatives = 4970, candidate-pool negatives = 1016

Positives by corpus part: {'candidate': 128, 'background': 1}. 1995-2015 test n = 17.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.910 [0.890, 0.928] | **0.764 [0.723, 0.803]** | 0.186 [0.116, 0.256] | 0.357 [0.271, 0.442] | 0.434 [0.349, 0.519] | 0.18 |
| 1995-2015 | V4 | 0.973 [0.953, 0.989] | **0.893 [0.823, 0.954]** | 0.412 | 0.588 | 0.706 | - |
| 2016-2025 | V5 | 0.812 [0.771, 0.849] | **0.755 [0.713, 0.794]** | 0.178 [0.109, 0.248] | 0.256 [0.178, 0.333] | 0.341 [0.256, 0.419] | 0.00 |
| 1995-2015 | V5 | 0.912 [0.816, 0.978] | **0.899 [0.806, 0.967]** | 0.353 | 0.471 | 0.529 | - |
| 2016-2025 | BM25 | 0.833 [0.794, 0.868] | **0.738 [0.692, 0.782]** | 0.217 [0.147, 0.287] | 0.287 [0.209, 0.364] | 0.349 [0.264, 0.426] | 0.06 |
| 1995-2015 | BM25 | 0.929 [0.872, 0.976] | **0.858 [0.757, 0.944]** | 0.412 | 0.471 | 0.706 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.010 | 0.020 | 0.040 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.129; CIs do NOT overlap); V5 dropped (-0.144; CIs do NOT overlap); BM25 dropped (-0.120; CIs overlap).

## Panpsychism: n positives = 61, negatives = 5261, candidate-pool negatives = 1306

Positives by corpus part: {'candidate': 61}. 1995-2015 test n = 7.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.923 [0.874, 0.960] | **0.832 [0.767, 0.885]** | 0.246 [0.148, 0.361] | 0.475 [0.344, 0.607] | 0.623 [0.492, 0.738] | 0.16 |
| 1995-2015 | V4 | 0.994 [0.988, 0.998] | **0.973 [0.946, 0.993]** | 0.571 | 0.857 | 1.000 | - |
| 2016-2025 | V5 | 0.902 [0.854, 0.940] | **0.866 [0.815, 0.909]** | 0.344 [0.230, 0.459] | 0.475 [0.344, 0.590] | 0.557 [0.426, 0.689] | 0.00 |
| 1995-2015 | V5 | 0.985 [0.978, 0.993] | **0.970 [0.956, 0.984]** | 0.143 | 0.571 | 0.857 | - |
| 2016-2025 | BM25 | 0.792 [0.714, 0.858] | **0.705 [0.619, 0.780]** | 0.131 [0.049, 0.213] | 0.262 [0.148, 0.377] | 0.361 [0.246, 0.492] | 0.06 |
| 1995-2015 | BM25 | 0.917 [0.783, 0.994] | **0.861 [0.659, 0.985]** | 0.571 | 0.571 | 0.571 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.010 | 0.019 | 0.038 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.141; CIs do NOT overlap); V5 dropped (-0.104; CIs do NOT overlap); BM25 dropped (-0.156; CIs overlap).

## PP: n positives = 151, negatives = 4832, candidate-pool negatives = 881

Positives by corpus part: {'candidate': 151}. 1995-2015 test n = 99.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.869 [0.842, 0.896] | **0.678 [0.633, 0.725]** | 0.192 [0.126, 0.258] | 0.291 [0.218, 0.364] | 0.377 [0.298, 0.457] | 0.06 |
| 1995-2015 | V4 | 0.944 [0.929, 0.958] | **0.760 [0.713, 0.806]** | 0.364 | 0.414 | 0.525 | - |
| 2016-2025 | V5 | 0.774 [0.733, 0.815] | **0.835 [0.800, 0.869]** | 0.166 [0.106, 0.225] | 0.225 [0.159, 0.298] | 0.338 [0.258, 0.411] | 0.00 |
| 1995-2015 | V5 | 0.844 [0.794, 0.891] | **0.874 [0.833, 0.913]** | 0.152 | 0.242 | 0.343 | - |
| 2016-2025 | BM25 | 0.820 [0.780, 0.858] | **0.720 [0.675, 0.767]** | 0.258 [0.192, 0.325] | 0.325 [0.252, 0.397] | 0.404 [0.325, 0.483] | 0.04 |
| 1995-2015 | BM25 | 0.869 [0.829, 0.906] | **0.660 [0.603, 0.717]** | 0.253 | 0.374 | 0.434 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.010 | 0.021 | 0.041 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.082; CIs overlap); V5 dropped (-0.039; CIs overlap); BM25 rose (+0.060; CIs overlap).

# EXCLUDING 2020-2022 (sensitivity check)

## Champagne: n positives = 18 **(n < 20: exploratory)**, negatives = 3606, candidate-pool negatives = 934

Positives by corpus part: {'candidate': 18}. 1995-2015 test n = 3.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.899 [0.835, 0.949] | **0.754 [0.629, 0.861]** | 0.278 [0.111, 0.500] | 0.444 [0.222, 0.667] | 0.500 [0.278, 0.722] | 0.18 |
| 1995-2015 | V4 | 0.981 [0.960, 0.997] | **0.915 [0.823, 0.987]** | 0.333 | 0.333 | 0.667 | - |
| 2016-2025 | V5 | 0.837 [0.718, 0.935] | **0.845 [0.742, 0.930]** | 0.333 [0.111, 0.556] | 0.389 [0.167, 0.611] | 0.556 [0.333, 0.778] | 0.00 |
| 1995-2015 | V5 | 0.977 [0.944, 1.000] | **0.966 [0.927, 0.998]** | 0.333 | 0.667 | 0.667 | - |
| 2016-2025 | BM25 | 0.758 [0.628, 0.874] | **0.660 [0.517, 0.797]** | 0.222 [0.056, 0.444] | 0.222 [0.056, 0.444] | 0.278 [0.111, 0.500] | 0.06 |
| 1995-2015 | BM25 | 0.838 [0.706, 0.983] | **0.705 [0.491, 0.948]** | 0.000 | 0.000 | 0.333 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.014 | 0.028 | 0.055 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.161; CIs overlap); V5 dropped (-0.121; CIs overlap); BM25 dropped (-0.045; CIs overlap).

## GWT: n positives = 143, negatives = 3288, candidate-pool negatives = 616

Positives by corpus part: {'candidate': 143}. 1995-2015 test n = 77.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.880 [0.854, 0.903] | **0.745 [0.700, 0.786]** | 0.231 [0.161, 0.301] | 0.350 [0.273, 0.427] | 0.503 [0.420, 0.587] | 0.06 |
| 1995-2015 | V4 | 0.912 [0.888, 0.937] | **0.809 [0.758, 0.861]** | 0.208 | 0.286 | 0.455 | - |
| 2016-2025 | V5 | 0.603 [0.550, 0.655] | **0.705 [0.660, 0.749]** | 0.042 [0.014, 0.077] | 0.070 [0.028, 0.119] | 0.126 [0.077, 0.189] | 0.00 |
| 1995-2015 | V5 | 0.592 [0.520, 0.662] | **0.711 [0.646, 0.775]** | 0.013 | 0.013 | 0.039 | - |
| 2016-2025 | BM25 | 0.771 [0.730, 0.809] | **0.691 [0.644, 0.737]** | 0.077 [0.035, 0.119] | 0.168 [0.112, 0.231] | 0.273 [0.203, 0.350] | 0.00 |
| 1995-2015 | BM25 | 0.779 [0.731, 0.825] | **0.673 [0.610, 0.736]** | 0.091 | 0.117 | 0.156 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.015 | 0.030 | 0.061 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.064; CIs overlap); V5 held (-0.006; CIs overlap); BM25 held (+0.018; CIs overlap).

## IIT: n positives = 87, negatives = 3327, candidate-pool negatives = 655

Positives by corpus part: {'candidate': 87}. 1995-2015 test n = 17.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.908 [0.883, 0.930] | **0.762 [0.711, 0.811]** | 0.345 [0.241, 0.448] | 0.391 [0.287, 0.494] | 0.552 [0.448, 0.655] | 0.28 |
| 1995-2015 | V4 | 0.973 [0.953, 0.989] | **0.893 [0.823, 0.954]** | 0.412 | 0.588 | 0.706 | - |
| 2016-2025 | V5 | 0.791 [0.739, 0.842] | **0.738 [0.685, 0.790]** | 0.241 [0.149, 0.333] | 0.299 [0.207, 0.402] | 0.402 [0.299, 0.506] | 0.00 |
| 1995-2015 | V5 | 0.912 [0.816, 0.978] | **0.899 [0.806, 0.967]** | 0.353 | 0.471 | 0.529 | - |
| 2016-2025 | BM25 | 0.825 [0.775, 0.873] | **0.736 [0.677, 0.793]** | 0.264 [0.184, 0.356] | 0.322 [0.218, 0.425] | 0.414 [0.310, 0.517] | 0.08 |
| 1995-2015 | BM25 | 0.929 [0.872, 0.976] | **0.858 [0.757, 0.944]** | 0.412 | 0.471 | 0.706 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.015 | 0.030 | 0.060 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.131; CIs do NOT overlap); V5 dropped (-0.161; CIs do NOT overlap); BM25 dropped (-0.122; CIs overlap).

## Panpsychism: n positives = 33, negatives = 3531, candidate-pool negatives = 859

Positives by corpus part: {'candidate': 33}. 1995-2015 test n = 7.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.909 [0.843, 0.964] | **0.812 [0.727, 0.886]** | 0.273 [0.121, 0.424] | 0.424 [0.273, 0.606] | 0.727 [0.576, 0.879] | 0.28 |
| 1995-2015 | V4 | 0.994 [0.988, 0.998] | **0.973 [0.946, 0.993]** | 0.571 | 0.857 | 1.000 | - |
| 2016-2025 | V5 | 0.920 [0.875, 0.958] | **0.890 [0.836, 0.937]** | 0.424 [0.273, 0.606] | 0.545 [0.364, 0.727] | 0.576 [0.394, 0.727] | 0.00 |
| 1995-2015 | V5 | 0.985 [0.978, 0.993] | **0.970 [0.956, 0.984]** | 0.143 | 0.571 | 0.857 | - |
| 2016-2025 | BM25 | 0.830 [0.741, 0.909] | **0.750 [0.652, 0.838]** | 0.152 [0.030, 0.273] | 0.273 [0.121, 0.424] | 0.515 [0.333, 0.697] | 0.08 |
| 1995-2015 | BM25 | 0.917 [0.783, 0.994] | **0.861 [0.659, 0.985]** | 0.571 | 0.571 | 0.571 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.014 | 0.028 | 0.057 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.161; CIs do NOT overlap); V5 dropped (-0.080; CIs do NOT overlap); BM25 dropped (-0.111; CIs overlap).

## PP: n positives = 98, negatives = 3236, candidate-pool negatives = 565

Positives by corpus part: {'candidate': 98}. 1995-2015 test n = 99.

| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|---|
| 2016-2025 | V4 (selected) | 0.855 [0.819, 0.888] | **0.647 [0.590, 0.706]** | 0.194 [0.122, 0.276] | 0.286 [0.204, 0.378] | 0.408 [0.316, 0.510] | 0.10 |
| 1995-2015 | V4 | 0.944 [0.929, 0.958] | **0.760 [0.713, 0.806]** | 0.364 | 0.414 | 0.525 | - |
| 2016-2025 | V5 | 0.777 [0.728, 0.825] | **0.837 [0.795, 0.878]** | 0.194 [0.122, 0.265] | 0.245 [0.163, 0.337] | 0.378 [0.286, 0.469] | 0.00 |
| 1995-2015 | V5 | 0.844 [0.794, 0.891] | **0.874 [0.833, 0.913]** | 0.152 | 0.242 | 0.343 | - |
| 2016-2025 | BM25 | 0.810 [0.760, 0.857] | **0.710 [0.653, 0.764]** | 0.245 [0.163, 0.337] | 0.296 [0.214, 0.388] | 0.378 [0.286, 0.469] | 0.04 |
| 1995-2015 | BM25 | 0.869 [0.829, 0.906] | **0.660 [0.603, 0.717]** | 0.253 | 0.374 | 0.434 | - |
| *chance (2016-2025)* | | 0.500 | 0.500 | 0.015 | 0.031 | 0.062 | - |

Candidate-only AUC vs 1995-2015: V4 dropped (-0.113; CIs do NOT overlap); V5 dropped (-0.037; CIs overlap); BM25 rose (+0.050; CIs overlap).

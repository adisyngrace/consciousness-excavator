# Level 3 evaluation: TEST results (prompt 05, Step 4)

Pre-registered plan and amendment: `reports/eval_plan.md`. **The variant (V4) was selected on the dev halves and approved before this run; nothing on this page selects, tunes or changes a variant.**

**How to read the two AUC columns.** The all-negatives AUC is confounded by the corpus-part mix: positives come from the Level 2 silver set and are 99-100% candidate pool for GWT and predictive processing, while only 4-13% of negatives are. A variant that merely prefers theory-flavoured neuroscience/consciousness text gains on it. **The candidate-only AUC (negatives restricted to the candidate pool) is the more informative number.** Negatives are unlabeled, not known irrelevant, so every metric is a lower bound.

Hub rate and metric definitions as in `reports/level3_eval_dev.md` (hub pools here use the test positives for GWT/PP); CIs are 2,000 bootstrap resamples of the positives (seed 20261011). n is shown in every table heading.

## Champagne (exploratory, small n; all positives): n positives = 3, negatives = 7780, candidate-pool negatives = 1000

Positives by corpus part (seed/cand/bg/rand): 0/3/0/0

| variant | AUC, all negatives [95% CI] | **AUC, candidate-pool negatives only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|
| V4 (selected) | 0.981 [0.960, 0.997] | **0.915 [0.823, 0.987]** | 0.333 [0.000, 1.000] | 0.333 [0.000, 1.000] | 0.667 [0.000, 1.000] | 0.18 |
| V0 | 0.986 [0.967, 0.998] | **0.939 [0.859, 0.991]** | 0.333 [0.000, 1.000] | 0.667 [0.000, 1.000] | 0.667 [0.000, 1.000] | 0.08 |
| V1 | 0.985 [0.978, 0.998] | **0.945 [0.918, 0.988]** | 0.333 [0.000, 1.000] | 0.333 [0.000, 1.000] | 1.000 [1.000, 1.000] | 0.04 |
| V2 | 0.990 [0.978, 0.998] | **0.977 [0.952, 0.993]** | 0.667 [0.000, 1.000] | 0.667 [0.000, 1.000] | 1.000 [1.000, 1.000] | 0.00 |
| V5 | 0.977 [0.944, 1.000] | **0.966 [0.927, 0.998]** | 0.333 [0.000, 1.000] | 0.667 [0.000, 1.000] | 0.667 [0.000, 1.000] | 0.00 |
| BM25 | 0.838 [0.706, 0.983] | **0.705 [0.491, 0.948]** | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.333 [0.000, 1.000] | 0.10 |
| *chance* | 0.500 | 0.500 | 0.006 | 0.013 | 0.026 | - |

_n = 3: confidence intervals are wide and the numbers are qualitative only._

## GWT (test half): n positives = 77, negatives = 7610, candidate-pool negatives = 831

Positives by corpus part (seed/cand/bg/rand): 0/77/0/0

| variant | AUC, all negatives [95% CI] | **AUC, candidate-pool negatives only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|
| V4 (selected) | 0.912 [0.888, 0.937] | **0.809 [0.758, 0.861]** | 0.208 [0.117, 0.299] | 0.286 [0.182, 0.390] | 0.455 [0.351, 0.571] | 0.06 |
| V0 | 0.899 [0.873, 0.923] | **0.798 [0.747, 0.847]** | 0.195 [0.104, 0.286] | 0.273 [0.169, 0.364] | 0.377 [0.273, 0.494] | 0.04 |
| V1 | 0.805 [0.769, 0.840] | **0.651 [0.586, 0.715]** | 0.078 [0.026, 0.143] | 0.130 [0.065, 0.208] | 0.169 [0.091, 0.260] | 0.00 |
| V2 | 0.612 [0.544, 0.679] | **0.722 [0.660, 0.783]** | 0.013 [0.000, 0.039] | 0.039 [0.000, 0.091] | 0.078 [0.026, 0.143] | 0.00 |
| V5 | 0.592 [0.520, 0.662] | **0.711 [0.646, 0.775]** | 0.013 [0.000, 0.039] | 0.013 [0.000, 0.039] | 0.039 [0.000, 0.091] | 0.00 |
| BM25 | 0.779 [0.731, 0.825] | **0.673 [0.610, 0.736]** | 0.091 [0.039, 0.156] | 0.117 [0.052, 0.195] | 0.156 [0.078, 0.247] | 0.04 |
| *chance* | 0.500 | 0.500 | 0.007 | 0.013 | 0.026 | - |

## IIT (exploratory, small n; all positives): n positives = 17, negatives = 7744, candidate-pool negatives = 968

Positives by corpus part (seed/cand/bg/rand): 1/14/2/0

| variant | AUC, all negatives [95% CI] | **AUC, candidate-pool negatives only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|
| V4 (selected) | 0.973 [0.953, 0.989] | **0.893 [0.823, 0.954]** | 0.412 [0.176, 0.647] | 0.588 [0.353, 0.824] | 0.706 [0.471, 0.882] | 0.24 |
| V0 | 0.976 [0.959, 0.990] | **0.903 [0.838, 0.959]** | 0.471 [0.235, 0.706] | 0.647 [0.412, 0.882] | 0.706 [0.471, 0.882] | 0.12 |
| V1 | 0.929 [0.874, 0.974] | **0.821 [0.705, 0.921]** | 0.412 [0.176, 0.647] | 0.471 [0.235, 0.706] | 0.588 [0.353, 0.824] | 0.08 |
| V2 | 0.908 [0.834, 0.968] | **0.906 [0.833, 0.966]** | 0.412 [0.176, 0.647] | 0.412 [0.176, 0.647] | 0.529 [0.294, 0.765] | 0.00 |
| V5 | 0.912 [0.816, 0.978] | **0.899 [0.806, 0.967]** | 0.353 [0.118, 0.588] | 0.471 [0.235, 0.706] | 0.529 [0.294, 0.765] | 0.00 |
| BM25 | 0.929 [0.872, 0.976] | **0.858 [0.757, 0.944]** | 0.412 [0.176, 0.647] | 0.471 [0.235, 0.706] | 0.706 [0.471, 0.882] | 0.10 |
| *chance* | 0.500 | 0.500 | 0.006 | 0.013 | 0.026 | - |

_n = 17: confidence intervals are wide and the numbers are qualitative only._

## Panpsychism (exploratory, small n; all positives): n positives = 7, negatives = 7766, candidate-pool negatives = 987

Positives by corpus part (seed/cand/bg/rand): 0/7/0/0

| variant | AUC, all negatives [95% CI] | **AUC, candidate-pool negatives only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|
| V4 (selected) | 0.994 [0.988, 0.998] | **0.973 [0.946, 0.993]** | 0.571 [0.286, 0.857] | 0.857 [0.571, 1.000] | 1.000 [1.000, 1.000] | 0.20 |
| V0 | 0.990 [0.985, 0.996] | **0.960 [0.937, 0.982]** | 0.429 [0.143, 0.714] | 0.571 [0.286, 0.857] | 1.000 [1.000, 1.000] | 0.10 |
| V1 | 0.983 [0.960, 0.996] | **0.947 [0.881, 0.987]** | 0.429 [0.143, 0.718] | 0.714 [0.429, 1.000] | 0.857 [0.571, 1.000] | 0.08 |
| V2 | 0.954 [0.929, 0.977] | **0.941 [0.911, 0.971]** | 0.143 [0.000, 0.429] | 0.286 [0.000, 0.571] | 0.286 [0.000, 0.571] | 0.00 |
| V5 | 0.985 [0.978, 0.993] | **0.970 [0.956, 0.984]** | 0.143 [0.000, 0.429] | 0.571 [0.143, 0.857] | 0.857 [0.571, 1.000] | 0.00 |
| BM25 | 0.917 [0.783, 0.994] | **0.861 [0.659, 0.985]** | 0.571 [0.143, 0.857] | 0.571 [0.143, 0.857] | 0.571 [0.143, 0.857] | 0.06 |
| *chance* | 0.500 | 0.500 | 0.006 | 0.013 | 0.026 | - |

_n = 7: confidence intervals are wide and the numbers are qualitative only._

## PP (test half): n positives = 99, negatives = 7048, candidate-pool negatives = 275

Positives by corpus part (seed/cand/bg/rand): 1/98/0/0

| variant | AUC, all negatives [95% CI] | **AUC, candidate-pool negatives only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |
|---|---|---|---|---|---|---|
| V4 (selected) | 0.944 [0.929, 0.958] | **0.760 [0.713, 0.806]** | 0.364 [0.273, 0.465] | 0.414 [0.313, 0.505] | 0.525 [0.424, 0.626] | 0.06 |
| V0 | 0.944 [0.928, 0.959] | **0.784 [0.741, 0.827]** | 0.364 [0.273, 0.465] | 0.434 [0.333, 0.525] | 0.525 [0.424, 0.626] | 0.02 |
| V1 | 0.923 [0.900, 0.943] | **0.854 [0.817, 0.888]** | 0.303 [0.212, 0.394] | 0.414 [0.323, 0.515] | 0.465 [0.364, 0.566] | 0.04 |
| V2 | 0.798 [0.750, 0.845] | **0.835 [0.794, 0.874]** | 0.101 [0.040, 0.162] | 0.182 [0.111, 0.263] | 0.253 [0.172, 0.343] | 0.00 |
| V5 | 0.844 [0.794, 0.891] | **0.874 [0.833, 0.913]** | 0.152 [0.081, 0.222] | 0.242 [0.162, 0.323] | 0.343 [0.253, 0.434] | 0.00 |
| BM25 | 0.869 [0.829, 0.906] | **0.660 [0.603, 0.717]** | 0.253 [0.172, 0.343] | 0.374 [0.273, 0.475] | 0.434 [0.333, 0.535] | 0.08 |
| *chance* | 0.500 | 0.500 | 0.007 | 0.014 | 0.028 | - |

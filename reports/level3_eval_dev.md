# Level 3 evaluation: DEV results (prompt 05, Step 3)

Pre-registered plan: `reports/eval_plan.md`. Test halves of GWT and PP were NOT read.

## Plain-language summary

- **The pre-registered rule selects V4** (equal component weights, no contrast): mean dev AUC 0.922, tied within 0.01 with V3 (0.921), and V4 has the lower hub rate (0.05 vs 0.09). V0 (0.911) is also close. The confidence intervals of V0, V3 and V4 overlap on both theories, so the data do not separate these three; the rule picked V4 on a nominal 0.002 lead plus the hub tie-break.
- **Every conceptual variant except V1b, V2 and V5 beats BM25** on all-negatives AUC (BM25 0.848 mean), but the margin is modest (GWT: V4 0.914 vs BM25 0.819; PP: V4 0.931 vs BM25 0.877). BM25 is a strong baseline here because the claims contain topic words ("workspace", "broadcast", "prediction") that survive masking.
- **The contrast variants hurt on this test.** Subtracting the generic-consciousness profile (V1, V1b) or the other theories (V2, V5) lowers AUC, to chance for GWT (V1b/V2/V5 about 0.45-0.51). This is partly built into the test: the masked positives are themselves consciousness papers, so any step that penalises "consciousness-like" text penalises them. The test therefore under-rewards the contrast variants' real purpose (damping generic drift); hub rate and hand labelling are the check for that.
- **Pool-composition caveat (your addition 2).** Positives come almost entirely from the theory-term candidate pool (99-100% for GWT and PP dev) while only 4-11% of negatives do. Restricted to candidate-pool negatives, AUCs drop sharply (V4: GWT 0.81, PP 0.73; V0: 0.78, 0.75) and the ranking of variants changes: for PP the contrast variants V5 (0.851), V2 (0.819) and V1 (0.809) are best and V4 is below V0/V3. So the all-negatives AUC rewards "looks like a neuroscience/consciousness paper" partly, and the selected V4 is not clearly best on the harder comparison. The selection rule is unchanged (it was pre-registered on all-negatives AUC); I flag the disagreement for your decision. V4 still beats BM25 on the candidate-only AUC for both theories.
- **Mask-artifact control (your addition 1): no sign of a deletion artifact.** Masked vs unmasked AUC differs by 0.00-0.02 and mean scores shift by at most 0.08 negative-pool SDs for every variant (BM25 0.08 on PP), so deletion costs almost nothing and the scores are not driven by the removed terms. Note this cuts both ways: it also means these positives are retrievable by their surrounding conceptual vocabulary.
- **Absolute recall is low** (V4 recall@100: GWT 0.26, PP 0.36 of 76/98 positives vs chance 0.013), because negatives are unlabeled and include many genuine neighbours. Use the comparison between variants, not the absolute values.
- **Hub rates are low for every variant** (0.00-0.12), so hubs are not the main problem under this definition. V1/V1b top-50s are dominated by off-topic complexity/biology papers (cytoskeleton, gene expression, stem-cell niche), which is the other side of the contrast: removing generic consciousness text lets generic-sounding abstractions through.


## Selection rule applied

Mean dev AUC (GWT, PP): V0 0.911, V1 0.841, V1b 0.620, V2 0.644, V3 0.921, V4 0.922, V5 0.662, BM25 0.848.

Best non-baseline: **V4**; within 0.01 of it (tied): V3, V4; mean hub rates of the tied: V3 0.09, V4 0.05. **Rule selects: V4.**

BM25 loses to / beats each variant on dev AUC (GWT, PP): V0: beats BM25; V1: mixed; V1b: loses to BM25; V2: loses to BM25; V3: beats BM25; V4: beats BM25; V5: loses to BM25.

## Notes on the metrics

- AUC is the probability that a masked positive outscores a random negative; with negatives only, mean percentile rank equals 100 x AUC, so the two columns carry the same information (both kept as pre-registered).
- Recall@k: share of positives whose rank among the negatives (1 + number of negatives scoring higher) is <= k. Chance = k / n_neg.
- Negatives are *unlabeled*, not known irrelevant: genuine conceptual neighbours are scored as errors, so every number is a lower bound and the comparison between variants matters more than the absolute values.
- 95% CIs: 2,000 bootstrap resamples of the positives (negatives fixed), seed 20261011.
- Hub rate: share of the variant's top 50 for the theory that is also in the top 50 of >= 2 other theories (each theory's top 50 drawn from its own pool: eligible negatives + eval positives; GWT/PP use dev positives only; the other three use all their positives).

## Corpus-part mix of positives and negatives (1995-2015)

| theory | n pos | pos seed/cand/bg/rand | n neg | neg seed/cand/bg/rand | pos cand % | neg cand % |
|---|---|---|---|---|---|---|
| Champagne | 3 | 0/3/0/0 | 7780 | 3/1000/4880/1897 | 100% | 13% |
| GWT (dev) | 76 | 0/75/1/0 | 7610 | 3/831/4879/1897 | 99% | 11% |
| IIT | 17 | 1/14/2/0 | 7744 | 1/968/4878/1897 | 82% | 12% |
| Panpsychism | 7 | 0/7/0/0 | 7766 | 2/987/4880/1897 | 100% | 13% |
| PP (dev) | 98 | 0/98/0/0 | 7048 | 2/275/4874/1897 | 100% | 4% |

Positives are drawn from the Level 2 silver set, so they over-represent the theory-term candidate pool; a variant that merely prefers candidate-pool papers gains an advantage on the all-negatives AUC. The candidate-only AUC below removes that.

## GWT dev (n positives = 76, n negatives = 7610; candidate-pool negatives = 831)

| variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | mean pct rank [95% CI] | AUC vs candidate negatives only | hub rate |
|---|---|---|---|---|---|---|---|
| V0 | 0.892 [0.867, 0.914] | 0.105 [0.039, 0.171] | 0.158 [0.079, 0.237] | 0.224 [0.132, 0.316] | 89.2 [86.7, 91.4] | 0.781 [0.729, 0.827] | 0.04 |
| V1 | 0.784 [0.743, 0.820] | 0.039 [0.000, 0.092] | 0.039 [0.000, 0.092] | 0.079 [0.026, 0.145] | 78.4 [74.3, 82.0] | 0.625 [0.561, 0.688] | 0.00 |
| V1b | 0.453 [0.391, 0.517] | 0.000 [0.000, 0.000] | 0.013 [0.000, 0.039] | 0.013 [0.000, 0.039] | 45.3 [39.1, 51.7] | 0.431 [0.365, 0.501] | 0.00 |
| V2 | 0.512 [0.434, 0.586] | 0.000 [0.000, 0.000] | 0.013 [0.000, 0.039] | 0.066 [0.013, 0.132] | 51.2 [43.4, 58.6] | 0.619 [0.544, 0.688] | 0.00 |
| V3 | 0.896 [0.871, 0.921] | 0.158 [0.079, 0.237] | 0.237 [0.145, 0.329] | 0.368 [0.263, 0.474] | 89.6 [87.1, 92.1] | 0.790 [0.736, 0.842] | 0.06 |
| V4 | 0.914 [0.890, 0.936] | 0.184 [0.105, 0.263] | 0.276 [0.184, 0.368] | 0.329 [0.224, 0.434] | 91.4 [89.0, 93.6] | 0.810 [0.758, 0.858] | 0.04 |
| V5 | 0.509 [0.424, 0.585] | 0.000 [0.000, 0.000] | 0.013 [0.000, 0.039] | 0.092 [0.039, 0.158] | 50.9 [42.4, 58.5] | 0.621 [0.540, 0.692] | 0.00 |
| BM25 | 0.819 [0.775, 0.862] | 0.171 [0.092, 0.263] | 0.197 [0.118, 0.289] | 0.289 [0.197, 0.395] | 81.9 [77.5, 86.2] | 0.728 [0.668, 0.785] | 0.10 |
| *chance* | 0.500 | 0.007 | 0.013 | 0.026 | 50.0 | 0.500 | - |

## PP dev (n positives = 98, n negatives = 7048; candidate-pool negatives = 275)

| variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | mean pct rank [95% CI] | AUC vs candidate negatives only | hub rate |
|---|---|---|---|---|---|---|---|
| V0 | 0.930 [0.909, 0.948] | 0.265 [0.184, 0.347] | 0.367 [0.276, 0.459] | 0.459 [0.367, 0.551] | 93.0 [90.9, 94.8] | 0.747 [0.697, 0.793] | 0.02 |
| V1 | 0.899 [0.872, 0.922] | 0.194 [0.122, 0.266] | 0.286 [0.194, 0.378] | 0.378 [0.286, 0.469] | 89.9 [87.2, 92.2] | 0.807 [0.761, 0.850] | 0.04 |
| V1b | 0.786 [0.740, 0.830] | 0.122 [0.061, 0.194] | 0.143 [0.082, 0.214] | 0.214 [0.143, 0.296] | 78.6 [74.0, 83.0] | 0.775 [0.728, 0.819] | 0.04 |
| V2 | 0.776 [0.731, 0.818] | 0.133 [0.071, 0.204] | 0.153 [0.082, 0.224] | 0.255 [0.173, 0.347] | 77.6 [73.1, 81.8] | 0.819 [0.782, 0.853] | 0.00 |
| V3 | 0.945 [0.927, 0.961] | 0.347 [0.255, 0.439] | 0.449 [0.357, 0.541] | 0.582 [0.480, 0.673] | 94.5 [92.7, 96.1] | 0.762 [0.714, 0.807] | 0.12 |
| V4 | 0.931 [0.910, 0.948] | 0.265 [0.184, 0.347] | 0.357 [0.265, 0.449] | 0.469 [0.367, 0.571] | 93.1 [91.0, 94.8] | 0.723 [0.671, 0.772] | 0.06 |
| V5 | 0.816 [0.767, 0.860] | 0.194 [0.122, 0.276] | 0.235 [0.153, 0.327] | 0.388 [0.296, 0.480] | 81.6 [76.7, 86.0] | 0.851 [0.811, 0.886] | 0.00 |
| BM25 | 0.877 [0.841, 0.910] | 0.235 [0.153, 0.316] | 0.367 [0.276, 0.469] | 0.459 [0.367, 0.561] | 87.7 [84.1, 91.0] | 0.669 [0.617, 0.721] | 0.12 |
| *chance* | 0.500 | 0.007 | 0.014 | 0.028 | 50.0 | 0.500 | - |

## Mask-artifact control (dev positives): masked vs unmasked text

Same dev positives and same negatives; unmasked = original main-index chunks. Score columns are the variant's own units (mean over dev positives). `z-shift` expresses the masked-minus-unmasked mean score change in negative-pool SDs.

| theory | variant | AUC unmasked | AUC masked | mean score unmasked | mean score masked | z-shift (SD of negatives) |
|---|---|---|---|---|---|---|
| GWT | V0 | 0.897 | 0.892 | 2.173 | 2.162 | -0.01 |
| GWT | V1 | 0.792 | 0.784 | 1.204 | 1.182 | -0.04 |
| GWT | V1b | 0.463 | 0.453 | 0.397 | 0.374 | -0.04 |
| GWT | V2 | 0.521 | 0.512 | -0.319 | -0.333 | -0.03 |
| GWT | V3 | 0.901 | 0.896 | 1.971 | 1.959 | -0.01 |
| GWT | V4 | 0.924 | 0.914 | 2.346 | 2.283 | -0.06 |
| GWT | V5 | 0.519 | 0.509 | -0.244 | -0.260 | -0.04 |
| GWT | BM25 | 0.818 | 0.819 | 0.548 | 0.550 | +0.02 |
| PP | V0 | 0.934 | 0.930 | 2.952 | 2.931 | -0.02 |
| PP | V1 | 0.903 | 0.899 | 2.334 | 2.294 | -0.05 |
| PP | V1b | 0.800 | 0.786 | 1.810 | 1.749 | -0.08 |
| PP | V2 | 0.782 | 0.776 | 0.712 | 0.694 | -0.04 |
| PP | V3 | 0.949 | 0.945 | 2.561 | 2.535 | -0.03 |
| PP | V4 | 0.936 | 0.931 | 2.971 | 2.944 | -0.03 |
| PP | V5 | 0.828 | 0.816 | 0.563 | 0.540 | -0.07 |
| PP | BM25 | 0.894 | 0.877 | 0.548 | 0.538 | -0.08 |

## Most frequent hub papers (in the top 50 of several theories), per variant

**V0**: PMC3485814 (3 theories) Components of aesthetic experience: aesthetic fascination, a; PMC4158462 (3 theories) Conceptions about the mind-body problem and their relations ; PMC3790330 (3 theories) The evolutionary and genetic origins of consciousness in the; PMC331407 (3 theories) Measuring information integration; PMC3667233 (3 theories) Conscious Experience and Episodic Memory: Hippocampus at the; PMC4594572 (3 theories) The natural history of consciousness, and the question of wh; PMC3192380 (2 theories) What The Cognitive Neurosciences Mean To Me; PMC543470 (2 theories) An information integration theory of consciousness; PMC4271595 (2 theories) Multiscale Enaction Model (MEM): the case of complexity and ; PMC3914914 (2 theories) Mind and matter

**V1**: PMC3485814 (3 theories) Components of aesthetic experience: aesthetic fascination, a; PMC3985726 (3 theories) Emergent complexity of the cytoskeleton: from single filamen; PMC4465832 (3 theories) Emergent Self-Organized Criticality in Gene Expression Dynam; PMC3030540 (3 theories) A stem cell niche dominance theorem; PMC2713405 (2 theories) Qualia: The Geometry of Integrated Information; PMC3196211 (2 theories) Moments in Time; PMC4271595 (2 theories) Multiscale Enaction Model (MEM): the case of complexity and ; PMC4249989 (2 theories) Local shape of pictorial relief; PMC4270440 (2 theories) Evolution of Integrated Causal Structures in Animats Exposed; PMC3034721 (2 theories) Conceptualising population health: from mechanistic thinking

**V1b**: PMC3985726 (3 theories) Emergent complexity of the cytoskeleton: from single filamen; PMC4465832 (3 theories) Emergent Self-Organized Criticality in Gene Expression Dynam; PMC4553904 (3 theories) A Duet for one☆; PMC2713405 (2 theories) Qualia: The Geometry of Integrated Information; PMC4249989 (2 theories) Local shape of pictorial relief; PMC3376373 (2 theories) Phylogenetic Inference via Sequential Monte Carlo; PMC4311632 (2 theories) Two routes to actorhood: lexicalized potency to act and iden; PMC2698886 (2 theories) Evolution of resource cycling in ecosystems and individuals; PMC3687335 (2 theories) The autoregulation of a eukaryotic DNA transposon; PMC4661186 (2 theories) The Natural Emergence of (Bio)Semiosic Phenomena

**V2**: 

**V3**: PMC3790330 (5 theories) The evolutionary and genetic origins of consciousness in the; PMC4594572 (4 theories) The natural history of consciousness, and the question of wh; PMC4387919 (4 theories) What makes you think you are conscious? An agnosticist manif; PMC4037890 (3 theories) Medicine and Mind-Body Dualism: A Reply to Mehta's Critique; PMC4271595 (3 theories) Multiscale Enaction Model (MEM): the case of complexity and ; PMC3868016 (3 theories) The myth of cognitive agency: subpersonal thinking as a cycl; PMC4158462 (3 theories) Conceptions about the mind-body problem and their relations ; PMC2823620 (3 theories) Psychosomatic medicine and the philosophy of life; PMC2948146 (3 theories) Mind Operational Semantics and Brain Operational Architecton; PMC2713405 (3 theories) Qualia: The Geometry of Integrated Information

**V4**: PMC4594572 (4 theories) The natural history of consciousness, and the question of wh; PMC3485814 (3 theories) Components of aesthetic experience: aesthetic fascination, a; PMC2823620 (3 theories) Psychosomatic medicine and the philosophy of life; PMC3786226 (3 theories) The embodied transcendental: a Kantian perspective on neurop; PMC4661186 (3 theories) The Natural Emergence of (Bio)Semiosic Phenomena; PMC4369653 (3 theories) Neuromodulation and the mind-brain relation; PMC4158462 (3 theories) Conceptions about the mind-body problem and their relations ; PMC3185290 (3 theories) William James, Gustav Fechner, and Early Psychophysics; PMC331407 (3 theories) Measuring information integration; PMC3667233 (3 theories) Conscious Experience and Episodic Memory: Hippocampus at the

**V5**: PMC4088924 (2 theories) In your face: transcendence in embodied interaction

**BM25**: PMC3868016 (4 theories) The myth of cognitive agency: subpersonal thinking as a cycl; PMC3653222 (3 theories) A Commentary On De Sousa's “Towards An Integrative Theory Of; PMC3790330 (3 theories) The evolutionary and genetic origins of consciousness in the; PMC4037890 (3 theories) Medicine and Mind-Body Dualism: A Reply to Mehta's Critique; PMC543470 (3 theories) An information integration theory of consciousness; PMC4407481 (3 theories) The attention schema theory: a mechanistic account of subjec; PMC4122207 (3 theories) The biological function of consciousness; PMC4330879 (3 theories) Visual anticipation biases conscious decision making but not; PMC4594572 (3 theories) The natural history of consciousness, and the question of wh; PMC3192380 (2 theories) What The Cognitive Neurosciences Mean To Me

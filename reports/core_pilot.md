# CORE philosophy pilot: Champagne's semiotic account and panpsychism (prompt 09, Steps 3-5)

**Exploratory.** A separate corpus of CORE open-access papers (`source = core`, `section_quality = coarse`), pre-registered in `reports/eval_plan.md` (addenda of 2026-10-14 (a)-(d), committed before any CORE chunk was embedded or evaluated). Nothing here enters the PubMed Central tables, exports or app. Frozen and untouched: `terms.yaml`, profile claims, V4, the existing embeddings and reports. CORE-derived text is in gitignored `data/` only; this file contains titles, years, repositories, links, scores, claim ids and counts, no excerpts.

## Read this first

- **Champagne's full positive set is mostly general Peircean-semiotics papers, not consciousness work.** In the 10 hand-labelled sampled hits, 1 was about consciousness-related work (Y), 8 were Peirce's semiotics outside consciousness (P: rock art, gender studies, literature, anthropology, physics) and 1 was not a real use (N, "firstness" in a textbook). Claims about *consciousness-relevant neighbours* of the semiotic account therefore rest on the consciousness-relevant subset (set B), not on the full set A. Any Champagne result on set A measures retrieval of Peircean-semiotics literature in general.
- Panpsychism's sampled hits were 9 of 10 genuine (the one N is "combination problem" in a speech-recognition paper).
- **Positives come from the candidate pool**, and the pool is the term search itself, so candidate-pool AUC and the primary adjacent-background AUC both reward topical similarity to the theory's vocabulary region. Negatives are unlabeled, so every AUC is a lower bound.
- **The text is PDF-derived**, with page furniture, hyphenation breaks and mixed repository front matter (boilerplate stripped as pre-registered). z-score statistics, BM25 IDF and BM25 normalisation are computed on this CORE chunk set, not on the PubMed Central statistics, so numbers are not exactly comparable with the PMC runs.
- **Small n and a thin early period:** no candidates before 2000 and only 69 candidates in 1995-2015 against 160 in 2016-2025. The distractors are *approximately random within relevance-ordered hits*, not a uniform sample.
- CORE terms: free-licence conditions and the "machine processing only" statement apply; the licence field is unknown for every record (the API returns none).

## Step 3: chunking and embedding

78,278 chunks (3,396 abstract, 74,882 body) for 2,213 papers; no paper unchunked. Model bge-base-en-v1.5, normalised, separate shards in `data/embeddings_core/`. Self-retrieval test: Loading weights:   0%|          | 0/199 [00:00<?, ?it/s]
Loading weights: 100%|██████████| 199/199 [00:00<00:00, 6775.66it/s]
self-retrieval: True [(37317, 37317), (52332, 52332), (61232, 61232), (75067, 75067), (9077, 9077), (46475, 46475), (68111, 68111), (13331, 13331)]
shape (78278, 768) norms ok True.

## Hit labels and per-term precision (20 sampled direct-mention hits)

| theory | matched term | n | Y | P | N | precision Y | precision Y+P |
|---|---|---|---|---|---|---|---|
| Champagne | firstness | 2 | 0 | 1 | 1 | 0% | 50% |
| Champagne | peircean semiotics | 6 | 0 | 6 | 0 | 0% | 100% |
| Champagne | synechism | 2 | 1 | 1 | 0 | 50% | 100% |
| Panpsychism | combination problem | 1 | 0 | 0 | 1 | 0% | 0% |
| Panpsychism | panpsychism | 5 | 5 | 0 | 0 | 100% | 100% |
| Panpsychism | panpsychist | 3 | 3 | 0 | 0 | 100% | 100% |
| Panpsychism | panpsychists | 1 | 1 | 0 | 0 | 100% | 100% |
| **Champagne overall** | all | 10 | 1 | 8 | 1 | 10% | 90% |
| **Panpsychism overall** | all | 10 | 9 | 0 | 1 | 90% | 90% |

Per-term n is 1 to 6, so these are indications only. Demotion rule used for set C (below 80%: Y+P for Champagne, Y for panpsychism): Champagne "firstness", panpsychism "combination problem".

## Positive sets

| theory | A: all exclusive positives (ref. split) | B: consciousness-relevant subset | C: term-precision-trimmed |
|---|---|---|---|
| Champagne | 77 | 18 | 65 |
| Panpsychism | 89 | 80 | 83 |

Sets: A = exclusive silver papers with a reference split; B = A papers with consciousness vocabulary in title or abstract or at least 3 times overall; C = A papers with a hit from a non-demoted term. A set below 20 papers is exploratory. The previously drafted "primary" subset is dropped.

Sets with n < 20 (exploratory, qualitative only): Champagne B.

### Counts by period and repository (candidates and positives)

**Champagne**

| group | n | 1995-2015 | 2016-2025 | top repositories (n) |
|---|---|---|---|---|
| candidate pool | 99 | 34 | 65 | Journals from University of Tartu 9; PhilPapers 7; Crossref 6; Research Repository 4; AIR Universita degli studi di Milano 3; E-Jurnal UIN (Universitas Islam Negeri) Alauddin Makassar 2 |
| set A | 77 | 22 | 55 | Journals from University of Tartu 9; PhilPapers 5; Crossref 4; AIR Universita degli studi di Milano 3; Research Repository 3; Neliti 2 |
| set B | 18 | 5 | 13 | AIR Universita degli studi di Milano 3; Journals from University of Tartu 2; PhilPapers 2; RIUCV (Univ. Católica de Valencia) 2; VBN (Videnbasen)  Aalborg Universitets forskningsportal 1; Akademicka Platforma Czasopism 1 |
| set C | 65 | 19 | 46 | Journals from University of Tartu 8; PhilPapers 5; AIR Universita degli studi di Milano 3; Research Repository 3; Crossref 3; Neliti 2 |

**Panpsychism**

| group | n | 1995-2015 | 2016-2025 | top repositories (n) |
|---|---|---|---|---|
| candidate pool | 130 | 35 | 95 | PhilPapers 37; Crossref 8; arXiv.org e-Print Archive 7; California Institute of Integral Studies libraries 5; PhilSci Archive 4; University of St Andrews Research Portal 2 |
| set A | 89 | 18 | 71 | PhilPapers 28; California Institute of Integral Studies libraries 5; Crossref 3; arXiv.org e-Print Archive 3; PhilSci Archive 3; UCL Discovery 2 |
| set B | 80 | 14 | 66 | PhilPapers 27; California Institute of Integral Studies libraries 5; Crossref 3; PhilSci Archive 3; UCL Discovery 2; Hrčak - Portal of scientific journals of Croatia 2 |
| set C | 83 | 16 | 67 | PhilPapers 27; California Institute of Integral Studies libraries 5; Crossref 3; PhilSci Archive 3; UCL Discovery 2; Hrčak - Portal of scientific journals of Croatia 2 |

## Step 4: masked-positive retrieval

Positives are masked with the Level 2 term list and landmark authors (deletion masking, leak check run; any leak would be listed in the masking log), then re-embedded. Negatives: CORE papers with `names_theory_loosely = 0` for the theory. **Primary metric: AUC against adjacent-background negatives.** Also shown: candidate-pool negatives (CORE hits that do not name the theory), all negatives, distractors only (easy). Recall@k is the share of positives ranked within the top k of positives plus the stated negatives; chance recall is shown.

### Champagne, A: all exclusive positives (ref. split): n positives = 77

| negatives | n neg | variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | chance r@50/100/200 |
|---|---|---|---|---|---|---|---|
| adjacent-background (primary) | 1488 | V4 | 0.793 [0.729, 0.849] | 0.44 | 0.53 | 0.61 | 0.034/0.067/0.134 |
| adjacent-background (primary) | 1488 | BM25 | 0.598 [0.534, 0.660] | 0.10 | 0.13 | 0.26 | 0.034/0.067/0.134 |
| candidate-pool | 136 | V4 | 0.727 [0.644, 0.804] | 0.70 | 0.79 | 1.00 | 0.368/0.735/1.000 |
| candidate-pool | 136 | BM25 | 0.479 [0.406, 0.551] | 0.38 | 0.68 | 1.00 | 0.368/0.735/1.000 |
| all negatives | 2120 | V4 | 0.823 [0.765, 0.872] | 0.43 | 0.52 | 0.60 | 0.024/0.047/0.094 |
| all negatives | 2120 | BM25 | 0.644 [0.583, 0.702] | 0.09 | 0.12 | 0.25 | 0.024/0.047/0.094 |
| distractors only | 496 | V4 | 0.938 [0.903, 0.967] | 0.86 | 0.88 | 0.96 | 0.101/0.202/0.403 |
| distractors only | 496 | BM25 | 0.827 [0.774, 0.871] | 0.52 | 0.70 | 0.86 | 0.101/0.202/0.403 |

*Year-matched sensitivity check* (negatives re-weighted to the set's year distribution over bins 1995-2009, 2010-2015, 2016-2019, 2020-2025; beside, not instead of, the table above):

| negatives | variant | unweighted AUC | year-matched AUC [95% CI] | effective n of weighted negatives |
|---|---|---|---|---|
| adjacent-background (primary) | V4 | 0.793 | 0.756 [0.683, 0.820] | 850 of 1488 |
| adjacent-background (primary) | BM25 | 0.598 | 0.567 [0.501, 0.632] | 850 of 1488 |
| candidate-pool | V4 | 0.727 | 0.727 [0.645, 0.804] | 133 of 136 |
| candidate-pool | BM25 | 0.479 | 0.480 [0.407, 0.552] | 133 of 136 |
| all negatives | V4 | 0.823 | 0.795 [0.731, 0.851] | 1291 of 2120 |
| all negatives | BM25 | 0.644 | 0.619 [0.557, 0.679] | 1291 of 2120 |

### Champagne, B: consciousness-relevant subset: n positives = 18 **(n < 20: exploratory)**

| negatives | n neg | variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | chance r@50/100/200 |
|---|---|---|---|---|---|---|---|
| adjacent-background (primary) | 1488 | V4 | 0.863 [0.793, 0.929] | 0.39 | 0.44 | 0.56 | 0.034/0.067/0.134 |
| adjacent-background (primary) | 1488 | BM25 | 0.725 [0.604, 0.835] | 0.28 | 0.28 | 0.44 | 0.034/0.067/0.134 |
| candidate-pool | 136 | V4 | 0.803 [0.687, 0.906] | 0.78 | 0.94 | 1.00 | 0.368/0.735/1.000 |
| candidate-pool | 136 | BM25 | 0.623 [0.472, 0.769] | 0.56 | 0.83 | 1.00 | 0.368/0.735/1.000 |
| all negatives | 2120 | V4 | 0.888 [0.830, 0.943] | 0.39 | 0.44 | 0.56 | 0.024/0.047/0.094 |
| all negatives | 2120 | BM25 | 0.761 [0.651, 0.860] | 0.22 | 0.28 | 0.44 | 0.024/0.047/0.094 |
| distractors only | 496 | V4 | 0.989 [0.982, 0.995] | 1.00 | 1.00 | 1.00 | 0.101/0.202/0.403 |
| distractors only | 496 | BM25 | 0.909 [0.833, 0.964] | 0.67 | 0.83 | 0.94 | 0.101/0.202/0.403 |

*Year-matched sensitivity check* (negatives re-weighted to the set's year distribution over bins 1995-2009, 2010-2015, 2016-2019, 2020-2025; beside, not instead of, the table above):

| negatives | variant | unweighted AUC | year-matched AUC [95% CI] | effective n of weighted negatives |
|---|---|---|---|---|
| adjacent-background (primary) | V4 | 0.863 | 0.825 [0.737, 0.909] | 821 of 1488 |
| adjacent-background (primary) | BM25 | 0.725 | 0.693 [0.565, 0.814] | 821 of 1488 |
| candidate-pool | V4 | 0.803 | 0.801 [0.684, 0.905] | 135 of 136 |
| candidate-pool | BM25 | 0.623 | 0.625 [0.474, 0.770] | 135 of 136 |
| all negatives | V4 | 0.888 | 0.860 [0.787, 0.928] | 1252 of 2120 |
| all negatives | BM25 | 0.761 | 0.736 [0.621, 0.843] | 1252 of 2120 |

### Champagne, C: term-precision-trimmed: n positives = 65

| negatives | n neg | variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | chance r@50/100/200 |
|---|---|---|---|---|---|---|---|
| adjacent-background (primary) | 1488 | V4 | 0.877 [0.830, 0.916] | 0.51 | 0.62 | 0.71 | 0.034/0.067/0.134 |
| adjacent-background (primary) | 1488 | BM25 | 0.642 [0.578, 0.704] | 0.12 | 0.15 | 0.29 | 0.034/0.067/0.134 |
| candidate-pool | 136 | V4 | 0.831 [0.761, 0.891] | 0.82 | 0.91 | 1.00 | 0.368/0.735/1.000 |
| candidate-pool | 136 | BM25 | 0.521 [0.443, 0.597] | 0.42 | 0.72 | 1.00 | 0.368/0.735/1.000 |
| all negatives | 2120 | V4 | 0.899 [0.860, 0.932] | 0.49 | 0.60 | 0.69 | 0.024/0.047/0.094 |
| all negatives | 2120 | BM25 | 0.687 [0.628, 0.743] | 0.11 | 0.14 | 0.29 | 0.024/0.047/0.094 |
| distractors only | 496 | V4 | 0.984 [0.972, 0.993] | 0.97 | 0.98 | 1.00 | 0.101/0.202/0.403 |
| distractors only | 496 | BM25 | 0.867 [0.822, 0.905] | 0.57 | 0.75 | 0.92 | 0.101/0.202/0.403 |

*Year-matched sensitivity check* (negatives re-weighted to the set's year distribution over bins 1995-2009, 2010-2015, 2016-2019, 2020-2025; beside, not instead of, the table above):

| negatives | variant | unweighted AUC | year-matched AUC [95% CI] | effective n of weighted negatives |
|---|---|---|---|---|
| adjacent-background (primary) | V4 | 0.877 | 0.848 [0.792, 0.896] | 856 of 1488 |
| adjacent-background (primary) | BM25 | 0.642 | 0.609 [0.542, 0.674] | 856 of 1488 |
| candidate-pool | V4 | 0.831 | 0.831 [0.761, 0.891] | 134 of 136 |
| candidate-pool | BM25 | 0.521 | 0.522 [0.444, 0.598] | 134 of 136 |
| all negatives | V4 | 0.899 | 0.878 [0.831, 0.917] | 1299 of 2120 |
| all negatives | BM25 | 0.687 | 0.660 [0.599, 0.720] | 1299 of 2120 |

### Panpsychism, A: all exclusive positives (ref. split): n positives = 89

| negatives | n neg | variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | chance r@50/100/200 |
|---|---|---|---|---|---|---|---|
| adjacent-background (primary) | 1488 | V4 | 0.877 [0.833, 0.915] | 0.48 | 0.62 | 0.76 | 0.034/0.067/0.134 |
| adjacent-background (primary) | 1488 | BM25 | 0.831 [0.776, 0.881] | 0.45 | 0.53 | 0.71 | 0.034/0.067/0.134 |
| candidate-pool | 112 | V4 | 0.888 [0.846, 0.925] | 0.92 | 0.99 | 1.00 | 0.446/0.893/1.000 |
| candidate-pool | 112 | BM25 | 0.862 [0.811, 0.908] | 0.85 | 1.00 | 1.00 | 0.446/0.893/1.000 |
| all negatives | 2096 | V4 | 0.900 [0.863, 0.932] | 0.46 | 0.58 | 0.75 | 0.024/0.048/0.095 |
| all negatives | 2096 | BM25 | 0.854 [0.804, 0.898] | 0.45 | 0.49 | 0.71 | 0.024/0.048/0.095 |
| distractors only | 496 | V4 | 0.973 [0.950, 0.990] | 0.93 | 0.97 | 0.99 | 0.101/0.202/0.403 |
| distractors only | 496 | BM25 | 0.919 [0.881, 0.952] | 0.80 | 0.85 | 0.92 | 0.101/0.202/0.403 |

*Year-matched sensitivity check* (negatives re-weighted to the set's year distribution over bins 1995-2009, 2010-2015, 2016-2019, 2020-2025; beside, not instead of, the table above):

| negatives | variant | unweighted AUC | year-matched AUC [95% CI] | effective n of weighted negatives |
|---|---|---|---|---|
| adjacent-background (primary) | V4 | 0.877 | 0.847 [0.796, 0.891] | 717 of 1488 |
| adjacent-background (primary) | BM25 | 0.831 | 0.813 [0.756, 0.866] | 717 of 1488 |
| candidate-pool | V4 | 0.888 | 0.891 [0.848, 0.928] | 95 of 112 |
| candidate-pool | BM25 | 0.862 | 0.861 [0.810, 0.907] | 95 of 112 |
| all negatives | V4 | 0.900 | 0.881 [0.838, 0.917] | 1056 of 2096 |
| all negatives | BM25 | 0.854 | 0.841 [0.789, 0.888] | 1056 of 2096 |

### Panpsychism, B: consciousness-relevant subset: n positives = 80

| negatives | n neg | variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | chance r@50/100/200 |
|---|---|---|---|---|---|---|---|
| adjacent-background (primary) | 1488 | V4 | 0.920 [0.893, 0.943] | 0.53 | 0.68 | 0.82 | 0.034/0.067/0.134 |
| adjacent-background (primary) | 1488 | BM25 | 0.874 [0.827, 0.914] | 0.50 | 0.59 | 0.76 | 0.034/0.067/0.134 |
| candidate-pool | 112 | V4 | 0.933 [0.912, 0.951] | 0.99 | 1.00 | 1.00 | 0.446/0.893/1.000 |
| candidate-pool | 112 | BM25 | 0.902 [0.858, 0.938] | 0.90 | 1.00 | 1.00 | 0.446/0.893/1.000 |
| all negatives | 2096 | V4 | 0.938 [0.917, 0.956] | 0.50 | 0.64 | 0.81 | 0.024/0.048/0.095 |
| all negatives | 2096 | BM25 | 0.893 [0.850, 0.929] | 0.50 | 0.55 | 0.76 | 0.024/0.048/0.095 |
| distractors only | 496 | V4 | 0.993 [0.990, 0.995] | 1.00 | 1.00 | 1.00 | 0.101/0.202/0.403 |
| distractors only | 496 | BM25 | 0.948 [0.918, 0.972] | 0.86 | 0.90 | 0.96 | 0.101/0.202/0.403 |

*Year-matched sensitivity check* (negatives re-weighted to the set's year distribution over bins 1995-2009, 2010-2015, 2016-2019, 2020-2025; beside, not instead of, the table above):

| negatives | variant | unweighted AUC | year-matched AUC [95% CI] | effective n of weighted negatives |
|---|---|---|---|---|
| adjacent-background (primary) | V4 | 0.920 | 0.894 [0.859, 0.924] | 681 of 1488 |
| adjacent-background (primary) | BM25 | 0.874 | 0.857 [0.807, 0.901] | 681 of 1488 |
| candidate-pool | V4 | 0.933 | 0.935 [0.914, 0.953] | 91 of 112 |
| candidate-pool | BM25 | 0.902 | 0.900 [0.857, 0.938] | 91 of 112 |
| all negatives | V4 | 0.938 | 0.921 [0.895, 0.943] | 1004 of 2096 |
| all negatives | BM25 | 0.893 | 0.881 [0.836, 0.919] | 1004 of 2096 |

### Panpsychism, C: term-precision-trimmed: n positives = 83

| negatives | n neg | variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | chance r@50/100/200 |
|---|---|---|---|---|---|---|---|
| adjacent-background (primary) | 1488 | V4 | 0.914 [0.884, 0.941] | 0.52 | 0.66 | 0.81 | 0.034/0.067/0.134 |
| adjacent-background (primary) | 1488 | BM25 | 0.864 [0.819, 0.909] | 0.48 | 0.57 | 0.75 | 0.034/0.067/0.134 |
| candidate-pool | 112 | V4 | 0.927 [0.903, 0.948] | 0.98 | 1.00 | 1.00 | 0.446/0.893/1.000 |
| candidate-pool | 112 | BM25 | 0.893 [0.851, 0.933] | 0.89 | 1.00 | 1.00 | 0.446/0.893/1.000 |
| all negatives | 2096 | V4 | 0.933 [0.910, 0.954] | 0.49 | 0.63 | 0.80 | 0.024/0.048/0.095 |
| all negatives | 2096 | BM25 | 0.885 [0.844, 0.924] | 0.48 | 0.53 | 0.75 | 0.024/0.048/0.095 |
| distractors only | 496 | V4 | 0.992 [0.988, 0.995] | 0.99 | 1.00 | 1.00 | 0.101/0.202/0.403 |
| distractors only | 496 | BM25 | 0.944 [0.914, 0.970] | 0.84 | 0.89 | 0.96 | 0.101/0.202/0.403 |

*Year-matched sensitivity check* (negatives re-weighted to the set's year distribution over bins 1995-2009, 2010-2015, 2016-2019, 2020-2025; beside, not instead of, the table above):

| negatives | variant | unweighted AUC | year-matched AUC [95% CI] | effective n of weighted negatives |
|---|---|---|---|---|
| adjacent-background (primary) | V4 | 0.914 | 0.886 [0.848, 0.921] | 702 of 1488 |
| adjacent-background (primary) | BM25 | 0.864 | 0.846 [0.797, 0.894] | 702 of 1488 |
| candidate-pool | V4 | 0.927 | 0.931 [0.906, 0.952] | 92 of 112 |
| candidate-pool | BM25 | 0.893 | 0.892 [0.850, 0.933] | 92 of 112 |
| all negatives | V4 | 0.933 | 0.915 [0.887, 0.941] | 1033 of 2096 |
| all negatives | BM25 | 0.885 | 0.872 [0.829, 0.914] | 1033 of 2096 |

### Compared with the PubMed Central runs (same theories; candidate-pool-only AUC, V4 / BM25)

| theory | PMC 1995-2015 (n pos) | PMC 2016-2025 (n pos) | CORE set A, candidate-pool (n pos) | CORE set A, adjacent-background (primary) |
|---|---|---|---|---|
| Champagne | 0.915 / 0.705 (n 3) | 0.732 / 0.695 (n 25) | 0.727 / 0.479 (n 77) | 0.793 / 0.598 |
| Panpsychism | 0.973 / 0.861 (n 7) | 0.832 / 0.705 (n 61) | 0.888 / 0.862 (n 89) | 0.877 / 0.831 |

PMC and CORE differ in text type, negative pools and z-score basis; read as indicative only.

### 2 x 2 discriminability (V4, set A positives)

Entry = mean percentile rank (100 = best, chance 50) of the column theory's masked positives among its negatives, scored by the ROW profile. The diagonal should be the larger value in each column.

Negatives: adjacent-background (primary)

| row profile \ column positives | Champagne (n=77) | Panpsychism (n=89) |
|---|---|---|
| **Champagne** | **79.3** | 69.4 |
| **Panpsychism** | 47.6 | **87.7** |

Negatives: all negatives

| row profile \ column positives | Champagne (n=77) | Panpsychism (n=89) |
|---|---|---|
| **Champagne** | **82.3** | 73.8 |
| **Panpsychism** | 53.6 | **90.0** |

Overlap rate (two-theory version of the hub rate): share of a theory's top 50 unmasked papers (naming neither theory) that also appear in the other theory's top 50: Champagne 0.04, panpsychism 0.04.

## Step 5: top 30 per theory under V4, papers that do not name the theory (`names_theory_loosely = 0`)

The lists of CORE titles, links and ids are withheld from the public release pending CORE's response on licensing. Aggregate scores are in `results/philosophy_pilot_metrics.csv`.

## Near-duplicate records

Near-duplicates (same normalized title and year, or normalized-title similarity above 0.9; titles under 8 characters ignored): **22 pairs** (18 with identical normalized titles in different years or repositories), involving 38 papers; collapsing to one record per cluster would remove 20 of 2213 papers (**0.9%**). Records with the same title and year were already removed at build time (`dup_within_core`, 2,762 dropped). The rate is below the 2% threshold, so the primary metric was **not** rerun; the top-30 lists below and the exported files are collapsed to one record per cluster (the best-ranked is kept; lists are filled to 30 unique). The blind packets in `data/judge_core/` were built before this collapse and are on hold, untouched.

Observations on the withheld lists: lists withheld from the public release.

## Caveats

- Positives are exclusive silver papers found through the same term list that defines the pool; mostly candidate-pool papers.
- Champagne set A is mostly general Peircean-semiotics literature (see the top of this file); set B has the consciousness-relevant papers, and its n is shown above.
- PDF-derived text, repository boilerplate (stripped by rule), mixed languages removed only by a stopword rule; reference lists were split off for 73% of papers (positives require a split).
- Different z-score and BM25 statistics from the PMC runs (the CORE statistics include the positives' unmasked chunks); small n; negatives are unlabeled (lower bounds).
- No judging was run. The blind packets (top 20 per theory) are in `data/judge_core/` and have not been read.
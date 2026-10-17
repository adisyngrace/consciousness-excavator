# Level 3 evaluation plan (pre-registered, prompt 05 Step 0)

Written 2026-10-11 BEFORE any variant has been run. No variant is added, dropped or re-parameterised after this point without the user's approval. Weights, lambda and profiles are the ones already in `profiles/` and `profiles/config.yaml`; nothing is tuned.

## Setup shared by all variants
- Corpus window 1995-2015, same chunks and bge-base embeddings as the first look (main embeddings untouched).
- **Positives** for theory T: silver-set papers (`direct_mention = 1` for T) that are direct mentions of T only (multi-theory papers excluded), with all T terms/author names masked (Step 1) and re-embedded. A masked positive's chunks replace its unmasked chunks.
- **Negatives** for T: every other paper with chunks and `names_theory_loosely = 0` for T. Negatives are "unlabeled", not "known irrelevant"; some are real conceptual neighbors, so all metrics are lower bounds and the comparison between variants matters more than absolute values.
- **z-score statistics** (per-component mean/SD) are frozen from the original unmasked 105,289-chunk matrix, so masking one theory's positives cannot shift the scale. Each theory's evaluation uses its own masked positives; other theories' positives stay unmasked when they appear as negatives (they carry `names_theory_loosely = 0` only if they do not name T).
- **Paper score** = best chunk score per paper unless a variant says otherwise. Ranking pool for T = T's positives + T's negatives.

## Variants
| ID | Definition |
|---|---|
| **V0** | Current method. Chunk score = max over T's components of weight x z (claims 1.0, description windows 0.5, seed abstracts 0.5). Paper = best chunk. Raw, no contrast. |
| **V1** | V0 chunk score minus 0.5 x z_generic (generic consciousness profile, max over its paragraphs). This is the current Level 3 score. |
| **V1b** | As V1 with lambda = 1.0. |
| **V2** | Other-theories contrast. Paper score for T (V0 paper score) minus the mean of the V0 paper scores for the other four theories. No generic term. |
| **V3** | Breadth aggregation. For each paper and each component of T, take the best chunk's weighted z (weight x z) in that paper; the paper's score is the mean of its top 3 distinct components. Weights as in V0. No contrast. |
| **V4** | V0 with all component weights = 1.0 (claims, windows, seeds equal). Raw. |
| **V5** | V2 and V3 combined: V3 paper score for T minus the mean of the V3 paper scores of the other four theories. |
| **BM25** | Okapi BM25 (k1 = 1.5, b = 0.75; stop-words removed, lowercased, no stemming) over the same chunks. Each claim text of T is a query; chunk score per claim = BM25; chunk score for T = max over claims of the score normalised by that claim's max over all chunks; paper = best chunk (aggregated as V0, claims only since BM25 on short window/seed text is not the baseline we want). The masked positive text is used for the positives. |

Notes: V1b/V2/V3/V4/V5 each change one thing relative to V0 (V5 is the pre-declared combination). The generic/other-theory contrasts use the same frozen z-scores. Components in V3 are those of T only (claims + windows + seeds); if T has fewer than 3 components, the mean is over those available (not expected).

## Metrics (primary)
- **AUC** of masked positives vs negatives (probability a random positive outscores a random negative; ties count half).
- **Recall@100**: share of positives ranked in the top 100 of the pool. Also reported: recall@50 and recall@200.
- **Mean percentile rank** of positives among negatives (100 = best; chance 50).
- 95% bootstrap CIs (2,000 resamples of positives, fixed seed 20261011, negatives held fixed), with n positives beside every number.
- **Chance:** AUC 0.5; recall@k = k / pool size (mean over positives); percentile 50.
- **Hub rate** (secondary, selection tie-break): share of a variant's top 50 papers for T (pool = T positives + negatives) that also appear in the top 50 of at least two other theories under the same variant. Lower is better; the 10 most frequent hub papers are listed.

## Selection rule (fixed in advance)
Choose the variant with the highest **mean AUC across the dev halves of GWT and predictive processing**. If two variants are within 0.01 mean AUC (point estimates), choose the one with the lower mean hub rate across those two dev sets. BM25 is a baseline and is not eligible for selection. If no variant exceeds BM25 on dev AUC for both theories, that is reported as the headline finding and I stop and ask before proceeding. The test halves are not touched until the user approves the selection (Step 4); IIT, panpsychism and Champagne are small-n, exploratory evaluation only and play no role in selection.

## Splits
GWT and PP exclusive silver sets split 50/50 by paper, seed 20261011, into dev and test. IIT, panpsychism and Champagne: all positives, exploratory.

---

## AMENDMENT 2026-10-11 (made AFTER seeing the dev results; selection unchanged)

V4 was approved by the user as the pre-registered selection. The following additions do not change any variant, the selection rule or the selection (no variant is added or removed):
1. **Test-half variants.** On the test halves of GWT and predictive processing, evaluate V4, V0, V1, V2, V5 and BM25 (this extends the original list "selected variant, V0, V1, BM25"). IIT, panpsychism and Champagne (all positives, exploratory) use the same six variants.
2. **Both AUCs side by side.** Every variant is reported with AUC against all negatives AND AUC against candidate-pool negatives only. The all-negatives AUC is confounded by the corpus-part mix (positives are 99-100% candidate pool vs 4-13% of negatives), so the candidate-only AUC is the more informative number.
3. **Masking examples re-shown** after the punctuation fix.
4. **No selection or change of variant on test results.**
5. **Step 5:** discriminability matrix for both V4 and V5.
6. **Step 6:** labeling sheet with a `variant` column and the paper's corpus part: top 10 per theory under V4 for IIT, panpsychism and Champagne; top 10 each under V4 and V5 for GWT and predictive processing (replaces the original "top 30 per theory"). A V4 top-20 report is also written.

---

## AMENDMENT 2026-10-12 (prompt 07, PRE-REGISTERED before any 2016-2025 paper is downloaded, embedded or scored)

**What this test is.** An **out-of-time generalization test**: does the frozen method (profiles, V4, V5, BM25, as built and selected on 1995-2015 data) still find masked theory papers published in 2016-2025? It is NOT a forecast from 1995-2015 knowledge: the profiles are written from the current LoC description text, which is not limited to pre-2016 work. This wording is used everywhere.

**Frozen, not touched:** `src/terms.yaml`, profile claims/windows/seeds, `profiles/config.yaml` (weights, lambda), the selected variant V4, the existing 1995-2015 embeddings, and the z-score statistics (per-component mean/SD from the original unmasked 105,289-chunk 1995-2015 matrix). 2016-2025 chunks are z-scored with those frozen statistics. Nothing is tuned, selected or re-chosen on this data.

**Variants:** V4 (selected), V5 (pre-declared contrast variant, evaluated because it is the other candidate for GWT/PP) and BM25 only. BM25 has no trained statistics; its IDF and per-claim max normalisation are computed over the 2016-2025 evaluation chunk set (same k1 = 1.5, b = 0.75, same preprocessing).

**Positives:** exclusive silver-set papers for 2016-2025 (`direct_mention = 1` for the theory only, frozen scanner), with theory terms and landmark authors masked exactly as in `src/eval/mask.py` (deletion masking), masked chunks re-embedded. **Negatives:** every other 2016-2025 paper with chunks and `names_theory_loosely = 0` for the theory. Negatives are unlabeled, so all metrics are lower bounds.

**Metrics (same as the 1995-2015 test):** AUC against all negatives; AUC against candidate-pool negatives only (the more informative number, because positives are almost all candidate-pool papers); recall@50/100/200; hub rate (top 50 of a theory also in the top 50 of at least two other theories); 95% bootstrap CIs (2,000 resamples of positives, negatives fixed, seed 20261011); n beside every number. Theories with fewer than 20 positives (and any with fewer than 5 exclusive silver papers) are exploratory, reported qualitatively. No dev/test split: nothing is selected on these data, so all positives are used once.

**Sensitivity check:** every metric is reported twice, with all years 2016-2025 and with 2020-2022 papers excluded from both positives and negatives. Reason: open-access volume jumps ~2.4x in 2020-2022 and post-2020 COVID-era papers (a large share of the random and the background pools, e.g. anesthesia, attention, phenomenology hits) are negatives of a different kind. Results are interpreted on both; a difference between the two is reported, not resolved in favour of either.

**Pool design (caps approved at the Step 0 checkpoint):** per-theory strong-term candidates capped at 400, conceptual background (same adjacent-topic queries and theory-phrase exclusion as 1995-2015) capped at 3,000, random neuroscience/psychology/medicine sample capped at 1,000 (equal per-year quota, fixed seeds). Sampling is random within caps, so silver-set sizes per theory are partly set by the caps.

**Reporting commitments:** performance is reported as held, dropped or rose relative to the 1995-2015 test, side by side, with negative results stated as they are.

## ADDENDUM 2026-10-12 (prompt 07; written and committed BEFORE any out-of-time result exists)

After the Step 2 checkpoint (exclusive silver sets for 2016-2025: Champagne 25, GWT 213, IIT 129, panpsychism 61, PP 151):
1. **Quantitative reporting** applies to every theory with at least 20 exclusive positives. All five now qualify (Champagne n = 25 is the smallest). n is shown beside every number. The earlier "exploratory below 20" rule stays for any theory that falls below 20 after the 2020-2022 exclusion; such a cell is flagged.
2. **Discriminability matrix for 2016-2025** for V4 and V5, against all negatives and against candidate-pool negatives only, in the same format as `reports/level3_discriminability.md` (own-theory profile vs the other four on each theory's masked positives).
3. **Caveats stated in the report:** (a) exclusive positives are single-theory papers; a large share of GWT and IIT papers name both theories (306 of 519 GWT and 333 of 462 IIT direct-mention papers are multi-theory) and are therefore not positives, so positives are not a random sample of each theory's literature; (b) positives come almost entirely from the capped candidate pool (400 per theory, random within the pool), so the candidate-only AUC is the more informative number and the all-negatives AUC is confounded by corpus-part mix; (c) the random background sample is week-clustered (random weekly FIRST_PDATE slices per year), not uniform; (d) Champagne's primary (title/abstract or >= 3 mentions) subset is only 8 papers.

---

## ADDENDUM 2026-10-14 (prompt 09, CORE philosophy pilot; PRE-REGISTERED before any CORE record is pulled into the project, embedded or scored)

**Status of this test: exploratory.** Separate corpus (`source = core`, `section_quality = coarse`), separate embeddings, exports and report. Nothing is merged into the PubMed Central tables or any existing result. Frozen and untouched: `src/terms.yaml`, profile claims/windows/seeds, `profiles/config.yaml`, V4, existing embeddings, existing reports and results files. Only Champagne's semiotic account and panpsychism are evaluated.

**Positives** for theory T: exclusive silver-set CORE papers (`direct_mention = 1` for T only, no other theory directly mentioned), found by the frozen scanner in coarse mode (body text vs trailing reference list only; no per-section tags), with T's terms and landmark authors masked exactly as in `src/eval/mask.py` (deletion), masked chunks re-embedded. **Negatives:** every other CORE paper with chunks and `names_theory_loosely = 0` for T. Negatives are unlabeled, so all metrics are lower bounds.

**Variants:** V4 (frozen) and BM25 only (k1 1.5, b 0.75, same preprocessing; IDF and per-claim max normalisation computed over the CORE chunk set). No other variant, no tuning, no selection.

**z-scores:** V4 needs per-component mean/SD. For this pilot they are computed on the CORE chunk set itself (the text type, PDF-derived, differs from PMC XML, so the PMC statistics are not appropriate); stated as such in the report. Profile components are the existing embedded ones.

**Metrics:** AUC against all negatives and against candidate-pool negatives only (the more informative number); recall@50, 100, 200; hub rate; 95% bootstrap CIs (2,000 resamples of positives, negatives fixed, seed 20261014); n beside every number. Theories with fewer than 20 positives are exploratory and reported qualitatively, whatever the numbers. A 2x2 discriminability check (Champagne profile vs panpsychism profile on each other's masked positives) is included.

**Pool design:** theory candidates (frozen strong terms; cap ~300 per theory), adjacent background (philosophy of mind / semiotics topics that do not name the theories; cap ~1,500), broad distractors (cap ~500, approximately random within relevance-ordered hits, labelled as such). English, 1995-2025. Dedup against the PMC corpus by DOI, then normalized title + year. Text rule: abstract plus at most 6,000 body words, trailing reference list removed by a heading rule, drop < 3,000 characters, OCR-garbage and non-English; every drop logged. Seeds fixed; no PDF download or parsing (only text CORE itself returns).

**Reporting commitments:** side by side with the PMC numbers for the same theories; negative results, including BM25 matching V4, are reported as they are. Caveats stated: positives come mostly from the candidate pool, PDF-derived text, different z-score basis, small n.

## ADDENDUM 2026-10-14 (b) (prompt 09; written and committed BEFORE any CORE evaluation runs)

1. **Primary metric: AUC of masked exclusive positives against adjacent-background negatives only** (the philosophy-of-mind / semiotics pool), because the broad-distractor negatives are easy. Also reported: AUC against candidate-pool negatives, and AUC against all negatives. n beside every number; same CIs, seed and recall@k as above. Distractors are described everywhere as "approximately random within relevance-ordered hits".
2. **CORE terms handling:** all CORE-derived text stays in gitignored `data/` and in terminal output. Tracked files (`reports/`, `results/`, `docs/`) contain only titles, years, repository names, CORE links, DOIs, scores, claim ids and counts: no excerpts, snippets or quotations. This replaces the 200-character snippet allowance in the prompt. Step 2 hit snippets are shown in the terminal only. The license field is "unknown" (the CORE API returns no license field), explained in `results/README.md`.
3. **No judging in this pilot session.** Judge packets are built under `data/judge_core/` only and are not read or judged.

## ADDENDUM 2026-10-14 (c) (prompt 09; written and committed BEFORE the CORE scan or any evaluation runs)

1. **Silver-set positives require a reference split.** A CORE paper can be a positive only if the heading rule split its reference list off (`ref_split = 1`). Papers without a split can serve as negatives only if they match no term of the theory (`names_theory_loosely = 0`); those that match are excluded from both positives and negatives. Silver-set sizes are reported with this rule applied; a theory with fewer than 20 exclusive positives is stated plainly as exploratory.
2. **Boilerplate stripping.** Lines repeated verbatim in at least 5 documents from the same repository, within the first 40 lines of the text, are removed from the cleaned text before scanning and chunking. Lines and papers affected are counted; 3 before/after examples are shown in the terminal only.
3. **Year-matched sensitivity analysis in Step 4,** labelled as a sensitivity check beside (not replacing) the pre-registered metrics: negatives subsampled or re-weighted to match the candidates' (positives') year distribution. The Step 4 report also gives candidate and positive counts by repository and by period (1995-2015 / 2016-2025).
4. Step 2 hit snippets are shown in the terminal only and written to no file.

## ADDENDUM 2026-10-14 (d) (prompt 09; written and committed BEFORE any CORE chunk is embedded or any CORE evaluation runs)

Hand labels of the 20 sampled direct-mention hits (10 per theory) were kept in `reports/core_pilot_labels.csv` in the working repo (withheld here pending CORE's response). Champagne labels are Y (about consciousness-related work), P (Peirce's semiotics outside consciousness) or N (not a real use); panpsychism labels are Y or N. Champagne: 1 Y, 8 P, 1 N of 10. Panpsychism: 9 Y, 1 N of 10.

**Three positive sets per theory** (all exclusive silver papers with a reference split; B and C are subsets of A and are fixed by rules written here, not by any retrieval score):
- **A, full set (pre-registered).** All exclusive positives with a reference split.
- **B, consciousness-relevant subset.** Papers in A whose title or abstract contains a consciousness-vocabulary word, or whose title + abstract + body contains at least 3 occurrences (words: conscious, consciousness, phenomenal, qualia, sentient/sentience, subjective experience, hard problem). Claims about consciousness-relevant neighbours rest on B.
- **C, term-precision-trimmed set.** Papers in A with at least one counted strong-term hit from a term that is not demoted. A term is demoted if its labelled precision (Y+P for Champagne, Y for panpsychism) is below 80% in the 20-item sample: Champagne "firstness" (1 of 2) and panpsychism "combination problem" (0 of 1). n per term is tiny; this follows the CLAUDE.md demotion rule and is a sensitivity check, not a re-tune of `terms.yaml` (frozen, unchanged).
Metrics for each set as in addendum (b). Primary metric stays AUC against adjacent-background negatives (all three sets). A set with fewer than 20 papers is exploratory.

**Year-matched sensitivity (addendum (c) item 3) method.** Negatives are re-weighted so that their year distribution (bins 1995-2009, 2010-2015, 2016-2019, 2020-2025) matches the positive set's; weighted percentile ranks, bootstrap over positives, weights fixed. Reported beside, not instead of, the unweighted metrics, with the effective n of the weighted negatives.

**Other fixed choices.** Hub rate with two theories cannot use the "two other theories" rule; it is reported as the share of a theory's top 50 unmasked non-naming papers that also appear in the other theory's top 50 (overlap rate). The "primary" subset column is dropped from all outputs. Titles are unescaped (HTML entities, literal `\uXXXX` sequences and tags). Chunking: abstract and body windows of 180 words with 30 overlap, abstract and body as the only two sections; z-score statistics, BM25 IDF and normalisation from the CORE chunk set; bootstrap seed 20261014. Top-30 lists and judge packets (top 20 per theory, V4, names_theory_loosely = 0, 10% repeats, blind, under `data/judge_core/` only, not read or judged here) follow in Step 5.

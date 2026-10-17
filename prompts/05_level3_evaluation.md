# Prompt 05: Level 3 evaluation (scoring variants, term-masked test, discriminability)

**How to run:** start a fresh Claude Code session in the repo root and type:
`Read CLAUDE.md and reports/STATUS.md, then read prompts/05_level3_evaluation.md and follow it step by step. Stop at every checkpoint.`

**Why this exists:** the first-look report showed generic drift (the same off-topic papers recurring across theories) and showed that the description windows and seed abstracts never affect rankings. Instead of tuning by eye, we choose the scoring method by measuring how well each variant retrieves known theory papers with their terms masked out. The choice is made on a development half of the data and reported on a held-out half.

**Your job:** approve the variant list (Step 0), approve the variant chosen on the dev set (Step 4), and later hand-label the labeling sheet.

---

Read CLAUDE.md, reports/STATUS.md and reports/level3_first_look.md first. Do not edit terms.yaml, the profile claims or the chunk embeddings unless I say so.

## Step 0: Pre-register the variants (before running anything)
Write `reports/eval_plan.md` listing exactly the scoring variants to compare, so that none is added after seeing results. Use these:
- **V0:** current method (max over components of weight times z; claims 1.0, windows 0.5, seeds 0.5), raw score.
- **V1:** V0 with the contrast against the generic consciousness profile, lambda 0.5 (the current Level 3 score).
- **V1b:** same with lambda 1.0.
- **V2:** other-theories contrast: score for theory T minus the mean score of the other four theories, per paper.
- **V3:** breadth aggregation: a paper's score for T is the mean of its top 3 components' best-chunk z-scores (components must be distinct), so a paper must match several claims, not one.
- **V4:** equal weights (claims, windows and seeds all 1.0), otherwise V0.
- **V5:** V2 and V3 combined.
- **BM25 baseline:** keyword retrieval over the same chunks using the claim texts as queries, aggregated to paper level the same way as V0. This is the "term search" baseline that conceptual retrieval has to beat.

Also state the primary metrics (AUC, recall@100 and mean percentile rank) and the selection rule (highest mean AUC on the dev sets of GWT and predictive processing, ties broken by lower hub rate, see Step 3).

**Checkpoint: show me eval_plan.md and wait for approval.**

## Step 1: Masked silver sets
- Positives are the silver-set papers (direct_mention = 1) that mention only that theory (exclude multi-theory papers). Use the 1995-2015 corpus.
- Write `src/eval/mask.py` that masks, in every chunk of a positive paper, every strong, abbreviation, close and weak term for that theory, plus that theory's landmark author surnames (including in-text citations such as "Dehaene and Naccache, 2001"). Replace with a neutral token. Test it on synthetic texts and show me 5 before/after examples.
- Re-chunk and re-embed only the masked positives (about 400 papers), with the same chunker and model, cached separately from the main embeddings.
- Negatives for each theory are all other eligible papers (names_theory_loosely = 0 for that theory). Note in the report that negatives are "unlabeled", not "known irrelevant": some are genuine conceptual neighbors, so every metric is a lower bound, and the comparison between variants matters more than absolute values.

## Step 2: Dev/test split
- For GWT and predictive processing, split the exclusive silver set 50/50 by paper with a fixed seed into dev and test. Do not look at test results until Step 4 is approved.
- IIT (about 17), panpsychism (about 7) and Champagne (3) are too small to split. Use all of their positives for evaluation only, with the variant chosen from GWT and predictive processing, and label them "exploratory, small n".

## Step 3: Run the variants on dev
For each variant and each of GWT and PP dev, compute AUC, recall@50, recall@100, recall@200 and mean percentile rank of the masked positives among the negatives, each with a 95% bootstrap confidence interval. Also compute:
- **Hub rate:** the share of a variant's top 50 papers (per theory) that also appear in the top 50 of at least two other theories. Lower is better. List the 10 most frequent hub papers.
- **Chance level** for each metric.
- Whether the BM25 baseline beats or loses to each variant.

Write the results to `reports/level3_eval_dev.md`, with a table of variants by metrics and a plain-language summary.

**Checkpoint: show me the dev results and which variant the pre-registered rule selects. Wait for my approval before touching the test half.**

## Step 4: Test results (only after approval)
Evaluate the selected variant, V0, V1 and BM25 on the test halves of GWT and PP, and on all positives of IIT, panpsychism and Champagne (exploratory). Report the same metrics with confidence intervals and the sample size n beside every number.

## Step 5: Discriminability matrix
For the selected variant, compute a 5x5 matrix: rows are profiles, columns are the five theories' masked positives, entries are the mean percentile rank of that column's positives under that row's profile (all positives, no split). The diagonal should be highest in each column. Report which theory pairs are confused, and mark low-n columns.

## Step 6: Labeling sheet and refreshed first look
- Regenerate the top 20 per theory under the selected variant into `reports/level3_top20.md` (title, year, best-matching claim, 200-character snippet, other theories named).
- Write `reports/labeling_sheet.csv` with the top 30 per theory: theory, pmcid, title, year, best claim id, score, snippet, and empty columns label (R = relevant conceptual neighbor, G = generic consciousness or neuroscience, O = off-topic) and note. I will label 20 per theory.
- Update `reports/STATUS.md` and commit.

## Constraints
- Pre-register: no variant is added after Step 0 without my approval.
- Never use the test half to choose anything.
- Fixed random seeds, cached, resumable, commit after each step.
- Do not edit terms.yaml, profile claims or the main chunk embeddings.
- If a step would take more than half a day, stop and propose a cut.
- Public data only.

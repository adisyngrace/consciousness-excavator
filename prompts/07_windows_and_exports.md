# Prompt 07: Time windows (2016-2025 corpus), out-of-time test, and app-ready exports

**How to run:** start a fresh Claude Code session in the repo root and type:
`Read CLAUDE.md and reports/STATUS.md, then read prompts/07_windows_and_exports.md and follow it step by step. Stop at every checkpoint.`

**What this does:**
1. Extends the corpus to 2016-2025 so the 1995-2020 and 1995-2025 windows exist.
2. Runs an **out-of-time test**: do the profiles and the selected scoring (V4), which were built and chosen using 1995-2015 data, still find masked theory papers published in 2016-2025?
3. Computes how each theory's neighborhood and mention rate change across the three windows.
4. Exports small, tracked result tables so the app (next prompt) needs no heavy models.

**Be honest about what the test is.** The concept profiles are written from the current LoC description text, which is not limited to papers before 2016. So this is an **out-of-time generalization test** (does the frozen method hold up on later literature?), not a literal forecast from 1995-2015 knowledge. Use that wording everywhere.

**Budget:** about one day, with the embedding job running in the background. If a Step 0 estimate exceeds 3 hours in total, use the smaller caps it offers.

---

Read CLAUDE.md, reports/STATUS.md, reports/eval_plan.md and reports/level3_eval_test.md first. Do not edit terms.yaml, the profile claims, the selected variant (V4) or the existing 1995-2015 embeddings. Nothing in this prompt may tune anything.

## Step 0: Plan and estimate (before downloading anything)
1. Check whether the Level 2 table of Europe PMC per-year term counts (term_counts_by_year or equivalent) exists. If it does not, plan to build it for 1995-2025 for each theory's strong terms, normalized per 10,000 open-access full-text papers that year.
2. Using Europe PMC server-side hit counts only, estimate for 2016-2025: the number of open-access full-text papers matching each theory's strong terms, and the size of the background pools. Propose caps that mirror the 1995-2015 design in smaller form: per-theory strong-term papers (cap about 400), a conceptual background pool (cap about 3,000, same adjacent topic queries as before) and a random background sample (cap about 1,000).
3. Estimate chunk count and embedding time with bge-base on this machine (about 35 chunks/s). Show a total time budget.
4. **Pre-register the out-of-time test** by appending an amendment to `reports/eval_plan.md` before running anything: variants V4 (selected), V5 and BM25 only; the same metrics (AUC against all negatives, AUC against candidate-pool negatives only, recall@50/100/200, hub rate, bootstrap confidence intervals, n); positives are exclusive silver-set papers from 2016-2025 with terms masked exactly as before; z-score statistics frozen from the original 1995-2015 matrix; no tuning, no selection, nothing chosen on this data. State that post-2020 COVID-era papers dominate the random background and that results will be reported with and without 2020-2022 as a sensitivity check.

**Checkpoint: show me the plan, caps, time estimate and the amendment. Wait for my go-ahead.**

## Step 1: Build the 2016-2025 corpus
Reuse the Europe PMC client, parser and query definitions. Build the three parts (theory-candidate, conceptual background, random) with the approved caps, tagged in corpus_membership with window = 2016-2025. Cache everything, resumable, no re-downloads. Log failures. Print counts per part and per year (note the growth in open-access volume and the COVID-era spike).

## Step 2: Level 2 scan on the new papers
Run the frozen scanner (terms.yaml unchanged) over the new papers, including the weak and close-term logic and the multi-theory flags. Report per theory: direct-mention papers, weak, close, exclusive silver set for 2016-2025, and how many are primary. If any theory has fewer than 5 exclusive silver papers, say so: it becomes exploratory.

**Checkpoint: show me the silver-set sizes per theory for 2016-2025 and wait.**

## Step 3: Chunk and embed (background)
Chunk with the same rules (abstract, introduction, discussion, 180 words with 30 overlap), embed with the same model under caffeinate, resumable, progress log, shards written to a separate directory from the 1995-2015 embeddings. Do not change the existing embeddings. Test that re-embedding a few chunks returns them as their own nearest neighbors.

## Step 4: Out-of-time evaluation
Run exactly the pre-registered test: masked exclusive silver positives from 2016-2025, negatives from 2016-2025 papers that do not name the theory, variants V4, V5, BM25. Report for each theory and variant, side by side with the 1995-2015 test results from `reports/level3_eval_test.md`: AUC (all negatives), AUC (candidate-pool negatives only), recall@50/100/200, with confidence intervals and n; and the same with 2020-2022 excluded. Say plainly whether performance held, dropped or rose, and treat theories with fewer than 20 positives as exploratory. Write `reports/level3_out_of_time.md`.

## Step 5: Window comparison
1. **Mention trends:** per theory, normalized direct-mention rate per year 1995-2025 from the server-side counts, plus a table for the three nested windows.
2. **Retrieval across windows:** make `retrieve(theory, year_min, year_max)` work over the combined chunk sets (frozen z-score statistics) for the windows 1995-2015, 1995-2020 and 1995-2025, using V4 with the standard exclusion (names_theory_loosely = 0).
3. **Neighborhood shift:** per theory, for each window, the top 50 papers: the share published after 2015 (and after 2020), and the overlap of the top 50 between windows. List 5 new top-ranked papers per theory that appear only in the larger windows, with title, year and a 200-character snippet, to use as demo examples. Do not judge them.
4. Write `reports/level3_windows.md`.

## Step 6: App-ready exports (small, tracked, in `results/`)
Write these CSV files, no embeddings, no full texts, snippets at most 200 characters, and nothing from CORE:
- `results/level1_references.csv`: theory, raw reference text, parsed title, year, DOI, PMCID, resolution status, open-access full text yes or no.
- `results/level2_mentions.csv`: theory, pmcid, title, year, journal, mention tier (direct, weak, close), mention strength, section of first hit, one snippet.
- `results/level3_top.csv`: for each theory and each of the three windows, the top 30 papers under V4 (names_theory_loosely = 0): rank, pmcid, title, year, score, best claim id, the best claim's text, snippet, other theories named, and the judge verdict, confidence, reason and evidence where the paper was judged (join on pmcid from `results/judgments.csv`; leave empty otherwise).
- `results/window_trends.csv`: theory, year, hits, total open-access papers, rate per 10,000.
- `results/summary_metrics.csv`: one row per theory with its headline numbers (seed counts, silver-set sizes, V4 AUCs, judged R share).
- A `results/README.md` describing every file and column, and the caveats (open access only; negatives unlabeled; the judge is an LLM; small n for three theories).

Update `reports/STATUS.md` and commit (results/ and reports/ are tracked; data/ stays ignored).

## Constraints
- Inspect before assuming; show real examples.
- No tuning of variants, profiles, terms, weights or lambda on 2016-2025 results.
- Report negative results as they are.
- Everything cached, resumable, fixed seeds, commit after each step.
- If a step would take more than half a day, stop and propose a cut.
- Public data only. Do not redistribute full texts.

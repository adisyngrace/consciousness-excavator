# Prompt 08: Streamlit app, demo script and README

**How to run:** start a fresh Claude Code session in the repo root and type:
`Read CLAUDE.md and reports/STATUS.md, then read prompts/08_app_and_demo.md and follow it step by step. Stop at every checkpoint.`

**Before you run it:** prompt 07 Step 6 must be finished, so that `results/` contains the CSV files and `results/README.md`.

**What this does:** builds a Streamlit app with three tabs per theory (references, direct mentions, conceptual associations) plus a window selector, reading only the tracked tables in `results/` (no database, no embeddings, no models), so it runs on any machine and starts fast. It also writes a demo script and a project README.

**Your job:** approve the layout (Step 0), look at the running app and give feedback (Step 3).

**Budget:** about half a day.

---

Read CLAUDE.md, reports/STATUS.md and results/README.md first. Do not edit anything under src/ except new files for the app, and do not change terms, profiles, variants or any result file. The app is a viewer: it computes nothing new except simple filtering and display.

## Step 0: Inspect the data and propose the layout
1. Load every file in `results/` and print its columns, row counts, and 3 sample rows. Report anything missing or inconsistent (empty columns, mismatched theory names, missing windows).
2. Propose the app layout as a plain-text wireframe, covering:
   - **Sidebar:** theory selector (five theories), window selector (1995-2015, 1995-2020, 1995-2025), and an "About this tool" link.
   - **Header per theory:** theory name, a two-line description built from its LoC description (no new claims), and a coverage badge (dense or sparse, with the number of exclusive direct-mention papers) so users know when results are exploratory.
   - **Tab 1, References (Level 1):** the LoC references table with year, DOI link, resolution status and open-access full text yes or no, plus a one-line summary (how many are books or videos, how many resolve to full text).
   - **Tab 2, Direct mentions (Level 2):** a table filtered to the chosen window with mention tier and strength filters, a snippet expander per paper, and a line chart of the normalized mention rate per year with the selected window highlighted. For 2016-2025 rows, show a visible note that the list is a capped sample while totals come from the full counts.
   - **Tab 3, Conceptual associations (Level 3):** the top 30 under V4 for the chosen window. Each card shows the title (linked to its PubMed Central page), year, which core claim it parallels (id and text), a short snippet, other theories named, and the judge verdict, confidence, reason and evidence quote, or a clear "not judged" label. Add a filter for "judged as relevant only", and a headline sentence such as "N papers the judge rated as conceptual neighbors of this theory that never name it" (1995-2015 window only, where the judging was done).
   - **Tab 4, Evaluation and limits:** the headline metrics table (seed counts, silver-set sizes, V4 versus BM25 AUC in both periods with n and confidence intervals, judged relevant share), and a plain-language list of limitations (open access only, negatives unlabeled, the judge is an LLM, small samples, candidate-pool confound, capped 2016-2025 sample, profiles drawn from current LoC text so the out-of-time test is a generalization test, not a forecast).
3. Say exactly which numbers and labels appear on screen and which file each comes from.

**Checkpoint: show me the data inventory and the wireframe. Wait for my go-ahead.**

## Step 1: Data layer and tests
Write `app/data.py` that loads and validates the CSV files once (cached), exposes small functions for each tab, and fails with a clear message if a file or column is missing. Add tests (pytest) for loading, filtering by window and the empty-result cases. Add streamlit and pandas to requirements.txt, pinned to the versions installed in .venv, using `.venv/bin/python -m pip` only.

## Step 2: Build the app
Write `app/app.py` following the approved wireframe. Rules:
- Show every metric with its n and confidence interval where one exists; label small-n results "exploratory".
- Never present a judged verdict as ground truth; always label it "LLM judge (Claude), blind to ranking; checked against my labels on a sample".
- Never show unjudged papers as relevant; use "not judged" explicitly. For windows beyond 1995-2015, papers outside the judged set are unjudged.
- Keep text short, readable and free of jargon; use plain labels (for example "Never names the theory" for the exclusion).
- Handle empty states gracefully (for example a theory with no rows in a window).
- No network calls at run time except links the user clicks. No model loading.
- Add a Streamlit smoke test (using streamlit.testing if available) that renders each theory and window combination without errors.

## Step 3: Run it and review with me
Run the app locally with `.venv/bin/python -m streamlit run app/app.py`, tell me the URL and how to stop it, and list what to check. Then wait. I will click through it and send feedback.

**Checkpoint: wait for my feedback and apply it (layout, wording, anything confusing).**

## Step 4: Demo script
Write `docs/demo_script.md`, a 4-minute spoken demo following the app, with the real numbers pulled from `results/summary_metrics.csv`, not typed by hand. Structure:
1. The problem and the idea (30 seconds): theories of consciousness, literature is scattered, keyword search misses papers that discuss the ideas without the name.
2. Three levels, shown live with one theory (GWT): references, direct mentions, then conceptual associations with two judged examples.
3. A sparse theory (Champagne or panpsychism) to show honest limits.
4. The window selector: how the neighborhood shifts, with the caveat that it is descriptive.
5. How I checked it: the term-masked test against keyword search, the judge, my labels, the out-of-time result, and what did not work (contrast variants, the predictive processing keyword baseline result).
6. Limits and what comes next (the philosophy literature outside open access, a second source such as CORE).
Add a short list of likely questions with honest answers, including: why not just search the term, why LLM judging is not ground truth, what the numbers do not show.

## Step 5: README
Write `README.md` at the repo root: what the project is, the three levels, how to run the app, how the results were produced (a one-line pointer per prompt/stage), a map of the repo, the data sources, licenses and public-data notes, and the main limitations. State that full texts and embeddings are not included and are regenerated by the pipeline. Update reports/STATUS.md and commit.

## Constraints
- Inspect before assuming; show real examples.
- The app reads only from `results/`. If something it needs is missing, tell me and I will decide whether to add it to the exports. Do not read the database from the app.
- No new analysis, no tuning, no changed numbers.
- Commit after each step. Public data only. Do not redistribute full texts.

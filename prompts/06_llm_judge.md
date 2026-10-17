# Prompt 06: LLM judge (Claude Code as the judge)

**How to run:** start a fresh Claude Code session in the repo root and type:
`Read CLAUDE.md and reports/STATUS.md, then read prompts/06_llm_judge.md and follow it step by step. Stop at every checkpoint.`

**Before you run it:** fill in the `label` column of `reports/labeling_sheet.csv` (R, G or O) and save it as CSV. Do not tell Claude Code your labels or mention them in the session before Step 4: the judge must stay blind to them.

**What this does:** for the top 30 Level 3 papers per theory, Claude Code reads each paper's abstract and best-matching passages and gives a verdict (R = real conceptual neighbor, G = generic consciousness or neuroscience, O = off-topic) with a one-line reason and a short quote that is checked against the source text. It also judges the BM25 keyword-baseline results mixed in blindly, so we can compare conceptual search with keyword search on the same rubric. Your hand labels then check the judge.

**Budget:** about 2 hours. If it runs long, cut the BM25 comparison to the top 20 per theory and tell me.

---

Read CLAUDE.md, reports/STATUS.md and reports/eval_plan.md first. Do not edit terms.yaml, the profiles, the embeddings or the selected variant (V4). Do not tune anything based on judgments.

**Blindness rules (important).** While judging (Steps 1-3), do NOT open `reports/labeling_sheet.csv`, the method-membership file, any rank or score, or any other result file. Judge only from the packets you are given. After Step 3 you may open them.

## Step 0: Build the judging set
1. **V4 list:** for each of the five theories, the top 30 papers under V4 (1995-2015, names_theory_loosely = 0 for that theory, same rules as the evaluation).
2. **BM25 list (GWT and predictive processing only):** the top 30 papers under the BM25 baseline with the same exclusion and corpus.
3. Take the union per theory, deduplicate, and give every item an anonymous id. Store which method(s) produced each item in `data/judge/method_membership.csv`, which you must not open until Step 4.
4. **Repeats:** duplicate a random 10% of items (fixed seed) under new item ids, to measure the judge's consistency.
5. Shuffle items within each theory (fixed seed) and write batches of 10 as `data/judge/packets/batch_NN.md`. Every packet must have the same format whichever method produced the item:
   - theory name and its core claims (id and text, from `profiles/`)
   - paper title, year, abstract
   - the 2 best-matching chunks for that theory, chosen by the same V4 component score for every item
   Do not include scores, ranks, corpus part or method.

**Checkpoint: show me item counts per theory and method, the repeat count, and 3 example packets. Wait for my go-ahead.**

## Step 1: The rubric
Write the exact instructions the judge uses to `prompts/judge_rubric.md` and show them to me. They must say:
- **R (relevant conceptual neighbor):** the paper's own content, as shown in the packet, makes a claim, uses a mechanism or addresses a problem that parallels a specific core claim of the theory, even in different words. Name the claim id(s).
- **G (generic):** about consciousness, awareness or general neuroscience, but with no specific parallel to a core claim. The same brain region, the same task, or "consciousness" in general is not enough.
- **O (off-topic):** unrelated to the theory's ideas.
- Judge only from the packet text. Do not use outside knowledge about the paper. If the packet is too thin to decide, give a low-confidence verdict.
- Each judgment is JSON: `item_id`, `verdict`, `confidence` (high, medium, low), `claim_ids` (list, empty unless R), `reason` (one sentence), `evidence` (a quote of at most 20 words copied exactly from the packet), `names_theory_in_text` (true if the packet text actually names the theory, which should not happen), `better_fit_theory` (another theory name if the paper fits it clearly better, else null).
- For Champagne's semiotic account, R requires a parallel to sign, meaning, interpretation or the phenomenology of qualities, not just "communication" or "language".

**Checkpoint: show me the rubric and wait for approval.**

## Step 2: Judge
Process the batches one at a time, in order: read a packet file, then write `data/judge/judgments/batch_NN.json` (a JSON list, one object per item). Process one theory fully before the next, commit after each theory, and make the process resumable (skip batches whose judgment file exists). Print progress after each batch.

## Step 3: Validate and ingest
Write `src/judge/ingest.py` that:
- validates each judgment against the schema,
- checks that `evidence` appears verbatim in that item's packet text (whitespace-normalized) and flags failures,
- loads valid judgments into a SQLite table `judgments` (item_id, theory, pmcid, verdict, confidence, claim_ids, reason, evidence, flags),
- lists items that failed validation. Re-judge only those, once.

## Step 4: Analysis (blindness ends here)
Now you may open the method-membership file and `reports/labeling_sheet.csv`. Write `reports/level3_judge.md` with:
1. **Verdict distribution per theory** for the V4 list, with the share of R among the top 10, 20 and 30.
2. **V4 versus BM25 on GWT and predictive processing:** R share at 10, 20 and 30 for each method, with 95% bootstrap confidence intervals. State that the judge was blind to the method.
3. **Judge consistency:** agreement and Cohen's kappa on the repeated items.
4. **Agreement with my hand labels:** a confusion matrix and Cohen's kappa on the rows of the labeling sheet that have labels. If the label column is empty, say so and skip this part; do not fill it in.
5. **R share by corpus part** (seed, candidate, background, random), to check whether results lean on the candidate pool.
6. **Flags:** how many items have `names_theory_in_text` true (which would indicate an exclusion leak) or a `better_fit_theory`, and the confusion across theories.
7. **Exports for the app:** for each theory, the 10 best R-judged papers (high confidence first) with title, year, reason and evidence quote.
8. **Caveats paragraph** to include in the write-up: the judge is an LLM, shares biases with other LLMs, saw only abstracts and two passages, is not independent of the profiles' author, and its agreement with my labels is only as good as the small sample allows.

## Step 5: Wrap up
Save the final judgments to `data/judge/judgments_final.csv` for the app, update `reports/STATUS.md`, and commit. Stop and wait for me.

## Constraints
- Stay blind until Step 4. Never show the judge a score, rank, corpus part or method.
- Do not use the judgments to change the profiles, variant or terms.
- Report negative results as they are, including if the BM25 list does as well as the V4 list.
- Fixed random seeds, resumable, commit after each theory.
- Public data only. Quotes in reports are short (at most 20 words) and come from open-access papers.

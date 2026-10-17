# Prompt 09: Philosophy pilot with CORE (Champagne's semiotic account and panpsychism)

**How to run:** start a fresh Claude Code session in the repo root and type:
`Read CLAUDE.md and reports/STATUS.md, then read prompts/09_philosophy_pilot_core.md and follow it step by step. Stop at every checkpoint.`

**Before you run it:** register for a free CORE API key (on core.ac.uk, its API page) and add it to `.env` as `CORE_API_KEY=...`. Never paste the key into chat or commit it.

**What this does:** adds a small, separate, clearly labeled **exploratory** corpus of open-access philosophy and humanities papers from CORE for the two theories PubMed Central covers worst, and repeats the same masked-term test and the same V4 scoring on it. It does not change any existing result. This prompt supersedes the earlier optional CORE prompt (03).

**Scope rules (important):**
- Only the two pilot theories: Champagne's semiotic account and panpsychism.
- Only records where CORE itself returns the full text. **Do not download or parse PDFs and do not build a PDF pipeline.** Skip records without text.
- Everything stays separate: its own corpus tag, its own embeddings, its own exports, its own report. Nothing is merged into the PubMed Central tables or the existing app results.
- Frozen and not to be edited: terms.yaml, profile claims, V4 scoring, existing embeddings, existing reports and results files.
- Full texts stay under `data/` (gitignored). Exports contain titles, years, links, license labels and snippets of at most 200 characters only.

**Budget:** about one day. If any estimate in Step 0 exceeds 3 hours in total, use the smaller caps it offers. Hard stop: if this is not finished, stop and report; it becomes future work.

---

Read CLAUDE.md, reports/STATUS.md, reports/eval_plan.md and results/README.md first.

## Step 0: Inspect, plan and pre-register
1. **Inspect the CORE API (do not assume).** Read the current documentation and run small test requests with `CORE_API_KEY`. Show me: the search endpoint and query syntax; how to filter by year and language; how to ask for records that include full text; which fields come back (title, year, DOI, abstract, full text, repository, license, download URL) with one real example record; the free-key rate limits; and the API terms of use that matter for storing text and publishing excerpts. If the key is missing or blocked by the network, show me the exact error and stop.
2. **Check the existing code layout:** is the corpus code behind the common `Source` interface (`src/corpus/sources/`)? If not, propose the lightest way to add a CORE source without touching the Europe PMC path.
3. **Propose caps and the pool design,** mirroring the earlier design in small form:
   - theory candidates: for each pilot theory, records matching its strong terms from the frozen terms.yaml (cap about 300 each);
   - adjacent background: philosophy-of-mind and semiotics topics that do not name the theories (for example mind-body problem, qualia, phenomenology, intentionality, sign, meaning, semiosis, Peirce, philosophy of mind), cap about 1,500;
   - broad distractors: a general sample across other humanities and social science topics (cap about 500), if the API supports a sample that is not just recent items; otherwise say so.
   Years 1995-2025, English only, tagged by year.
4. **Per-document text rule:** use the abstract (if present) plus at most the first 6,000 words of body text, with trailing reference lists removed by a heading rule; drop documents under 3,000 characters, likely OCR garbage (high share of non-dictionary tokens) and non-English text; deduplicate against the PubMed Central corpus by DOI, then by normalized title plus year. Log every drop with a reason.
5. **Estimate** document count, chunk count (180 words, 30 overlap, no section detection) and embedding time with bge-base at about 35 chunks per second.
6. **Pre-register** an addendum in `reports/eval_plan.md` before running anything, committed now: positives are exclusive silver-set CORE papers (names only that one theory, found by the frozen scanner in coarse mode); negatives are CORE papers that do not name the theory; terms and landmark authors masked exactly as before; variants are V4 (frozen) and BM25 only; metrics are AUC against all negatives and against candidate-pool negatives only, recall at 50, 100 and 200, bootstrap intervals, and n; z-score statistics computed on the CORE chunk set itself (the text type differs from PubMed Central XML) and stated as such; theories with fewer than 20 positives are exploratory; no tuning, no selection; results reported whatever they are.

**Checkpoint: show me the API findings, the proposed pool design and caps, the time estimate and the addendum. Wait for my go-ahead.**

## Step 1: Pull the pilot corpus
Implement the CORE source, cache every response, make it resumable and idempotent, respect the rate limits, and log failures. Build the three parts with the approved caps. Store each paper with source = core, section_quality = coarse, repository, license label (as CORE reports it, or unknown), year, title, abstract, a flag for whether the reference list was split off, and the word count used.

Print: counts per part and per year; share of records that came with full text; documents dropped by reason; duplicate rate against the PubMed Central corpus; word-count distribution; top 10 repositories; license label counts; and 5 random cleaned documents (title, year, repository, first 300 characters).

**Checkpoint: show me this and wait.**

## Step 2: Level 2 scan in coarse mode
Run the frozen scanner over the CORE papers using the coarse rule (body text versus trailing references only; no per-section tags). Report per pilot theory: direct, weak, close, exclusive silver set, and how many are primary. Then print **10 random direct-mention hits per theory with surrounding text** so I can check precision by eye, since text extracted from PDFs is noisier. Say which papers lack a reference split and how that affects mention counts.

**Checkpoint: show me the silver-set sizes and the snippets. Wait for my labels before continuing.**

## Step 3: Chunk and embed (background)
Chunk and embed the CORE papers with the same model and rules as before, under caffeinate, resumable, with a progress log, into a separate embeddings directory. Cap chunks per paper as in the text rule above. Run the self-retrieval test (a few re-embedded chunks return themselves).

## Step 4: Evaluation
Run exactly the pre-registered test for Champagne and panpsychism: V4 and BM25 on masked exclusive positives against the negatives, both AUCs, recall at 50, 100 and 200, bootstrap intervals, n beside every number, hub rate. Report next to the PubMed Central numbers for the same theories. Also report how the Champagne and panpsychism profiles rank each other's masked positives (a 2 by 2 version of the discriminability check). State the caveats: positives mostly come from the candidate pool; the CORE text is PDF-derived; z-score statistics differ from the PubMed Central runs; small n. Write `reports/core_pilot.md`.

## Step 5: Top results and judge packets
1. For each pilot theory, list the top 30 CORE papers under V4 that do not name the theory (names_theory_loosely = 0), with title, year, repository, license label, link, best-matching claim id and text, a snippet of at most 200 characters, and other theories named.
2. Build **blind judge packets** for the top 20 per theory in the same format and with the same rubric as prompt 06 (no scores, ranks or method), so I can run the blind judge in a separate fresh session. Do not judge anything yourself in this session.

## Step 6: Exports and wrap-up
Write small tracked files in `results/`: `philosophy_pilot_top.csv` (the lists from Step 5, with an explicit judged column that is false until the judge runs), `philosophy_pilot_metrics.csv` (counts, silver-set sizes, AUCs with n and intervals for V4 and BM25), and add a clearly separate section to `results/README.md` describing them, the exploratory status, the license caveats and the fact that nothing from this pilot enters the main tables. Update `reports/STATUS.md` and commit. Do not change the app.

## Constraints
- Inspect before assuming; show real API responses and real examples.
- No PDF downloading or extraction. No full-text redistribution.
- No tuning, no variant selection, no changes to frozen items. Pre-register before running.
- Report negative results as they are, including if BM25 matches V4.
- Never print or commit the API key.
- Fixed random seeds, cached, resumable, commit after each step.
- If a step would take more than half a day, stop and propose a cut.

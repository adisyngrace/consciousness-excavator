# Prompt 03: Add CORE as a second corpus source (gated, optional)

**How to run:** only after prompt 02 is finished (corpus built, Level 2 report reviewed). Start a fresh Claude Code session in the repo root and type:
`Read prompts/03_add_core_source.md and follow it step by step. Stop at every checkpoint.`

**Before you run it:** register for a free CORE API key (search for "CORE API key" on core.ac.uk), then add it to `.env` as `CORE_API_KEY=...`.

**Why this exists:** PMC is thin on philosophy. CORE aggregates open-access papers from institutional and subject repositories worldwide, including full text, which should help panpsychism and Champagne's semiotic account. The tradeoff is messier text (PDF-derived, no reliable sections).

**Budget:** half a day at most. If it is going badly by midday, stop and tell me. The schedule cut order puts this first.

---

Read CLAUDE.md, `reports/level1_resolution.md` and `reports/level2_terms.md` first.

## Step 0: Go/no-go check
From the two reports, tell me per theory: number of full-text seed papers in PMC, number of corpus papers with direct mentions, and number of Unpaywall-identified open-access copies outside PMC. Recommend **go** or **no-go** for CORE, and which theories to pilot on (default: panpsychism and the semiotic account). Go is justified if any theory has fewer than about 15 PMC full-text seeds or very few candidate-pool papers. **Wait for my decision.**

## Step 1: Inspect the API (don't assume)
Read the current CORE API documentation and run small test requests using `CORE_API_KEY`. Show me:
- The search endpoint, the query syntax, and how to filter by year range, language, and "has full text".
- Which fields come back (title, year, DOI, abstract, full text, download URL, license, repository/source) with one real example record.
- The rate limits for a free key, and whether the bulk data dumps would be a better route for the volume we need. Recommend one with a rough time estimate.

**Checkpoint: wait for my go-ahead.**

## Step 2: Implement `src/corpus/sources/core.py`
Implement the same `Source` interface as the Europe PMC source. Rows go into `papers` with `source = 'core'`, plus `license`, `repository`, and `section_quality = 'coarse'`. Cache everything and keep it idempotent. Respect rate limits and log failures with reasons.

## Step 3: Pilot pull
For the pilot theories only, years 1995-2015, English only, full text present:
- Query each theory's strong terms (from `terms.yaml`) and a handful of adjacent topic queries, capped at 500 papers per theory (record total hits).
- **Deduplicate against existing papers** by DOI first, then by normalized title plus year. Record the duplicate rate.
- Text cleaning: collapse whitespace and hyphenation, drop documents under about 3,000 characters of text, and flag likely OCR garbage (a high share of non-dictionary tokens) and non-English text. Log every dropped document with a reason.
- Coarse section handling: find a trailing "References" or "Bibliography" heading and split it off, so reference lists never count as body text. If no heading is found, set `reference_split = false` and flag the paper so Level 2 treats mentions with lower confidence. Do not try to detect introduction or discussion sections.

**Checkpoint: print counts per theory (found, kept, dropped by reason, duplicates), and 5 random cleaned documents (title, year, repository, first 300 characters of body). Wait for my go-ahead.**

## Step 4: Run the Level 2 scanner on CORE papers
Reuse the existing scanner unchanged apart from honoring `section_quality = 'coarse'` (no per-section tags; body versus references only). Then write `reports/core_pilot.md`:
- Per pilot theory, by source (PMC versus CORE): corpus size, share with `direct_mention`, mention-strength distribution, year distribution
- License distribution and repository breakdown (top 10 repositories)
- Text quality stats (average length, share flagged OCR or no reference split)
- 20 random CORE direct-mention hits per theory with snippets, for my precision audit
- A recommendation: keep CORE and extend to all five theories, keep it for the pilot theories only, or drop it, with reasons

**Checkpoint: wait for my decision.**

## Step 5: Wire it through
If I say keep: extend the pull to the agreed theories (same caps), make sure the Level 2 query API (`get_mentions`) accepts an optional `source` filter, and make sure downstream code (chunking, embedding, retrieval) treats `source` as a filterable column, so the UI can show PMC and CORE results separately.

## Constraints
- Inspect before assuming. Show me real API responses.
- Do not redistribute CORE text. Full texts stay under `data/` (gitignored); the app shows snippets, titles, links and IDs only.
- Store the license on every paper.
- No silent drops, idempotent, cached, commit after each step.
- If this passes half a day, stop and propose a cut.

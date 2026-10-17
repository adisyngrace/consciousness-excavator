# Prompt 01: Level 1 (LoC scraper + ID resolution)

**How to run:** start Claude Code in the repo root, then type:
`Read prompts/01_level1_scraper.md and follow it step by step. Stop at every checkpoint.`

---

Read CLAUDE.md first. We're starting **Level 1**: extracting references from the Landscape of Consciousness site and resolving them to DOIs and PMC IDs.

Work in these steps, and **stop and show me output at each checkpoint** before moving on.

## Step 0: Scaffold
- Create the repo structure from CLAUDE.md, a Python virtual environment (`.venv`), a `requirements.txt`, a `.env.example` (with `CONTACT_EMAIL`, `USER_AGENT`, and a placeholder `CORE_API_KEY` for later), a `.gitignore` (ignore `data/` and `.env`), and `src/db.py` with a SQLite schema:
  - `theories(id, name, loc_url, description_text)`
  - `loc_references(id, theory_id, raw_text, parsed_title, parsed_authors, parsed_year, parsed_journal, doi, pmcid, pmid, resolution_status, resolution_source, notes)`
- Add an on-disk HTTP cache and a rate-limited request helper (about 1 request/second by default, configurable) using the User-Agent from `.env`.

## Step 1: Inspect the site (do NOT write a parser yet)
- Fetch https://loc.closertotruth.com/robots.txt and summarize what it allows.
- Fetch the site's landing page and find the pages for our 5 theories: Champagne's semiotic account, Global Workspace Theory, Integrated Information Theory, Panpsychism, and Predictive Processing / Free Energy Principle. Show me the URLs you found and the exact titles on the site. If any theory is missing or ambiguous, ask me.
- For each of the 5 pages, save the raw HTML to the cache and tell me: where the description text lives, where the references live, and how they're formatted (lists, links, plain strings, DOI links, etc.). Show me 3 raw reference examples per theory.
- If the content is rendered by JavaScript and plain requests don't get it, tell me and propose the lightest fix (a hidden API endpoint, or Playwright as a last resort).

**Checkpoint: wait for my go-ahead.**

## Step 2: Parse
- Write the parser for descriptions and references, with `pytest` tests built from the saved HTML fixtures.
- Store the description text in `theories` and every reference in `loc_references` with `raw_text` preserved exactly.
- Parse out title, authors, year, journal where possible. Where a reference is a book, chapter or other non-article, flag it in `notes`, don't discard it.
- Print per-theory counts: references found, how many have a DOI already in the page, how many look like books.

**Checkpoint: show me 10 random parsed references per theory next to their raw text so I can check parsing quality by eye.**

## Step 3: Resolve IDs
For each reference without a DOI:
1. Query the **Crossref** API (use the `mailto` polite pool) with the bibliographic string, and accept a match only if the title similarity and year agree above a threshold. Store the score.
2. For each DOI, find the PMCID and PMID via the **Europe PMC** search API (`DOI:"..."`), and record whether the paper is **open access with full text available**.
3. For resolved DOIs that are NOT in PMC open access, ask **Unpaywall** (free API, pass my email from `.env`) whether an open-access copy exists elsewhere. Store `oa_url`, `oa_host_type` (repository, publisher, etc.) and `license` in new columns. These are candidates for the optional CORE source later; do not download anything yet.
4. Set `resolution_status` to one of: `resolved_fulltext`, `resolved_no_fulltext`, `doi_only`, `unresolved`, `non_article`. Record the source and the match score. Log every failure with its reason.

## Step 4: Report
Print and save `reports/level1_resolution.md` with, per theory:
- Total references
- Count in each `resolution_status`
- % with open-access full text in Europe PMC
- The year distribution of resolved references (so we can see how many fall inside 1995-2015, 1995-2020 and 1995-2025)
- Count of non-PMC papers that Unpaywall says have an open-access copy elsewhere (potential CORE candidates)
- 10 unresolved examples with the likely reason

Flag any theory with fewer than ~15 full-text seed papers, since those will need backup seeds (abstracts, descriptions).

## Constraints
- Don't guess at site structure; inspect and show me first.
- No silent drops: every reference must end up in the DB with a status.
- Keep it re-runnable: running the pipeline twice must not duplicate rows or re-download anything.
- Commit after each step with a clear message.

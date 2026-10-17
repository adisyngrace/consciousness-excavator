# CLAUDE.md: Consciousness Theory Literature Excavator

**At the start of every session, read `reports/STATUS.md`** (what is done, what is pending, and what to do next).

## What this project is
A solo hackathon project, **due Oct 16, 2026**. The tool takes 5 theories of consciousness from Kuhn's "Landscape of Consciousness" (https://loc.closertotruth.com/) and finds the literature associated with each, at three levels:

1. **Level 1: References.** The reference lists on each theory's LoC page, resolved to DOIs and PMC IDs. This is the seed set.
2. **Level 2: Direct term mentions.** Full-text hits for each theory's name, synonyms, abbreviations and key authors, with counts and context snippets.
3. **Level 3: Conceptual associations (the core).** Papers that are conceptually related to a theory but do NOT contain its direct terms. This is the most important part of the project.

The point is to excavate associated ideas, not to do term search.

## The 5 theories
1. Champagne's semiotic account (confirm exact LoC title/slug by inspecting the site)
2. Global Workspace Theory (GWT / GNW)
3. Integrated Information Theory (IIT)
4. Panpsychism
5. Predictive Processing / Free Energy Principle (confirm the LoC entry; if it has no reference list, fall back to Higher-Order Theories or Attention Schema Theory and tell me)

## Sources (decisions already made, don't relitigate)
- **Primary corpus: PubMed Central Open Access via the Europe PMC REST API.** PubMed itself has abstracts only; we need full, free text. Gives clean JATS XML with sections.
- **Optional second source: CORE** (open-access repository aggregator, full text, free API key in `.env` as `CORE_API_KEY`). Added only after the PMC pipeline works (see prompt 03), mainly to improve philosophy-side coverage for panpsychism and the semiotic account. **CORE pilot is a GO for panpsychism and Champagne.** The PDF-to-text pipeline built for CORE also reads OA-PDF seeds (see Level 1 seed decisions below). CORE text is messier (PDF-derived, no reliable sections), so it is flagged `section_quality = coarse`.
- **Level 1 helpers (not corpus sources):** Crossref (reference string to DOI), Europe PMC (DOI to PMCID and full-text availability), Unpaywall (find open-access copies of DOIs that are not in PMC).
- **Not used:** PhilPapers (index and abstracts, mostly no full text, restrictive redistribution terms), OpenAlex/citation graph (cut for schedule), Semantic Scholar.
- No common `Source` interface was built. Europe PMC code is flat (`src/corpus/epmc.py`, `build.py`); the CORE pilot is standalone (`src/corpus/core.py`, `build_core.py`, separate `core_*` tables, `source = core`). CORE-derived text stays in gitignored `data/` and terminal output only; tracked files hold only titles, years, repositories, links, DOIs, scores, claim ids and counts.
- Only full-text, openly available papers go into the corpus. Abstracts may be used only as profile-only seeds and must be labeled that way.
- Coverage skews to neuroscience, psychology and medicine. Philosophy-heavy theories will be thin. Report it, don't hide it.

## Time windows
Nested: 1995-2015 inside 1995-2020 inside 1995-2025.
- Build and validate on **1995-2015** first.
- Later windows: Europe PMC server-side per-year counts for trends (no downloads), and embed only incremental papers matched by theory queries plus a small random sample. Never embed the full 2025 corpus.
- Normalize all counts per 10,000 open-access papers that year.

## Architecture
Every stage reads from and writes to **SQLite** (`data/project.db`) or **Parquet** (`data/*.parquet`). Stages are independently re-runnable and idempotent. All HTTP responses are cached on disk (`data/cache/`).

```
src/
  config.py            # theories, windows, paths
  terms.yaml           # per-theory term tiers (I edit this by hand)
  db.py                # schema + helpers
  level1_loc/          # scrape LoC, parse references, resolve IDs
  corpus/
    epmc.py, build.py  # Europe PMC; core.py, build_core.py (CORE pilot, standalone)
  level2_terms/        # scanner, query API
  level3_concepts/     # profiles, chunking, embeddings, retrieval, exclusion, contrastive scoring
  eval/                # term-masked retrieval, discriminability, prediction test
  judge/               # LLM relevance judge + explanations (top ~30/theory only)
  app/                 # Streamlit UI
tests/
reports/
data/                  # gitignored
prompts/               # the stage prompts
```

## Level 2 rules (the baseline Level 3 must beat)
- Term tiers: `strong` (full names; a hit is a direct mention), `abbreviation` (counts only if a strong term for the same theory is in the same paper), `author` (weak signal, never counts alone), `excluded_generic` (never counted).
- **Domain co-occurrence rule:** a strong-term hit counts only if the paper also contains cognitive-neuroscience/philosophy-of-mind context vocabulary (listed in `terms.yaml`), to remove chemistry, signal-processing and computing uses of terms like "free energy" or "global workspace".
- Reference lists are scanned separately and never counted as mentions.
- After the precision audit, any term below about 80% precision is demoted to the weak tier.

## Level 3 method
1. Concept profile per theory = LoC description text + an LLM-written core-claims summary (I review and edit by hand) + abstract-only seeds + OA-PDF seeds. Abstract-only and OA-PDF seeds are **profile-only** (not part of the corpus). Full-text resolved seeds are in the corpus; they may also feed profiles except in the masked test below.
2. Chunk full texts (prefer abstract, introduction, discussion), embed, index in FAISS or Chroma.
3. Retrieve nearest passages to each profile.
4. **Exclude papers flagged `direct_mention`** by Level 2.
5. **Contrastive scoring** to fight generic "consciousness" drift: score = similarity to the theory profile minus similarity to a generic consciousness profile (and optionally minus the mean similarity to the other four theories).
6. LLM judge on the top ~30 per theory, instructed to reject papers that are merely about consciousness in general. Judge outputs a short explanation of the specific parallel.
7. Final score = contrastive embedding similarity + LLM judgment. (Citation graph is CUT; future work.)

## Evaluation (one command)
- **Term-masked retrieval test (replaces the 20% seed hold-out):** LoC reference lists are small and book-heavy (full-text seeds by any OA route, all years: Champagne 8, GWT 3, IIT 7, Panpsychism 13, Predictive Processing 4; in 1995-2015: 11 = Champagne 4, GWT 1, IIT 2, Panpsychism 2, PP 2, of which only 3 are Europe PMC XML and in the corpus (IIT 2, PP 1; all three are silver-set papers) and 8 are OA-PDF, profile-only, text not yet extracted), so seeds are too few for a hold-out test or as the main profile source. Instead: take Level 2 silver-standard papers (strong-term direct mentions), mask direct and close terms in their text, build profiles WITHOUT those papers, and test whether profiles rank them above background and random papers. Report recall@k, AUC and n per theory. Champagne and panpsychism are low-n and reported qualitatively.
- **Discriminability matrix:** a theory's profile should retrieve its own literature better than the other four.
- **Prediction test (window experiment):** profiles from LoC text plus the 1995-2015 corpus only, tested on 2016-2025 silver-set papers with terms masked.
- Hand-label about 20 Level 3 results per theory (I do this myself).

## Working rules
- **Inspect before assuming.** Never guess the structure of an external site or API. Fetch a real example, show me, then write the parser.
- **Stop at every checkpoint** in the stage prompt and wait for my go-ahead.
- Print sanity checks at the end of every stage (counts, rates, random samples).
- **No silent failures.** Log every record that fails to parse or resolve, with the reason.
- Respect robots.txt and rate limits. Use a descriptive User-Agent with my contact email from `.env`.
- Python 3.11+, type hints, small functions, `pytest` for parsers and scanners. Use a virtual environment (`.venv`).
- Secrets in `.env`, never committed. Do not commit `data/`.
- Commit after each working step with a clear message.
- Public data only. Nothing sensitive, personal or student-related enters this repo or any prompt (university AI governance requirement).
- If something would take more than a few hours or threaten the schedule, stop and propose a cut.

## Schedule (revised: today is Oct 9)
| Day | Goal |
|---|---|
| Oct 9 | Setup, Level 1 (scrape, parse, resolve, report) |
| Oct 10 | Corpus pull (Europe PMC, 1995-2015) + Level 2 scanner and report |
| Oct 11 | CORE pilot (go for panpsychism and Champagne); chunk, embed, index; concept profiles |
| Oct 12 | Level 3 retrieval with exclusion and contrastive scoring; evaluation |
| Oct 13 | LLM judge on top ~30 per theory; hand-labeling |
| Oct 14 | Window / prediction experiment |
| Oct 15 | Streamlit UI (3 tabs per theory plus window and source filters) and demo script |
| Oct 16 | Buffer, polish, submit |

**Cut order if behind:** CORE first, then per-theory hand-labeling down to 10, then the 1995-2025 window (keep server-side trend counts only).

## Headline results the demo needs
- LoC reference resolution rate per theory
- "N papers closely tied to theory X that never mention it" (Level 3 versus Level 2)
- Term-masked recall@k / AUC (with n) and the discriminability matrix
- Whether the 1995-2015 map predicts 2016-2025 associations
- Dense versus sparse coverage story (PMC versus CORE, neuroscience versus philosophy theories)

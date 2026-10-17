# Prompt 02: Corpus pull (Europe PMC) + Level 2 (direct term mentions)

**How to run:** after Level 1 is done and `reports/level1_resolution.md` exists, start a fresh Claude Code session in the repo root and type:
`Read prompts/02_corpus_and_level2.md and follow it step by step. Stop at every checkpoint.`

**Why corpus and Level 2 are one prompt:** Level 2 needs local full texts, and Level 3's "exclude papers that mention the theory directly" step needs a term scan across the *entire* corpus, not just search hits. So Level 2 is built as a scanner that runs over every local document.

**Your job in this stage:** review and edit `terms.yaml` at the Step 2 checkpoint, and hand-check the precision audit in Step 6.

---

Read CLAUDE.md and `reports/level1_resolution.md` first. We're now building the **1995-2015 full-text corpus** and **Level 2 (direct term mentions)**. Work step by step and **stop at each checkpoint** to show me output before continuing.

## Step 0: Plan, then confirm
Before writing code, inspect the Europe PMC REST API docs and run a few small test queries (do not assume syntax). Confirm and show me:
- How to restrict to open-access, full-text-available records and to a publication-year range.
- Whether the default search covers full text for open-access articles (so a query for a phrase can match inside the body, not just title/abstract).
- The endpoint and format for retrieving full-text XML by PMCID, and how the JATS XML separates abstract, body and reference list.
- Whether the bulk open-access downloads would be faster than per-article requests for the volumes below. Recommend one approach with a rough time estimate.

**Checkpoint: wait for my go-ahead.**

## Step 1: Build the corpus (1995-2015 only for now)
The corpus has three parts, each tagged in a `corpus_membership` table so we can analyse them separately:

1. **Seed papers:** every Level 1 reference with status `resolved_fulltext` and year in 1995-2015.
2. **Theory-candidate pool:** for each theory, full-text search hits for its name and main synonyms (from `terms.yaml`, Step 2), capped at a configurable maximum per theory (default 2,000, randomly sampled if hits exceed it, with the total hit count recorded).
3. **Conceptual background pool:** open-access 1995-2015 papers matching broad topic queries that are *adjacent* to the theories but don't name them. Examples to start from: "prediction error", "hierarchical Bayesian inference", "attention", "working memory", "perceptual awareness", "binocular rivalry", "anesthesia", "sign processing", "semiotics", "information integration", "emergence", "mind-body". Cap about 5,000 total. Plus a **random background sample** of about 2,000 across neuroscience/psychology/medicine, so Level 3 has distractors to beat.

**Write the corpus code behind a common `Source` interface** (`src/corpus/sources/base.py` with `search(query, year_min, year_max, limit)` and `get_fulltext(id)`), implemented first by `europepmc.py`. Every row in `papers` gets a `source` column (`europepmc` for now). A second source, CORE, will be added later by prompt 03 without changing anything downstream.

Store per paper in SQLite `papers`: pmcid, pmid, doi, title, year, journal, abstract, license (if available), path to cached XML. Extract full text from the XML into sections: abstract, introduction, body, discussion, back-matter. **Keep the reference list separate and never merge it into body text.**

Everything cached to disk and idempotent: rerunning must not re-download. Respect rate limits and the User-Agent from `.env`. Log failed downloads with reasons.

**Checkpoint: print corpus size per part, year distribution, % with an identifiable introduction/discussion section, and 5 random papers (title, year, first 300 characters of body). Wait for my go-ahead.**

## Step 2: Term lists (`src/terms.yaml`)
Create `terms.yaml` with, per theory, these tiers:
- **strong:** unambiguous full names and phrases (for example "global workspace theory", "integrated information theory", "panpsychism"). A hit here is a direct mention.
- **abbreviation:** short forms (GWT, GNW, IIT, PP, FEP). These are ambiguous (IIT is an Indian institute, GWT is a web toolkit), so a hit counts only if a strong term for the same theory also appears in the same paper. Otherwise record it as `unconfirmed`.
- **author:** key names (for example Baars, Dehaene, Tononi, Koch, Friston, Clark, Chalmers, Strawson, Goff). These are weak signals. Record them separately and never treat them alone as a direct mention.
- **domain_context:** a list of cognitive-neuroscience and philosophy-of-mind vocabulary (brain, neural, cortex, cognition, awareness, perception, conscious, mind, phenomenal, and so on). A strong-term hit counts as a direct mention only if at least N of these appear in the same paper (start with N = 2, make it configurable). This removes chemistry, signal-processing and computing uses of terms like "free energy" or "global workspace".
- **excluded_generic:** words we deliberately do NOT count even though related ("sign", "information", "prediction", "workspace" alone, "consciousness").

Seed a first draft from the LoC descriptions and my CLAUDE.md, with a header comment on each theory explaining the choices. **Include inflections** (for example panpsychist, panpsychic, "free-energy principle", "free energy principle", "predictive coding", "predictive processing", "Bayesian brain").

For the Champagne semiotic account, look at the LoC page and the seed papers to find its real vocabulary rather than guessing. Flag to me which of its terms are too generic to use.

**Checkpoint: show me `terms.yaml`. I will edit it. Wait for my go-ahead.**

## Step 3: The scanner
Write `src/level2_terms/scan.py`:
- Match case-insensitively with word boundaries, handling hyphens, plural forms and spelling variants.
- Scan **per section** (title, abstract, body, back-matter) and record which section each hit is in.
- Scan the **reference list separately** and store those as `cited_in_references` (for example, a paper that cites Tononi 2004 is a useful weak signal, but it's NOT a direct mention).
- Store in a `term_hits` table: pmcid, theory, term, tier, section, count, plus up to 3 context snippets (about 150 characters either side, whitespace-normalized).
- Compute a per-paper, per-theory `direct_mention` flag: true if any `strong` term appears in the title, abstract or body, or any `abbreviation` appears confirmed by a strong term. Also store `mention_strength` (total strong-term count) and `title_or_abstract_hit`.
- Run it over **every paper in the corpus**, not just the search hits, so the flags can drive Level 3's exclusion step.
- Add `pytest` tests with small synthetic texts covering: abbreviation ambiguity, hyphen variants, a term appearing only in the reference list, a generic word that must not count, and a strong term in a paper with no domain-context vocabulary (must not count).

## Step 4: Corpus-wide counts for the time trend
For each theory's strong terms, use Europe PMC's server-side hit counts per publication year, 1995-2025, restricted to open-access full text. Store as `term_counts_by_year` (theory, year, hits, total_OA_papers_that_year). Also store the **normalized rate** (hits per 10,000 OA papers) because open-access volume grows sharply over time. This feeds the 1995-2015 vs 1995-2020 vs 1995-2025 comparison later and needs no downloads.

## Step 5: Query API
Write `src/level2_terms/query.py` with `get_mentions(theory, year_min, year_max, min_strength=1, limit=None)` returning papers with title, year, journal, mention counts by section, and snippets, sorted by mention strength. The UI will call this directly.

## Step 6: Validation and report
Write `reports/level2_terms.md` and print it. Per theory:
- **Per-term precision table:** for every strong term, the share of audited hits that are true positives. Propose demoting any term below about 80% to the weak tier, and show me before applying it.
- Number of corpus papers with `direct_mention`, split by corpus part (seed / candidate / background / random)
- **Seed recall:** what fraction of Level 1 seed papers in the corpus directly mention their own theory. (Seed papers that don't mention the theory are interesting: they're early Level 3 examples. List them.)
- Mention-strength distribution (how many papers mention it once versus many times)
- Abbreviation `unconfirmed` counts, to show how much noise the ambiguity rule removed
- **Precision audit:** 20 random direct-mention hits per theory, each showing the snippet, so I can mark true or false positive by eye
- Server-side trend table from Step 4
- The corpus-wide share of documents flagged `direct_mention` for **more than one** theory (overlap between theories)

**Checkpoint: show me the report and wait for my review of the precision audit.**

## Constraints
- Inspect before assuming (API behavior, XML structure). Show me examples.
- No silent drops. Every paper gets a row, and every failure a logged reason.
- Idempotent and cached. Commit after each step.
- Keep the scanner fast: precompile regexes, and do not load the whole corpus into memory.
- Level 2 is the baseline Level 3 must beat, so keep the `direct_mention` definition explicit and documented in the code, since we'll cite it in the demo.
- If any step would eat more than half a day, stop and propose a cut (smaller caps, fewer background queries) rather than pushing through.

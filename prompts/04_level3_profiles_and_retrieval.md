# Prompt 04: Level 3 (concept profiles, embeddings, retrieval)

**How to run:** start a fresh Claude Code session in the repo root and type:
`Read CLAUDE.md and reports/STATUS.md, then read prompts/04_level3_profiles_and_retrieval.md and follow it step by step. Stop at every checkpoint.`

**Your job in this stage:** edit each theory's core-claims text at the Step 1 checkpoint (this is the intellectual core of the project), and judge the first Level 3 results in Step 5.

**Budget:** about one day. If an estimate in Step 0 threatens that, take the smaller-scope option it offers.

---

Read CLAUDE.md and reports/STATUS.md first. Level 1 and Level 2 are done and `terms.yaml` is frozen: do not edit it. We are now building **Level 3: conceptual associations**, i.e. papers related to a theory that do not name it.

Key facts to respect:
- A paper "never names the theory" only if `names_theory_loosely = 0` for that theory (not merely `direct_mention = 0`). Weak mentions and close-term papers still count as naming it loosely.
- **No silver-set paper (direct mention) and no paper that names the theory loosely may be used to build a profile.** Profiles come from LoC text, seed abstracts and seed full texts, and my edited core claims only. The silver set is reserved for evaluation in the next prompt.
- Champagne (3 silver papers) and panpsychism (7 exclusive) are low-n. Build their profiles the same way, but expect qualitative evaluation.

## Step 0: Hardware, model choice, and seed reconciliation
1. **Hardware:** inspect this machine (chip, RAM, whether Apple MPS acceleration is available) and tell me.
2. **Embedding model:** recommend one local sentence-embedding model suited to scientific text (candidates: a general model such as BGE base or small, or SPECTER2). Test that it downloads and runs here (if the download is blocked, show me the exact error, since the network may be restricted). Benchmark it on 500 real chunks and give me an estimated total time for the planned corpus scope (Step 2). If the estimate is over about 2 hours, offer a smaller scope (abstract plus discussion only, or a capped sample of background papers) and wait for my choice.
3. **Seed reconciliation:** the Level 1 report says 11 full-text seeds fall in 1995-2015 (by any open-access route, including PDF links), but the database counts only 3 as full text in the corpus. Print all of them per theory with their route (Europe PMC XML, OA PDF link, abstract only), year and status, explain the gap, and update the seed figures in CLAUDE.md.

**Checkpoint: show me the hardware, the model recommendation with the benchmark and time estimate, and the seed table. Wait for my go-ahead.**

## Step 1: Concept profiles
For each of the five theories create `profiles/<theory>.yaml` with these parts:
- **loc_description:** the LoC description text from the database, as stored.
- **core_claims:** 5-8 short statements (1-2 sentences each) of what the theory claims, drafted by you from the LoC description and the seed abstracts only. Write them in plain mechanistic language (what is said to produce or explain consciousness, and how), not as a list of keywords. Mark each claim with its source (description or which seed). Do not use the silver set to write them. I will edit these by hand, so keep them clear and easy to change.
- **seed_passages:** abstracts of abstract-only seeds, and for seeds with full text available, their abstract plus introduction or discussion. Label each as profile-only.

Also create two contrast profiles:
- **generic_consciousness:** a neutral description of consciousness research in general (awareness, subjective report, neural correlates, anesthesia, disorders of consciousness), with no theory-specific claims.
- **other_theories:** for each theory, the set of the other four theories' profiles, for the optional cross-theory contrast.

**Checkpoint: show me all the profile files and wait. I will edit the core claims, then tell you to continue.**

## Step 2: Chunking
- Scope: all corpus papers 1995-2015 in `papers` (source `europepmc`; CORE papers will join later through the same table).
- Chunk the abstract, introduction and discussion sections (not every passage), at about 200-300 tokens with a small overlap, never crossing a section boundary. Papers without a parsed introduction or discussion contribute their abstract and the first part of the body.
- Store chunks in SQLite `chunks` (chunk_id, pmcid, section, position, year, source, corpus_part, text). Print how many chunks there are per section and per corpus part (seed, candidate, background, random).

## Step 3: Embed and index
- Embed all chunks with the approved model. Run it in the background, resumable, writing embeddings to disk in batches (file names include the model name and version). Print progress to a log so I can check it.
- Index with FAISS or plain numpy, whichever is simpler; the corpus is small enough that exact search is fine.
- Also embed each profile component (each core claim, each description paragraph, each seed passage) and the two contrast profiles.
- Test: embed a few known chunks and confirm that nearest-neighbor search returns them first.

## Step 4: Retrieval and scoring
Write `src/level3_concepts/retrieve.py` with `retrieve(theory, year_min, year_max, mode, k)`:
1. Score every chunk by its similarity to the theory's profile components. Aggregate to a paper-level score in two ways, so I can compare: the best chunk, and the mean of the top 3 chunks.
2. **Exclusion:** the Level 3 result set keeps only papers with `names_theory_loosely = 0` for that theory. Support a flag to include weak and close-term papers, shown with their tag.
3. **Contrastive score:** `score = sim(theory profile) - lambda * sim(generic_consciousness)`, lambda default 0.5 and configurable. Also support the optional version that subtracts the mean similarity to the other four theories. Return both the raw and the contrastive scores.
4. Return per paper: PMCID, title, year, journal, corpus part, raw and contrastive scores, the best-matching passage, and a list of other theories it names (so cross-theory overlap is visible).
5. Respect the time window arguments (1995-2015 for now).

## Step 5: First look
Write `reports/level3_first_look.md` with, for each theory, the **top 20 papers by raw score and the top 20 by contrastive score** (title, year, section of the best passage, a 200-character snippet), and print:
- The overlap between the two top-20 lists.
- The share of each top-20 coming from each corpus part (seed, candidate, background, random). If the results are almost all from the candidate pool, say so, since that suggests the pool queries are doing the work.
- For each theory, how many of the top 20 name another theory.
- A reminder that Champagne and panpsychism results are exploratory.

**Checkpoint: show me the report. I will read the results and judge them. Wait for my feedback. Do not tune lambda or change profiles on your own.**

## Constraints
- Inspect before assuming. Show me real examples.
- Never use silver-set or loosely-naming papers in any profile.
- No silent drops: log every paper that has no chunks and why.
- Everything cached, resumable and idempotent. Commit after each step and update reports/STATUS.md.
- If a step would take more than half a day, stop and propose a cut.
- Public data only.

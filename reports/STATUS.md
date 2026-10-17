# STATUS (FINAL, 2026-10-14: tag v1.0-submission)

## FINAL STATE
- **Done:** Level 1 (LoC references resolved), Level 2 (term scanner, silver sets, audits), Level 3 (profiles, V4 retrieval, masked-term evaluation, discriminability, LLM judge on the 1995-2015 top 30 per theory), 2016-2025 out-of-time test and window trends, app exports in `results/`, Streamlit app, demo script, README, and the exploratory CORE philosophy pilot (Steps 0-6, `reports/core_pilot.md`, `results/philosophy_pilot_*.csv`). `src/terms.yaml` and the profiles are frozen. Nothing from CORE is in the main tables or the app.
- **ON HOLD:** the blind LLM judge on CORE text. It waits for answers from **CORE** (licence for research use; the API has no license field and its terms limit data to machine processing) and from **ASU** (AI governance). Do not run or prepare more judging, do not read `data/judge_core/` before then. The packets there pre-date the near-duplicate collapse, so a rebuild would differ slightly.
- **Not done / future work:** OA-PDF seed text extraction, hand labels beyond the sheet, citation graph, `reports/abbreviation_audit.csv` labelling.
- **App:** `python3.11 -m venv .venv; .venv/bin/python -m pip install -r app/requirements.txt; .venv/bin/python -m streamlit run app/app.py` (streamlit and pandas only; reads `results/`; verified in a clean venv from a `git archive` checkout: no exceptions, no torch or sentence-transformers imported).
- **Tests:** `.venv/bin/python -m pytest -q` (needs the root `requirements.txt`). `tests/test_tracked_text.py` guards `results/`, `reports/`, `docs/` against pasted source text (cell length, banned columns, quotation length, and a shingle check against the CORE texts when `data/core_pilot.db` exists).

## HOW TO REGENERATE EVERYTHING (all under `.venv`, secrets in `.env`; stages are idempotent and cached; `data/` is gitignored)
1. Level 1: `src/level1_extract.py`, `parse.py`, `resolve.py`, `oa.py` (see `reports/level1_resolution.md`).
2. Corpus 1995-2015: `python -m src.corpus.build seeds candidates background random fetch parse stats`; Level 2: `python -m src.level2_terms.scan` then `trends`, `abbrev_audit`, `report`.
3. Profiles and embeddings: `python -m src.level3_concepts.make_profiles` (never `--force` over reviewed claims), `chunk`, `embed` (caffeinate; ~50 min), `embed_profiles`, `windows --apply-flags`, `first_look`.
4. Evaluation: `python -m src.eval.positives`, `run_dev`, `run_test`, `matrix`, `labeling`; judge: `python -m src.judge.build` (blind) then `src.judge.analyze` after judging.
5. 2016-2025: `python -m src.corpus.build_late candidates background random fetch parse trim stats`, `python -m src.level3_concepts.late chunk | embed | selftest`, `python -m src.eval.late masked | report`, `python -m src.level3_concepts.retrieve_window`.
6. Exports and app: `python -m src.export`, `python app/build_descriptions.py`, `python app/build_demo.py`.
7. CORE pilot (needs `CORE_API_KEY`; first pull takes ~45 min of throttled API calls, cached afterwards): `python -m src.corpus.build_core`, `python -m src.corpus.core_scan`, `python -m src.corpus.core_l3 chunk | embed | selftest`, `python -m src.eval.core_pilot masked | report`, `python -m src.eval.core_export`. Do NOT run `python -m src.eval.core_pilot packets` while the judge is on hold.


Read this at the start of every session. All agreed Level 2 term changes are applied and the live DB is rescanned.
`src/terms.yaml` is FROZEN: no further edits unless the user asks (record the reason).

## WHERE WE STOPPED (2026-10-11, end of day)
Prompt 05 (Level 3 evaluation) is complete through Step 6 and everything is committed (last code commit `6b804f3`). **Nothing is running**
(no embedding or eval jobs; all caches are on disk in gitignored `data/eval/` and `data/embeddings/`). We are waiting on the USER to hand-label
`reports/labeling_sheet.csv` (70 rows; columns `label` = R/G/O and `note` empty). Do not label for them.

Finished tonight (details in the Prompt 05 section below):
- V4 (equal component weights, no contrast) approved as the pre-registered selection; amendment logged in `reports/eval_plan.md`.
- Masked-positive evaluation: `reports/level3_eval_dev.md`, `reports/level3_eval_test.md` (V4, V0, V1, V2, V5, BM25; both AUCs; candidate-only AUC is the more informative number).
- Discriminability matrix (V4 and V5): `reports/level3_discriminability.md`. V4 diagonal wins 5/5; V5 wins 4/5 on all negatives (GWT column fails).
- Labeling sheet and V4 top-20: `reports/labeling_sheet.csv`, `reports/level3_top20.md`. 72 tests pass.
Open observations to carry forward (not decisions): on predictive processing the candidate-only AUC favours V5 (0.874) and V1 (0.854) over V4 (0.760);
IIT, panpsychism and Champagne profiles partly retrieve each other's positives; the labels are the check on generic drift.

## NEXT STEPS, in order
1. USER: hand-label `reports/labeling_sheet.csv` (R relevant conceptual neighbor, G generic consciousness/neuroscience, O off-topic; 20 per theory was the target, 10 per variant on the sheet). Cut order allows 10 per theory.
2. Compute precision of R per theory and per variant (V4 vs V5 for GWT/PP) from the labelled sheet; decide, with the user, whether to keep V4 or adopt a contrast variant for the final Level 3 score. Any change is a new, logged amendment, not a silent switch.
3. LLM judge on the top ~30 per theory under the chosen variant (Oct 13 in the schedule); it must reject generic-consciousness papers and write a one-line parallel explanation. Final score = embedding score + judgment.
4. Window / prediction experiment (Oct 14): profiles from LoC text + the 1995-2015 corpus, tested on 2016-2025 silver papers with terms masked.
5. Streamlit UI and demo script (Oct 15); buffer and submit (Oct 16).
6. Still open and optional: CORE pilot (panpsychism, Champagne) is the first cut if behind; `reports/abbreviation_audit.csv` is unlabelled (no rule change planned); the 8 OA-PDF seeds are profile-only with text not extracted.
Standing rules: `src/terms.yaml` is FROZEN; never read or select on test results; keep the "never mentions" claims on `names_theory_loosely = 0`.

## Finished
- **Level 1** (LoC scrape, reference parsing, DOI/PMCID resolution). Report: `reports/level1_resolution.md`.
  Seed gap RECONCILED (prompt 04 Step 0): 11 full-text seeds in 1995-2015 by any OA route = Champagne 4, GWT 1, IIT 2,
  Panpsychism 2, PP 2. Only 3 are Europe PMC XML in the corpus (IIT PMC4014402, PMC4387509; PP PMC3347222) and all 3 are
  silver-set papers. The other 8 are OA-PDF links (profile-only; text not yet extracted). CLAUDE.md updated.
- **Corpus Step 1** (Europe PMC, 1995-2015): 7,794 papers (seed 3, candidate 1,009, background 4,891, random 1,907).
  Report: `reports/corpus_step1.md`.
- **Level 2, Steps 1-7, as of commit `e292d3e`:**
  - `terms.yaml` v2 approved: `close_term`, `adjacent`, `landmark_refs`, `domain_context` (N=2).
  - Scanner (`src/level2_terms/scan.py`) run over all 7,793 papers with text (1 logged `no_text`); tables `term_hits`,
    `paper_flags`, `scan_log`, view `multi_theory_papers`. The `direct_mention` definition is in the scan.py docstring.
  - Term-masking utility (`mask.py`): blanks strong, close and abbreviation terms; 0 residual terms on all 444 silver papers.
  - Server-side Europe PMC counts per year 1995-2025 (`term_counts_by_year`); query API (`query.py`: `get_mentions`,
    `direct_mention_ids`); silver subsets (`silver.py`: all, exclusive, primary, consciousness, consciousness_any).
  - Hand-labelled precision audit (`reports/precision_audit_labels.csv`), abbreviation audit sheet (unlabelled),
    overlap list (`reports/level2_overlap_papers.csv`), report `reports/level2_terms.md`. 57 tests pass.
  - Silver-set sizes (direct mentions): GWT 173, Predictive Processing/FEP 244, IIT 23, Panpsychism 17, Champagne 3.
    Panpsychism and Champagne are too small for quantitative claims (report qualitatively).

## Level 2 final changes (applied 2026-10-10)
- "predictive machine" demoted strong -> close_term (PMC3343024 is now close-only).
- `needs_corroboration: [predictive processing]`: bare phrase counts as direct only in title/abstract or with another
  strong/close term. Otherwise `weak_mention` (43 papers): not in the silver set, tier `strong_uncorroborated`.
  New `paper_flags` columns: `weak_mention`, `any_mention_level` (direct > weak > close > none), `names_theory_loosely`
  (direct OR weak OR close). Level 3 filter: `query.names_theory_ids(theory)`. Any "never names the theory" claim must
  use `names_theory_loosely = 0`, NOT `direct_mention = 0`.
- "information integration theory" added as an IIT strong term (all 17 corpus papers hand-labelled Y). IIT 23 -> 39.
- PP direct 244 -> 200 (43 weak + 1 close-only). No hand-labelled positive is lost.
- Three of the 15 audited dropped papers were labelled Y (PMC4371585, PMC4142339, PMC6089086) and PMC3840313 is `?`;
  they are weak (accepted cost of the rule). Unconfirmed PP/PC abbreviation rows: 20/20 labelled N; abbreviation rule unchanged.
- PP consciousness-relevant subset: PRIMARY = strict (title/abstract or >= 3 occurrences) = 58 of 200;
  secondary: lenient (>= 1) = 98, full = 200.
- 61 tests pass. Pre-rescan DB backup: `data/excavator.pre_final_rescan.db` (gitignored).
- Open: `reports/abbreviation_audit.csv` is still unlabelled (no rule change planned).

## Superseded 2026-10-10 'Next' (done: chunking, embeddings, profiles, evaluation)
See WHERE WE STOPPED and NEXT STEPS above.

## Prompt 04 (Level 3) progress
- Step 0 done (2026-10-10), awaiting go-ahead: M2 / 8 GB / MPS available; sentence-transformers 6.1 + faiss installed in `.venv`
  (venv had no pip; bootstrapped with ensurepip). bge-small 105 chunks/s (~17 min), bge-base 35/s (~50 min) for ~104.7k chunks.
- Step 1 done (2026-10-10), AWAITING USER EDITS to `profiles/*.yaml` core_claims (do not regenerate: `make_profiles.py` refuses to
  overwrite without --force). Decisions: bge-base-en-v1.5 (query prefix for claims, none for chunks), numpy, caffeinate,
  resumable batches; the 3 in-corpus seeds are excluded from profiles entirely; OA-PDF/abstract-only seeds use abstracts
  only (labelled profile-only, no PDF pipeline). Chunking + embedding start only after the user approves the profiles.
- Steps 2-3 launched 2026-10-11: `chunks` table built (105,289 chunks, 7,783 of 7,794 corpus papers; 11 logged in `chunk_log`).
  Embedding job (`src.level3_concepts.embed`, bge-base, caffeinate, 52 shards of 2048, resumable) writes to
  `data/embeddings/BAAI_bge-base-en-v1.5__a5beb1e3/`, log `data/logs/embed.log`. To resume after a stop, rerun
  `caffeinate -i .venv/bin/python -m src.level3_concepts.embed >> data/embed.stdout 2>&1 &` (finished shards are skipped).
  Four weak seeds moved to `excluded_seeds`. Pending: user confirms the LoC sub-page keep/drop table (`use_in_profile` flags),
  then window splitting with equal per-theory caps and profile embeddings.
- Sub-page flags applied 2026-10-11 (`profiles/*.yaml: loc_description_pages`, `use_in_profile`; text never deleted). Dropped pages:
  IIT koch-compares-...-with-panpsychism; Panpsychism faggin-..., panpsychism-additional-theories; PP ostendorf-...; plus the Champagne
  Peirce page's "note-on-placement" segment. Windows (~150 words, within pages) capped at 11 per theory (= GWT's 11) and spread over
  kept pages (`src/level3_concepts/windows.py`). Weights in `profiles/config.yaml` (claims 1.0, windows 0.5, seeds 0.5).
  NEXT (after the user says claim edits are done): embed profile components (claims with the BGE query prefix, windows/seeds without),
  then Step 4. Do not run Step 4 before that.
- DECISION 2026-10-11 (scoring, Step 4): option (b). For each profile component, z-score its cosine to EVERY embedded chunk (all ~105k, before
  any exclusion); chunk score = max over components of weight * z (claims 1.0, description windows 0.5, seed abstracts 0.5). generic_consciousness
  is z-scored the same way; contrastive = z_theory - lambda * z_generic (lambda 0.5, configurable); same for the optional other-theories contrast.
  Keep raw cosine in output. Step 5 report adds per-theory top-20 weighted vs claims-only with overlap count. Do NOT tune lambda/weights/profiles.
  WAITING for the user to say the claim edits are done; then: confirm chunk job finished (log + 52 shards), embed profile components
  (claims with BGE query prefix, windows/seeds without), run Steps 4-5, stop at the first-look checkpoint.
- 2026-10-11: claims approved and applied (panpsychism 7 claims). Chunk embeddings finished (52/52 shards, 105,289 x 768, self-retrieval test passed).
  Profile components embedded (106: claims with BGE query prefix; windows/seeds/generic without) -> `data/embeddings/profiles__*.npz`.
  Steps 4-5 run: `src/level3_concepts/retrieve.py` (z-scored weighted max, lambda 0.5 from `profiles/config.yaml`, not tuned),
  report `reports/level3_first_look.md`. AT FIRST-LOOK CHECKPOINT: waiting for the user's judgement. Do not tune lambda/weights/profiles.
  Known: weighted vs claims-only top-20 overlap is 20/20 for all theories (windows/seeds at 0.5 weight never win the max).

## Prompt 05 (Level 3 evaluation) progress
- Step 0 done and approved (2026-10-11): `reports/eval_plan.md` (pre-registered; user additions: neutral deletion masking + masked-vs-unmasked control, corpus-part mix, candidate-only AUC).
- Steps 1-2 done: `src/eval/mask.py` (deletion, terms + landmark authors incl. in-text citations), `src/eval/positives.py`; exclusive positives GWT 153, PP 197, IIT 17, panpsychism 7, Champagne 3; 5,707 masked chunks embedded in `data/eval/` (gitignored). Dev/test split seed 20261011: GWT 76/77, PP 98/99.
- Step 3 done: `src/eval/run_dev.py` -> `reports/level3_eval_dev.md`. Rule selects **V4**. AT DEV CHECKPOINT: waiting for user approval before the test halves are touched (Step 4). Do not read test results before approval.
- 2026-10-11 (later): V4 APPROVED as the selected variant. Amendment logged in `reports/eval_plan.md` (test variants V4/V0/V1/V2/V5/BM25; both AUCs side by side, candidate-only AUC is the more informative; no selection on test; matrix for V4 and V5; labeling sheet = top 10 per theory, V4 for IIT/panpsychism/Champagne, V4 and V5 for GWT/PP).
- Masking bug found while re-showing examples (a removed trailing citation also ate the enclosing ")"; no term leaked). Fixed in `src/eval/mask.py`, masked chunks re-embedded (old copy in `data/eval_old/`), dev rerun: mean AUC shifted by <= 0.0014 per variant, V4 still selected.
- Step 4 done: `reports/level3_eval_test.md`. Step 5 done: `reports/level3_discriminability.md` (V4 and V5). Step 6 done: `reports/labeling_sheet.csv` (70 rows: 10 each, V4 for Champagne/IIT/Panpsychism; V4 and V5 for GWT/PP; empty label R/G/O and note columns), `reports/level3_top20.md` (V4). STOPPED: waiting for the user (hand-labelling next; user labels, do not label for them).

## Prompt 06 (LLM judge) progress (2026-10-12)
- Step 0 done and approved: `src/judge/build.py` (seed 20261012) wrote 26 packet batches to `data/judge/packets/` (gitignored) and `data/judge/method_membership.csv` (DO NOT OPEN before Step 4). 209 items incl. 21 repeats (each repeat in a later batch than its original; verified). BM25 only for GWT and PP.
- Step 1 done and approved: `prompts/judge_rubric.md` (includes one-line descriptions of the five theories for `better_fit_theory`).
- Step 2 NOT started: judge batch_01..26 in order, writing `data/judge/judgments/batch_NN.json`. Stay blind: do not open `reports/labeling_sheet.csv`, the membership file, or any score/rank/result file until Step 4.
- Step 4 extras requested by the user: report the number of items with no abstract, split by method, and say whether that could bias V4 vs BM25. Do not pre-label packets in checkpoint messages.

## Prompt 06 Steps 4-5 DONE (2026-10-12)
- Blindness ended. `src/judge/analyze.py` -> `reports/level3_judge.md` (verdicts per theory, V4 vs BM25 with bootstrap CIs, repeats, agreement with the hand labels, corpus part, flags, app exports, PP014 sensitivity, caveats).
- `results/judgments.csv` (tracked, pmcid filled via the membership file, no method column) and `data/judge/judgments_final.csv` (gitignored, adds is_repeat); `judgments.pmcid` filled in `data/project.db`.
- Headline (PP014 revised to G): R share top 30 under V4: Champagne 17%, GWT 53%, IIT 20%, panpsychism 17%, PP 40%. V4 vs BM25: GWT +27 pts [+3, +50]; PP -3 pts [-27, +20] (a tie). Repeats 21/21 agree (same-session, an upper bound). Judge vs hand labels (55 matched of 70): 65% agree, kappa 0.44 (R vs not-R 0.55). PP014 sensitivity changes no conclusion.
- Open: `reports/labeling_sheet.csv` has uncommitted edits by the user (stray title line removed); label provenance in git says AI-proposed, user-reviewed. 15 labelled V5 rows were never judged (outside the V4/BM25 top 30).
- Next: Oct 13 hand-labeling/decision on the final Level 3 score; window experiment Oct 14.

## Prompt 07 (windows, out-of-time test, exports) progress (2026-10-12)
- Step 0 done and approved; out-of-time test pre-registered in `reports/eval_plan.md` (commit a9b8e7a). User decisions: `corpus_membership.window` column (done, idempotent migration + test), equal per-year random quota, BM25 stats from the 2016-2025 chunk set (note in report). Step 6 additions: `results/level2_mentions.csv` 2016-2025 rows labelled as a capped sample (sample_cap column); any 2016-2025 mention totals in summary_metrics and app tables come from the full server-side `term_counts_by_year`, never the capped sample. Out-of-time report must restate that positives are almost all candidate-pool papers so the candidate-only AUC is the more informative number.
- Step 1 done: `src/corpus/build_late.py` (window='2016-2025'): 5,438 papers (candidate 1,482, background 2,973, random 1,000 = 100/year). Random pool sampled from random weekly FIRST_PDATE slices per year (week-clustered, not uniform). 3 fetch failures (HTTP 500, logged; scan status no_text). Backup before the build: `data/excavator.pre_late_window.db`. Logs `data/logs/late_fetch.log`, `late_scan.log`.
- Step 2 done: frozen scanner run over new papers (1995-2015 rows untouched, 7,794 skipped). AT STEP 2 CHECKPOINT: waiting for the user. Do not chunk/embed (Step 3) before approval.
- Step 3 done: `chunks_late` (83,691 chunks, 5,432 of 5,438 papers; 6 unchunked, logged in `chunk_log_late`), embeddings in `data/embeddings_late/` (41 shards; self-retrieval test passed, norms ok). Code: `src/level3_concepts/late.py`; `embed.py` now takes table/dir/log arguments (1995-2015 embeddings untouched).
- Step 4 done: `reports/level3_out_of_time.md` (V4/V5/BM25, with and without 2020-2022; side by side with 1995-2015), `reports/level3_discriminability_late.md` (diagonal wins 5/5 in all 8 matrices). Exclusive positives 2016-2025: Champagne 25, GWT 213, IIT 129, panpsychism 61, PP 151 (excluding 2020-22: 18/143/87/33/98). Headline: V4 candidate-only AUC dropped for all five (0.915->0.732, 0.809->0.744, 0.893->0.764, 0.973->0.832, 0.760->0.678) but stays well above 0.5; BM25 ahead of V4 on PP (0.720 vs 0.678). Code `src/eval/late.py`; masked cache `data/eval_late/`.
- Step 5 done: `reports/level3_windows.md` (mention trends from `term_counts_by_year`, `src/level3_concepts/retrieve_window.py` V4 over 1995-2015/2020/2025; the 1995-2015 window reproduces `level3_top20.md` 20/20 for all theories; new-paper demo examples not judged). STOPPED before Step 6 (exports), waiting for the user.
- Step 6 done (2026-10-12): `src/export.py` writes `results/level1_references.csv` (145), `level2_mentions.csv` (2,748, with `sample_cap`/`sample_note`), `level3_top.csv` (450, explicit `judged` column; only the 1995-2015 V4 top 30 are judged), `window_trends.csv` (155), `summary_metrics.csv` (V4/BM25 candidate-only AUC with CI and n for both periods; mention totals from server-side counts only), `discriminability.csv` (100, V4, both periods and pools), plus `results/README.md`. PROMPT 07 COMPLETE; next in the schedule: Streamlit UI and demo script (prompt 08). Waiting for the user.

## Prompt 09 (CORE philosophy pilot, Champagne + panpsychism) progress (2026-10-14)
- Exploratory, separate: `data/core_pilot.db` (core_* tables), `data/embeddings_core/`, `data/eval_core/`, `data/judge_core/` (all gitignored). CORE text never in tracked files; no snippets. `src/corpus/{core,build_core,core_scan,core_l3}.py`, `src/eval/core_pilot.py`. Pre-registration: `reports/eval_plan.md` addenda (a)-(d) (2026-10-14). CLAUDE.md corrected (no `Source` interface was built).
- Corpus: 2,213 papers (candidates 229 = Champagne 99 + panpsychism 130, adjacent background 1,488, distractors 496 "approximately random within relevance-ordered hits"); license "unknown" (API has no field); 78,278 chunks embedded (self-retrieval passed). Boilerplate strip: 446 repeated lines, 4,154 instances, 803 papers.
- Silver (exclusive, ref split): Champagne A 77 / B (consciousness-relevant) 18 (n < 20, exploratory) / C 65; panpsychism A 89 / B 80 / C 83. Labels: `reports/core_pilot_labels.csv` (withheld in the public release) (Champagne 1 Y, 8 P, 1 N; panpsychism 9 Y, 1 N).
- Step 4 report `reports/core_pilot.md` (primary = AUC vs adjacent-background negatives; year-matched sensitivity; 2x2 matrix; counts by repository and period; top-30 lists, unjudged). Champagne full positive set is mostly general Peircean-semiotics papers; consciousness claims rest on set B.
- Step 5: blind judge packets for the top 20 per theory (+10% repeats; 6 batches) in `data/judge_core/packets/`, mapping in `data/judge_core/membership.csv`. NOT read, NOT judged. The judge must be run in a separate fresh session with `prompts/judge_rubric.md`.
- Step 6 DONE: `results/philosophy_pilot_top.csv` (withheld in the public release; 60 rows, near-duplicates collapsed, titles cleaned, judged = false) and `results/philosophy_pilot_metrics.csv` (63 rows: counts, sets A/B/C, V4/BM25 AUC with CIs for the primary and candidate-pool metrics, year-matched sensitivity); separate pilot section in `results/README.md` (licence caveat, unknown license field, exploratory status, Champagne = mostly general Peircean semiotics). Near-duplicates: 22 pairs / 38 papers / 20 removable = 0.9% (< 2%, so no collapsed rerun). `src/corpus/core_dups.py`, `src/eval/core_export.py`. App unchanged.
- **BLIND JUDGE ON HOLD** until CORE and ASU respond: do not run or prepare further judging. Packets already in `data/judge_core/` (built before the duplicate collapse, unread) stay untouched. The report's top-30 lists are now collapsed, so a future packets rebuild would differ slightly from those packets.
- Open: answer from CORE (licence for research use) and from ASU (AI governance) before any further use of CORE text.

# Submission: Consciousness Theory Literature Excavator

## What is in the repo
Pipeline (`src/`), Streamlit app (`app/`), app-ready tables (`results/`, columns in `results/README.md`), one report per stage
plus `reports/STATUS.md`, concept profiles (`profiles/`), prompts (`prompts/`), tests (`tests/`), demo script (`docs/demo_script.md`).
Full texts, embeddings and the database are not included. No licence is granted yet (all rights reserved).

## Run the app
```
python3.11 -m venv .venv
.venv/bin/python -m pip install -r app/requirements.txt
.venv/bin/python -m streamlit run app/app.py
```

## Headline results (generated from `results/summary_metrics.csv`)
Candidate-only AUC of the conceptual method (V4) versus a BM25 keyword baseline on term-masked silver-set papers (n positives in brackets).
Judge column: share of the 1995-2015 V4 top 30 rated relevant (`judged_R_share_v4_top30_1995_2015`).

| Theory | LoC refs | Full-text seeds | V4 AUC 1995-2015 (n) | BM25 1995-2015 | V4 AUC 2016-2025 (n) | BM25 2016-2025 | Judge R share |
|---|---|---|---|---|---|---|---|
| champagne_semiotic | 29 | 8 | 0.915 (3) | 0.705 | 0.732 (25) | 0.695 | 0.17 |
| global_workspace | 13 | 3 | 0.809 (77) | 0.673 | 0.744 (213) | 0.690 | 0.53 |
| integrated_information | 22 | 7 | 0.893 (17) | 0.858 | 0.764 (129) | 0.738 | 0.20 |
| panpsychism | 56 | 13 | 0.973 (7) | 0.861 | 0.832 (61) | 0.705 | 0.17 |
| predictive_processing_fep | 25 | 4 | 0.760 (99) | 0.660 | 0.678 (151) | 0.720 | 0.40 |

## CORE philosophy pilot (generated from `results/philosophy_pilot_metrics.csv`)
Exploratory; Champagne and panpsychism only; set A (all exclusive), candidate-pool negatives. CORE text is not redistributed.

| Theory | V4 AUC [95% CI] | BM25 AUC | n positives | n negatives |
|---|---|---|---|---|
| champagne_semiotic | 0.727 [0.644, 0.804] | 0.479 | 77 | 136 |
| panpsychism | 0.888 [0.846, 0.925] | 0.862 | 89 | 112 |

## Main limitations
- Open access only; coverage skews to neuroscience, psychology and medicine. Philosophy-heavy theories are thin.
- Small samples for Champagne, IIT and panpsychism in 1995-2015. Negatives are unlabeled, so AUCs are lower bounds.
- The judge is an LLM, not ground truth, and only the 1995-2015 top 30 per theory were judged.
- Keyword ranking is competitive; out-of-time AUC dropped for every theory. Profiles use current LoC text, so the out-of-time test checks generalization, not forecasting.
- CORE text is PDF-derived and messy; the pilot is exploratory and kept out of the main tables and app.

## Open items
- **Licence:** awaiting answers from CORE (research-use licence) and the institution (ASU AI governance).
- **Judge on CORE text is on hold** until those answers arrive.
- Future work: OA-PDF seed text extraction, citation graph, abbreviation audit labelling.

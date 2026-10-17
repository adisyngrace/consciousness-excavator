"""Generate SUBMISSION.md; headline numbers are read from results/*.csv."""
from pathlib import Path
import pandas as pd

R = Path(__file__).resolve().parents[1]
sm = pd.read_csv(R / "results/summary_metrics.csv")
pp = pd.read_csv(R / "results/philosophy_pilot_metrics.csv")

rows = []
for _, r in sm.iterrows():
    rows.append(
        f"| {r.theory} | {r.loc_references} | {r.loc_fulltext_seeds_any_oa_route} "
        f"| {r.V4_cand_auc_1995_2015:.3f} ({r.cand_auc_1995_2015_n_positives}) | {r.BM25_cand_auc_1995_2015:.3f} "
        f"| {r.V4_cand_auc_2016_2025:.3f} ({r.cand_auc_2016_2025_n_positives}) | {r.BM25_cand_auc_2016_2025:.3f} "
        f"| {r.judged_R_share_v4_top30_1995_2015:.2f} |")

c = pp[(pp.record_type == "auc") & (pp.positive_set == "A") & pp.negatives.str.contains("candidate-pool")]
prow = []
for (t, ), g in c.groupby(["theory"]):
    v4 = g[g.variant == "V4"].iloc[0]
    bm = g[g.variant == "BM25"].iloc[0]
    prow.append(f"| {t} | {v4.value:.3f} [{v4.ci_lo:.3f}, {v4.ci_hi:.3f}] | {bm.value:.3f} | {int(v4.n_positives)} | {int(v4.n_negatives)} |")

out = f"""# Submission: Consciousness Theory Literature Excavator

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
""" + "\n".join(rows) + f"""

## CORE philosophy pilot (generated from `results/philosophy_pilot_metrics.csv`)
Exploratory; Champagne and panpsychism only; set A (all exclusive), candidate-pool negatives. CORE text is not redistributed.

| Theory | V4 AUC [95% CI] | BM25 AUC | n positives | n negatives |
|---|---|---|---|---|
""" + "\n".join(prow) + """

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
"""
(R / "SUBMISSION.md").write_text(out)

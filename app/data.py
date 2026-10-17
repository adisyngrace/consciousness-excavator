"""Data layer for the viewer app: loads and validates the tracked tables in results/ (nothing else)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parent.parent / "results"

THEORIES: dict[str, str] = {
    "champagne_semiotic": "Champagne's semiotic account",
    "global_workspace": "Global Workspace Theory",
    "integrated_information": "Integrated Information Theory",
    "panpsychism": "Panpsychism",
    "predictive_processing_fep": "Predictive Processing / Free Energy Principle",
}
WINDOWS: dict[str, int] = {"1995-2015": 2015, "1995-2020": 2020, "1995-2025": 2025}
EXPLORATORY_N = 20  # a period or metric with fewer positives than this is tagged "exploratory"

REQUIRED: dict[str, list[str]] = {
    "level1_references.csv": ["theory", "raw_reference", "parsed_title", "year", "doi", "pmcid",
                              "resolution_status", "oa_fulltext", "oa_route"],
    "level2_mentions.csv": ["theory", "window", "pmcid", "title", "year", "journal", "mention_tier",
                            "mention_strength", "first_hit_section", "snippet", "sample_cap", "sample_note"],
    "level3_top.csv": ["theory", "window", "rank", "pmcid", "title", "year", "score_v4", "best_claim_id",
                       "best_claim_text", "snippet", "other_theories_named", "judged", "judge_verdict",
                       "judge_confidence", "judge_reason", "judge_evidence"],
    "window_trends.csv": ["theory", "year", "hits", "total_oa_papers", "rate_per_10k"],
    "summary_metrics.csv": ["theory", "loc_references", "loc_fulltext_seeds_any_oa_route",
                            "silver_exclusive_1995_2015_corpus", "silver_exclusive_2016_2025_capped_sample",
                            "silver_2016_2025_sample_cap", "V4_cand_auc_1995_2015", "V4_cand_auc_1995_2015_ci_lo",
                            "V4_cand_auc_1995_2015_ci_hi", "V4_cand_auc_2016_2025", "V4_cand_auc_2016_2025_ci_lo",
                            "V4_cand_auc_2016_2025_ci_hi", "BM25_cand_auc_1995_2015",
                            "BM25_cand_auc_1995_2015_ci_lo", "BM25_cand_auc_1995_2015_ci_hi",
                            "BM25_cand_auc_2016_2025", "BM25_cand_auc_2016_2025_ci_lo",
                            "BM25_cand_auc_2016_2025_ci_hi", "cand_auc_1995_2015_n_positives",
                            "cand_auc_2016_2025_n_positives", "judged_R_share_v4_top30_1995_2015", "judged_n"],
    "discriminability.csv": ["period", "pool", "variant", "row_profile", "column_positives",
                             "n_column_positives", "mean_percentile_rank", "is_diagonal"],
    "theory_descriptions.csv": ["theory", "theory_name", "excerpt", "source_url"],
}


class DataError(RuntimeError):
    """A results file or column the app needs is missing."""


def _read(name: str, results_dir: Path) -> pd.DataFrame:
    path = results_dir / name
    if not path.exists():
        raise DataError(f"Missing file: {path}. Run `python -m src.export` and app/build_descriptions.py.")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in REQUIRED[name] if c not in df.columns]
    if missing:
        raise DataError(f"{name} is missing columns: {missing}")
    return df


@lru_cache(maxsize=4)
def load_all(results_dir: Path = RESULTS) -> dict[str, pd.DataFrame]:
    """Load and validate every table once; numeric columns are converted here."""
    t = {name: _read(name, results_dir) for name in REQUIRED}
    for name, cols in {"level1_references.csv": ["year"], "level2_mentions.csv": ["year", "mention_strength"],
                       "level3_top.csv": ["rank", "year", "score_v4"],
                       "window_trends.csv": ["year", "hits", "total_oa_papers", "rate_per_10k"],
                       "discriminability.csv": ["n_column_positives", "mean_percentile_rank"]}.items():
        for c in cols:
            t[name][c] = pd.to_numeric(t[name][c], errors="coerce")
    return t


def _check_theory(theory: str) -> None:
    if theory not in THEORIES:
        raise KeyError(f"Unknown theory {theory!r}")


def _check_window(window: str) -> int:
    if window not in WINDOWS:
        raise KeyError(f"Unknown window {window!r}")
    return WINDOWS[window]


def pmc_url(pmcid: str) -> str:
    return f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"


# ---- header ---------------------------------------------------------------------------------------------------
def description(theory: str, d: dict | None = None) -> dict:
    _check_theory(theory)
    df = (d or load_all())["theory_descriptions.csv"]
    return df[df.theory == theory].iloc[0].to_dict()


def exclusive_counts(theory: str, d: dict | None = None) -> dict:
    """Exclusive direct-mention paper counts for both periods, each with an 'exploratory' flag."""
    _check_theory(theory)
    s = (d or load_all())["summary_metrics.csv"]
    r = s[s.theory == theory].iloc[0]
    n1, n2 = int(r["silver_exclusive_1995_2015_corpus"]), int(r["silver_exclusive_2016_2025_capped_sample"])
    return {"n_1995_2015": n1, "n_2016_2025": n2, "exploratory_1995_2015": n1 < EXPLORATORY_N,
            "exploratory_2016_2025": n2 < EXPLORATORY_N, "cap_note": r["silver_2016_2025_sample_cap"]}


# ---- tab 1 ----------------------------------------------------------------------------------------------------
def references(theory: str, d: dict | None = None) -> pd.DataFrame:
    _check_theory(theory)
    df = (d or load_all())["level1_references.csv"]
    return df[df.theory == theory].reset_index(drop=True)


def reference_summary(theory: str, d: dict | None = None) -> dict:
    r = references(theory, d)
    return {"total": len(r), "non_article": int((r.resolution_status == "non_article").sum()),
            "open_fulltext": int((r.oa_fulltext == "yes").sum()),
            "europe_pmc_fulltext": int((r.oa_route == "europe_pmc").sum())}


# ---- tab 2 ----------------------------------------------------------------------------------------------------
def mentions(theory: str, window: str, tiers: list[str] | None = None, min_strength: int = 0,
             d: dict | None = None) -> pd.DataFrame:
    """Level 2 rows filtered on the year column (not the window label)."""
    _check_theory(theory)
    end = _check_window(window)
    df = (d or load_all())["level2_mentions.csv"]
    m = (df.theory == theory) & (df.year <= end) & (df.mention_strength >= min_strength)
    if tiers is not None:
        m &= df.mention_tier.isin(tiers)
    return df[m].sort_values(["mention_strength", "year"], ascending=[False, True]).reset_index(drop=True)


def includes_capped_sample(window: str) -> bool:
    """True when the view can contain 2016-2025 rows (a capped sample, not totals)."""
    return _check_window(window) > 2015


def sample_cap_note(theory: str, d: dict | None = None) -> str:
    return exclusive_counts(theory, d)["cap_note"]


def trends(theory: str, d: dict | None = None) -> pd.DataFrame:
    _check_theory(theory)
    df = (d or load_all())["window_trends.csv"]
    return df[df.theory == theory].sort_values("year").reset_index(drop=True)


# ---- tab 3 ----------------------------------------------------------------------------------------------------
def top_papers(theory: str, window: str, judged_relevant_only: bool = False, d: dict | None = None) -> pd.DataFrame:
    _check_theory(theory)
    _check_window(window)
    df = (d or load_all())["level3_top.csv"]
    out = df[(df.theory == theory) & (df.window == window)]
    if judged_relevant_only:
        out = out[(out.judged == "true") & (out.judge_verdict == "R")]
    return out.sort_values("rank").reset_index(drop=True)


def judge_counts(theory: str, window: str, d: dict | None = None) -> dict:
    t = top_papers(theory, window, d=d)
    j = t[t.judged == "true"]
    return {"shown": len(t), "judged": len(j), "unjudged": len(t) - len(j),
            "R": int((j.judge_verdict == "R").sum()), "G": int((j.judge_verdict == "G").sum()),
            "O": int((j.judge_verdict == "O").sum())}


def headline_count(theory: str, d: dict | None = None) -> int:
    """Judged conceptual neighbors (R) that never name the theory, 1995-2015 window only (where judging was done)."""
    return judge_counts(theory, "1995-2015", d)["R"]


# ---- tab 4 ----------------------------------------------------------------------------------------------------
def metrics(d: dict | None = None) -> pd.DataFrame:
    """One tidy row per theory x period: V4 and BM25 candidate-only AUC with CI, n and an exploratory flag."""
    s = (d or load_all())["summary_metrics.csv"]
    rows = []
    for _, r in s.iterrows():
        for per in ("1995_2015", "2016_2025"):
            n = int(r[f"cand_auc_{per}_n_positives"])
            row = {"theory": r["theory"], "period": per.replace("_", "-"), "n_positives": n,
                   "exploratory": n < EXPLORATORY_N}
            for m in ("V4", "BM25"):
                row[m] = float(r[f"{m}_cand_auc_{per}"])
                row[f"{m}_lo"] = float(r[f"{m}_cand_auc_{per}_ci_lo"])
                row[f"{m}_hi"] = float(r[f"{m}_cand_auc_{per}_ci_hi"])
            rows.append(row)
    return pd.DataFrame(rows)


def seeds_and_silver(d: dict | None = None) -> pd.DataFrame:
    s = (d or load_all())["summary_metrics.csv"]
    return pd.DataFrame({
        "theory": s.theory, "LoC references": s.loc_references.astype(int),
        "Full-text seeds (any open route)": s.loc_fulltext_seeds_any_oa_route.astype(int),
        "Direct-mention papers, 1995-2015": s.silver_exclusive_1995_2015_corpus.astype(int),
        "Direct-mention papers, 2016-2025 (capped sample)": s.silver_exclusive_2016_2025_capped_sample.astype(int),
        "Judged relevant share (V4 top 30)": s.judged_R_share_v4_top30_1995_2015.astype(float),
        "Judged n": s.judged_n.astype(int)})


def discriminability(period: str, pool: str = "candidate_pool_only", d: dict | None = None) -> pd.DataFrame:
    """Matrix (rows = profile, columns = positives) of mean percentile rank for V4."""
    df = (d or load_all())["discriminability.csv"]
    sub = df[(df.period == period) & (df.pool == pool) & (df.variant == "V4")]
    if sub.empty:
        return pd.DataFrame()
    return sub.pivot(index="row_profile", columns="column_positives", values="mean_percentile_rank")

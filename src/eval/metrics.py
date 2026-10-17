"""Metrics for masked-positive retrieval against unlabeled negatives (prompt 05 Step 3).

Per positive: percentile (share of negatives it outscores, ties half), rank (1 + negatives scoring higher).
AUC = mean percentile / 100 (identical to mean percentile rank by construction); recall@k = share of positives with
rank <= k. Bootstrap: resample positives (negatives fixed), BOOT draws, fixed seed.
"""
import numpy as np

BOOT, SEED, KS = 2000, 20261011, (50, 100, 200)


def per_positive(s_pos: np.ndarray, s_neg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    neg = np.sort(s_neg)
    lo = np.searchsorted(neg, s_pos, "left")
    hi = np.searchsorted(neg, s_pos, "right")
    pct = (lo + 0.5 * (hi - lo)) / len(neg) * 100
    rank = 1 + (len(neg) - hi)
    return pct, rank


def _boot(vals: np.ndarray, rng: np.random.Generator) -> tuple[float, float, float]:
    idx = rng.integers(0, len(vals), size=(BOOT, len(vals)))
    m = vals[idx].mean(1)
    return float(vals.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def summarize(s_pos: np.ndarray, s_neg: np.ndarray) -> dict:
    pct, rank = per_positive(s_pos, s_neg)
    rng = np.random.default_rng(SEED)
    out = {"n_pos": len(s_pos), "n_neg": len(s_neg)}
    out["mpr"] = _boot(pct, rng)
    out["auc"] = tuple(x / 100 for x in out["mpr"])
    for k in KS:
        out[f"r{k}"] = _boot((rank <= k).astype(float), np.random.default_rng(SEED))
    out["chance"] = {"auc": 0.5, "mpr": 50.0, **{f"r{k}": min(1.0, k / len(s_neg)) for k in KS}}
    return out

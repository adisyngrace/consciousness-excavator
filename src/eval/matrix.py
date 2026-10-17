"""Step 5 of prompt 05: discriminability matrix (V4 and V5). Rows = theory profiles, columns = theories' masked positives
(ALL positives, no split). Entry = mean percentile rank (0-100) of the column's positives among that column theory's
negatives (names_theory_loosely = 0 for the column theory), scored with the ROW profile on the chunk set where the
column's positives are masked. A second matrix restricts negatives to the candidate pool.
usage: python -m src.eval.matrix  -> reports/level3_discriminability.md
"""
import json

import numpy as np

from src.eval import positives as P
from src.eval.metrics import per_positive
from src.eval.run_dev import SHORT, masks
from src.eval.scoring import THEORIES, bank, build_pool


def main() -> None:
    bk = bank()
    splits = json.loads((P.EVAL / "splits.json").read_text())["positives"]
    pools = {t: build_pool(t, True) for t in THEORIES}
    L = ["# Level 3 discriminability matrix (prompt 05, Step 5)", "",
         "Rows are theory profiles; columns are the theories' masked positives (all exclusive silver positives, no split). Entry = mean percentile rank (100 = best, chance 50) of the column's positives among that column theory's negatives, under the ROW profile. **The diagonal should be the largest value in each column.** Columns marked † have n < 20 (exploratory). Negatives are unlabeled; the candidate-pool-only matrix is the more informative one (the all-negatives numbers reward neuroscience/consciousness-flavoured text in general).", ""]
    for v in ("V4", "V5"):
        for restrict in ("all negatives", "candidate-pool negatives only"):
            M = np.zeros((5, 5))
            for j, tc in enumerate(THEORIES):
                pl = pools[tc]
                ip, ineg = masks(pl, bk, tc, splits[tc])
                if restrict != "all negatives":
                    ineg = ineg & np.array([bk.part_of[p] == "candidate" for p in pl.papers])
                for i, tr in enumerate(THEORIES):
                    s = pl.by_theory[v][tr]
                    M[i, j] = per_positive(s[ip], s[ineg])[0].mean()
            n = [len(splits[t]) for t in THEORIES]
            L += [f"## {v}: {restrict}", "", "| row profile \\ column positives | " + " | ".join(f"{SHORT[t]}{'†' if len(splits[t]) < 20 else ''} (n={len(splits[t])})" for t in THEORIES) + " |", "|---|" + "---|" * 5]
            for i, tr in enumerate(THEORIES):
                L.append(f"| **{SHORT[tr]}** | " + " | ".join((f"**{M[i, j]:.1f}**" if i == j else f"{M[i, j]:.1f}") for j in range(5)) + " |")
            wins = [int(M[:, j].argmax() == j) for j in range(5)]
            conf = [f"{SHORT[THEORIES[j]]} positives: {SHORT[THEORIES[i]]} profile >= own ({M[i, j]:.1f} vs {M[j, j]:.1f})" for j in range(5) for i in range(5) if i != j and M[i, j] >= M[j, j]]
            miss = [SHORT[t] for t, w in zip(THEORIES, wins) if not w]
            L += ["", f"Diagonal is the column maximum in {sum(wins)}/5 columns" + (f" (not in: {', '.join(miss)})" if miss else "") + ". "
                  + ("Confused pairs: " + "; ".join(conf) + "." if conf else "No profile beats a column's own profile."), ""]
    (P.EVAL.parent.parent / "reports" / "level3_discriminability.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()

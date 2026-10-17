"""Step 4 of prompt 05 (+ amendment 2026-10-11): test halves of GWT and PP, all positives of IIT, panpsychism, Champagne.

Variants: V4 (selected on dev), V0, V1, V2, V5, BM25. NOTHING here selects or changes a variant (amendment item 4).
usage: python -m src.eval.run_test   -> reports/level3_eval_test.md
"""
import json
from collections import Counter

import numpy as np

from src.eval import positives as P
from src.eval.metrics import summarize
from src.eval.run_dev import HUB_K, SHORT, eval_positives, fmt, masks
from src.eval.scoring import THEORIES, bank, build_pool

VARS = ["V4", "V0", "V1", "V2", "V5", "BM25"]
EXPLORATORY = {"integrated_information", "panpsychism", "champagne_semiotic"}


def main() -> None:
    bk = bank()
    splits = json.loads((P.EVAL / "splits.json").read_text())
    pools = {t: build_pool(t, True) for t in THEORIES}
    pos = {t: eval_positives(splits, t, "test") for t in THEORIES}
    top = {v: {} for v in VARS}
    for t in THEORIES:
        pl = pools[t]
        ip, ineg = masks(pl, bk, t, pos[t])
        el = np.where(ip | ineg)[0]
        for v in VARS:
            top[v][t] = list(pl.papers[el[np.argsort(-pl.scores[v][el], kind="stable")][:HUB_K]])
    hub = {}
    for v in VARS:
        cnt = Counter(p for t in THEORIES for p in top[v][t])
        for t in THEORIES:
            hub[v, t] = float(np.mean([cnt[p] >= 3 for p in top[v][t]]))
    L = ["# Level 3 evaluation: TEST results (prompt 05, Step 4)", "",
         "Pre-registered plan and amendment: `reports/eval_plan.md`. **The variant (V4) was selected on the dev halves and approved before this run; nothing on this page selects, tunes or changes a variant.**", "",
         "**How to read the two AUC columns.** The all-negatives AUC is confounded by the corpus-part mix: positives come from the Level 2 silver set and are 99-100% candidate pool for GWT and predictive processing, while only 4-13% of negatives are. A variant that merely prefers theory-flavoured neuroscience/consciousness text gains on it. **The candidate-only AUC (negatives restricted to the candidate pool) is the more informative number.** Negatives are unlabeled, not known irrelevant, so every metric is a lower bound.", "",
         "Hub rate and metric definitions as in `reports/level3_eval_dev.md` (hub pools here use the test positives for GWT/PP); CIs are 2,000 bootstrap resamples of the positives (seed 20261011). n is shown in every table heading.", ""]
    for t in THEORIES:
        pl = pools[t]
        ip, ineg = masks(pl, bk, t, pos[t])
        icand = ineg & np.array([bk.part_of[p] == "candidate" for p in pl.papers])
        npos = int(ip.sum())
        tag = "exploratory, small n; all positives" if t in EXPLORATORY else "test half"
        pc = Counter(bk.part_of[p] for p in pl.papers[ip])
        L += [f"## {SHORT[t]} ({tag}): n positives = {npos}, negatives = {int(ineg.sum())}, candidate-pool negatives = {int(icand.sum())}", "",
              f"Positives by corpus part (seed/cand/bg/rand): {'/'.join(str(pc[k]) for k in ('seed', 'candidate', 'background', 'random'))}", "",
              "| variant | AUC, all negatives [95% CI] | **AUC, candidate-pool negatives only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |", "|---|---|---|---|---|---|---|"]
        for v in VARS:
            s = pl.scores[v]
            r, rc = summarize(s[ip], s[ineg]), summarize(s[ip], s[icand])
            L.append(f"| {v}{' (selected)' if v == 'V4' else ''} | {fmt(r['auc'])} | **{fmt(rc['auc'])}** | {fmt(r['r50'])} | {fmt(r['r100'])} | {fmt(r['r200'])} | {hub[v, t]:.2f} |")
        ch = r["chance"]
        L += [f"| *chance* | 0.500 | 0.500 | {ch['r50']:.3f} | {ch['r100']:.3f} | {ch['r200']:.3f} | - |", ""]
        if t in EXPLORATORY:
            L += [f"_n = {npos}: confidence intervals are wide and the numbers are qualitative only._", ""]
    (P.EVAL.parent.parent / "reports" / "level3_eval_test.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()

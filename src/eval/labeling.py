"""Step 6 of prompt 05 (+ amendment): labeling sheet and V4 top-20 report from the UNMASKED main index.

Eligible papers: names_theory_loosely = 0 for the theory (1995-2015). Sheet: top 10 under V4 for IIT, panpsychism and
Champagne; top 10 each under V4 and V5 for GWT and predictive processing. Empty `label` (R relevant conceptual neighbor,
G generic consciousness/neuroscience, O off-topic) and `note` columns are for the user.
usage: python -m src.eval.labeling -> reports/labeling_sheet.csv, reports/level3_top20.md
"""
import csv

import numpy as np

from src.eval import positives as P
from src.eval.run_dev import SHORT
from src.eval.scoring import THEORIES, bank, build_pool

SHEET_PLAN = {"champagne_semiotic": ["V4"], "global_workspace": ["V4", "V5"], "integrated_information": ["V4"],
              "panpsychism": ["V4"], "predictive_processing_fep": ["V4", "V5"]}


def best_passage(bk, t: str, variant: str, pmcid: str) -> dict:
    """Best chunk of a paper for theory t: V4 uses equal weights, V5 the V0 weights (windows/seeds 0.5)."""
    ix = bk.ix
    rows = np.where(ix.pmcid == pmcid)[0]
    sel = np.where(ix.ctheory == t)[0]
    w = np.ones(len(sel)) if variant == "V4" else ix.weight[sel]
    W = ix.z[np.ix_(rows, sel)] * w
    r, k = np.unravel_index(W.argmax(), W.shape)
    cl = [j for j, s in enumerate(sel) if ix.kind[s] == "core_claim"]
    kc = cl[int(W[:, cl].max(0).argmax())]
    text = ix.conn.execute("SELECT text FROM chunks WHERE chunk_id=?", (int(rows[r]),)).fetchone()[0]
    return {"best_component": str(ix.ids[sel[k]]), "best_claim": str(ix.ids[sel[kc]]), "section": str(ix.section[rows[r]]), "snippet": " ".join(text.split())[:200]}


def ranked(bk, pool, t: str, v: str, k: int) -> list[dict]:
    s = pool.scores[v]
    el = np.array([bk.flag.get((p, t), 1) == 0 for p in pool.papers])
    idx = np.where(el)[0]
    idx = idx[np.argsort(-s[idx], kind="stable")][:k]
    out = []
    for rank, i in enumerate(idx, 1):
        p = str(pool.papers[i])
        meta = bk.ix.conn.execute("SELECT title, year FROM papers WHERE pmcid=?", (p,)).fetchone()
        other = [r["theory"] for r in bk.ix.conn.execute("SELECT theory FROM paper_flags WHERE pmcid=? AND any_mention_level!='none' AND theory!=?", (p, t))]
        out.append({"theory": SHORT[t], "variant": v, "rank": rank, "pmcid": p, "title": meta["title"], "year": meta["year"], "corpus_part": bk.part_of[p],
                    "score": round(float(s[i]), 3), **best_passage(bk, t, v, p), "other_theories_named": ",".join(other)})
    return out


def main() -> None:
    bk = bank()
    pools = {t: build_pool(t, False) for t in THEORIES}
    sheet, top20 = [], ["# Level 3 top 20 per theory under V4 (unmasked, term-excluded: names_theory_loosely = 0)", "",
                        "Selected variant V4 = equal component weights, no contrast. Champagne and panpsychism are exploratory.", ""]
    for t in THEORIES:
        for v in SHEET_PLAN[t]:
            sheet += [{**r, "label": "", "note": ""} for r in ranked(bk, pools[t], t, v, 10)]
        top20 += [f"## {SHORT[t]}", "", "| # | PMCID | year | part | title | best claim | other theories named | 200-char snippet |", "|---|---|---|---|---|---|---|---|"]
        for r in ranked(bk, pools[t], t, "V4", 20):
            top20.append(f"| {r['rank']} | {r['pmcid']} | {r['year']} | {r['corpus_part']} | {r['title'][:80]} | {r['best_claim']} | {r['other_theories_named'] or '-'} | …{r['snippet']}… |")
        top20.append("")
    cols = ["theory", "variant", "rank", "pmcid", "title", "year", "corpus_part", "score", "best_claim", "best_component", "section", "snippet", "other_theories_named", "label", "note"]
    with open(P.EVAL.parent.parent / "reports" / "labeling_sheet.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(sheet)
    (P.EVAL.parent.parent / "reports" / "level3_top20.md").write_text("\n".join(top20))
    from collections import Counter
    print(len(sheet), "rows;", Counter((r["theory"], r["variant"]) for r in sheet))
    print("corpus part of sheet rows:", Counter((r["variant"], r["corpus_part"]) for r in sheet))


if __name__ == "__main__":
    main()

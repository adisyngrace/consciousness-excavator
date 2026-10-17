"""CORE pilot Step 6: small tracked exports in results/ (prompt 09). Only titles, years, repositories, CORE links, DOIs,
scores, claim ids, counts and set labels; no snippets or text. Every row is labelled exploratory / source CORE / license
unknown; `judged` is false for every row (no judging has been run). Near-duplicate records are collapsed in the top lists.
usage: python -m src.eval.core_export
"""
import csv
import json
from collections import Counter

from src.corpus import core_dups
from src.eval import core_pilot as CP, metrics
from src.level3_concepts import embed

RESULTS = embed.ROOT.parent / "results"
STATUS = "exploratory; source CORE; license unknown"
SET_LABEL = {"A": "A_all_exclusive_ref_split", "B": "B_consciousness_relevant", "C": "C_term_precision_trimmed"}
PRIMARY, CAND = "adjacent-background (primary)", "candidate-pool"


def write_top(P: CP.Pilot) -> int:
    tops = CP.top_lists(P, CP.TOP)
    cols = ["theory", "rank", "core_id", "title", "year", "repository", "core_link", "doi", "score_v4", "best_claim_id",
            "other_theories_named", "judged", "source", "license", "status"]
    with open(RESULTS / "philosophy_pilot_top.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        n = 0
        for t in CP.PILOT:
            for k, r in enumerate(tops[t], 1):
                w.writerow({"theory": t, "rank": k, "core_id": r["core_id"], "title": CP.clean_title(r["title"]), "year": r["year"],
                            "repository": r["repository"], "core_link": r["link"], "doi": r["doi"], "score_v4": round(r["score_v4"], 3),
                            "best_claim_id": r["best_component"], "other_theories_named": r["other_theories_named"], "judged": "false",
                            "source": "CORE", "license": "unknown", "status": STATUS})
                n += 1
    return n


def write_metrics(P: CP.Pilot) -> int:
    cols = ["record_type", "theory", "positive_set", "set_label", "negatives", "variant", "metric", "value", "ci_lo", "ci_hi",
            "n_positives", "n_negatives", "n_effective_negatives", "note", "judged", "source", "license", "status"]
    rows = []

    def add(**kw):
        rows.append({**{c: "" for c in cols}, "judged": "false", "source": "CORE", "license": "unknown", "status": STATUS, **kw})

    conn = P.conn
    q = lambda s, *a: conn.execute(s, a).fetchall()
    for part, n in q("SELECT part, COUNT(*) FROM core_papers GROUP BY part"):
        add(record_type="count", metric=f"papers_{part}", value=n)
    add(record_type="count", metric="papers_total", value=q("SELECT COUNT(*) FROM core_papers")[0][0])
    add(record_type="count", metric="chunks_total", value=q("SELECT COUNT(*) FROM core_chunks")[0][0])
    add(record_type="count", metric="papers_without_reference_split", value=q("SELECT COUNT(*) FROM core_papers WHERE ref_split=0")[0][0])
    nd = core_dups.summary(conn)
    add(record_type="count", metric="near_duplicate_pairs", value=nd["pairs"], note="same normalized title+year, or title similarity > 0.9; share removable = %.1f%%" % (100 * nd["removable_share"]))
    for t in CP.PILOT:
        cand = [c for c, r in P.paper.items() if r["part"] == "candidate" and t in (r["cand_theories"] or "").split(";")]
        add(record_type="count", theory=t, metric="candidate_pool_papers", value=len(cand))
        for s in CP.SETS:
            ids = P.sets[t][s]
            per = Counter("1995-2015" if P.paper[i]["year"] <= 2015 else "2016-2025" for i in ids)
            add(record_type="count", theory=t, positive_set=s, set_label=SET_LABEL[s], metric="silver_positives", value=len(ids),
                n_positives=len(ids), note=("n<20: exploratory; " if len(ids) < 20 else "") + f"1995-2015: {per['1995-2015']}; 2016-2025: {per['2016-2025']}")
    for t in CP.PILOT:
        for s in CP.SETS:
            pos, negs = P.masks(t, s)
            if pos.sum() == 0:
                continue
            for pool in (PRIMARY, CAND):
                m = negs[pool]
                w = P.weights(t, pos, m)
                for v in ("V4", "BM25"):
                    r = metrics.summarize(P.pools[t][v][pos], P.pools[t][v][m])
                    add(record_type="auc", theory=t, positive_set=s, set_label=SET_LABEL[s], negatives=pool, variant=v, metric="auc",
                        value=round(r["auc"][0], 4), ci_lo=round(r["auc"][1], 4), ci_hi=round(r["auc"][2], 4), n_positives=int(pos.sum()),
                        n_negatives=int(m.sum()), note="n<20: exploratory" if pos.sum() < 20 else "")
                    ws = CP.weighted_summary(P.pools[t][v][pos], P.pools[t][v][m], w)
                    add(record_type="auc_year_matched", theory=t, positive_set=s, set_label=SET_LABEL[s], negatives=pool, variant=v,
                        metric="auc_year_matched", value=round(ws["auc"][0], 4), ci_lo=round(ws["auc"][1], 4), ci_hi=round(ws["auc"][2], 4),
                        n_positives=int(pos.sum()), n_negatives=int(m.sum()), n_effective_negatives=round(ws["n_eff_neg"]),
                        note="sensitivity check: negatives re-weighted to the positives' year distribution")
    with open(RESULTS / "philosophy_pilot_metrics.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    P = CP.Pilot()
    print("top rows:", write_top(P), "metric rows:", write_metrics(P))

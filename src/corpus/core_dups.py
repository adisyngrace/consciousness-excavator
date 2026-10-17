"""CORE pilot: near-duplicate records (prompt 09 Step 6). Two records are near-duplicates if they have the same normalized
title and year, or normalized-title similarity (rapidfuzz ratio) above 0.9. Clusters are connected components; one
representative per cluster is kept for exports and the collapsed sensitivity row. Titles only; no CORE text.
The same-title-and-year case was already removed at build time (`dup_within_core`); what remains here are same titles in other
years and similar titles."""
import re
import sqlite3

from rapidfuzz import fuzz, process

from src.corpus.build_core import DB, norm_title

THRESH = 90.0


def clusters(conn: sqlite3.Connection) -> tuple[dict[str, str], list[tuple[str, str, float]]]:
    """(rep_of: core_id -> representative core_id, pairs: (id_a, id_b, similarity 0-100))."""
    rows = conn.execute("SELECT core_id, title, year, part, ref_split, n_words FROM core_papers ORDER BY core_id").fetchall()
    ids = [r[0] for r in rows]
    nt = [norm_title(r[1]) for r in rows]
    sim = process.cdist(nt, nt, scorer=fuzz.ratio, score_cutoff=THRESH, workers=-1)
    pairs = [(ids[i], ids[j], float(sim[i, j])) for i in range(len(ids)) for j in range(i + 1, len(ids))
             if sim[i, j] >= THRESH and len(nt[i]) >= 8]                  # ignore very short titles ("Expectation")
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, _ in pairs:
        parent[find(a)] = find(b)
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(find(r[0]), []).append(r)
    pos_any = {r[0] for r in conn.execute("SELECT core_id FROM core_paper_flags WHERE direct_mention=1")}
    part_rank = {"candidate": 0, "background": 1, "distractor": 2}
    rep_of = {}
    for g in groups.values():
        best = min(g, key=lambda r: (r[0] not in pos_any, -r[4], part_rank[r[3]], -r[5], int(r[0])))
        for r in g:
            rep_of[r[0]] = best[0]
    return rep_of, pairs


def summary(conn: sqlite3.Connection) -> dict:
    rep_of, pairs = clusters(conn)
    n = len(rep_of)
    extra = sum(1 for k, v in rep_of.items() if k != v)
    return {"n_papers": n, "pairs": len(pairs), "same_title_pairs": sum(1 for p in pairs if p[2] == 100.0),
            "papers_in_clusters": len({x for p in pairs for x in p[:2]}), "removable": extra, "removable_share": extra / n}


if __name__ == "__main__":
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    print(summary(c))

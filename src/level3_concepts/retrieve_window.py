"""Prompt 07 Step 5: V4 retrieval over the combined chunk sets (1995-2015 main index + 2016-2025 late index).

V4 = chunk score = max over the theory's components of z (all component weights 1.0, no contrast); paper = best chunk.
z-score statistics are FROZEN from the 1995-2015 matrix (the same mean/SD for the late chunks). Standard exclusion:
only papers with names_theory_loosely = 0 for the theory. Nothing is tuned.

    retrieve("global_workspace", 1995, 2025, k=50)

usage: python -m src.level3_concepts.retrieve_window   -> reports/level3_windows.md
"""
import json
from functools import lru_cache

import numpy as np

from src import db
from src.level3_concepts import embed, embed_profiles, late as L3, retrieve as base

THEORIES = base.THEORY_KEYS
WINDOWS = [(1995, 2015), (1995, 2020), (1995, 2025)]


class Combined:
    def __init__(self) -> None:
        ix = base.index()
        self.ix = ix
        mean, std = ix.cos.mean(0), ix.cos.std(0)
        d = L3.DIR
        E = np.concatenate([np.load(f) for f in sorted(d.glob("shard_*.npy")) if ".tmp" not in f.name])
        p = np.load(embed_profiles.out_path(), allow_pickle=False)
        self.conn = db.connect()
        rows = self.conn.execute(f"SELECT chunk_id, pmcid, section, year, corpus_part, text FROM {L3.TABLE} ORDER BY chunk_id").fetchall()
        assert len(rows) == len(E)
        self.z = np.vstack([ix.z, (E @ p["emb"].T - mean) / std])
        self.pmcid = np.concatenate([ix.pmcid, [r["pmcid"] for r in rows]])
        self.year = np.concatenate([ix.year, [r["year"] for r in rows]])
        self.part = np.concatenate([ix.part, [r["corpus_part"] for r in rows]])
        self.text_late = [r["text"] for r in rows]
        self.n0 = len(ix.E)
        self.meta = json.loads(str(p["meta"]))
        self.ids, self.kind, self.ctheory = ix.ids, ix.kind, ix.ctheory
        self.names = {}
        for r in self.conn.execute("SELECT pmcid, theory FROM paper_flags WHERE any_mention_level!='none'"):
            self.names.setdefault(r["pmcid"], []).append(r["theory"])
        self.flag = {(r["pmcid"], r["theory"]): r["names_theory_loosely"] for r in self.conn.execute("SELECT pmcid, theory, names_theory_loosely FROM paper_flags")}
        self.papers = {r["pmcid"]: r for r in self.conn.execute("SELECT pmcid, title, year, journal FROM papers")}
        self.claim_text = {m["id"]: m["text"] for m in self.meta if m["kind"] == "core_claim"} if "id" in self.meta[0] else {}

    def chunk_text(self, i: int) -> str:
        if i >= self.n0:
            return self.text_late[i - self.n0]
        return self.conn.execute("SELECT text FROM chunks WHERE chunk_id=?", (int(i),)).fetchone()[0]


@lru_cache(maxsize=1)
def combined() -> Combined:
    return Combined()


def retrieve(theory: str, year_min: int, year_max: int, k: int = 50) -> list[dict]:
    c = combined()
    sel = np.where(c.ctheory == theory)[0]
    zs = c.z[:, sel]
    score = zs.max(1)
    ok = np.where((c.year >= year_min) & (c.year <= year_max))[0]
    ok = ok[[c.flag.get((p, theory)) == 0 for p in c.pmcid[ok]]]
    order = ok[np.lexsort((-score[ok], c.pmcid[ok]))]
    pm = c.pmcid[order]
    first = np.flatnonzero(np.r_[True, pm[1:] != pm[:-1]])
    best = order[first]
    top = best[np.argsort(-score[best], kind="stable")][:k]
    claim_sel = np.where((c.ctheory == theory) & (c.kind == "core_claim"))[0]
    out = []
    for rank, i in enumerate(top, 1):
        p = c.pmcid[i]
        bc = claim_sel[c.z[i, claim_sel].argmax()]
        out.append({"rank": rank, "pmcid": p, "title": c.papers[p]["title"], "year": int(c.papers[p]["year"]), "score": float(score[i]),
                    "corpus_part": str(c.part[i]), "best_component": str(c.ids[sel[zs[i].argmax()]]), "best_claim": str(c.ids[bc]),
                    "chunk_id": int(i), "names_other_theories": [t for t in c.names.get(p, []) if t != theory]})
    return out


def snippet(i: int, n: int = 200) -> str:
    t = " ".join(combined().chunk_text(i).split())
    return t[:n] + ("…" if len(t) > n else "")


def trends_tables(conn) -> list[str]:
    names = {"champagne_semiotic": "Champagne", "global_workspace": "GWT", "integrated_information": "IIT", "panpsychism": "Panpsychism", "predictive_processing_fep": "PP"}
    rows = {(r[0], r[1]): (r[2], r[3], r[4]) for r in conn.execute("SELECT theory, year, hits, total_oa, rate_per_10k FROM term_counts_by_year")}
    L = ["## 1. Mention trends (Europe PMC server-side counts, full corpus; not the capped samples)", "",
         "Hits = open-access full-text papers matching any STRONG phrase of the theory (abbreviations excluded; no domain-context rule is possible server-side, so these are upper bounds on direct mentions). Rate = hits per 10,000 OA full-text papers published that year. 2024-2025 are incomplete or embargoed in PMC, read the tail with care. Per-year table below; the same numbers are exported in Step 6.", "",
         "### Nested windows", "", "| theory | 1995-2015 hits | rate /10k | 1995-2020 hits | rate /10k | 1995-2025 hits | rate /10k |", "|---|---|---|---|---|---|---|"]
    for t in THEORIES:
        cells = []
        for a, b in WINDOWS:
            h = sum(rows[t, y][0] for y in range(a, b + 1)); tot = sum(rows[t, y][1] for y in range(a, b + 1))
            cells += [f"{h:,}", f"{10000 * h / tot:.2f}"]
        L.append(f"| {names[t]} | " + " | ".join(cells) + " |")
    L += ["", "### Rate per 10,000 OA papers, by year", "", "| year | OA papers | " + " | ".join(names[t] for t in THEORIES) + " |", "|---|---|" + "---|" * 5]
    for y in range(1995, 2026):
        L.append(f"| {y} | {rows[THEORIES[0], y][1]:,} | " + " | ".join(f"{rows[t, y][2]:.2f} ({rows[t, y][0]})" for t in THEORIES) + " |")
    return L


def main() -> None:
    c = combined()
    names = {"champagne_semiotic": "Champagne", "global_workspace": "GWT", "integrated_information": "IIT", "panpsychism": "Panpsychism", "predictive_processing_fep": "PP"}
    L = ["# Level 3 across time windows (prompt 07, Step 5)", "",
         "V4 (frozen), exclusion `names_theory_loosely = 0`, z-score statistics frozen from 1995-2015. **Composition caveat:** the 1995-2015 corpus (7,794 papers) and the 2016-2025 corpus (5,438 papers) were built with different caps and pool definitions, and the 2016-2025 candidate pools are capped samples (400 per theory for GWT, IIT, PP). A window's top 50 therefore reflects both the literature and the sampling; shifts are descriptive, not a measure of how the field moved. "
         "The 1995-2015 window is the original index; for it, V4 reproduces the earlier top lists.", ""]
    L += trends_tables(c.conn)
    L += ["", "## 2. Neighborhood shift (top 50 per window under V4)", "",
          "| theory | window | top-50 share published after 2015 | after 2020 | overlap with 1995-2015 top 50 | overlap with 1995-2020 top 50 |", "|---|---|---|---|---|---|"]
    tops, new_examples = {}, {}
    for t in THEORIES:
        tops[t] = {w: retrieve(t, w[0], w[1], 50) for w in WINDOWS}
        base = {r["pmcid"] for r in tops[t][WINDOWS[0]]}
        mid = {r["pmcid"] for r in tops[t][WINDOWS[1]]}
        for w in WINDOWS:
            ids = {r["pmcid"] for r in tops[t][w]}
            yrs = [r["year"] for r in tops[t][w]]
            L.append(f"| {names[t]} | {w[0]}-{w[1]} | {sum(y > 2015 for y in yrs) / 50:.0%} | {sum(y > 2020 for y in yrs) / 50:.0%} | {len(ids & base)} | {len(ids & mid)} |")
        new_examples[t] = [r for r in tops[t][WINDOWS[2]] if r["pmcid"] not in base][:5]
    L += ["", "## 3. New top-ranked papers that appear only in the larger windows (5 per theory, for demo examples; NOT judged)", "",
          "Highest-ranked papers of the 1995-2025 top 50 that are not in the 1995-2015 top 50. Rank is within the 1995-2025 window. No relevance judgement is implied.", ""]
    for t in THEORIES:
        L += [f"### {names[t]}", ""]
        for r in new_examples[t]:
            L.append(f"- **#{r['rank']}** {r['title']} ({r['year']}, {r['pmcid']}, {r['corpus_part']}; also names: {', '.join(r['names_other_theories']) or 'none'}): “{snippet(r['chunk_id'])}”")
        L.append("")
    (embed.ROOT.parent / "reports" / "level3_windows.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()

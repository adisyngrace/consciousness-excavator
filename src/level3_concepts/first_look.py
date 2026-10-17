"""Step 5 of prompt 04: reports/level3_first_look.md. Read-only first look; nothing is tuned.

Per theory: top 20 by raw score and by contrastive score (best-chunk aggregation, weighted components), plus
overlap of the two lists, corpus-part shares (with the eligible-pool base rate), how many name another theory,
weighted vs claims-only top-20 overlap, and best-chunk vs top-3-mean overlap.

usage: python -m src.level3_concepts.first_look
"""
import re
from collections import Counter
from pathlib import Path

from src.level3_concepts import retrieve as R

OUT = Path(__file__).resolve().parents[2] / "reports" / "level3_first_look.md"
K = 20
NAMES = {"champagne_semiotic": "Champagne's semiotic account", "global_workspace": "Global Workspace Theory",
         "integrated_information": "Integrated Information Theory", "panpsychism": "Panpsychism",
         "predictive_processing_fep": "Predictive Processing / Free Energy Principle"}
PARTS = ("seed", "candidate", "background", "random")


def snip(t: str, n: int = 200) -> str:
    return re.sub(r"\s+", " ", t)[:n].replace("|", "/")


def table(rows: list[dict]) -> list[str]:
    L = ["| # | PMCID | year | title | part | best passage section | best component | z (weighted) | raw cos | other theories named | 200-char snippet |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        L.append(f"| {i} | {r['pmcid']} | {r['year']} | {(r['title'] or '')[:90].replace('|', '/')} | {r['corpus_part']} | {r['section']} | "
                 f"{r['best_component']} | {r['score']:.2f} | {r['raw_cosine']:.3f} | {','.join(r['names_other_theories']) or '-'} | …{snip(r['passage'])}… |")
    return L


def ids(rows):
    return [r["pmcid"] for r in rows]


def build() -> str:
    ix = R.index()
    cfg = R.config()
    L = ["# Level 3 first look (1995-2015, term-excluded)", "",
         f"Weighted z-scored components (claims 1.0, description windows 0.5, seed abstracts 0.5); contrastive = z_theory - {cfg['lambda_generic']} * z_generic "
         "(lambda default, NOT tuned). Papers with names_theory_loosely = 1 for the theory are excluded. Aggregation: best chunk per paper unless noted. "
         "**Champagne (3 silver papers) and panpsychism (7 exclusive) are exploratory only.**", ""]
    summary = []
    pool_base = {}
    for th, name in NAMES.items():
        raw, con = R.retrieve(th, score="raw", k=K), R.retrieve(th, score="contrastive", k=K)
        raw_c, con_c = R.retrieve(th, score="raw", components="claims_only", k=K), R.retrieve(th, score="contrastive", components="claims_only", k=K)
        con_t3 = R.retrieve(th, score="contrastive", mode="top3", k=K)
        everyone = R.retrieve(th, score="contrastive", k=10**6)
        pool = Counter(r["corpus_part"] for r in everyone)
        n_pool = sum(pool.values())
        L += [f"## {name}", "", f"Eligible papers (do not name the theory, have chunks): **{n_pool}**; pool by part: "
              + ", ".join(f"{p} {pool.get(p, 0)} ({100 * pool.get(p, 0) / n_pool:.0f}%)" for p in PARTS), "",
              f"### Top {K} by raw score (weighted z)", ""] + table(raw) + ["", f"### Top {K} by contrastive score", ""] + table(con) + [""]
        parts = lambda rows: {p: sum(r["corpus_part"] == p for r in rows) for p in PARTS}
        ov = len(set(ids(raw)) & set(ids(con)))
        L += [f"- overlap raw vs contrastive top-{K}: **{ov}/{K}**",
              f"- corpus part of raw top-{K}: {parts(raw)}; contrastive top-{K}: {parts(con)}",
              f"- naming another theory: raw {sum(bool(r['names_other_theories']) for r in raw)}/{K}, contrastive {sum(bool(r['names_other_theories']) for r in con)}/{K}",
              f"- weighted vs claims-only overlap: raw {len(set(ids(raw)) & set(ids(raw_c)))}/{K}, contrastive {len(set(ids(con)) & set(ids(con_c)))}/{K}",
              f"- best-chunk vs top-3-mean overlap (contrastive): {len(set(ids(con)) & set(ids(con_t3)))}/{K}", "",
              f"### Contrastive top {K}, claims only (for the weighted vs claims-only comparison)", ""] + table(con_c) + [""]
        summary.append((name, n_pool, ov, parts(raw), parts(con), sum(bool(r['names_other_theories']) for r in con),
                        len(set(ids(raw)) & set(ids(raw_c))), len(set(ids(con)) & set(ids(con_c))), pool))
    S = ["## Summary", "", "| Theory | eligible | raw/contrastive overlap | contrastive top-20 by part (seed/cand/bg/rand) | pool base rate cand % | names another theory | weighted vs claims-only overlap (raw / contr.) |",
         "|---|---|---|---|---|---|---|"]
    for name, n, ov, pr, pc, nm, ow_r, ow_c, pool in summary:
        S.append(f"| {name} | {n} | {ov}/{K} | {'/'.join(str(pc[p]) for p in PARTS)} | {100 * pool.get('candidate', 0) / n:.0f}% | {nm}/{K} | {ow_r}/{K} / {ow_c}/{K} |")
    cand_heavy = [s[0] for s in summary if s[4]["candidate"] >= 15]
    S += ["", ("Candidate-pool dominance (>= 15 of 20 contrastive results from the candidate part, which came from theory-term queries): "
               + (", ".join(cand_heavy) if cand_heavy else "none") + "."), "",
          "Reminder: Champagne and panpsychism results are exploratory (3 and 7 exclusive silver papers); judge them qualitatively.", ""]
    return "\n".join(L[:4] + S + L[4:])


if __name__ == "__main__":
    text = build()
    OUT.write_text(text)
    print(text.split("## Champagne")[0])

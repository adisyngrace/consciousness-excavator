"""Abbreviation audit sheet: 10 random papers per abbreviation, each with a snippet, the number of times the
abbreviation occurs, and whether a strong term of the same theory is in the paper (the rule's confirmation).
You label each row yourself: TP = the abbreviation means the theory, FP = something else.

usage: python -m src.level2_terms.abbrev_audit      -> reports/abbreviation_audit.md and .csv
"""
import csv
import json
import random
import re
from pathlib import Path

from src import db

ROOT = Path(__file__).resolve().parents[2]
ABBREVS = [("global_workspace", "GWT"), ("global_workspace", "GNW"), ("integrated_information", "IIT"),
           ("predictive_processing_fep", "PP"), ("predictive_processing_fep", "PC"), ("predictive_processing_fep", "FEP")]
N = 10


def build(conn, rng: random.Random) -> tuple[list[dict], list[str]]:
    rows, md = [], []
    for theory, ab in ABBREVS:
        hits = conn.execute("""SELECT pmcid, tier, section, count, snippets FROM term_hits WHERE theory=? AND term=?
                               AND tier IN ('abbreviation','abbreviation_unconfirmed') ORDER BY pmcid, section""",
                            (theory, ab)).fetchall()
        by_paper = {}
        for h in hits:
            by_paper.setdefault(h["pmcid"], []).append(h)
        conf = sum(1 for v in by_paper.values() if v[0]["tier"] == "abbreviation")
        pick = rng.sample(sorted(by_paper), min(N, len(by_paper)))
        md += [f"### {ab} ({theory})", "",
               f"{len(by_paper)} corpus papers use `{ab}`: {conf} with a strong term of the same theory (confirmed), "
               f"{len(by_paper) - conf} without (unconfirmed). Showing {len(pick)} at random.", ""]
        for i, p in enumerate(pick, 1):
            hs = by_paper[p]
            h = rng.choice(hs)
            snip = json.loads(h["snippets"])[0]
            snip = re.sub(rf"(?<!\w){re.escape(ab)}(?!\w)", f"**{ab}**", snip, count=1)
            strong = conn.execute("""SELECT term, SUM(count) n FROM term_hits WHERE pmcid=? AND theory=? AND tier='strong'
                                     GROUP BY term ORDER BY n DESC""", (p, theory)).fetchall()
            title, year = conn.execute("SELECT title, year FROM papers WHERE pmcid=?", (p,)).fetchone()
            total = sum(x["count"] for x in hs)
            st = ", ".join(f"{s['term']} x{s['n']}" for s in strong) or "none"
            md.append(f"{i}. {p} ({year}) *{title[:80]}*  \n   uses of {ab}: {total} | strong term in paper: "
                      f"**{'yes' if hs[0]['tier'] == 'abbreviation' else 'NO'}** ({st}) | [{h['section']}]  \n   …{snip}…")
            rows.append({"abbreviation": ab, "theory": theory, "n": i, "pmcid": p, "uses": total,
                         "strong_term_present": int(hs[0]["tier"] == "abbreviation"), "strong_terms": st,
                         "section": h["section"], "snippet": snip, "label": ""})
        md.append("")
    return rows, md


if __name__ == "__main__":
    conn = db.connect()
    rows, md = build(conn, random.Random(20261010))
    head = ["# Abbreviation audit", "",
            "Label each row TP (the abbreviation means the theory) or FP (something else) in "
            "`reports/abbreviation_audit.csv`. Abbreviations never create a direct mention on their own; this audit "
            "checks whether the confirmation rule (strong term in the same paper) is the right gate.", ""]
    (ROOT / "reports" / "abbreviation_audit.md").write_text("\n".join(head + md) + "\n")
    with (ROOT / "reports" / "abbreviation_audit.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("\n".join(head + md))

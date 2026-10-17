"""Step 4: Europe PMC server-side hit counts per publication year (1995-2025), open-access full text, no downloads.

Per theory: OR of its STRONG phrases (quoted; abbreviations excluded; no domain_context rule is possible
server-side, so these are phrase-hit counts and an upper bound on direct mentions). Normalised to hits per 10,000
OA full-text papers published that year. 2024-2025 are incomplete/embargoed in PMC; read the tail with care.

usage: python -m src.level2_terms.trends
"""
import json
from datetime import datetime, timezone

from src import db, http
from src.corpus import epmc
from src.level2_terms.terms import TERMS_PATH
import yaml

YEARS = range(1995, 2026)
BASE = "OPEN_ACCESS:y AND HAS_FT:y"


def _count(query: str) -> int:
    http.DELAY = epmc.SEARCH_DELAY
    r = http.get(epmc.REST + "search", params={"query": query, "format": "json", "resultType": "lite", "pageSize": 1})
    if r["status"] != 200:
        raise RuntimeError(f"HTTP {r['status']} for {query[:100]}")
    return int(json.loads(r["text"])["hitCount"])


def theory_query(strong: list[str]) -> str:
    return "(" + " OR ".join(f'"{t}"' for t in strong) + ")"


def run(conn) -> None:
    doc = yaml.safe_load(TERMS_PATH.read_text())["theories"]
    totals = {y: _count(f"{BASE} AND PUB_YEAR:{y}") for y in YEARS}
    for key, spec in doc.items():
        q = theory_query(spec["strong"])
        for y in YEARS:
            hits = _count(f"{q} AND {BASE} AND PUB_YEAR:{y}")
            conn.execute("INSERT OR REPLACE INTO term_counts_by_year VALUES (?,?,?,?,?,?)",
                         (key, y, hits, totals[y], 10000 * hits / totals[y] if totals[y] else 0.0, q))
    conn.commit()


def print_table(conn) -> None:
    keys = [r[0] for r in conn.execute("SELECT DISTINCT theory FROM term_counts_by_year ORDER BY theory")]
    print("year | OA total | " + " | ".join(keys))
    for y in YEARS:
        cells = []
        for k in keys:
            h, rate = conn.execute("SELECT hits, rate_per_10k FROM term_counts_by_year WHERE theory=? AND year=?", (k, y)).fetchone()
            cells.append(f"{h} ({rate:.2f})")
        tot = conn.execute("SELECT total_oa FROM term_counts_by_year WHERE year=? LIMIT 1", (y,)).fetchone()[0]
        print(f"{y} | {tot} | " + " | ".join(cells))


if __name__ == "__main__":
    c = db.connect()
    run(c)
    print_table(c)

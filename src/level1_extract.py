"""Level 1, steps 1-2: fetch pooled LoC pages, parse, store. Idempotent."""
import sys

from src import db, http
from src.config import BASE, THEORIES
from src.parse import parse_page


def run() -> None:
    conn = db.connect()
    for name, slugs in THEORIES.items():
        descs = []
        for slug in slugs:
            url = BASE + slug
            r = http.get(url)
            if r["status"] != 200:
                print(f"WARN {url}: HTTP {r['status']}", file=sys.stderr)
                continue
            desc, refs = parse_page(r["text"])
            if not refs:
                print(f"WARN {url}: no references parsed", file=sys.stderr)
            descs.append(f"## {slug}\n{desc}")
            conn.execute("INSERT OR IGNORE INTO theories(name) VALUES (?)", (name,))
            tid = conn.execute("SELECT id FROM theories WHERE name=?", (name,)).fetchone()["id"]
            for ref in refs:
                conn.execute(
                    """INSERT INTO loc_references
                       (theory_id, raw_text, parsed_title, parsed_authors, parsed_year, parsed_journal,
                        doi, notes, source_url)
                       VALUES (?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(theory_id, raw_text) DO UPDATE SET
                         parsed_title=excluded.parsed_title, parsed_authors=excluded.parsed_authors,
                         parsed_year=excluded.parsed_year, parsed_journal=excluded.parsed_journal,
                         doi=COALESCE(loc_references.doi, excluded.doi), notes=excluded.notes""",
                    (tid, ref.raw_text, ref.title, ref.authors, ref.year, ref.journal, ref.doi,
                     "; ".join(ref.notes) or None, url))
        conn.execute("UPDATE theories SET loc_url=?, description_text=? WHERE name=?",
                     (BASE + slugs[0], "\n\n".join(descs), name))
    conn.commit()


if __name__ == "__main__":
    run()

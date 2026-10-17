"""Step 2 of prompt 04: chunk the corpus into the SQLite `chunks` table.

Scope: papers in `corpus_membership` (the Level 2 scan scope; `papers` also holds ~4.4k fetched-but-not-member papers
with no Level 2 flags, which are out of scope). Sections: abstract, introduction, discussion. A paper with neither a
parsed introduction nor a parsed discussion contributes its abstract plus the first BODY_FALLBACK_WORDS words of body.
Windows are WORDS words with OVERLAP words of overlap (about 240-300 tokens), never crossing a section boundary;
sections under MIN_WORDS words are skipped.
Chunk ids are contiguous from 0, ordered by (pmcid, section order, position), so embedding shards are stable.
Papers that yield no chunk are logged in `chunk_log` with the reason. Idempotent: does nothing if chunks exist
(use --rebuild to redo; that invalidates any embeddings).

usage: python -m src.level3_concepts.chunk [--rebuild]
"""
import argparse
import sys
from collections import Counter

from src import db

WORDS, OVERLAP, BODY_FALLBACK_WORDS, MIN_WORDS = 180, 30, 600, 20
SECTION_ORDER = ("abstract", "introduction", "discussion", "body")
PART_PRECEDENCE = ("seed", "candidate", "background", "random")
SOURCE = "europepmc"

DDL = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id INTEGER PRIMARY KEY, pmcid TEXT NOT NULL, section TEXT NOT NULL, position INTEGER NOT NULL,
    year INTEGER, source TEXT NOT NULL, corpus_part TEXT NOT NULL, n_words INTEGER NOT NULL, text TEXT NOT NULL,
    UNIQUE (pmcid, section, position)
);
CREATE INDEX IF NOT EXISTS ix_chunks_pmcid ON chunks(pmcid);
CREATE TABLE IF NOT EXISTS chunk_log (pmcid TEXT PRIMARY KEY, reason TEXT NOT NULL);
"""


def windows(text: str, size: int = WORDS, overlap: int = OVERLAP, min_words: int = MIN_WORDS, tail: int = 10) -> list[str]:
    """Overlapping word windows. A tail of <= `tail` new words is absorbed into the previous window (so no chunk is
    mostly overlap); a section shorter than `min_words` yields nothing."""
    w = text.split()
    if len(w) < min_words:
        return []
    out, i = [], 0
    while i < len(w):
        end = i + size
        if len(w) - end <= tail:
            end = len(w)
        out.append(" ".join(w[i:end]))
        if end >= len(w):
            break
        i += size - overlap
    return out


def paper_texts(secs: dict[str, str]) -> dict[str, str]:
    """Sections to chunk for one paper (see module docstring)."""
    use = {s: secs[s] for s in ("abstract", "introduction", "discussion") if (secs.get(s) or "").strip()}
    if not (secs.get("introduction") or "").strip() and not (secs.get("discussion") or "").strip() and (secs.get("body") or "").strip():
        use["body"] = " ".join(secs["body"].split()[:BODY_FALLBACK_WORDS])
    return use


def corpus_part(parts: list[str]) -> str:
    return next(p for p in PART_PRECEDENCE if p in parts)


def build(conn, rebuild: bool = False) -> None:
    conn.executescript(DDL)
    if conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] and not rebuild:
        print("chunks already built (use --rebuild)")
        return
    conn.execute("DELETE FROM chunks")
    conn.execute("DELETE FROM chunk_log")
    parts: dict[str, list[str]] = {}
    for r in conn.execute("SELECT pmcid, part FROM corpus_membership"):
        parts.setdefault(r["pmcid"], []).append(r["part"])
    meta = {r["pmcid"]: r for r in conn.execute("SELECT pmcid, year, fetch_status, parse_status FROM papers")}
    cid = 0
    for pmcid in sorted(parts):
        m = meta.get(pmcid)
        if m is None:
            conn.execute("INSERT INTO chunk_log VALUES (?,?)", (pmcid, "no papers row"))
            continue
        secs = {r["section"]: r["text"] for r in conn.execute("SELECT section, text FROM paper_sections WHERE pmcid=?", (pmcid,))}
        use = paper_texts(secs)
        rows = []
        for sec in SECTION_ORDER:
            for pos, t in enumerate(windows(use.get(sec, ""))):
                rows.append((cid + len(rows), pmcid, sec, pos, m["year"], SOURCE, corpus_part(parts[pmcid]), len(t.split()), t))
        if not rows:
            reason = f"no abstract/intro/discussion/body text (fetch={m['fetch_status']} parse={m['parse_status']})"
            conn.execute("INSERT INTO chunk_log VALUES (?,?)", (pmcid, reason))
            print(f"[no_chunks] {pmcid}: {reason}", file=sys.stderr)
            continue
        conn.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?)", rows)
        cid += len(rows)
    conn.commit()


def report(conn) -> None:
    q = lambda s: conn.execute(s).fetchall()
    print("\n== chunk sanity ==")
    print("total chunks:", q("SELECT COUNT(*) FROM chunks")[0][0], "| papers with chunks:", q("SELECT COUNT(DISTINCT pmcid) FROM chunks")[0][0],
          "| in corpus:", q("SELECT COUNT(DISTINCT pmcid) FROM corpus_membership")[0][0])
    print("contiguous ids:", q("SELECT MIN(chunk_id)=0 AND MAX(chunk_id)=COUNT(*)-1 FROM chunks")[0][0] == 1)
    print("per section:", {r[0]: r[1] for r in q("SELECT section, COUNT(*) FROM chunks GROUP BY 1")})
    print("per corpus_part (chunks / papers):", {r[0]: (r[1], r[2]) for r in q("SELECT corpus_part, COUNT(*), COUNT(DISTINCT pmcid) FROM chunks GROUP BY 1")})
    print("section x part:", {(r[0], r[1]): r[2] for r in q("SELECT section, corpus_part, COUNT(*) FROM chunks GROUP BY 1,2")})
    print("words/chunk: min/avg/max =", q("SELECT MIN(n_words), ROUND(AVG(n_words),1), MAX(n_words) FROM chunks")[0][:])
    print("body-fallback papers:", q("SELECT COUNT(DISTINCT pmcid) FROM chunks WHERE section='body'")[0][0])
    print("chunk_log (papers without chunks):", Counter(r[0] for r in q("SELECT reason FROM chunk_log")))
    for r in q("SELECT pmcid, reason FROM chunk_log LIMIT 5"):
        print("  ", tuple(r))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    conn = db.connect()
    build(conn, ap.parse_args().rebuild)
    report(conn)

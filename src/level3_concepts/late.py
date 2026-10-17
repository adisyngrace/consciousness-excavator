"""Prompt 07 Step 3: chunk and embed the 2016-2025 papers into SEPARATE storage (the 1995-2015 `chunks` table and
embeddings are never touched).

  table  chunks_late (same columns and chunking rules as `chunks`; chunk ids contiguous from 0)
  shards data/embeddings_late/<model>__<rev>/shard_XXXXX.npy, log data/logs/embed_late.log

usage: python -m src.level3_concepts.late chunk | embed | selftest
"""
import sys

import numpy as np

from src import db
from src.level3_concepts import chunk as C, embed as E

WINDOW = "2016-2025"
TABLE = "chunks_late"
DIR = E.ROOT / "embeddings_late" / E.out_dir().name


def build(conn, rebuild: bool = False) -> None:
    conn.executescript(C.DDL.replace("chunks", TABLE).replace("chunk_log", "chunk_log_late").replace("ix_" + TABLE + "_pmcid", "ix_late_pmcid"))
    if conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] and not rebuild:
        print("chunks_late already built (use rebuild)")
        return
    conn.execute(f"DELETE FROM {TABLE}")
    conn.execute("DELETE FROM chunk_log_late")
    parts: dict[str, list[str]] = {}
    for r in conn.execute("SELECT pmcid, part FROM corpus_membership WHERE window=?", (WINDOW,)):
        parts.setdefault(r["pmcid"], []).append(r["part"])
    meta = {r["pmcid"]: r for r in conn.execute("SELECT pmcid, year, fetch_status, parse_status FROM papers")}
    cid = 0
    for pmcid in sorted(parts):
        m = meta[pmcid]
        secs = {r["section"]: r["text"] for r in conn.execute("SELECT section, text FROM paper_sections WHERE pmcid=?", (pmcid,))}
        use = C.paper_texts(secs)
        rows = []
        for sec in C.SECTION_ORDER:
            for pos, t in enumerate(C.windows(use.get(sec, ""))):
                rows.append((cid + len(rows), pmcid, sec, pos, m["year"], C.SOURCE, C.corpus_part(parts[pmcid]), len(t.split()), t))
        if not rows:
            conn.execute("INSERT INTO chunk_log_late VALUES (?,?)", (pmcid, f"no text (fetch={m['fetch_status']} parse={m['parse_status']})"))
            continue
        conn.executemany(f"INSERT INTO {TABLE} VALUES (?,?,?,?,?,?,?,?,?)", rows)
        cid += len(rows)
    conn.commit()
    q = lambda s: conn.execute(s).fetchall()
    print("chunks_late:", q(f"SELECT COUNT(*) FROM {TABLE}")[0][0], "chunks;", q(f"SELECT COUNT(DISTINCT pmcid) FROM {TABLE}")[0][0],
          "of", len(parts), "papers; unchunked:", [tuple(r) for r in q("SELECT * FROM chunk_log_late")])
    print("per part (chunks, papers):", {r[0]: (r[1], r[2]) for r in q(f"SELECT corpus_part, COUNT(*), COUNT(DISTINCT pmcid) FROM {TABLE} GROUP BY 1")})
    print("per section:", {r[0]: r[1] for r in q(f"SELECT section, COUNT(*) FROM {TABLE} GROUP BY 1")})


def selftest(conn, k: int = 8) -> None:
    """Re-embed k random chunks; each must be its own nearest neighbour among all stored late embeddings."""
    from sentence_transformers import SentenceTransformer
    emb = np.concatenate([np.load(DIR / f"shard_{i:05d}.npy") for i in range(-(-conn.execute(f'SELECT COUNT(*) FROM {TABLE}').fetchone()[0] // E.SHARD))])
    ids = np.random.default_rng(20261012).choice(len(emb), k, replace=False)
    model = SentenceTransformer(E.MODEL, device="mps"); model.max_seq_length = E.MAXLEN
    texts = [conn.execute(f"SELECT text FROM {TABLE} WHERE chunk_id=?", (int(i),)).fetchone()[0] for i in ids]
    new = model.encode(texts, batch_size=E.BATCH, normalize_embeddings=True)
    nn = (new @ emb.T).argmax(1)
    print("self-retrieval:", all(nn == ids), [(int(a), int(b)) for a, b in zip(ids, nn)])
    print("shape", emb.shape, "norms ok", bool(np.allclose(np.linalg.norm(emb, axis=1), 1, atol=1e-3)))
    assert all(nn == ids)


if __name__ == "__main__":
    cmd = sys.argv[1]
    c = db.connect()
    if cmd == "chunk":
        build(c)
    elif cmd == "embed":
        try:
            E.main(TABLE, DIR, "embed_late.log")
        except Exception as e:
            E._log(f"FAILED: {e!r}", "embed_late.log"); sys.exit(1)
    elif cmd == "selftest":
        selftest(c)

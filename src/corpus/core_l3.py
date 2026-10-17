"""CORE pilot Step 3: chunk and embed the CORE papers into SEPARATE storage (prompt 09).

  table   core_chunks in data/core_pilot.db (abstract and body windows, 180 words / 30 overlap, no other sections; the
          abstract is its own section so passages for judge packets can skip it; body already capped at 6,000 words)
  shards  data/embeddings_core/<model>__<rev>/shard_XXXXX.npy (same model, normalisation and shard size as the main run)
  log     data/logs/embed_core.log   (resumable; run under caffeinate)

usage: python -m src.corpus.core_l3 chunk | embed | selftest
"""
import json
import sqlite3
import sys

import numpy as np

from src.corpus.build_core import DB
from src.level3_concepts import chunk as C, embed as E

DIR = E.ROOT / "embeddings_core" / E.out_dir().name
DDL = """CREATE TABLE IF NOT EXISTS core_chunks (chunk_id INTEGER PRIMARY KEY, core_id TEXT NOT NULL, section TEXT NOT NULL,
  position INTEGER NOT NULL, year INTEGER, part TEXT, n_words INTEGER NOT NULL, text TEXT NOT NULL, UNIQUE (core_id, section, position));
CREATE INDEX IF NOT EXISTS ix_core_chunks_id ON core_chunks(core_id);
CREATE TABLE IF NOT EXISTS core_chunk_log (core_id TEXT PRIMARY KEY, reason TEXT NOT NULL);"""


def paper_chunks(abstract: str, body: str) -> list[tuple[str, int, str]]:
    out = [("abstract", i, t) for i, t in enumerate(C.windows(abstract or ""))]
    return out + [("body", i, t) for i, t in enumerate(C.windows(body or ""))]


def build(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    if conn.execute("SELECT COUNT(*) FROM core_chunks").fetchone()[0]:
        print("core_chunks already built (delete the table AND the shards to rebuild)")
        return
    cid = 0
    for core_id, year, part in conn.execute("SELECT core_id, year, part FROM core_papers ORDER BY core_id").fetchall():
        ab, body = conn.execute("SELECT abstract, body FROM core_texts WHERE core_id=?", (core_id,)).fetchone()
        rows = [(cid + k, core_id, s, p, year, part, len(t.split()), t) for k, (s, p, t) in enumerate(paper_chunks(ab, body))]
        if not rows:
            conn.execute("INSERT INTO core_chunk_log VALUES (?,?)", (core_id, "no chunks (text too short)"))
            continue
        conn.executemany("INSERT INTO core_chunks VALUES (?,?,?,?,?,?,?,?)", rows)
        cid += len(rows)
    conn.commit()
    q = lambda s: conn.execute(s).fetchall()
    print("core_chunks:", q("SELECT COUNT(*) FROM core_chunks")[0][0], "chunks;", q("SELECT COUNT(DISTINCT core_id) FROM core_chunks")[0][0],
          "papers; unchunked:", q("SELECT COUNT(*) FROM core_chunk_log")[0][0])
    print("per section:", dict(q("SELECT section, COUNT(*) FROM core_chunks GROUP BY 1")))


def embed(conn: sqlite3.Connection) -> None:
    import sentence_transformers
    from datetime import datetime
    import time
    from sentence_transformers import SentenceTransformer
    log = lambda m: E._log(m, "embed_core.log")
    n = conn.execute("SELECT COUNT(*) FROM core_chunks").fetchone()[0]
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "manifest.json").write_text(json.dumps({"model": E.MODEL, "revision": E.revision(E.MODEL), "sentence_transformers": sentence_transformers.__version__,
                                                   "n_chunks": n, "shard": E.SHARD, "max_seq_length": E.MAXLEN, "chunk_prefix": "", "normalized": True}, indent=1))
    n_shards = -(-n // E.SHARD)
    todo = [k for k in range(n_shards) if not (DIR / f"shard_{k:05d}.npy").exists()]
    log(f"start: {n} chunks, {n_shards} shards, {len(todo)} to do")
    if not todo:
        return
    model = SentenceTransformer(E.MODEL, device="mps")
    model.max_seq_length = E.MAXLEN
    t0, done = time.time(), 0
    for k in todo:
        lo, hi = k * E.SHARD, min((k + 1) * E.SHARD, n)
        rows = conn.execute("SELECT text FROM core_chunks WHERE chunk_id>=? AND chunk_id<? ORDER BY chunk_id", (lo, hi)).fetchall()
        emb = model.encode([r[0] for r in rows], batch_size=E.BATCH, normalize_embeddings=True, show_progress_bar=False)
        tmp = DIR / f"shard_{k:05d}.tmp.npy"
        np.save(tmp, emb.astype(np.float32))
        tmp.rename(DIR / f"shard_{k:05d}.npy")
        done += hi - lo
        rate = done / (time.time() - t0)
        log(f"shard {k + 1}/{n_shards} done ({hi}/{n}) {rate:.0f} chunks/s, ETA {(n - hi) / rate / 60:.0f} min")
    log("finished")


def load_embeddings(conn: sqlite3.Connection) -> np.ndarray:
    n = conn.execute("SELECT COUNT(*) FROM core_chunks").fetchone()[0]
    return np.concatenate([np.load(DIR / f"shard_{k:05d}.npy") for k in range(-(-n // E.SHARD))])


def selftest(conn: sqlite3.Connection, k: int = 8) -> None:
    from sentence_transformers import SentenceTransformer
    emb = load_embeddings(conn)
    ids = np.random.default_rng(20261014).choice(len(emb), k, replace=False)
    model = SentenceTransformer(E.MODEL, device="mps"); model.max_seq_length = E.MAXLEN
    texts = [conn.execute("SELECT text FROM core_chunks WHERE chunk_id=?", (int(i),)).fetchone()[0] for i in ids]
    nn = (model.encode(texts, batch_size=E.BATCH, normalize_embeddings=True) @ emb.T).argmax(1)
    print("self-retrieval:", all(nn == ids), [(int(a), int(b)) for a, b in zip(ids, nn)])
    print("shape", emb.shape, "norms ok", bool(np.allclose(np.linalg.norm(emb, axis=1), 1, atol=1e-3)))
    assert all(nn == ids)


if __name__ == "__main__":
    c = sqlite3.connect(DB)
    c.row_factory = None
    try:
        {"chunk": build, "embed": embed, "selftest": selftest}[sys.argv[1]](c)
    except Exception as e:
        E._log(f"FAILED: {e!r}", "embed_core.log")
        sys.exit(1)

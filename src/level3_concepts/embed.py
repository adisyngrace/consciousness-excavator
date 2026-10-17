"""Step 3 of prompt 04: embed all chunks (no query prefix) with bge-base-en-v1.5, on MPS, in resumable shards.

Output: data/embeddings/<model>__<hf revision>/shard_XXXXX.npy (float32, rows = chunk ids [k*SHARD, (k+1)*SHARD),
L2-normalised) plus manifest.json. A shard that exists is skipped, so the job can be killed and restarted. Progress is
appended to data/logs/embed.log. Run under caffeinate:  caffeinate -i .venv/bin/python -m src.level3_concepts.embed
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from src import db

MODEL = "BAAI/bge-base-en-v1.5"
SHARD, BATCH, MAXLEN = 2048, 16, 384
ROOT = Path(__file__).resolve().parents[2] / "data"


def revision(model: str) -> str:
    snaps = sorted((Path.home() / ".cache/huggingface/hub" / f"models--{model.replace('/', '--')}" / "snapshots").glob("*"))
    return snaps[-1].name[:8] if snaps else "unknown"


def out_dir(model: str = MODEL) -> Path:
    return ROOT / "embeddings" / f"{model.replace('/', '_')}__{revision(model)}"


def _log(msg: str, logfile: str = "embed.log") -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    (ROOT / "logs").mkdir(exist_ok=True)
    with open(ROOT / "logs" / logfile, "a") as f:
        f.write(line + "\n")


def main(table: str = "chunks", d: Path | None = None, logfile: str = "embed.log") -> None:
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    conn = db.connect()
    log = lambda m: _log(m, logfile)
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    d = d or out_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps({"model": MODEL, "revision": revision(MODEL), "sentence_transformers":
        sentence_transformers.__version__, "n_chunks": n, "shard": SHARD, "max_seq_length": MAXLEN, "chunk_prefix": "",
        "normalized": True, "dtype": "float32"}, indent=1))
    n_shards = -(-n // SHARD)
    todo = [k for k in range(n_shards) if not (d / f"shard_{k:05d}.npy").exists()]
    log(f"start: {n} chunks, {n_shards} shards, {len(todo)} to do, dir={d.name}")
    if not todo:
        return
    model = SentenceTransformer(MODEL, device="mps")
    model.max_seq_length = MAXLEN
    t0, done = time.time(), 0
    for k in todo:
        lo, hi = k * SHARD, min((k + 1) * SHARD, n)
        rows = conn.execute(f"SELECT text FROM {table} WHERE chunk_id>=? AND chunk_id<? ORDER BY chunk_id", (lo, hi)).fetchall()
        assert len(rows) == hi - lo
        emb = model.encode([r[0] for r in rows], batch_size=BATCH, normalize_embeddings=True, show_progress_bar=False)
        tmp = d / f"shard_{k:05d}.tmp.npy"
        np.save(tmp, emb.astype(np.float32))
        tmp.rename(d / f"shard_{k:05d}.npy")
        done += hi - lo
        rate = done / (time.time() - t0)
        log(f"shard {k + 1}/{n_shards} done ({hi}/{n} chunks) {rate:.0f} chunks/s, ETA {(n - hi) / rate / 60:.0f} min")
    log("finished")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:   # no silent failures
        _log(f"FAILED: {e!r}")
        sys.exit(1)

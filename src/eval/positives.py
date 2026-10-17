"""Steps 1-2 of prompt 05: exclusive silver positives, masked re-chunking/re-embedding, dev/test split.

Positives for theory T: silver set (direct_mention = 1) AND direct mention of no other theory, with chunks in the main
index. Their abstract/intro/discussion text is masked (src/eval/mask.py), re-chunked with the SAME chunker and embedded
with the SAME model as the main index. Cached separately in data/eval/ (main embeddings are never touched):
  masked_chunks.json   rows {theory, pmcid, section, position, text}
  masked_emb.npy       float32, same row order
  splits.json          GWT and PP exclusive positives split 50/50 by paper (seed SEED) into dev/test
usage: python -m src.eval.positives
"""
import json
import random
import sys
from pathlib import Path

import numpy as np

from src import db
from src.eval.mask import leaks_for_theory, mask_for_theory
from src.level2_terms.silver import silver
from src.level3_concepts import chunk, embed

EVAL = embed.ROOT / "eval"
SEED = 20261011
THEORIES = ["champagne_semiotic", "global_workspace", "integrated_information", "panpsychism", "predictive_processing_fep"]
SPLIT_THEORIES = ["global_workspace", "predictive_processing_fep"]


def positives(conn) -> dict[str, list[str]]:
    have = {r[0] for r in conn.execute("SELECT DISTINCT pmcid FROM chunks")}
    return {t: sorted(silver(conn, t, "exclusive") & have) for t in THEORIES}


def split(pos: dict[str, list[str]]) -> dict[str, dict[str, list[str]]]:
    out = {}
    for t in SPLIT_THEORIES:
        ids = list(pos[t])
        random.Random(SEED).shuffle(ids)
        h = len(ids) // 2
        out[t] = {"dev": sorted(ids[:h]), "test": sorted(ids[h:])}
    return out


def masked_chunks(conn, theory: str, pmcid: str) -> list[dict]:
    secs = {r["section"]: r["text"] for r in conn.execute("SELECT section, text FROM paper_sections WHERE pmcid=?", (pmcid,))}
    use = chunk.paper_texts(secs)
    rows = []
    for sec in chunk.SECTION_ORDER:
        for pos, t in enumerate(chunk.windows(mask_for_theory(use.get(sec, ""), theory))):
            rows.append({"theory": theory, "pmcid": pmcid, "section": sec, "position": pos, "text": t})
    return rows


def build() -> None:
    conn = db.connect()
    EVAL.mkdir(exist_ok=True)
    pos = positives(conn)
    sp = split(pos)
    (EVAL / "splits.json").write_text(json.dumps({"seed": SEED, "positives": pos, "split": sp}, indent=1))
    if (EVAL / "masked_emb.npy").exists():
        print("masked embeddings cached")
        return
    rows = []
    for t in THEORIES:
        for p in pos[t]:
            r = masked_chunks(conn, t, p)
            if not r:
                print(f"[no_masked_chunks] {t} {p}", file=sys.stderr)
            bad = [x for c in r for x in leaks_for_theory(c["text"], t)]
            if bad:
                print(f"[LEAK] {t} {p}: {bad[:5]}", file=sys.stderr)
            rows += r
    (EVAL / "masked_chunks.json").write_text(json.dumps(rows))
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(embed.MODEL, device="mps")
    model.max_seq_length = embed.MAXLEN
    emb = model.encode([r["text"] for r in rows], batch_size=embed.BATCH, normalize_embeddings=True, show_progress_bar=False)
    np.save(EVAL / "masked_emb.npy", emb.astype(np.float32))
    print(f"masked chunks: {len(rows)} for {sum(len(v) for v in pos.values())} papers")


if __name__ == "__main__":
    build()
    d = json.loads((EVAL / "splits.json").read_text())
    for t in THEORIES:
        s = d["split"].get(t)
        print(t, "positives:", len(d["positives"][t]), ("dev/test: %d/%d" % (len(s["dev"]), len(s["test"])) if s else ""))

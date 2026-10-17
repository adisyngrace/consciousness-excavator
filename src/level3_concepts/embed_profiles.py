"""Embed the profile components with the same model as the chunks.

Core claims get the BGE query instruction prefix; description windows, seed abstracts and the generic-consciousness
paragraphs are embedded WITHOUT it (they are passage-like). Output: data/embeddings/profiles__<model>__<rev>.npz.
Components: claims (all), capped description windows (see windows.py), seed abstracts (not excluded_seeds), generic paragraphs.

usage: python -m src.level3_concepts.embed_profiles
"""
import json

import numpy as np
import yaml

from src.level3_concepts import embed, windows
from src.level3_concepts.make_profiles import PROFILES

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def profile_components() -> list[dict]:
    pages = {s: windows.load_profile(s)["loc_description_pages"] for s in windows.theory_stems()}
    _, capped = windows.capped_windows(pages)
    comps = []
    for stem, lst in windows.components(capped).items():
        key = windows.load_profile(stem)["key"]
        comps += [{**c, "theory": key, "stem": stem} for c in lst]
    gw = windows.load_weights()
    cfg = yaml.safe_load((PROFILES / "config.yaml").read_text())["contrast"]
    g = yaml.safe_load((PROFILES / "generic_consciousness.yaml").read_text())["paragraphs"]
    comps += [{"id": f"generic-p{i}", "kind": "generic", "weight": cfg["generic_paragraph_weight"], "text": t, "theory": "generic", "stem": "generic"}
              for i, t in enumerate(g, 1)]
    return comps


def out_path():
    return embed.ROOT / "embeddings" / f"profiles__{embed.out_dir().name}.npz"


def main() -> None:
    from sentence_transformers import SentenceTransformer
    comps = profile_components()
    model = SentenceTransformer(embed.MODEL, device="mps")
    model.max_seq_length = embed.MAXLEN
    texts = [(QUERY_PREFIX + c["text"]) if c["kind"] == "core_claim" else c["text"] for c in comps]
    emb = model.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    np.savez(out_path(), emb=emb, ids=np.array([c["id"] for c in comps]), kind=np.array([c["kind"] for c in comps]),
             weight=np.array([c["weight"] for c in comps], dtype=np.float32), theory=np.array([c["theory"] for c in comps]),
             meta=json.dumps([{k: c[k] for k in ("id", "kind", "theory", "weight", "text")} for c in comps]))
    kinds = {}
    for c in comps:
        kinds[(c["theory"], c["kind"])] = kinds.get((c["theory"], c["kind"]), 0) + 1
    print(f"embedded {len(comps)} components -> {out_path().name}")
    for k, v in sorted(kinds.items()):
        print("  ", k, v)


if __name__ == "__main__":
    main()

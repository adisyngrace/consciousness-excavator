"""Step 4 of prompt 04: score chunks and papers against the theory profiles.

Scoring (decision 2026-10-11, option b):
  1. cosine of every embedded chunk (all ~105k, before any exclusion) to every profile component;
  2. z-score each component's cosine over ALL chunks;
  3. theory chunk score = max over the theory's components of weight * z (claims 1.0, description windows 0.5,
     seed abstracts 0.5; weights in profiles/config.yaml);  `components="claims_only"` uses claims only;
  4. generic score = max over the generic_consciousness paragraphs of z (weight 1.0);
  5. contrastive = z_theory - lambda * z_generic [ - mu * mean z_theory of the other four theories ].
Raw cosine (of the best-matching component) is kept for display. Paper score = best chunk, or mean of the top 3 chunks.
Result set: only papers with names_theory_loosely = 0 for the theory (include_naming=True adds the rest, tagged).
Nothing here is tuned: lambda/mu come from profiles/config.yaml or arguments.

    retrieve("integrated_information", 1995, 2015, mode="best", k=20)
"""
from functools import lru_cache

import numpy as np
import yaml

from src import db
from src.level3_concepts import embed, embed_profiles
from src.level3_concepts.make_profiles import PROFILES

THEORY_KEYS = ["champagne_semiotic", "global_workspace", "integrated_information", "panpsychism", "predictive_processing_fep"]


def config() -> dict:
    return yaml.safe_load((PROFILES / "config.yaml").read_text())["contrast"]


def zscore(cos: np.ndarray) -> np.ndarray:
    """Per-column (component) z-score over all chunks."""
    return (cos - cos.mean(0)) / cos.std(0)


def max_weighted(z: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """-> (max_k w_k * z_k per row, argmax k per row)."""
    wz = z * w
    k = wz.argmax(1)
    return wz[np.arange(len(wz)), k], k


class Index:
    def __init__(self) -> None:
        d = embed.out_dir()
        self.E = np.concatenate([np.load(f) for f in sorted(d.glob("shard_*.npy")) if ".tmp" not in f.name])
        p = np.load(embed_profiles.out_path(), allow_pickle=False)
        self.ids, self.kind, self.weight, self.ctheory = p["ids"], p["kind"], p["weight"], p["theory"]
        self.cos = self.E @ p["emb"].T                       # (n_chunks, n_components) raw cosine
        self.z = zscore(self.cos)
        conn = db.connect()
        rows = conn.execute("SELECT chunk_id, pmcid, section, year, corpus_part FROM chunks ORDER BY chunk_id").fetchall()
        assert len(rows) == len(self.E), (len(rows), len(self.E))
        self.pmcid = np.array([r["pmcid"] for r in rows])
        self.section = np.array([r["section"] for r in rows])
        self.year = np.array([r["year"] for r in rows])
        self.part = np.array([r["corpus_part"] for r in rows])
        self.conn = conn
        self._theory_cache: dict = {}

    def theory_scores(self, theory: str, components: str = "weighted") -> tuple[np.ndarray, np.ndarray]:
        key = (theory, components)
        if key not in self._theory_cache:
            mask = self.ctheory == theory
            if components == "claims_only":
                mask &= self.kind == "core_claim"
            sel = np.where(mask)[0]
            s, k = max_weighted(self.z[:, sel], self.weight[sel])
            self._theory_cache[key] = (s, sel[k])
        return self._theory_cache[key]

    def generic_scores(self) -> np.ndarray:
        sel = np.where(self.ctheory == "generic")[0]
        return max_weighted(self.z[:, sel], self.weight[sel])[0]


@lru_cache(maxsize=1)
def index() -> Index:
    return Index()


def retrieve(theory: str, year_min: int = 1995, year_max: int = 2015, mode: str = "best", k: int = 20, score: str = "contrastive",
             components: str = "weighted", contrast: str = "generic", lam: float | None = None, mu: float | None = None,
             include_naming: bool = False) -> list[dict]:
    """mode: 'best' (best chunk) | 'top3' (mean of top-3 chunks). score: 'raw' | 'contrastive'.
    contrast: 'generic' | 'generic+others' | 'none'."""
    ix, cfg = index(), config()
    lam = cfg["lambda_generic"] if lam is None else lam
    mu = cfg["mu_other_theories"] if mu is None else mu
    zt, comp = ix.theory_scores(theory, components)
    zg = ix.generic_scores()
    contr = zt - lam * zg
    if contrast == "generic+others":
        contr = contr - mu * np.mean([ix.theory_scores(t, components)[0] for t in THEORY_KEYS if t != theory], axis=0)
    chunk_score = {"raw": zt, "contrastive": zt if contrast == "none" else contr}[score]
    flags = {r["pmcid"]: r for r in ix.conn.execute("SELECT pmcid, theory, any_mention_level, names_theory_loosely FROM paper_flags")
             if r["theory"] == theory}
    names = {}
    for r in ix.conn.execute("SELECT pmcid, theory FROM paper_flags WHERE any_mention_level!='none'"):
        names.setdefault(r["pmcid"], []).append(r["theory"])
    ok_chunk = (ix.year >= year_min) & (ix.year <= year_max)
    idx = np.where(ok_chunk)[0]
    if not include_naming:
        idx = idx[[flags.get(p) is not None and flags[p]["names_theory_loosely"] == 0 for p in ix.pmcid[idx]]]
    order = idx[np.lexsort((-chunk_score[idx], ix.pmcid[idx]))]
    out = []
    pm = ix.pmcid[order]
    bounds = np.flatnonzero(np.r_[True, pm[1:] != pm[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        grp = order[a:b]                       # chunks of one paper, best first
        best = grp[0]
        top3 = chunk_score[grp[:3]].mean()
        out.append((best, grp, chunk_score[best] if mode == "best" else top3, top3))
    out.sort(key=lambda t: -t[2])
    meta = {r["pmcid"]: r for r in ix.conn.execute("SELECT pmcid, title, year, journal FROM papers")}
    res = []
    for best, grp, s, top3 in out[:k]:
        p = ix.pmcid[best]
        text = ix.conn.execute("SELECT text FROM chunks WHERE chunk_id=?", (int(best),)).fetchone()[0]
        fl = flags.get(p)
        res.append({"pmcid": p, "title": meta[p]["title"], "year": int(meta[p]["year"]), "journal": meta[p]["journal"],
                    "corpus_part": str(ix.part[best]), "score": float(s), "score_best": float(chunk_score[best]), "score_top3": float(top3),
                    "raw_z_best": float(zt[best]), "raw_cosine": float(ix.cos[best, comp[best]]),
                    "generic_cosine": float(ix.cos[best, np.where(ix.ctheory == "generic")[0]].max()),
                    "section": str(ix.section[best]), "passage": text, "best_component": str(ix.ids[comp[best]]),
                    "tag": fl["any_mention_level"] if fl else "none",
                    "names_other_theories": [t for t in names.get(p, []) if t != theory]})
    return res

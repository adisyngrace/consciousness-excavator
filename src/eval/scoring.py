"""Step 3 of prompt 05: the pre-registered scoring variants (reports/eval_plan.md), at paper level.

For a theory T the evaluation chunk set is the main index with T's positives swapped for their masked chunks
(masked=True) or the plain main index (masked=False). z-score statistics are frozen from the ORIGINAL chunk matrix.
All variants return one score per paper (array aligned with Pool.papers).

  V0  max over T's components of weight*z, paper = best chunk          V1  chunk = V0 - 0.5*z_generic, paper = best chunk
  V1b as V1 with lambda 1.0                                            V2  paper V0(T) - mean paper V0(other four)
  V3  mean of top-3 distinct components' best-chunk weighted z         V4  V0 with all weights 1.0
  V5  paper V3(T) - mean paper V3(other four)                          BM25 claims as queries, normalised, max over claims
"""
import json
import re
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from src import db
from src.eval import positives as P
from src.level3_concepts import retrieve

VARIANTS = ["V0", "V1", "V1b", "V2", "V3", "V4", "V5", "BM25"]
THEORIES = P.THEORIES
K1, B = 1.5, 0.75


def _paper_max(a: np.ndarray, starts: np.ndarray) -> np.ndarray:
    return np.maximum.reduceat(a, starts, axis=0)


def top3_mean(m: np.ndarray) -> np.ndarray:
    return np.sort(m, axis=1)[:, -3:].mean(1)


class Bank:
    """Everything that is computed once: main index, masked rows, BM25 matrices."""

    def __init__(self) -> None:
        self.ix = retrieve.index()
        ix = self.ix
        self.n0 = len(ix.E)
        self.mean, self.std = ix.cos.mean(0), ix.cos.std(0)
        rows = json.loads((P.EVAL / "masked_chunks.json").read_text())
        self.mrows = rows
        M = np.load(P.EVAL / "masked_emb.npy")
        assert len(M) == len(rows)
        self.cos_all = np.vstack([ix.cos, M @ self._comp_emb().T])
        self.pmcid_all = np.concatenate([ix.pmcid, [r["pmcid"] for r in rows]])
        self.mtheory = np.array([r["theory"] for r in rows])
        conn = ix.conn
        self.part_of = {r["pmcid"]: r["corpus_part"] for r in conn.execute("SELECT DISTINCT pmcid, corpus_part FROM chunks")}
        self.title = {r["pmcid"]: r["title"] for r in conn.execute("SELECT pmcid, title FROM papers")}
        self.flag = {(r["pmcid"], r["theory"]): r["names_theory_loosely"] for r in conn.execute("SELECT pmcid, theory, names_theory_loosely FROM paper_flags")}
        self.meta = json.loads(str(np.load(__import__("src.level3_concepts.embed_profiles", fromlist=["x"]).out_path(), allow_pickle=False)["meta"]))
        self._bm25()

    def _comp_emb(self) -> np.ndarray:
        from src.level3_concepts import embed_profiles
        return np.load(embed_profiles.out_path(), allow_pickle=False)["emb"]

    def _bm25(self) -> None:
        conn = self.ix.conn
        texts = [r[0] for r in conn.execute("SELECT text FROM chunks ORDER BY chunk_id")]
        assert len(texts) == self.n0
        self.cv = CountVectorizer(stop_words="english", lowercase=True, dtype=np.float32)
        X0 = self.cv.fit_transform(texts)
        Xm = self.cv.transform([r["text"] for r in self.mrows])
        self.X = __import__("scipy.sparse", fromlist=["x"]).vstack([X0, Xm]).tocsr()
        self.dl = np.asarray(self.X.sum(1)).ravel()
        self.avgdl = self.dl[: self.n0].mean()
        df = np.asarray((X0 > 0).sum(0)).ravel()
        self.idf = np.log(1 + (self.n0 - df + 0.5) / (df + 0.5)).astype(np.float32)
        self.bm: dict[str, np.ndarray] = {}
        an = self.cv.build_analyzer()
        vocab = self.cv.vocabulary_
        for t in THEORIES:
            claims = [m["text"] for m in self.meta if m["theory"] == t and m["kind"] == "core_claim"]
            cols = []
            for c in claims:
                cols.append(sorted({vocab[w] for w in an(c) if w in vocab}))
            sc = np.zeros((self.X.shape[0], len(claims)), dtype=np.float32)
            for j, qc in enumerate(cols):
                sub = self.X[:, qc].tocsr()
                sub = sub.tocoo()
                tf = sub.data
                norm = K1 * (1 - B + B * self.dl[sub.row] / self.avgdl)
                val = self.idf[np.array(qc)[sub.col]] * tf * (K1 + 1) / (tf + norm)
                np.add.at(sc[:, j], sub.row, val)
                sc[:, j] /= sc[: self.n0, j].max()          # normalise by the claim's max over the ORIGINAL chunks
            self.bm[t] = sc.max(1)                            # chunk score = max over claims


_bank: Bank | None = None


def bank() -> Bank:
    global _bank
    if _bank is None:
        _bank = Bank()
    return _bank


@dataclass
class Pool:
    theory: str
    masked: bool
    papers: np.ndarray                  # pmcid per paper
    scores: dict[str, np.ndarray]       # variant -> score per paper (for theory)
    v0_all: dict[str, np.ndarray]       # theory -> V0 paper score (all five theories)
    gidx: np.ndarray
    by_theory: dict[str, dict[str, np.ndarray]]   # variant (V0-V5) -> theory -> paper scores (row profile t)


def build_pool(theory: str, masked: bool) -> Pool:
    bk = bank()
    ix = bk.ix
    if masked:
        pos_all = set(json.loads((P.EVAL / "splits.json").read_text())["positives"][theory])
        keep = np.where(~np.isin(ix.pmcid, list(pos_all)))[0]
        mrows = bk.n0 + np.where(bk.mtheory == theory)[0]
        gidx = np.concatenate([keep, mrows])
    else:
        gidx = np.arange(bk.n0)
    order = np.argsort(bk.pmcid_all[gidx], kind="stable")
    gidx = gidx[order]
    pm = bk.pmcid_all[gidx]
    starts = np.flatnonzero(np.r_[True, pm[1:] != pm[:-1]])
    z = (bk.cos_all[gidx] - bk.mean) / bk.std
    gen = np.where(ix.ctheory == "generic")[0]
    zg = (z[:, gen] * ix.weight[gen]).max(1)
    paper = {"V0": {}, "V1": {}, "V1b": {}, "V3": {}, "V4": {}}
    for t in THEORIES:
        sel = np.where(ix.ctheory == t)[0]
        W = z[:, sel] * ix.weight[sel]
        c0 = W.max(1)
        paper["V0"][t] = _paper_max(c0, starts)
        paper["V1"][t] = _paper_max(c0 - 0.5 * zg, starts)
        paper["V1b"][t] = _paper_max(c0 - 1.0 * zg, starts)
        paper["V3"][t] = top3_mean(_paper_max(W, starts))
        paper["V4"][t] = _paper_max(z[:, sel].max(1), starts)
    T = theory
    others = [t for t in THEORIES if t != T]
    sc = {v: paper[v][T] for v in ("V0", "V1", "V1b", "V3", "V4")}
    sc["V2"] = paper["V0"][T] - np.mean([paper["V0"][t] for t in others], axis=0)
    sc["V5"] = paper["V3"][T] - np.mean([paper["V3"][t] for t in others], axis=0)
    sc["BM25"] = _paper_max(bk.bm[T][gidx], starts)
    by = {v: dict(paper[v]) for v in ("V0", "V1", "V1b", "V3", "V4")}
    for v2, base in (("V2", "V0"), ("V5", "V3")):
        by[v2] = {t: paper[base][t] - np.mean([paper[base][u] for u in THEORIES if u != t], axis=0) for t in THEORIES}
    return Pool(T, masked, pm[starts], sc, paper["V0"], gidx, by)

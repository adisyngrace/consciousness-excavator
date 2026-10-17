"""Prompt 07 Step 4: out-of-time evaluation on 2016-2025 (pre-registered in reports/eval_plan.md, 2026-10-12 amendment + addendum).

Frozen: profiles, weights, V4/V5 definitions, and the z-score statistics (mean/SD of the ORIGINAL 1995-2015 chunk matrix).
Nothing here selects or tunes anything. Variants: V4, V5, BM25. BM25 IDF and per-claim max normalisation come from the
2016-2025 chunk set (BM25 has no trained statistics).

Positives: exclusive silver papers of 2016-2025 (single-theory direct mentions), masked with src/eval/mask.py, re-chunked and
re-embedded (cache: data/eval_late/). Negatives: every other 2016-2025 paper with chunks and names_theory_loosely = 0.

usage: python -m src.eval.late masked   (build masked chunks + embeddings)
       python -m src.eval.late report   (-> reports/level3_out_of_time.md, reports/level3_discriminability_late.md)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from src import db
from src.eval import positives as P
from src.eval.mask import leaks_for_theory
from src.eval.metrics import per_positive, summarize
from src.eval.run_dev import SHORT, fmt
from src.eval.scoring import K1, B, THEORIES, top3_mean, _paper_max
from src.level2_terms.silver import silver
from src.level3_concepts import embed, embed_profiles, late as L3, retrieve

EVAL_LATE = embed.ROOT / "eval_late"
REPORTS = embed.ROOT.parent / "reports"
VARS = ["V4", "V5", "BM25"]
HUB_K = 50
COVID = (2020, 2021, 2022)


class Late:
    def __init__(self) -> None:
        self.ix = retrieve.index()                                   # 1995-2015 main index: frozen stats + component metadata
        self.mean, self.std = self.ix.cos.mean(0), self.ix.cos.std(0)
        self.conn = db.connect()
        d = L3.DIR
        self.E = np.concatenate([np.load(f) for f in sorted(d.glob("shard_*.npy")) if ".tmp" not in f.name])
        rows = self.conn.execute(f"SELECT chunk_id, pmcid, year, corpus_part, text FROM {L3.TABLE} ORDER BY chunk_id").fetchall()
        assert len(rows) == len(self.E), (len(rows), len(self.E))
        self.pmcid = np.array([r["pmcid"] for r in rows])
        self.texts = [r["text"] for r in rows]
        self.year_of = {r["pmcid"]: r["year"] for r in rows}
        self.part_of = {r["pmcid"]: r["corpus_part"] for r in rows}
        self.comp = np.load(embed_profiles.out_path(), allow_pickle=False)
        self.cemb = self.comp["emb"]
        self.meta = json.loads(str(self.comp["meta"]))
        self.cos = self.E @ self.cemb.T
        self.flag = {(r["pmcid"], r["theory"]): r["names_theory_loosely"]
                     for r in self.conn.execute("SELECT pmcid, theory, names_theory_loosely FROM paper_flags")}
        self.pos = self._positives()
        self.mrows, self.M = self._masked()
        self.cos_all = np.vstack([self.cos, self.M @ self.cemb.T])
        self.pmcid_all = np.concatenate([self.pmcid, [r["pmcid"] for r in self.mrows]])
        self.mtheory = np.array([r["theory"] for r in self.mrows])
        self.texts_all = self.texts + [r["text"] for r in self.mrows]
        self._bm25()

    def _positives(self) -> dict[str, list[str]]:
        late = set(self.pmcid)
        return {t: sorted(silver(self.conn, t, "exclusive") & late) for t in THEORIES}

    def _masked(self):
        f_rows, f_emb = EVAL_LATE / "masked_chunks.json", EVAL_LATE / "masked_emb.npy"
        rows = json.loads(f_rows.read_text())
        M = np.load(f_emb)
        assert len(rows) == len(M)
        assert {(r["theory"], r["pmcid"]) for r in rows} <= {(t, p) for t in THEORIES for p in self.pos[t]}
        return rows, M

    def _bm25(self) -> None:
        from scipy import sparse
        from sklearn.feature_extraction.text import CountVectorizer
        n0 = len(self.texts)
        cv = CountVectorizer(stop_words="english", lowercase=True, dtype=np.float32)
        X0 = cv.fit_transform(self.texts)
        X = sparse.vstack([X0, cv.transform([r["text"] for r in self.mrows])]).tocsr()
        dl = np.asarray(X.sum(1)).ravel()
        avgdl = dl[:n0].mean()
        df = np.asarray((X0 > 0).sum(0)).ravel()
        idf = np.log(1 + (n0 - df + 0.5) / (df + 0.5)).astype(np.float32)
        an, vocab = cv.build_analyzer(), cv.vocabulary_
        self.bm = {}
        for t in THEORIES:
            claims = [m["text"] for m in self.meta if m["theory"] == t and m["kind"] == "core_claim"]
            sc = np.zeros((X.shape[0], len(claims)), dtype=np.float32)
            for j, c in enumerate(claims):
                qc = sorted({vocab[w] for w in an(c) if w in vocab})
                sub = X[:, qc].tocoo()
                tf = sub.data
                norm = K1 * (1 - B + B * dl[sub.row] / avgdl)
                np.add.at(sc[:, j], sub.row, idf[np.array(qc)[sub.col]] * tf * (K1 + 1) / (tf + norm))
                sc[:, j] /= sc[:n0, j].max()
            self.bm[t] = sc.max(1)


def build_pool(lt: Late, theory: str):
    """Papers, per-variant scores for `theory`, and by_theory[v][row profile] (V4/V5) over the chunk set with `theory`'s positives masked."""
    ix = lt.ix
    keep = np.where(~np.isin(lt.pmcid, lt.pos[theory]))[0]
    gidx = np.concatenate([keep, len(lt.pmcid) + np.where(lt.mtheory == theory)[0]])
    gidx = gidx[np.argsort(lt.pmcid_all[gidx], kind="stable")]
    pm = lt.pmcid_all[gidx]
    starts = np.flatnonzero(np.r_[True, pm[1:] != pm[:-1]])
    z = (lt.cos_all[gidx] - lt.mean) / lt.std
    v3, v4 = {}, {}
    for t in THEORIES:
        sel = np.where(ix.ctheory == t)[0]
        W = z[:, sel] * ix.weight[sel]
        v3[t] = top3_mean(_paper_max(W, starts))
        v4[t] = _paper_max(z[:, sel].max(1), starts)
    by = {"V4": v4, "V5": {t: v3[t] - np.mean([v3[u] for u in THEORIES if u != t], axis=0) for t in THEORIES}}
    sc = {"V4": v4[theory], "V5": by["V5"][theory], "BM25": _paper_max(lt.bm[theory][gidx], starts)}
    return pm[starts], sc, by


def masks(lt: Late, papers: np.ndarray, t: str, exclude_years=()):
    is_pos = np.isin(papers, lt.pos[t])
    names0 = np.array([lt.flag.get((p, t), 1) == 0 for p in papers])
    ok = ~np.isin([lt.year_of[p] for p in papers], list(exclude_years)) if exclude_years else np.ones(len(papers), bool)
    cand = np.array([lt.part_of[p] == "candidate" for p in papers])
    return is_pos & ok, names0 & ~is_pos & ok, names0 & ~is_pos & ok & cand


# ---------------------------------------------------------------------------------------------------------
def build_masked() -> None:
    conn = db.connect()
    EVAL_LATE.mkdir(exist_ok=True)
    late = {r[0] for r in conn.execute(f"SELECT DISTINCT pmcid FROM {L3.TABLE}")}
    pos = {t: sorted(silver(conn, t, "exclusive") & late) for t in THEORIES}
    (EVAL_LATE / "positives.json").write_text(json.dumps(pos, indent=1))
    if (EVAL_LATE / "masked_emb.npy").exists():
        print("masked embeddings cached")
        return
    rows = []
    for t in THEORIES:
        for p in pos[t]:
            r = P.masked_chunks(conn, t, p)
            bad = [x for c in r for x in leaks_for_theory(c["text"], t)]
            if not r:
                print(f"[no_masked_chunks] {t} {p}", file=sys.stderr)
            if bad:
                print(f"[LEAK] {t} {p}: {bad[:5]}", file=sys.stderr)
            rows += r
    (EVAL_LATE / "masked_chunks.json").write_text(json.dumps(rows))
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(embed.MODEL, device="mps")
    model.max_seq_length = embed.MAXLEN
    emb = model.encode([r["text"] for r in rows], batch_size=embed.BATCH, normalize_embeddings=True, show_progress_bar=False)
    np.save(EVAL_LATE / "masked_emb.npy", emb.astype(np.float32))
    print(f"masked chunks: {len(rows)} for {sum(len(v) for v in pos.values())} papers; n per theory", {t: len(v) for t, v in pos.items()})


# ---------------------------------------------------------------------------------------------------------
def parse_old(path: Path) -> dict:
    """{theory short name: {variant: (auc_all, auc_cand, r50, r100, r200)}} from reports/level3_eval_test.md (1995-2015)."""
    out, cur = {}, None
    names = {"Champagne": "Champagne", "GWT": "GWT", "IIT": "IIT", "Panpsychism": "Panpsychism", "PP": "PP"}
    for ln in path.read_text().splitlines():
        m = re.match(r"## (\w+) \((.*?)\): n positives = (\d+)", ln)
        if m:
            cur = names[m.group(1)]
            out[cur] = {"n": int(m.group(3)), "rows": {}}
        m = re.match(r"\| (V4|V5|BM25)[^|]*\| ([\d.]+) \[([\d.]+), ([\d.]+)\] \| \*\*([\d.]+) \[([\d.]+), ([\d.]+)\]\*\* \| ([\d.]+) \[[^|]*\| ([\d.]+) \[[^|]*\| ([\d.]+) \[", ln)
        if m and cur:
            g = m.groups()
            out[cur]["rows"][g[0]] = dict(auc=(float(g[1]), float(g[2]), float(g[3])), cand=(float(g[4]), float(g[5]), float(g[6])),
                                          r50=float(g[7]), r100=float(g[8]), r200=float(g[9]))
    return out


def verdict(new: tuple, old: tuple) -> str:
    d = new[0] - old[0]
    overlap = not (new[1] > old[2] or old[1] > new[2])
    kind = "rose" if d > 0.02 else "dropped" if d < -0.02 else "held"
    return f"{kind} ({d:+.3f}; CIs {'overlap' if overlap else 'do NOT overlap'})"


def evaluate(lt: Late, pools, excl):
    res, tops = {}, {v: {} for v in VARS}
    for t in THEORIES:
        papers, sc, _ = pools[t]
        ip, ineg, icand = masks(lt, papers, t, excl)
        el = np.where(ip | ineg)[0]
        for v in VARS:
            tops[v][t] = list(papers[el[np.argsort(-sc[v][el], kind="stable")][:HUB_K]])
        res[t] = dict(n_pos=int(ip.sum()), n_neg=int(ineg.sum()), n_cand=int(icand.sum()),
                      pos_parts=Counter(lt.part_of[p] for p in papers[ip]),
                      v={v: dict(all=summarize(sc[v][ip], sc[v][ineg]), cand=summarize(sc[v][ip], sc[v][icand])) for v in VARS})
    hub = {}
    for v in VARS:
        cnt = Counter(p for t in THEORIES for p in tops[v][t])
        for t in THEORIES:
            hub[v, t] = float(np.mean([cnt[p] >= 3 for p in tops[v][t]]))
    return res, hub


def matrix(lt: Late, pools, excl, restrict_cand: bool, v: str):
    M = np.zeros((5, 5))
    for j, tc in enumerate(THEORIES):
        papers, _, by = pools[tc]
        ip, ineg, icand = masks(lt, papers, tc, excl)
        neg = icand if restrict_cand else ineg
        for i, tr in enumerate(THEORIES):
            s = by[v][tr]
            M[i, j] = per_positive(s[ip], s[neg])[0].mean()
    return M


def report() -> None:
    lt = Late()
    old = parse_old(REPORTS / "level3_eval_test.md")
    pools = {t: build_pool(lt, t) for t in THEORIES}
    n_all = {t: len(lt.pos[t]) for t in THEORIES}
    out = ["# Level 3 out-of-time evaluation, 2016-2025 (prompt 07, Step 4)", "",
           "Pre-registered in `reports/eval_plan.md` (amendment and addendum of 2026-10-12, both committed before any result existed). "
           "**This is an out-of-time generalization test of the frozen method (profiles, V4 selected on 1995-2015, z-score statistics frozen from the 1995-2015 matrix), not a forecast:** the concept profiles come from the current LoC description text, which is not limited to papers before 2016. Nothing on this page selects, tunes or changes anything.", "",
           "## Read this first", "",
           "- **Candidate-only AUC is the more informative number.** Positives are almost entirely candidate-pool papers (see the per-theory 'positives by corpus part' lines), while most negatives are background or random papers; the all-negatives AUC therefore rewards any variant that prefers theory-flavoured neuroscience/consciousness text. Candidate-only restricts negatives to the candidate pool.",
           "- **Exclusive positives are single-theory papers.** A large share of GWT and IIT papers name both theories (306 of 519 GWT and 333 of 462 IIT direct-mention papers in this window) and are not positives. Positives are therefore not a random sample of each theory's literature.",
           "- **Positives come from the capped candidate pool** (random sample of at most 400 papers per theory from the Europe PMC phrase hits), so the silver sets for GWT, IIT and PP are samples; panpsychism and Champagne were taken whole.",
           "- **The random background sample is week-clustered** (random weekly FIRST_PDATE slices per year, 100 per year), not a uniform draw over each year.",
           "- **Champagne's primary subset is only 8 papers** (title/abstract mention or >= 3 mentions); the other 17 of its 25 exclusive positives have no title/abstract mention and fewer than 3 strong-term mentions. Its numbers are quantitative by the n >= 20 rule but fragile.",
           "- **BM25 statistics** (IDF, per-claim max normalisation) come from the 2016-2025 chunk set; z-scores for V4/V5 use the frozen 1995-2015 statistics.",
           "- **Negatives are unlabeled**, so every metric is a lower bound. 1995-2015 rows below are copied from `reports/level3_eval_test.md` (GWT and PP: test halves, n = 77 and 99; the others: all positives, n = 3, 17, 7). The 1995-2015 and 2016-2025 negative pools differ in size and composition, so differences are indicative, not exact.",
           "- CIs: 2,000 bootstrap resamples of the positives (seed 20261011), negatives fixed.", ""]
    for label, excl in (("ALL YEARS 2016-2025", ()), ("EXCLUDING 2020-2022 (sensitivity check)", COVID)):
        res, hub = evaluate(lt, pools, excl)
        out += [f"# {label}", ""]
        for t in THEORIES:
            r = res[t]
            o = old[SHORT[t]]
            expl = " **(n < 20: exploratory)**" if r["n_pos"] < 20 else ""
            out += [f"## {SHORT[t]}: n positives = {r['n_pos']}{expl}, negatives = {r['n_neg']}, candidate-pool negatives = {r['n_cand']}", "",
                    f"Positives by corpus part: {dict(r['pos_parts'])}. 1995-2015 test n = {o['n']}.", "",
                    "| window | variant | AUC, all negatives [95% CI] | **AUC, candidate-pool only** [95% CI] | recall@50 | recall@100 | recall@200 | hub rate |", "|---|---|---|---|---|---|---|---|"]
            for v in VARS:
                a, c = r["v"][v]["all"], r["v"][v]["cand"]
                ov = o["rows"][v]
                out.append(f"| 2016-2025 | {v}{' (selected)' if v == 'V4' else ''} | {fmt(a['auc'])} | **{fmt(c['auc'])}** | {fmt(a['r50'])} | {fmt(a['r100'])} | {fmt(a['r200'])} | {hub[v, t]:.2f} |")
                out.append(f"| 1995-2015 | {v} | {ov['auc'][0]:.3f} [{ov['auc'][1]:.3f}, {ov['auc'][2]:.3f}] | **{ov['cand'][0]:.3f} [{ov['cand'][1]:.3f}, {ov['cand'][2]:.3f}]** | {ov['r50']:.3f} | {ov['r100']:.3f} | {ov['r200']:.3f} | - |")
            ch = r["v"]["V4"]["all"]["chance"]
            out += [f"| *chance (2016-2025)* | | 0.500 | 0.500 | {ch['r50']:.3f} | {ch['r100']:.3f} | {ch['r200']:.3f} | - |", "",
                    "Candidate-only AUC vs 1995-2015: " + "; ".join(f"{v} {verdict(r['v'][v]['cand']['auc'], old[SHORT[t]]['rows'][v]['cand'])}" for v in VARS) + ".", ""]
        if not excl:
            main_res = res
    # ---- discriminability matrices
    mat = ["# Level 3 discriminability matrix, 2016-2025 (prompt 07, addendum item 2)", "",
           "Same format as `reports/level3_discriminability.md`. Rows are theory profiles; columns are the theories' masked exclusive 2016-2025 positives. Entry = mean percentile rank (100 = best, chance 50) of the column's positives among that column theory's negatives, under the ROW profile. The diagonal should be the largest value in each column. Candidate-pool-only is the more informative matrix. The caveats of `reports/level3_out_of_time.md` apply (single-theory positives, capped candidate pool, week-clustered random sample).", ""]
    for label, excl in (("all years 2016-2025", ()), ("excluding 2020-2022", COVID)):
        npos = {t: int(masks(lt, pools[t][0], t, excl)[0].sum()) for t in THEORIES}
        for v in ("V4", "V5"):
            for restrict in (False, True):
                M = matrix(lt, pools, excl, restrict, v)
                mat += [f"## {v}: {'candidate-pool negatives only' if restrict else 'all negatives'}, {label}", "",
                        "| row profile \\ column positives | " + " | ".join(f"{SHORT[t]}{'†' if npos[t] < 20 else ''} (n={npos[t]})" for t in THEORIES) + " |", "|---|" + "---|" * 5]
                for i, tr in enumerate(THEORIES):
                    mat.append(f"| **{SHORT[tr]}** | " + " | ".join((f"**{M[i, j]:.1f}**" if i == j else f"{M[i, j]:.1f}") for j in range(5)) + " |")
                wins = [int(M[:, j].argmax() == j) for j in range(5)]
                conf = [f"{SHORT[THEORIES[j]]} positives: {SHORT[THEORIES[i]]} profile >= own ({M[i, j]:.1f} vs {M[j, j]:.1f})" for j in range(5) for i in range(5) if i != j and M[i, j] >= M[j, j]]
                miss = [SHORT[t] for t, w in zip(THEORIES, wins) if not w]
                mat += ["", f"Diagonal is the column maximum in {sum(wins)}/5 columns" + (f" (not in: {', '.join(miss)})" if miss else "") + ". " + ("Confused pairs: " + "; ".join(conf) + "." if conf else "No profile beats a column's own profile."), ""]
    (REPORTS / "level3_out_of_time.md").write_text("\n".join(out))
    (REPORTS / "level3_discriminability_late.md").write_text("\n".join(mat))
    print("wrote reports")


if __name__ == "__main__":
    {"masked": build_masked, "report": report}[sys.argv[1]]()

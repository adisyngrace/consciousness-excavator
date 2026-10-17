"""CORE philosophy pilot, Steps 4-5 (prompt 09; pre-registered in reports/eval_plan.md addenda of 2026-10-14 (a)-(d)).

Frozen: profiles/claims, V4 definition (max over a theory's components of z, all weights 1, paper = best chunk), BM25
definition. z-score mean/SD, BM25 IDF and per-claim normalisation are computed on the CORE chunk set itself (PDF-derived
text; stated in the report). Nothing is tuned or selected. Positive sets A (all exclusive with reference split),
B (consciousness-relevant), C (term-precision-trimmed). Primary metric: AUC vs adjacent-background negatives.
CORE text stays in data/; tracked outputs (reports/core_pilot.md) hold titles, years, repositories, links, scores, claim
ids and counts only.

usage: python -m src.eval.core_pilot masked | report | packets
"""
import csv
import html
import json
import random
import re
import sqlite3
import sys
from collections import Counter

import numpy as np

from src.corpus import core_dups, core_l3
from src.corpus.build_core import DB
from src.corpus.core_scan import PILOT, silver_ids
from src.eval import metrics
from src.eval.mask import leaks_for_theory, mask_for_theory
from src.level2_terms.terms import COUNTED_SECTIONS
from src.level3_concepts import embed, embed_profiles

metrics.SEED = 20261014                      # bootstrap seed for the pilot (pre-registered)
OUT = embed.ROOT / "eval_core"
REPORT = embed.ROOT.parent / "reports" / "core_pilot.md"
JUDGE = embed.ROOT / "judge_core"
SHORT = {"champagne_semiotic": "Champagne", "panpsychism": "Panpsychism"}
DEMOTED = {"champagne_semiotic": {"firstness"}, "panpsychism": {"combination problem"}}
CONS_RX = re.compile(r"\bconscious(?:ness)?\b|\bphenomenal\b|\bqualia\b|\bsentien(?:t|ce)\b|\bsubjective experience\b|\bhard problem\b", re.I)
BINS = ((1995, 2009), (2010, 2015), (2016, 2019), (2020, 2025))
SETS = ("A", "B", "C")
SET_NAME = {"A": "A: all exclusive positives (ref. split)", "B": "B: consciousness-relevant subset", "C": "C: term-precision-trimmed"}
TOP, JTOP = 30, 20


_ESC2 = {"22": '"', "26": "&", "27": "'", "3c": "<", "3e": ">"}
_MOJI = re.compile(r"[ÃÂâ][\u0080-\u00bf€™œžŸ“”‚ƒ„…†‡ˆ‰Š‹Œ‘’•–—˜š›]")


def clean_title(t: str) -> str:
    """Unescape HTML entities, Digital Commons style two-digit escapes (\\u27 = ', \\u3cem\\u3e = <em>), \\uXXXX, strip tags,
    repair UTF-8-read-as-cp1252 mojibake and drop replacement characters."""
    t = html.unescape(t or "")
    t = re.sub(r"\\u(22|26|27|3c|3e)", lambda m: _ESC2[m.group(1).lower()], t, flags=re.I)
    t = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    if _MOJI.search(t):
        try:
            t = t.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):             # truncated sequences (e.g. a lost closing byte)
            for bad, good in (("â€œ", "“"), ("â€™", "’"), ("â€“", "–"), ("â€”", "—"), ("â€˜", "‘"), ("â€\x9d", "”"), ("â€", "”")):
                t = t.replace(bad, good)
    return re.sub(r"\s+", " ", t.replace("\ufffd", "")).strip()


def connect() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def positive_sets(conn) -> dict[str, dict[str, list[str]]]:
    out = {}
    for th in PILOT:
        A = sorted(silver_ids(conn, th, True))
        B, C = [], []
        for cid in A:
            title, ab, body = conn.execute("SELECT title, p.abstract, body FROM core_papers p JOIN core_texts USING(core_id) WHERE core_id=?", (cid,)).fetchone()
            if CONS_RX.search(title or "") or CONS_RX.search(ab or "") or len(CONS_RX.findall(f"{title} {ab} {body}")) >= 3:
                B.append(cid)
            terms = {r[0].lower() for r in conn.execute("SELECT term FROM core_term_hits WHERE core_id=? AND theory=? AND tier='strong' AND section IN ('title','abstract','body')", (cid, th))}
            if terms - DEMOTED[th]:
                C.append(cid)
        out[th] = {"A": A, "B": B, "C": C}
    return out


def build_masked() -> None:
    conn = connect()
    OUT.mkdir(exist_ok=True)
    sets = positive_sets(conn)
    (OUT / "positive_sets.json").write_text(json.dumps(sets, indent=1))
    if (OUT / "masked_emb.npy").exists():
        print("masked embeddings cached")
        return
    rows = []
    for th in PILOT:
        for cid in sets[th]["A"]:
            ab, body = conn.execute("SELECT abstract, body FROM core_texts WHERE core_id=?", (cid,)).fetchone()
            r = [{"theory": th, "core_id": cid, "section": s, "position": p, "text": t}
                 for s, p, t in core_l3.paper_chunks(mask_for_theory(ab or "", th), mask_for_theory(body or "", th))]
            bad = [x for c in r for x in leaks_for_theory(c["text"], th)]
            if not r:
                print(f"[no_masked_chunks] {th} {cid}", file=sys.stderr)
            if bad:
                print(f"[LEAK] {th} {cid}: {bad[:5]}", file=sys.stderr)
            rows += r
    (OUT / "masked_chunks.json").write_text(json.dumps(rows))
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(embed.MODEL, device="mps")
    model.max_seq_length = embed.MAXLEN
    emb = model.encode([r["text"] for r in rows], batch_size=embed.BATCH, normalize_embeddings=True, show_progress_bar=False)
    np.save(OUT / "masked_emb.npy", emb.astype(np.float32))
    print(f"masked chunks: {len(rows)}; positives A: { {th: len(sets[th]['A']) for th in PILOT} }; B: { {th: len(sets[th]['B']) for th in PILOT} }; C: { {th: len(sets[th]['C']) for th in PILOT} }")


def weighted_summary(s_pos: np.ndarray, s_neg: np.ndarray, w: np.ndarray) -> dict:
    """AUC with weighted negatives (year-matched sensitivity). Bootstrap over positives, weights fixed."""
    o = np.argsort(s_neg)
    sn, cw = s_neg[o], np.concatenate([[0], np.cumsum(w[o])])
    lo, hi = np.searchsorted(sn, s_pos, "left"), np.searchsorted(sn, s_pos, "right")
    pct = (cw[lo] + 0.5 * (cw[hi] - cw[lo])) / cw[-1]
    rng = np.random.default_rng(metrics.SEED)
    m = pct[rng.integers(0, len(pct), size=(metrics.BOOT, len(pct)))].mean(1)
    return {"auc": (float(pct.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))), "n_eff_neg": float(w.sum() ** 2 / (w ** 2).sum())}


def year_bin(y: int) -> int:
    return next(i for i, (a, b) in enumerate(BINS) if a <= y <= b)


class Pilot:
    def __init__(self) -> None:
        self.conn = connect()
        rows = self.conn.execute("SELECT chunk_id, core_id, section, year, part, text FROM core_chunks ORDER BY chunk_id").fetchall()
        self.E = core_l3.load_embeddings(self.conn)
        assert len(rows) == len(self.E)
        self.cid = np.array([r["core_id"] for r in rows])
        self.sec = np.array([r["section"] for r in rows])
        self.texts = [r["text"] for r in rows]
        comp = np.load(embed_profiles.out_path(), allow_pickle=False)
        meta = json.loads(str(comp["meta"]))
        keep = [i for i, m in enumerate(meta) if m["theory"] in PILOT]
        self.meta = [meta[i] for i in keep]
        self.ctheory = np.array([m["theory"] for m in self.meta])
        self.cos = self.E @ comp["emb"][keep].T
        self.mean, self.std = self.cos.mean(0), self.cos.std(0)         # CORE-set statistics (pre-registered)
        self.sets = json.loads((OUT / "positive_sets.json").read_text())
        self.mrows = json.loads((OUT / "masked_chunks.json").read_text())
        M = np.load(OUT / "masked_emb.npy")
        assert len(M) == len(self.mrows)
        self.cos_all = np.vstack([self.cos, M @ comp["emb"][keep].T])
        self.cid_all = np.concatenate([self.cid, [r["core_id"] for r in self.mrows]])
        self.mtheory = np.array([r["theory"] for r in self.mrows])
        self.texts_all = self.texts + [r["text"] for r in self.mrows]
        p = {r["core_id"]: r for r in self.conn.execute("SELECT core_id, title, year, part, repository, link, doi, cand_theories, abstract FROM core_papers")}
        self.paper = p
        self.flag = {(r["core_id"], r["theory"]): r["names_theory_loosely"] for r in self.conn.execute("SELECT core_id, theory, names_theory_loosely FROM core_paper_flags")}
        self._bm25()
        self.pools = {t: self.build_pool(t) for t in PILOT}

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
        for t in PILOT:
            claims = [m["text"] for m in self.meta if m["theory"] == t and m["kind"] == "core_claim"]
            sc = np.zeros((X.shape[0], len(claims)), dtype=np.float32)
            for j, c in enumerate(claims):
                qc = sorted({vocab[w] for w in an(c) if w in vocab})
                sub = X[:, qc].tocoo()
                tf = sub.data
                norm = 1.5 * (1 - 0.75 + 0.75 * dl[sub.row] / avgdl)
                np.add.at(sc[:, j], sub.row, idf[np.array(qc)[sub.col]] * tf * 2.5 / (tf + norm))
                sc[:, j] /= sc[:n0, j].max()
            self.bm[t] = sc.max(1)

    def build_pool(self, theory: str) -> dict:
        """Papers and per-theory V4 / BM25 scores over the chunk set with `theory`'s set-A positives masked."""
        keep = np.where(~np.isin(self.cid, self.sets[theory]["A"]))[0]
        g = np.concatenate([keep, len(self.cid) + np.where(self.mtheory == theory)[0]])
        g = g[np.argsort(self.cid_all[g], kind="stable")]
        pm = self.cid_all[g]
        starts = np.flatnonzero(np.r_[True, pm[1:] != pm[:-1]])
        z = (self.cos_all[g] - self.mean) / self.std
        v4 = {t: np.maximum.reduceat(z[:, self.ctheory == t].max(1), starts) for t in PILOT}
        return {"papers": pm[starts], "V4": v4[theory], "by": v4, "BM25": np.maximum.reduceat(self.bm[theory][g], starts)}

    def masks(self, t: str, s: str):
        papers = self.pools[t]["papers"]
        pos = np.isin(papers, self.sets[t][s])
        names0 = np.array([self.flag[(p, t)] == 0 for p in papers])
        part = np.array([self.paper[p]["part"] for p in papers])
        neg = names0 & ~pos
        return pos, {"adjacent-background (primary)": neg & (part == "background"), "candidate-pool": neg & (part == "candidate"),
                     "all negatives": neg, "distractors only": neg & (part == "distractor")}

    def weights(self, t: str, pos: np.ndarray, neg: np.ndarray) -> np.ndarray | None:
        papers = self.pools[t]["papers"]
        yb = np.array([year_bin(self.paper[p]["year"]) for p in papers])
        pc = np.bincount(yb[pos], minlength=len(BINS)) / pos.sum()
        nc = np.bincount(yb[neg], minlength=len(BINS)) / neg.sum()
        w = np.where(nc > 0, pc / np.where(nc > 0, nc, 1), 0)
        return w[yb[neg]]

    def positives_scores(self, t, s, v):
        pos, negs = self.masks(t, s)
        return self.pools[t][v][pos], {k: self.pools[t][v][m] for k, m in negs.items()}


def counts_table(P: Pilot, ids: list[str]) -> tuple[Counter, Counter]:
    return Counter(P.paper[i]["repository"] for i in ids), Counter("1995-2015" if P.paper[i]["year"] <= 2015 else "2016-2025" for i in ids)


# ---------------------------------------------------------------------------------------------------------
def fmt(x) -> str:
    return f"{x[0]:.3f} [{x[1]:.3f}, {x[2]:.3f}]"


def unmasked_scores(P: Pilot) -> tuple[np.ndarray, dict, dict]:
    """Paper-level V4 on the UNMASKED chunk set for each theory: (papers, score, best chunk row, best component)."""
    order = np.argsort(P.cid, kind="stable")
    pm = P.cid[order]
    starts = np.flatnonzero(np.r_[True, pm[1:] != pm[:-1]])
    z = (P.cos[order] - P.mean) / P.std
    sc, best = {}, {}
    for t in PILOT:
        sel = np.where(P.ctheory == t)[0]
        zt = z[:, sel]
        cm = zt.max(1)
        sc[t] = np.maximum.reduceat(cm, starts)
        bi = {}
        for k, s in enumerate(starts):
            e = starts[k + 1] if k + 1 < len(starts) else len(pm)
            j = int(np.argmax(cm[s:e]))
            bi[pm[s]] = (int(order[s + j]), P.meta[sel[int(np.argmax(zt[s + j]))]]["id"])
        best[t] = bi
    return pm[starts], sc, best


def top_lists(P: Pilot, n: int) -> dict[str, list[dict]]:
    papers, sc, best = unmasked_scores(P)
    rep_of, _ = core_dups.clusters(P.conn)
    out = {}
    for t in PILOT:
        elig = [i for i, p in enumerate(papers) if P.flag[(p, t)] == 0]
        elig.sort(key=lambda i: -sc[t][i])
        rows, seen = [], set()
        for i in elig:
            p = papers[i]
            if rep_of[p] in seen:              # near-duplicate of a higher-ranked paper: collapsed (core_dups)
                continue
            seen.add(rep_of[p])
            if len(rows) == n:
                break
            named = [th for (c, th), f in P.flag.items() if c == p and f == 1]
            r = P.paper[p]
            rows.append({"core_id": p, "title": clean_title(r["title"]), "year": r["year"], "repository": r["repository"], "link": r["link"],
                         "doi": r["doi"] or "", "score_v4": float(sc[t][i]), "best_component": best[t][p][1], "best_chunk": best[t][p][0],
                         "other_theories_named": ";".join(sorted(named)), "part": r["part"]})
        out[t] = rows
    return out


def overlap_rate(P: Pilot) -> dict[str, float]:
    papers, sc, _ = unmasked_scores(P)
    elig = np.array([all(P.flag[(p, t)] == 0 for t in PILOT) for p in papers])
    top = {t: set(papers[np.where(elig)[0][np.argsort(-sc[t][elig], kind="stable")][:50]]) for t in PILOT}
    return {t: len(top[t] & top[u]) / 50 for t in PILOT for u in PILOT if u != t}


def label_precision() -> list[str]:
    rows = list(csv.DictReader(open(embed.ROOT.parent / "reports" / "core_pilot_labels.csv")))
    by: dict[tuple, Counter] = {}
    for r in rows:
        by.setdefault((r["theory"], r["matched_term"]), Counter())[r["label"]] += 1
    out = ["| theory | matched term | n | Y | P | N | precision Y | precision Y+P |", "|---|---|---|---|---|---|---|---|"]
    for (th, term), c in sorted(by.items()):
        n = sum(c.values())
        out.append(f"| {SHORT[th]} | {term.lower()} | {n} | {c['Y']} | {c['P']} | {c['N']} | {c['Y'] / n:.0%} | {(c['Y'] + c['P']) / n:.0%} |")
    for th in PILOT:
        c = Counter(r["label"] for r in rows if r["theory"] == th)
        out.append(f"| **{SHORT[th]} overall** | all | 10 | {c['Y']} | {c['P']} | {c['N']} | {c['Y'] / 10:.0%} | {(c['Y'] + c['P']) / 10:.0%} |")
    return out


def pmc_rows() -> dict:
    return {r["theory"]: r for r in csv.DictReader(open(embed.ROOT.parent / "results" / "summary_metrics.csv"))}


def report() -> None:
    P = Pilot()
    pmc = pmc_rows()
    selftest = (embed.ROOT / "logs" / "core_selftest.txt")
    o = ["# CORE philosophy pilot: Champagne's semiotic account and panpsychism (prompt 09, Steps 3-5)", "",
         "**Exploratory.** A separate corpus of CORE open-access papers (`source = core`, `section_quality = coarse`), pre-registered in `reports/eval_plan.md` (addenda of 2026-10-14 (a)-(d), committed before any CORE chunk was embedded or evaluated). Nothing here enters the PubMed Central tables, exports or app. Frozen and untouched: `terms.yaml`, profile claims, V4, the existing embeddings and reports. CORE-derived text is in gitignored `data/` only; this file contains titles, years, repositories, links, scores, claim ids and counts, no excerpts.", "",
         "## Read this first", "",
         "- **Champagne's full positive set is mostly general Peircean-semiotics papers, not consciousness work.** In the 10 hand-labelled sampled hits, 1 was about consciousness-related work (Y), 8 were Peirce's semiotics outside consciousness (P: rock art, gender studies, literature, anthropology, physics) and 1 was not a real use (N, \"firstness\" in a textbook). Claims about *consciousness-relevant neighbours* of the semiotic account therefore rest on the consciousness-relevant subset (set B), not on the full set A. Any Champagne result on set A measures retrieval of Peircean-semiotics literature in general.",
         "- Panpsychism's sampled hits were 9 of 10 genuine (the one N is \"combination problem\" in a speech-recognition paper).",
         "- **Positives come from the candidate pool**, and the pool is the term search itself, so candidate-pool AUC and the primary adjacent-background AUC both reward topical similarity to the theory's vocabulary region. Negatives are unlabeled, so every AUC is a lower bound.",
         "- **The text is PDF-derived**, with page furniture, hyphenation breaks and mixed repository front matter (boilerplate stripped as pre-registered). z-score statistics, BM25 IDF and BM25 normalisation are computed on this CORE chunk set, not on the PubMed Central statistics, so numbers are not exactly comparable with the PMC runs.",
         "- **Small n and a thin early period:** no candidates before 2000 and only 69 candidates in 1995-2015 against 160 in 2016-2025. The distractors are *approximately random within relevance-ordered hits*, not a uniform sample.",
         "- CORE terms: free-licence conditions and the \"machine processing only\" statement apply; the licence field is unknown for every record (the API returns none).", "",
         "## Step 3: chunking and embedding", "",
         f"78,278 chunks (3,396 abstract, 74,882 body) for 2,213 papers; no paper unchunked. Model bge-base-en-v1.5, normalised, separate shards in `data/embeddings_core/`. Self-retrieval test: {selftest.read_text().strip() if selftest.exists() else 'not run'}.", "",
         "## Hit labels and per-term precision (20 sampled direct-mention hits)", "", *label_precision(), "",
         "Per-term n is 1 to 6, so these are indications only. Demotion rule used for set C (below 80%: Y+P for Champagne, Y for panpsychism): Champagne \"firstness\", panpsychism \"combination problem\".", "",
         "## Positive sets", ""]
    o += ["| theory | " + " | ".join(SET_NAME[s] for s in SETS) + " |", "|---|---|---|---|"]
    for t in PILOT:
        o.append(f"| {SHORT[t]} | " + " | ".join(str(len(P.sets[t][s])) for s in SETS) + " |")
    o += ["", "Sets: A = exclusive silver papers with a reference split; B = A papers with consciousness vocabulary in title or abstract or at least 3 times overall; C = A papers with a hit from a non-demoted term. A set below 20 papers is exploratory. The previously drafted \"primary\" subset is dropped.", ""]
    flags = [f"{SHORT[t]} {s}" for t in PILOT for s in SETS if len(P.sets[t][s]) < 20]
    o.append("Sets with n < 20 (exploratory, qualitative only): " + (", ".join(flags) if flags else "none") + ".")
    o += ["", "### Counts by period and repository (candidates and positives)", ""]
    for t in PILOT:
        cand = [c for c, r in P.paper.items() if r["part"] == "candidate" and t in (r["cand_theories"] or "").split(";")]
        groups = [("candidate pool", cand)] + [(f"set {s}", P.sets[t][s]) for s in SETS]
        o += [f"**{SHORT[t]}**", "", "| group | n | 1995-2015 | 2016-2025 | top repositories (n) |", "|---|---|---|---|---|"]
        for name, ids in groups:
            repo, per = counts_table(P, ids)
            o.append(f"| {name} | {len(ids)} | {per['1995-2015']} | {per['2016-2025']} | " + "; ".join(f"{k} {v}" for k, v in repo.most_common(6)) + " |")
        o.append("")
    # ---------------- Step 4 results
    o += ["## Step 4: masked-positive retrieval", "",
          "Positives are masked with the Level 2 term list and landmark authors (deletion masking, leak check run; any leak would be listed in the masking log), then re-embedded. Negatives: CORE papers with `names_theory_loosely = 0` for the theory. **Primary metric: AUC against adjacent-background negatives.** Also shown: candidate-pool negatives (CORE hits that do not name the theory), all negatives, distractors only (easy). Recall@k is the share of positives ranked within the top k of positives plus the stated negatives; chance recall is shown.", ""]
    for t in PILOT:
        for s in SETS:
            pos, negs = P.masks(t, s)
            n_pos = int(pos.sum())
            tag = " **(n < 20: exploratory)**" if n_pos < 20 else ""
            o += [f"### {SHORT[t]}, {SET_NAME[s]}: n positives = {n_pos}{tag}", ""]
            if n_pos == 0:
                o += ["No positives.", ""]
                continue
            o += ["| negatives | n neg | variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | chance r@50/100/200 |", "|---|---|---|---|---|---|---|---|"]
            for pool, m in negs.items():
                for v in ("V4", "BM25"):
                    r = metrics.summarize(P.pools[t][v][pos], P.pools[t][v][m])
                    ch = r["chance"]
                    o.append(f"| {pool} | {int(m.sum())} | {v} | {fmt(r['auc'])} | {r['r50'][0]:.2f} | {r['r100'][0]:.2f} | {r['r200'][0]:.2f} | {ch['r50']:.3f}/{ch['r100']:.3f}/{ch['r200']:.3f} |")
            o += ["", f"*Year-matched sensitivity check* (negatives re-weighted to the set's year distribution over bins {', '.join(f'{a}-{b}' for a, b in BINS)}; beside, not instead of, the table above):", "",
                  "| negatives | variant | unweighted AUC | year-matched AUC [95% CI] | effective n of weighted negatives |", "|---|---|---|---|---|"]
            for pool in ("adjacent-background (primary)", "candidate-pool", "all negatives"):
                m = negs[pool]
                w = P.weights(t, pos, m)
                for v in ("V4", "BM25"):
                    ws = weighted_summary(P.pools[t][v][pos], P.pools[t][v][m], w)
                    u = metrics.summarize(P.pools[t][v][pos], P.pools[t][v][m])["auc"][0]
                    o.append(f"| {pool} | {v} | {u:.3f} | {fmt(ws['auc'])} | {ws['n_eff_neg']:.0f} of {int(m.sum())} |")
            o.append("")
    o += ["### Compared with the PubMed Central runs (same theories; candidate-pool-only AUC, V4 / BM25)", "",
          "| theory | PMC 1995-2015 (n pos) | PMC 2016-2025 (n pos) | CORE set A, candidate-pool (n pos) | CORE set A, adjacent-background (primary) |", "|---|---|---|---|---|"]
    for t in PILOT:
        r = pmc[t]
        pos, negs = P.masks(t, "A")
        c = {v: metrics.summarize(P.pools[t][v][pos], P.pools[t][v][negs["candidate-pool"]])["auc"][0] for v in ("V4", "BM25")}
        b = {v: metrics.summarize(P.pools[t][v][pos], P.pools[t][v][negs["adjacent-background (primary)"]])["auc"][0] for v in ("V4", "BM25")}
        o.append(f"| {SHORT[t]} | {float(r['V4_cand_auc_1995_2015']):.3f} / {float(r['BM25_cand_auc_1995_2015']):.3f} (n {r['cand_auc_1995_2015_n_positives']}) | {float(r['V4_cand_auc_2016_2025']):.3f} / {float(r['BM25_cand_auc_2016_2025']):.3f} (n {r['cand_auc_2016_2025_n_positives']}) | {c['V4']:.3f} / {c['BM25']:.3f} (n {int(pos.sum())}) | {b['V4']:.3f} / {b['BM25']:.3f} |")
    o += ["", "PMC and CORE differ in text type, negative pools and z-score basis; read as indicative only.", ""]
    # discriminability 2x2
    o += ["### 2 x 2 discriminability (V4, set A positives)", "",
          "Entry = mean percentile rank (100 = best, chance 50) of the column theory's masked positives among its negatives, scored by the ROW profile. The diagonal should be the larger value in each column.", ""]
    for pool in ("adjacent-background (primary)", "all negatives"):
        o += [f"Negatives: {pool}", "", "| row profile \\ column positives | " + " | ".join(f"{SHORT[t]} (n={len(P.sets[t]['A'])})" for t in PILOT) + " |", "|---|---|---|"]
        for tr in PILOT:
            cells = []
            for tc in PILOT:
                pos, negs = P.masks(tc, "A")
                s = P.pools[tc]["by"][tr]
                cells.append(f"{metrics.per_positive(s[pos], s[negs[pool]])[0].mean():.1f}")
            o.append(f"| **{SHORT[tr]}** | " + " | ".join(f"**{c}**" if i == j else c for j, (c, tc) in enumerate(zip(cells, PILOT)) for i in [PILOT.index(tr)]) + " |")
        o.append("")
    ov = overlap_rate(P)
    o += [f"Overlap rate (two-theory version of the hub rate): share of a theory's top 50 unmasked papers (naming neither theory) that also appear in the other theory's top 50: Champagne {ov[('champagne_semiotic')]:.2f}, panpsychism {ov[('panpsychism')]:.2f}.", ""]
    # ---------------- Step 5
    tops = top_lists(P, TOP)
    o += ["## Step 5: top 30 per theory under V4, papers that do not name the theory (`names_theory_loosely = 0`)", "",
          "Unmasked V4 scores (z on the CORE chunk set, unitless). `best component` is the profile component (claim id, `win-` description window or `seed-` abstract) closest to the paper's best passage. No snippets are shown (CORE terms handling); open the link to read the paper. **Unjudged.**", ""]
    for t in PILOT:
        o += [f"### {SHORT[t]}", "", "| # | title | year | repository | link | score | best component | other theories named |", "|---|---|---|---|---|---|---|---|"]
        for k, r in enumerate(tops[t], 1):
            o.append(f"| {k} | {r['title'][:110].replace('|', '/')} | {r['year']} | {r['repository'][:40]} | {r['link']} | {r['score_v4']:.2f} | {r['best_component']} | {r['other_theories_named'] or '-'} |")
        o.append("")
    nd = core_dups.summary(P.conn)
    o += ["## Near-duplicate records", "",
          f"Near-duplicates (same normalized title and year, or normalized-title similarity above 0.9; titles under 8 characters ignored): **{nd['pairs']} pairs** ({nd['same_title_pairs']} with identical normalized titles in different years or repositories), involving {nd['papers_in_clusters']} papers; collapsing to one record per cluster would remove {nd['removable']} of {nd['n_papers']} papers (**{100 * nd['removable_share']:.1f}%**). Records with the same title and year were already removed at build time (`dup_within_core`, 2,762 dropped). The rate is below the 2% threshold, so the primary metric was **not** rerun; the top-30 lists below and the exported files are collapsed to one record per cluster (the best-ranked is kept; lists are filled to 30 unique). The blind packets in `data/judge_core/` were built before this collapse and are on hold, untouched.", ""]
    o += ["Observations from the titles only (not judgments; nothing has been judged): the Champagne list is dominated by applied-semiotics papers (advertising, media, literature, culture) with a few philosophy-of-mind or Peirce papers, which matches the profile's semiotic vocabulary and the nature of set A; the panpsychism list mixes philosophy-of-mind and consciousness papers with some clearly unrelated technical titles (for example radar cross section, chaotic oscillators), and in the first version of this report ranks 29 and 30 were two CORE records of the same paper (now collapsed). Titles are cleaned of escape sequences and encoding damage.", ""]
    o += ["## Caveats", "",
          "- Positives are exclusive silver papers found through the same term list that defines the pool; mostly candidate-pool papers.",
          "- Champagne set A is mostly general Peircean-semiotics literature (see the top of this file); set B has the consciousness-relevant papers, and its n is shown above.",
          "- PDF-derived text, repository boilerplate (stripped by rule), mixed languages removed only by a stopword rule; reference lists were split off for 73% of papers (positives require a split).",
          "- Different z-score and BM25 statistics from the PMC runs (the CORE statistics include the positives' unmasked chunks); small n; negatives are unlabeled (lower bounds).",
          "- No judging was run. The blind packets (top 20 per theory) are in `data/judge_core/` and have not been read."]
    REPORT.write_text("\n".join(o))
    (OUT / "top_lists.json").write_text(json.dumps(tops))
    print("wrote", REPORT)


# ---------------------------------------------------------------------------------------------------------
def packets() -> None:
    """Blind packets for the top 20 per theory (V4, names_theory_loosely = 0) + 10% repeats, under data/judge_core/ only.
    No scores, ranks or method; same format as prompt 06 (src/judge/build.py). Packets are never read here."""
    from src.judge.build import claims, layout, BATCH
    P = Pilot()
    tops = json.loads((OUT / "top_lists.json").read_text()) if (OUT / "top_lists.json").exists() else top_lists(P, TOP)
    sel_by_theory = {t: np.where(P.ctheory == t)[0] for t in PILOT}
    (JUDGE / "packets").mkdir(parents=True, exist_ok=True)
    pref, member, bno, summary = {"champagne_semiotic": "CC", "panpsychism": "CP"}, [], 0, []
    z = (P.cos - P.mean) / P.std
    for t in PILOT:
        rng = random.Random(f"20261014-{t}")
        items = []
        for r in tops[t][:JTOP]:
            rows = np.where((P.cid == r["core_id"]) & (P.sec == "body"))[0]
            sc = z[np.ix_(rows, sel_by_theory[t])].max(1)
            ps = [{"section": "body", "text": " ".join(P.texts[rows[j]].split())} for j in np.argsort(-sc, kind="stable")[:2]]
            ab = clean_title(P.paper[r["core_id"]]["abstract"] or "")
            items.append({"pmcid": r["core_id"], "title": r["title"], "year": r["year"], "abstract": ab, "passages": ps, "repeat_of": ""})
        reps = [dict(i) for i in rng.sample(items, round(0.1 * len(items)))]
        for r in reps:
            r["repeat_of"] = r["pmcid"]
        allit = layout(items, reps, rng)
        cl = "\n".join(f"- **{c['id']}:** {c['text']}" for c in claims(t))
        for n, it in enumerate(allit, 1):
            it["item_id"] = f"{pref[t]}{n:03d}"
            member.append({"item_id": it["item_id"], "theory": t, "core_id": it["pmcid"], "is_repeat": int(bool(it["repeat_of"]))})
        for b in range(0, len(allit), BATCH):
            bno += 1
            body = "\n".join(
                f"### Item {i['item_id']}\n\n**Title:** {i['title']}\n**Year:** {i['year']}\n\n**Abstract:** {i['abstract'] or '(no abstract available)'}\n\n"
                + "\n\n".join(f"**Passage {k} ({p['section']}):** {p['text']}" for k, p in enumerate(i["passages"], 1)) + "\n"
                for i in allit[b:b + BATCH])
            (JUDGE / "packets" / f"batch_{bno:02d}.md").write_text(f"# Batch {bno:02d}\n\n**Theory:** {SHORT[t]} ({t})\n\n**Core claims:**\n{cl}\n\n---\n\n{body}")
        summary.append((t, len(items), len(reps)))
    with open(JUDGE / "membership.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "theory", "core_id", "is_repeat"])
        w.writeheader()
        w.writerows(member)
    print("packets written to data/judge_core/ (not read):", summary, "batches:", bno)


if __name__ == "__main__":
    {"masked": build_masked, "report": report, "packets": packets}[sys.argv[1]]()

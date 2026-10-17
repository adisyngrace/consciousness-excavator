"""Build the CORE philosophy-pilot corpus (prompt 09 Step 1) into data/core_pilot.db (separate from excavator.db).

Parts: candidate (frozen strong terms of Champagne / panpsychism, cap 300 each), background (adjacent philosophy-of-mind /
semiotics topics, 48 per year, records naming either pilot theory dropped), distractor (generic humanities / social
science query at random offsets within relevance-ordered hits: APPROXIMATELY RANDOM WITHIN RELEVANCE-ORDERED HITS, 16 per
year). Only records for which CORE returns full text are kept. No PDF is downloaded. Idempotent: rebuilds from the
on-disk response cache. Seed 20261014.  Run: python -m src.corpus.build_core
"""
import json
import random
import re
import sqlite3
import statistics
from collections import Counter
from pathlib import Path

import yaml

from src.corpus import core
from src.level2_terms.terms import term_regex

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "core_pilot.db"
MAIN_DB = ROOT / "data" / "excavator.db"
SEED = 20261014
PILOT = ("champagne_semiotic", "panpsychism")
Y0, Y1 = 1995, 2025
CAND_CAP, BG_PER_YEAR, DIST_PER_YEAR = 300, 48, 16
MAX_WORDS, MIN_CHARS, VOCAB_MIN_SHARE, STOP_MIN_SHARE = 6000, 3000, 0.75, 0.20
BG_TERMS = ["mind-body problem", "qualia", "phenomenology", "intentionality", "semiosis", "semiotics",
            "philosophy of mind", "Peirce", "phenomenal consciousness", "hard problem"]
DIST_TERMS = ["history", "sociology", "economics", "linguistics", "education", "literature", "politics", "law",
              "religion", "anthropology"]
STOP = set("the of and to in a is that for it as with was on by be this are or from at an which not have has but "
           "their its they we can more also these been were one all than other such may into only".split())
REF_HEAD = re.compile(r"^\W*(?:\d+\.?\s*)?(references|bibliography|works cited|literature cited|reference list|"
                      r"references and notes)\W*$", re.I | re.M)
DDL = """
DROP TABLE IF EXISTS core_papers; DROP TABLE IF EXISTS core_texts; DROP TABLE IF EXISTS core_drops;
CREATE TABLE core_papers (core_id TEXT PRIMARY KEY, source TEXT DEFAULT 'core', section_quality TEXT DEFAULT 'coarse',
  part TEXT, cand_theories TEXT, doi TEXT, title TEXT, year INTEGER, abstract TEXT, repository TEXT, license TEXT,
  link TEXT, download_url TEXT, ref_split INTEGER, n_words INTEGER, n_words_total INTEGER, vocab_share REAL);
CREATE TABLE core_texts (core_id TEXT PRIMARY KEY, abstract TEXT, body TEXT, refs TEXT);
CREATE TABLE core_drops (core_id TEXT, title TEXT, year INTEGER, part TEXT, reason TEXT);
"""


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def norm_doi(d: str | None) -> str:
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (d or "").strip().lower())


def load_vocab() -> set[str]:
    """Words seen >= 3 times in PMC abstracts/introductions/discussions: the 'dictionary' for the OCR-garbage rule."""
    conn = sqlite3.connect(MAIN_DB)
    cnt: Counter = Counter()
    for (t,) in conn.execute("SELECT text FROM paper_sections WHERE section IN ('abstract','introduction','discussion')"):
        cnt.update(re.findall(r"[a-z]{3,}", t.lower()))
    return {w for w, c in cnt.items() if c >= 3}


def pmc_keys() -> tuple[set[str], set[tuple[str, int]]]:
    conn = sqlite3.connect(MAIN_DB)
    dois, titles = set(), set()
    for doi, title, year in conn.execute("SELECT doi, title, year FROM papers"):
        if doi:
            dois.add(norm_doi(doi))
        titles.add((norm_title(title), year))
    return dois, titles


def strong_rx() -> re.Pattern:
    t = yaml.safe_load(open(ROOT / "src" / "terms.yaml"))["theories"]
    terms = sorted({s for th in PILOT for s in t[th]["strong"]}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(term_regex(s) for s in terms) + r")(?!\w)", re.I)


def split_refs(text: str) -> tuple[str, str, bool]:
    """Cut at the LAST references heading located in the final 60% of the text."""
    cut = None
    for m in REF_HEAD.finditer(text):
        if m.start() > 0.4 * len(text):
            cut = m.start()
    return (text[:cut], text[cut:], True) if cut is not None else (text, "", False)


def clean(rec: dict, vocab: set[str]) -> tuple[dict | None, str | None]:
    """Return (cleaned fields, None) or (None, drop reason)."""
    ft = (rec.get("fullText") or "").strip()
    if not ft:
        return None, "no_fulltext"
    ft = re.sub(r"[ \t ]+", " ", ft.replace("\r", ""))
    abstract = (rec.get("abstract") or "").strip()
    body, refs, split = split_refs(ft)
    words = body.split()
    if len(abstract) + len(body) < MIN_CHARS:
        return None, "too_short"
    toks = re.findall(r"[a-z]+", " ".join(words[:3000]).lower())
    if toks and sum(t in STOP for t in toks) / len(toks) < STOP_MIN_SHARE:
        return None, "not_english"
    alpha = [t for t in toks if len(t) >= 3]
    share = sum(t in vocab for t in alpha) / len(alpha) if alpha else 0.0
    if share < VOCAB_MIN_SHARE:
        return None, "ocr_garbage"
    used = body                                         # keep line breaks (boilerplate rule works on lines)
    if len(words) > MAX_WORDS:
        used = body[:[m.end() for m in re.finditer(r"\S+", body)][MAX_WORDS - 1]]
    return {"abstract": abstract, "body": used, "refs": refs, "ref_split": int(split), "vocab_share": share,
            "n_words": len(abstract.split()) + min(len(words), MAX_WORDS), "n_words_total": len(words)}, None


def fetch(q: str, n: int, offset0: int = 0) -> list[dict]:
    out, off = [], offset0
    while len(out) < n:
        d = core.search(q, limit=min(100, n - len(out)), offset=off)
        res = d.get("results", [])
        out += res
        off += len(res)
        if not res or off >= d.get("totalHits", 0) or off >= 9000:
            break
    return out


def total(q: str) -> int:
    return core.search(q, limit=1)["totalHits"]


def candidates(log) -> list[tuple[dict, str, str]]:
    t = yaml.safe_load(open(ROOT / "src" / "terms.yaml"))["theories"]
    rng, out = random.Random(SEED), []
    for th in PILOT:
        q = core.phrase_or(t[th]["strong"]) + " AND " + core.YEARS.format(a=Y0, b=Y1)
        recs = fetch(q, 2000)
        log(f"candidate {th}: totalHits={total(q)} fetched={len(recs)}")
        if len(recs) > CAND_CAP * 1.5:      # keep a surplus so drops do not starve the pool; capped after cleaning
            recs = rng.sample(recs, int(CAND_CAP * 1.5))
        out += [(r, "candidate", th) for r in recs]
    return out


def background(log) -> list[tuple[dict, str, str]]:
    out = []
    for y in range(Y0, Y1 + 1):
        q = core.phrase_or(BG_TERMS, ("title", "abstract")) + " AND " + core.YEARS.format(a=y, b=y)
        recs = fetch(q, 300)
        log(f"background {y}: fetched={len(recs)}")
        out += [(r, "background", "") for r in recs]
    return out


def distractors(log) -> list[tuple[dict, str, str]]:
    rng, out = random.Random(SEED + 1), []
    for y in range(Y0, Y1 + 1):
        q = core.phrase_or(DIST_TERMS, ("abstract",)) + " AND " + core.YEARS.format(a=y, b=y)
        n = total(q)
        recs: list[dict] = []
        for _ in range(2):
            off = rng.randrange(0, max(1, min(n, 8900) - 25))
            recs += core.search(q, limit=25, offset=off).get("results", [])
        log(f"distractor {y}: totalHits={n} fetched={len(recs)}")
        out += [(r, "distractor", "") for r in recs]
    return out


def build(log=print) -> None:
    vocab, (pmc_dois, pmc_titles), rx = load_vocab(), pmc_keys(), strong_rx()
    log(f"vocab {len(vocab)} words; PMC dedup keys {len(pmc_dois)} DOIs, {len(pmc_titles)} title-years")
    raw = candidates(log) + background(log) + distractors(log)
    conn = sqlite3.connect(DB)
    conn.executescript(DDL)
    rng = random.Random(SEED + 2)
    seen_id, seen_doi, seen_ty = set(), set(), set()
    cand_theories: dict[str, set] = {}
    kept: dict[str, list] = {"candidate": [], "background": [], "distractor": []}
    for rec, part, th in raw:
        cid, title, year = str(rec.get("id")), (rec.get("title") or "").strip(), rec.get("yearPublished")
        if part == "candidate":
            cand_theories.setdefault(cid, set()).add(th)
        def drop(reason):
            conn.execute("INSERT INTO core_drops VALUES (?,?,?,?,?)", (cid, title, year, part, reason))
        if cid in seen_id:
            if part == "candidate":
                pass
            continue                                   # same record found by several queries: not a drop
        doi, ty = norm_doi(rec.get("doi")), (norm_title(title), year)
        c, why = clean(rec, vocab)
        if why is None and not (Y0 <= (year or 0) <= Y1):
            why = "year_out_of_range"
        if why is None and doi and doi in pmc_dois:
            why = "dup_pmc_doi"
        if why is None and ty in pmc_titles:
            why = "dup_pmc_title_year"
        if why is None and ((doi and doi in seen_doi) or ty in seen_ty):
            why = "dup_within_core"
        if why is None and part != "candidate" and rx.search(title + " " + c["abstract"] + " " + rec["fullText"]):
            why = "names_pilot_theory"
        if why:
            drop(why)
            continue
        seen_id.add(cid); seen_ty.add(ty)
        if doi:
            seen_doi.add(doi)
        c.update(core_id=cid, part=part, title=title, year=year, doi=doi or None,
                 repository=(rec.get("dataProviders") or [{}])[0].get("name") or "unknown",
                 link=f"https://core.ac.uk/works/{cid}", download_url=rec.get("downloadUrl"))
        kept[part].append(c)
    # caps (random, seeded, after cleaning)
    final: list[dict] = []
    for th in PILOT:
        pool = [c for c in kept["candidate"] if th in cand_theories[c["core_id"]]]
        if len(pool) > CAND_CAP:
            pick = {c["core_id"] for c in rng.sample(pool, CAND_CAP)}
            for c in pool:
                if c["core_id"] not in pick:
                    conn.execute("INSERT INTO core_drops VALUES (?,?,?,?,?)", (c["core_id"], c["title"], c["year"], "candidate", "over_cap"))
            pool = [c for c in pool if c["core_id"] in pick]
        for c in pool:
            if c not in final:
                final.append(c)
    for part, per_year in (("background", BG_PER_YEAR), ("distractor", DIST_PER_YEAR)):
        for y in range(Y0, Y1 + 1):
            pool = [c for c in kept[part] if c["year"] == y]
            rng.shuffle(pool)
            for i, c in enumerate(pool):
                if i < per_year:
                    final.append(c)
                else:
                    conn.execute("INSERT INTO core_drops VALUES (?,?,?,?,?)", (c["core_id"], c["title"], y, part, "over_year_quota"))
    for c in final:
        ct = ";".join(sorted(cand_theories.get(c["core_id"], []))) if c["part"] == "candidate" else ""
        conn.execute("INSERT INTO core_papers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (c["core_id"], "core", "coarse", c["part"], ct, c["doi"], c["title"], c["year"], c["abstract"],
                      c["repository"], "unknown", c["link"], c["download_url"], c["ref_split"], c["n_words"],
                      c["n_words_total"], c["vocab_share"]))
        conn.execute("INSERT INTO core_texts VALUES (?,?,?,?)", (c["core_id"], c["abstract"], c["body"], c["refs"]))
    conn.commit()
    report(conn, raw)


def report(conn: sqlite3.Connection, raw: list) -> None:
    q = lambda s, *a: conn.execute(s, a).fetchall()
    n = q("SELECT COUNT(*) FROM core_papers")[0][0]
    print(f"\n== CORE pilot corpus: {n} papers kept ==")
    print("by part:", dict(q("SELECT part, COUNT(*) FROM core_papers GROUP BY part")))
    print("candidates by theory:", dict(Counter(t for (c,) in q("SELECT cand_theories FROM core_papers WHERE part='candidate'") for t in c.split(";"))))
    yrs = q("SELECT year, part, COUNT(*) FROM core_papers GROUP BY year, part")
    tab: dict = {}
    for y, p, c in yrs:
        tab.setdefault(y, {})[p] = c
    print("per year (cand/bg/dist):", {y: tuple(tab[y].get(p, 0) for p in ("candidate", "background", "distractor")) for y in sorted(tab)})
    seen = {str(r[0].get("id")): r[0] for r in raw}
    print(f"records pulled (unique): {len(seen)}; with fullText: {sum(bool((r.get('fullText') or '').strip()) for r in seen.values())} "
          f"({100*sum(bool((r.get('fullText') or '').strip()) for r in seen.values())/len(seen):.0f}%)")
    print("dropped by reason:", dict(q("SELECT reason, COUNT(*) FROM core_drops GROUP BY reason")))
    print("dropped by reason x part:", q("SELECT part, reason, COUNT(*) FROM core_drops GROUP BY part, reason"))
    dup = sum(1 for _, in q("SELECT 1 FROM core_drops WHERE reason LIKE 'dup_pmc%'"))
    print(f"duplicate rate vs PMC: {dup} dropped of {len(seen)} unique records ({100*dup/len(seen):.1f}%)")
    w = sorted(r[0] for r in q("SELECT n_words FROM core_papers"))
    print("words used: min %d p10 %d median %d p90 %d max %d" % (w[0], w[len(w)//10], statistics.median(w), w[9*len(w)//10], w[-1]))
    print("ref list split off:", dict(q("SELECT ref_split, COUNT(*) FROM core_papers GROUP BY ref_split")), "(1 = split)")
    print("top repositories:", q("SELECT repository, COUNT(*) c FROM core_papers GROUP BY repository ORDER BY c DESC LIMIT 10"))
    print("license labels:", dict(q("SELECT license, COUNT(*) FROM core_papers GROUP BY license")))
    print("5 random cleaned documents:")
    for cid, t, y, r, b in random.Random(SEED + 3).sample(q("SELECT p.core_id, title, year, repository, body FROM core_papers p JOIN core_texts USING(core_id)"), 5):
        print(f"  [{cid}] {t[:90]} ({y}, {r}): {b[:300]!r}")


if __name__ == "__main__":
    build()

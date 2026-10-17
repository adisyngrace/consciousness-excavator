"""Corpus builder, 2016-2025 (prompt 07 Step 1). Mirrors src/corpus/build.py in smaller form, tagged window='2016-2025'.

  candidates  per-theory phrase hits (same THEORY_QUERIES), random sample capped at 400 per theory
  background  same adjacent-topic queries and theory-phrase exclusion, water-filled to 3,000
  random      year-stratified (equal quota, 100/year) neuroscience/psychology/medicine OA sample. The 1995-2015 build
              enumerated each year's whole pool; at 2016-2025 volume (up to ~500k per year) that is not feasible, so each
              year is sampled from randomly chosen weekly FIRST_PDATE slices until >= POOL_PER_YEAR papers are
              enumerated, then a fixed-seed sample is drawn. Caveat: week-clustered, not a uniform draw over the year.
              150 per year are drawn (stub allowance); `trim` keeps the first 100 substantive ones per year.
  fetch/parse reuse src.corpus.build (resumable, cached, S3 first)

usage: python -m src.corpus.build_late candidates background random fetch parse trim stats
"""
import argparse
import random
import sys
from datetime import date, timedelta

from src import db
from src.corpus import build as B, epmc, queries as Q

WINDOW = "2016-2025"
Y0, Y1 = 2016, 2025
BASE = f"OPEN_ACCESS:y AND HAS_FT:y AND PUB_YEAR:[{Y0} TO {Y1}]"
CAPS = dict(candidate=400, background=3000, random=1000)
DRAW_PER_YEAR = 150
POOL_PER_YEAR = 900
SUBST = 2000


def set_membership(conn, part: str, tag: str, pmcids: list[str]) -> None:
    conn.execute("DELETE FROM corpus_membership WHERE part=? AND tag=? AND window=?", (part, tag, WINDOW))
    conn.executemany("INSERT OR IGNORE INTO corpus_membership(pmcid, part, tag, window) VALUES (?,?,?,?)",
                     [(p, part, tag, WINDOW) for p in pmcids])


def stage_candidates(conn, **_):
    for theory, phrases in Q.THEORY_QUERIES.items():
        union: dict[str, dict] = {}
        for ph in phrases:
            total, recs = epmc.search_all(f"{ph} AND {BASE}")
            B.log_search(conn, "candidate", theory + "@2016-2025", ph, total, len(recs), None, None)
            print(f"  {theory[:28]:28} {ph:45} hits={total:>5} with-PMCID={len(recs)}")
            union.update({r["pmcid"]: r for r in recs})
        keep = B.sample(list(union), CAPS["candidate"], f"late-candidate:{theory}")
        for p in keep:
            B.upsert_paper(conn, union[p])
        set_membership(conn, "candidate", theory, keep)
        B.log_search(conn, "candidate", theory + "@2016-2025", "UNION", len(union), len(union), len(keep), CAPS["candidate"])
        conn.commit()
        print(f"candidates[{theory}]: union {len(union)} -> kept {len(keep)}")


def stage_background(conn, **_):
    excl = Q.theory_phrase_exclusion()
    found = {}
    for topic, expr in Q.BACKGROUND_TOPICS.items():
        total, recs = epmc.search_all(f"{Q.tiab(expr)} AND {BASE} {excl}")
        found[topic] = (total, recs)
        print(f"  background {topic:34} hits={total:>6} with-PMCID={len(recs)}")
    quota = B.water_fill(CAPS["background"], {t: len(r) for t, (_, r) in found.items()})
    for topic, (total, recs) in found.items():
        by_id = {r["pmcid"]: r for r in recs}
        keep = B.sample(list(by_id), quota[topic], f"late-background:{topic}")
        for p in keep:
            B.upsert_paper(conn, by_id[p])
        set_membership(conn, "background", topic, keep)
        B.log_search(conn, "background", topic + "@2016-2025", Q.BACKGROUND_TOPICS[topic], total, len(recs), len(keep), quota[topic])
    conn.commit()
    print(f"background: {sum(quota.values())} papers (cap {CAPS['background']}); quota {quota}")


def _weeks(year: int) -> list[tuple[str, str]]:
    d, out = date(year, 1, 1), []
    while d.year == year:
        e = min(d + timedelta(days=6), date(year, 12, 31))
        out.append((d.isoformat(), e.isoformat()))
        d = e + timedelta(days=1)
    return out


def _year_pool(year: int) -> list[dict]:
    weeks = _weeks(year)
    random.Random(f"late-weeks:{year}").shuffle(weeks)
    pool: dict[str, dict] = {}
    for a, b in weeks:
        qy = f"{Q.RANDOM_FILTER} AND OPEN_ACCESS:y AND HAS_FT:y AND PUB_YEAR:{year} AND FIRST_PDATE:[{a} TO {b}]"
        _, recs = epmc.search_all(qy, max_enumerate=3000)       # cached on disk: reruns are free
        pool.update({r["pmcid"]: r for r in recs})
        if len(pool) >= POOL_PER_YEAR:
            break
    return list(pool.values())


def stage_random(conn, **_):
    for y in range(Y0, Y1 + 1):
        pool = _year_pool(y)
        by_id = {r["pmcid"]: r for r in pool}
        keep = B.sample(list(by_id), DRAW_PER_YEAR, f"late-random:{y}")
        for p in keep:
            B.upsert_paper(conn, by_id[p])
        set_membership(conn, "random", str(y), keep)
        B.log_search(conn, "random", f"{y}@2016-2025", "weekly FIRST_PDATE slices of RANDOM_FILTER", len(pool), len(pool), len(keep), DRAW_PER_YEAR)
        conn.commit()
        print(f"  random {y}: pool {len(pool)} -> drew {len(keep)}")


def stage_trim(conn, **_):
    """Keep the first 100 substantive (>= SUBST chars) papers per year in a fixed shuffled order; stubs leave membership
    (their rows stay in `papers`)."""
    quota = CAPS["random"] // (Y1 - Y0 + 1)
    for y in range(Y0, Y1 + 1):
        ids = [r[0] for r in conn.execute(
            "SELECT m.pmcid FROM corpus_membership m JOIN papers p USING(pmcid) WHERE m.part='random' AND m.tag=? AND m.window=? "
            "AND p.parse_status='ok' AND p.n_body_chars>=? ORDER BY m.pmcid", (str(y), WINDOW, SUBST))]
        random.Random(f"late-trim:{y}").shuffle(ids)
        keep = ids[:quota]
        set_membership(conn, "random", str(y), keep)
        print(f"  trim {y}: substantive {len(ids)} -> kept {len(keep)} (quota {quota})")
    conn.commit()


def stage_stats(conn, **_):
    q = lambda s, *a: conn.execute(s, a).fetchall()
    print(f"2016-2025 distinct papers: {q('SELECT COUNT(DISTINCT pmcid) FROM corpus_membership WHERE window=?', WINDOW)[0][0]}")
    for part in ("candidate", "background", "random"):
        r = q("""SELECT COUNT(DISTINCT m.pmcid), SUM(p.fetch_status='ok'), SUM(p.fetch_status='failed'), SUM(p.parse_status='ok'),
                 SUM(p.parse_status='ok' AND p.n_body_chars<?) FROM corpus_membership m JOIN papers p USING(pmcid)
                 WHERE m.window=? AND m.part=?""", SUBST, WINDOW, part)[0]
        print(f"  {part:10} papers={r[0]} fetched_ok={r[1]} failed={r[2]} parsed_ok={r[3]} stubs={r[4]}")
    for r in q("SELECT part, tag, COUNT(*) FROM corpus_membership WHERE window=? AND part!='random' GROUP BY 1,2", WINDOW):
        print(f"    {r[0]:10} {r[1]:48} {r[2]}")
    print("  per year (distinct papers, by part):")
    for r in q("""SELECT p.year, m.part, COUNT(DISTINCT m.pmcid) FROM corpus_membership m JOIN papers p USING(pmcid)
                  WHERE m.window=? GROUP BY 1,2 ORDER BY 1,2""", WINDOW):
        print(f"    {r[0]} {r[1]:10} {r[2]}")
    print("  fetch failures:", [tuple(r) for r in q("""SELECT p.fetch_error, COUNT(*) FROM papers p WHERE p.fetch_status='failed'
        AND p.pmcid IN (SELECT pmcid FROM corpus_membership WHERE window=?) GROUP BY 1""", WINDOW)])
    print("  parse failures:", [tuple(r) for r in q("""SELECT p.parse_error, COUNT(*) FROM papers p WHERE p.parse_status='failed'
        AND p.pmcid IN (SELECT pmcid FROM corpus_membership WHERE window=?) GROUP BY 1""", WINDOW)])


STAGES = {"candidates": stage_candidates, "background": stage_background, "random": stage_random,
          "fetch": lambda conn, **k: B.stage_fetch(conn, workers=4), "parse": lambda conn, **k: B.stage_parse(conn),
          "trim": stage_trim, "stats": stage_stats}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stages", nargs="+", choices=list(STAGES))
    a = ap.parse_args()
    conn = db.connect()
    for st in a.stages:
        print(f"== {st}", flush=True)
        STAGES[st](conn)
        conn.commit()

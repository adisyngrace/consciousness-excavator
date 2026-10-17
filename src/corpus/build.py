"""Corpus builder, 1995-2015. Stages (each idempotent, resumable):

  seeds       Level 1 refs with resolution_status='resolved_fulltext', year 1995-2015, with a PMCID
  candidates  per-theory full-text phrase hits (capped, randomly sampled; total hit count logged)
  background  adjacent-topic title/abstract hits excluding theory phrases (capped, water-filled across topics)
  random      year-stratified random sample of neuroscience/psychology/medicine OA papers
  fetch       download JATS XML for every paper in corpus_membership (4 parallel workers, ~4 req/s)
  parse       XML -> sections / references tables
  stats       print the Step 1 checkpoint summary

usage: python -m src.corpus.build seeds candidates background random fetch parse stats
"""
import argparse
import random
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from src import db
from src.corpus import epmc, jats, queries as Q

DATA = Path(__file__).resolve().parents[2] / "data"
WINDOW = f"{Q.YEARS[0]} AND {Q.YEARS[1]}"


# ---------- helpers -------------------------------------------------------------------------------------
def water_fill(budget: int, sizes: dict) -> dict:
    """Split budget across keys; small keys take everything they have, the surplus goes to larger keys."""
    out, remaining, left = {}, budget, len(sizes)
    for k, n in sorted(sizes.items(), key=lambda kv: kv[1]):
        take = min(n, remaining // left) if left else 0
        out[k], remaining, left = take, remaining - take, left - 1
    return out


def sample(ids: list[str], n: int, tag: str) -> list[str]:
    ids = sorted(set(ids))
    return ids if len(ids) <= n else sorted(random.Random(f"corpus:{tag}").sample(ids, n))


def upsert_paper(conn, rec: dict) -> None:
    conn.execute("""INSERT INTO papers(pmcid, pmid, doi, title, year, journal, source) VALUES (?,?,?,?,?,?,?)
                    ON CONFLICT(pmcid) DO UPDATE SET pmid=COALESCE(papers.pmid, excluded.pmid),
                      doi=COALESCE(papers.doi, excluded.doi), title=COALESCE(papers.title, excluded.title),
                      year=COALESCE(papers.year, excluded.year), journal=COALESCE(papers.journal, excluded.journal),
                      source=COALESCE(papers.source, excluded.source)""",
                 (rec["pmcid"], rec.get("pmid"), (rec.get("doi") or "").lower() or None, rec.get("title"),
                  int(rec["pubYear"]) if rec.get("pubYear") else None, rec.get("journalTitle"), rec.get("source")))


def set_membership(conn, part: str, tag: str, pmcids: list[str]) -> None:
    conn.execute("DELETE FROM corpus_membership WHERE part=? AND tag=?", (part, tag))
    conn.executemany("INSERT OR IGNORE INTO corpus_membership(pmcid, part, tag) VALUES (?,?,?)", [(p, part, tag) for p in pmcids])


def log_search(conn, part, tag, query, total, enumerated, sampled, cap) -> None:
    conn.execute("INSERT OR REPLACE INTO search_log VALUES (?,?,?,?,?,?,?,?)",
                 (part, tag, query, total, enumerated, sampled, cap, datetime.now(timezone.utc).isoformat(timespec="seconds")))


# ---------- stages --------------------------------------------------------------------------------------
def stage_seeds(conn, **_):
    rows = conn.execute("""SELECT r.pmcid, r.doi, r.parsed_title, r.parsed_year, t.name FROM loc_references r
        JOIN theories t ON t.id=r.theory_id WHERE r.resolution_status='resolved_fulltext' AND r.pmcid IS NOT NULL
        AND r.parsed_year BETWEEN ? AND ?""", Q.YEARS).fetchall()
    by_theory: dict[str, list[str]] = {}
    for r in rows:
        upsert_paper(conn, dict(pmcid=r["pmcid"], doi=r["doi"], title=r["parsed_title"], pubYear=r["parsed_year"]))
        by_theory.setdefault(r["name"], []).append(r["pmcid"])
    conn.execute("DELETE FROM corpus_membership WHERE part='seed'")
    for t, ids in by_theory.items():
        set_membership(conn, "seed", t, ids)
        log_search(conn, "seed", t, "level1:resolved_fulltext", len(ids), len(ids), len(ids), None)
    print(f"seeds: {len(rows)} papers across {len(by_theory)} theories")


def stage_candidates(conn, cap_candidate=2000, **_):
    for theory, phrases in Q.THEORY_QUERIES.items():
        union: dict[str, dict] = {}
        for ph in phrases:
            total, recs = epmc.search_all(f"{ph} AND {Q.BASE}")
            log_search(conn, "candidate", theory, ph, total, len(recs), None, None)
            print(f"  {theory[:28]:28} {ph:45} hits={total:>5} with-PMCID={len(recs)}")
            union.update({r["pmcid"]: r for r in recs})
        keep = sample(list(union), cap_candidate, f"candidate:{theory}")
        for p in keep:
            upsert_paper(conn, union[p])
        set_membership(conn, "candidate", theory, keep)
        log_search(conn, "candidate", theory, "UNION", len(union), len(union), len(keep), cap_candidate)
        conn.commit()
        print(f"candidates[{theory}]: union {len(union)} -> kept {len(keep)} (cap {cap_candidate})")


def stage_background(conn, cap_background=5000, **_):
    excl = Q.theory_phrase_exclusion()
    found: dict[str, tuple[int, list[dict]]] = {}
    for topic, expr in Q.BACKGROUND_TOPICS.items():
        qy = f"{Q.tiab(expr)} AND {Q.BASE} {excl}"
        total, recs = epmc.search_all(qy)
        found[topic] = (total, recs)
        print(f"  background {topic:34} hits={total:>6} with-PMCID={len(recs)}")
    quota = water_fill(cap_background, {t: len(r) for t, (_, r) in found.items()})
    for topic, (total, recs) in found.items():
        by_id = {r["pmcid"]: r for r in recs}
        keep = sample(list(by_id), quota[topic], f"background:{topic}")
        for p in keep:
            upsert_paper(conn, by_id[p])
        set_membership(conn, "background", topic, keep)
        log_search(conn, "background", topic, Q.BACKGROUND_TOPICS[topic], total, len(recs), len(keep), quota[topic])
    conn.commit()
    print(f"background: {sum(quota.values())} papers (cap {cap_background}); quota {quota}")


def _year_ids(year: int) -> tuple[int, list[tuple]]:
    """All PMCIDs for one year's filtered set, cached as a compact TSV so reruns are instant."""
    f = DATA / "ids" / f"random_{year}.tsv"
    if f.exists():
        lines = f.read_text().splitlines()
        return int(lines[0]), [tuple(l.split("\t")) for l in lines[1:]]
    qy = f"{Q.RANDOM_FILTER} AND OPEN_ACCESS:y AND HAS_FT:y AND PUB_YEAR:{year}"
    total, recs = epmc.search_all(qy, max_enumerate=500000, cache=False)
    rows = [(r["pmcid"], r.get("pmid") or "", (r.get("doi") or "").lower(), str(r.get("pubYear") or year), r.get("source") or "") for r in recs]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(str(total) + "\n" + "\n".join("\t".join(r) for r in rows))
    return total, rows


def stage_random(conn, random_total=2000, resample=False, **_):
    years = range(Q.YEARS[0], Q.YEARS[1] + 1)
    pools = {}
    for y in years:
        total, rows = _year_ids(y)
        pools[y] = (total, rows)
        print(f"  random {y}: filtered OA papers {total:>7} (enumerated {len(rows)})")
    quota = water_fill(random_total, {y: len(r) for y, (_, r) in pools.items()})
    for y, (total, rows) in pools.items():
        if not resample and conn.execute("SELECT 1 FROM corpus_membership WHERE part='random' AND tag=?", (str(y),)).fetchone():
            continue          # keep existing (possibly topped-up) sample; --resample to redraw
        by_id = {r[0]: r for r in rows}
        keep = sample(list(by_id), quota[y], f"random:{y}")
        for p in keep:
            r = by_id[p]
            upsert_paper(conn, dict(pmcid=r[0], pmid=r[1] or None, doi=r[2] or None, pubYear=r[3], source=r[4] or None))
        set_membership(conn, "random", str(y), keep)
        log_search(conn, "random", str(y), Q.RANDOM_FILTER[:60] + "...", total, len(rows), len(keep), quota[y])
    conn.commit()
    print(f"random: {sum(quota.values())} papers, per-year quota {quota}")


def stage_fetch(conn, workers=4, retry_failed=False, **_):
    states = ("pending", "failed") if retry_failed else ("pending",)
    # Priority order so a partial run is still useful and unbiased: seeds, theory candidates, the year-stratified
    # random sample, then the background pool. Shuffled (fixed seed) within a part, never in PMCID order,
    # which would front-load old papers and leave 2013-2015 for last.
    rows = conn.execute(
        f"""SELECT p.pmcid, MIN(CASE m.part WHEN 'seed' THEN 0 WHEN 'candidate' THEN 1 WHEN 'random' THEN 2 ELSE 3 END) prio
            FROM papers p JOIN corpus_membership m USING(pmcid)
            WHERE p.fetch_status IN ({','.join('?' * len(states))}) GROUP BY p.pmcid ORDER BY prio, p.pmcid""", states).fetchall()
    random.Random("fetch-order").shuffle(rows)
    todo = [r[0] for r in sorted(rows, key=lambda r: r[1])]
    print(f"fetch: {len(todo)} papers to download ({workers} workers)")
    ok = failed = 0
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(epmc.fetch_xml, p): p for p in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            p = futs[fut]
            try:
                good, err, src = fut.result()
            except Exception as e:                                   # never lose a paper silently
                good, err, src = False, f"exception: {type(e).__name__}: {e}", None
            conn.execute("UPDATE papers SET fetch_status=?, fetch_error=?, xml_path=?, xml_source=? WHERE pmcid=?",
                         ("ok" if good else "failed", err, str(epmc.xml_path(p)) if good else None, src, p))
            ok, failed = ok + good, failed + (not good)
            if i % 200 == 0:
                conn.commit()
                rate = i / (time.time() - t0)
                print(f"  {i}/{len(todo)}  ok={ok} failed={failed}  {rate:.1f}/s  eta {(len(todo) - i) / rate / 60:.0f} min", flush=True)
    conn.commit()
    print(f"fetch done: ok={ok} failed={failed}")


def stage_parse(conn, reparse=False, **_):
    where = "p.fetch_status='ok'" + ("" if reparse else " AND p.parse_status IS NULL")
    todo = [r[0] for r in conn.execute(f"SELECT p.pmcid FROM papers p WHERE {where} ORDER BY p.pmcid")]
    print(f"parse: {len(todo)} papers")
    bad = 0
    for i, pm in enumerate(todo, 1):
        try:
            P = jats.parse_jats(epmc.read_xml(pm))
        except Exception as e:
            conn.execute("UPDATE papers SET parse_status='failed', parse_error=? WHERE pmcid=?", (f"{type(e).__name__}: {e}"[:300], pm))
            bad += 1
            continue
        m, s = P.meta, P.sections
        conn.execute("DELETE FROM paper_sections WHERE pmcid=?", (pm,))
        conn.execute("DELETE FROM paper_refs WHERE pmcid=?", (pm,))
        conn.executemany("INSERT INTO paper_sections VALUES (?,?,?)", [(pm, k, v) for k, v in s.items() if v])
        conn.executemany("INSERT INTO paper_refs VALUES (?,?,?)", [(pm, j, r) for j, r in enumerate(P.refs)])
        conn.execute("""UPDATE papers SET title=COALESCE(?, title), abstract=?, journal=COALESCE(?, journal), license=?,
                        doi=COALESCE(?, doi), pmid=COALESCE(?, pmid), year=COALESCE(year, ?), n_refs=?, n_body_chars=?,
                        has_intro=?, has_discussion=?, parse_status='ok', parse_error=NULL WHERE pmcid=?""",
                     (m["title"], s["abstract"] or None, m["journal"], m["license"], m["doi"], m["pmid"], m["year"], m["n_refs"],
                      len(s["body"]) + len(s["introduction"]) + len(s["discussion"]), int(P.has_intro), int(P.has_discussion), pm))
        if i % 500 == 0:
            conn.commit()
            print(f"  {i}/{len(todo)}", flush=True)
    conn.commit()
    print(f"parse done, {bad} failures")


def stage_topup(conn, workers=4, random_total=2000, **_):
    """Replace stub / failed papers in the random sample with substantive ones (>= 2000 chars of text), per year.
    Draws extra IDs from the same cached year pool in a fixed shuffled order, downloads and parses them, and drops
    stubs from membership (the stub rows stay in `papers`, so nothing is silently lost)."""
    SUBST = 2000
    years = list(range(Q.YEARS[0], Q.YEARS[1] + 1))
    pools = {y: _year_ids(y) for y in years}
    quota = water_fill(random_total, {y: len(r) for y, (_, r) in pools.items()})
    order = {}
    for y in years:
        ids = sorted(r[0] for r in pools[y][1])
        random.Random(f"topup:{y}").shuffle(ids)
        order[y] = ids
    removed = {y: 0 for y in years}
    for rnd in range(5):
        # 1. drop stubs and failures from membership
        for y in years:
            bad = [r[0] for r in conn.execute(
                """SELECT m.pmcid FROM corpus_membership m JOIN papers p USING(pmcid) WHERE m.part='random' AND m.tag=?
                   AND (p.fetch_status='failed' OR (p.parse_status='ok' AND p.n_body_chars < ?))""", (str(y), SUBST))]
            conn.executemany("DELETE FROM corpus_membership WHERE pmcid=? AND part='random' AND tag=?", [(p, str(y)) for p in bad])
            removed[y] += len(bad)
        conn.commit()
        # 2. add fresh draws where a year is short (counting unfetched members as presumed good)
        added = 0
        for y in years:
            have = conn.execute("SELECT COUNT(*) FROM corpus_membership WHERE part='random' AND tag=?", (str(y),)).fetchone()[0]
            short = quota[y] - have
            if short <= 0:
                continue
            seen = {r[0] for r in conn.execute("SELECT pmcid FROM papers WHERE pmcid IN (%s)" % ",".join("?" * len(order[y])), order[y])} if len(order[y]) < 900 else \
                   {r[0] for r in conn.execute("SELECT pmcid FROM papers WHERE year=?", (y,))}
            fresh = [p for p in order[y] if p not in seen][: int(short * 1.8) + 3]
            by_id = {r[0]: r for r in pools[y][1]}
            for p in fresh:
                r = by_id[p]
                upsert_paper(conn, dict(pmcid=r[0], pmid=r[1] or None, doi=r[2] or None, pubYear=r[3], source=r[4] or None))
            conn.executemany("INSERT OR IGNORE INTO corpus_membership(pmcid, part, tag) VALUES (?,?,?)", [(p, "random", str(y)) for p in fresh])
            added += len(fresh)
        conn.commit()
        print(f"topup round {rnd + 1}: added {added} fresh draws")
        if not added:
            break
        stage_fetch(conn, workers=workers)
        stage_parse(conn)
    # final trim: more than quota substantive -> keep first quota in shuffled order; log per year
    for y in years:
        mem = [r[0] for r in conn.execute(
            "SELECT m.pmcid FROM corpus_membership m JOIN papers p USING(pmcid) WHERE m.part='random' AND m.tag=? AND p.parse_status='ok' AND p.n_body_chars>=?",
            (str(y), SUBST))]
        rank = {p: i for i, p in enumerate(order[y])}
        mem.sort(key=lambda p: rank.get(p, 10**9))
        keep = set(mem[: quota[y]])
        conn.execute("DELETE FROM corpus_membership WHERE part='random' AND tag=?", (str(y),))
        conn.executemany("INSERT INTO corpus_membership(pmcid, part, tag) VALUES (?,?,?)", [(p, "random", str(y)) for p in keep])
        log_search(conn, "random", str(y), "topup", pools[y][0], len(order[y]), len(keep), quota[y])
    conn.commit()
    short = {y: quota[y] - c for y, c in ((y, conn.execute("SELECT COUNT(*) FROM corpus_membership WHERE part='random' AND tag=?", (str(y),)).fetchone()[0]) for y in years) if quota[y] > c}
    print(f"topup done: stubs/failures removed per year {removed}; years short of quota: {short or 'none'}")


def stage_stats(conn, **_):
    from src.corpus.stats import print_stats
    print_stats(conn)


STAGES = {"seeds": stage_seeds, "candidates": stage_candidates, "background": stage_background, "random": stage_random,
          "fetch": stage_fetch, "parse": stage_parse, "topup": stage_topup, "stats": stage_stats}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stages", nargs="+", choices=STAGES)
    ap.add_argument("--cap-candidate", type=int, default=2000)
    ap.add_argument("--cap-background", type=int, default=5000)
    ap.add_argument("--random-total", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--resample", action="store_true", help="random stage: redraw the sample even if one exists")
    ap.add_argument("--reparse", action="store_true")
    a = ap.parse_args()
    conn = db.connect()
    conn.row_factory = sqlite3.Row
    for st in a.stages:
        print(f"== {st}")
        STAGES[st](conn, cap_candidate=a.cap_candidate, cap_background=a.cap_background, random_total=a.random_total,
                   workers=a.workers, retry_failed=a.retry_failed, reparse=a.reparse, resample=a.resample)
        conn.commit()

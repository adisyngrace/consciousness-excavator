"""CORE pilot, Step 2: boilerplate stripping and the frozen Level 2 scanner in COARSE mode (prompt 09).

Coarse mode: sections = {title, abstract, body}; the trailing reference list (split by build_core) is scanned only for
landmark references and never counted as mentions. Papers WITHOUT a reference split may have reference-list text in
`body`; per addendum (c) they cannot be silver positives. Hit snippets are NOT stored (CORE text rules): they are
recomputed in memory and printed to the terminal only.  Run: python -m src.corpus.core_scan
"""
import json
import random
import re
import sqlite3
from collections import Counter, defaultdict

from src.corpus.build_core import DB, SEED
from src.level2_terms.scan import scan_paper
from src.level2_terms.terms import COUNTED_SECTIONS, load_terms

PILOT = ("champagne_semiotic", "panpsychism")
HEAD_LINES, MIN_DOCS = 40, 5
FLAG_COLS = ("theory,direct_mention,weak_mention,any_mention_level,names_theory_loosely,mention_strength,"
             "title_or_abstract_hit,strong_blocked_by_domain,close_term_hit,adjacent_hit,abbrev_confirmed,"
             "abbrev_unconfirmed,cites_landmark,cites_author_year,domain_n,domain_ok").split(",")


def strip_boilerplate(conn: sqlite3.Connection, show: int = 3) -> None:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(core_texts)")]
    if "body_raw" not in cols:
        conn.execute("ALTER TABLE core_texts ADD COLUMN body_raw TEXT")
    conn.execute("UPDATE core_texts SET body_raw = body WHERE body_raw IS NULL")   # always strip from the raw body
    rows = conn.execute("SELECT core_id, repository, body_raw FROM core_texts JOIN core_papers USING(core_id)").fetchall()
    seen: dict[tuple, set] = defaultdict(set)
    heads = {}
    for cid, repo, body in rows:
        lines = body.split("\n")
        idx = [i for i, l in enumerate(lines) if l.strip()][:HEAD_LINES]
        heads[cid] = (lines, idx)
        for i in idx:
            seen[(repo, lines[i].strip())].add(cid)
    boiler = {k for k, v in seen.items() if len(v) >= MIN_DOCS}
    n_lines, affected, examples = 0, 0, []
    for cid, repo, body in rows:
        lines, idx = heads[cid]
        drop = {i for i in idx if (repo, lines[i].strip()) in boiler}
        if drop:
            new = "\n".join(l for i, l in enumerate(lines) if i not in drop)
            n_lines += len(drop)
            affected += 1
            if len(examples) < 40:
                examples.append((cid, repo, body, new))
        else:
            new = body
        conn.execute("UPDATE core_texts SET body=? WHERE core_id=?", (new, cid))
        conn.execute("UPDATE core_papers SET n_words = ? WHERE core_id=?",
                     (len(new.split()) + len((conn.execute('SELECT abstract FROM core_texts WHERE core_id=?', (cid,)).fetchone()[0] or '').split()), cid))
    conn.commit()
    print(f"boilerplate: {len(boiler)} distinct repeated lines (>= {MIN_DOCS} docs in one repository, first {HEAD_LINES} lines); "
          f"{n_lines} line instances removed from {affected} of {len(rows)} papers")
    for cid, repo, before, after in random.Random(SEED).sample(examples, min(show, len(examples))):
        print(f"\n--- example {cid} ({repo}) BEFORE: {before[:260]!r}\n    AFTER:  {after[:260]!r}")


def scan(conn: sqlite3.Connection) -> None:
    terms = load_terms()
    conn.executescript("DROP TABLE IF EXISTS core_term_hits; DROP TABLE IF EXISTS core_paper_flags;")
    conn.execute("CREATE TABLE core_term_hits (core_id TEXT, theory TEXT, term TEXT, tier TEXT, section TEXT, count INTEGER, domain_ok INTEGER)")
    conn.execute(f"CREATE TABLE core_paper_flags (core_id TEXT, {', '.join(c + (' TEXT' if c in ('theory', 'any_mention_level') else ' INTEGER') for c in FLAG_COLS)}, PRIMARY KEY (core_id, theory))")
    for cid, title, abstract, body, refs in conn.execute(
            "SELECT core_id, title, p.abstract, body, refs FROM core_papers p JOIN core_texts USING(core_id)").fetchall():
        rows, flags = scan_paper({"title": title, "abstract": abstract, "body": body}, [l for l in (refs or "").split("\n") if l.strip()], terms)
        conn.executemany("INSERT INTO core_term_hits VALUES (?,?,?,?,?,?,?)",
                         [(cid, r["theory"], r["term"], r["tier"], r["section"], r["count"], r["domain_ok"]) for r in rows])
        conn.executemany(f"INSERT INTO core_paper_flags VALUES (?,{','.join('?' * len(FLAG_COLS))})",
                         [(cid, *[f[c] for c in FLAG_COLS]) for f in flags])
    conn.commit()


def silver_ids(conn: sqlite3.Connection, theory: str, require_split: bool = True) -> list[str]:
    """Exclusive direct mentions of `theory` (no other of the 5 theories directly mentioned)."""
    q = """SELECT f.core_id FROM core_paper_flags f JOIN core_papers p USING(core_id)
           WHERE f.theory=? AND f.direct_mention=1
             AND NOT EXISTS (SELECT 1 FROM core_paper_flags g WHERE g.core_id=f.core_id AND g.theory<>f.theory AND g.direct_mention=1)"""
    if require_split:
        q += " AND p.ref_split=1"
    return [r[0] for r in conn.execute(q, (theory,))]


def report(conn: sqlite3.Connection) -> None:
    q = lambda s, *a: conn.execute(s, a).fetchall()
    print("\n== Level 2 coarse scan: pilot theories ==")
    for th in PILOT:
        lv = dict(q("SELECT any_mention_level, COUNT(*) FROM core_paper_flags WHERE theory=? GROUP BY 1", th))
        d_split = dict(q("SELECT p.ref_split, COUNT(*) FROM core_paper_flags f JOIN core_papers p USING(core_id) WHERE theory=? AND direct_mention=1 GROUP BY 1", th))
        by_part = dict(q("SELECT p.part, COUNT(*) FROM core_paper_flags f JOIN core_papers p USING(core_id) WHERE theory=? AND direct_mention=1 GROUP BY 1", th))
        ex_all, ex_split = silver_ids(conn, th, False), silver_ids(conn, th, True)
        prim = q(f"SELECT COUNT(*) FROM core_paper_flags WHERE theory=? AND core_id IN ({','.join('?' * len(ex_split))}) AND (title_or_abstract_hit=1 OR mention_strength>=3)", th, *ex_split)[0][0] if ex_split else 0
        loose_nosplit = q("SELECT COUNT(*) FROM core_paper_flags f JOIN core_papers p USING(core_id) WHERE theory=? AND names_theory_loosely=1 AND p.ref_split=0", th)[0][0]
        print(f"\n{th}: levels {lv}")
        print(f"  direct by ref_split (1=split): {d_split}; direct by part: {by_part}")
        print(f"  exclusive silver: {len(ex_all)} without split requirement; {len(ex_split)} WITH reference split (the positives); primary among those: {prim}")
        print(f"  no-split papers that name the theory loosely (excluded from positives AND negatives): {loose_nosplit}")
        if len(ex_split) < 20:
            print(f"  *** {th}: only {len(ex_split)} exclusive positives with a reference split: BELOW 20, exploratory/qualitative only ***")
        ms = sorted(r[0] for r in q("SELECT mention_strength FROM core_paper_flags WHERE theory=? AND direct_mention=1", th))
        if ms:
            print(f"  mention_strength of direct papers: median {ms[len(ms)//2]}, max {ms[-1]}")
    nos = q("SELECT COUNT(*) FROM core_papers WHERE ref_split=0")[0][0]
    print(f"\npapers without a reference split: {nos} of {q('SELECT COUNT(*) FROM core_papers')[0][0]}")
    print("  among them, by part:", dict(q("SELECT part, COUNT(*) FROM core_papers WHERE ref_split=0 GROUP BY 1")))


def show_hits(conn: sqlite3.Connection, n: int = 10) -> None:
    """10 random direct-mention hits per theory with surrounding text. Terminal only; nothing written."""
    terms, rng = load_terms(), random.Random(SEED + 4)
    for th in PILOT:
        pool = [r[0] for r in conn.execute("SELECT core_id FROM core_paper_flags WHERE theory=? AND direct_mention=1", (th,))]
        print(f"\n===== {th}: {len(pool)} direct-mention papers; 10 random hits (terminal only) =====")
        for cid in rng.sample(pool, min(n, len(pool))):
            title, year, abstract, body, refs, split, repo = conn.execute(
                "SELECT title, year, p.abstract, body, refs, ref_split, repository FROM core_papers p JOIN core_texts USING(core_id) WHERE core_id=?", (cid,)).fetchone()
            rows, _ = scan_paper({"title": title, "abstract": abstract, "body": body}, [], terms)
            hits = [r for r in rows if r["theory"] == th and r["tier"] == "strong" and r["section"] in COUNTED_SECTIONS]
            h = rng.choice(hits)
            print(f"\n[{cid}] {title[:80]} ({year}, {repo}; ref_split={split}) term={h['term']!r} section={h['section']} count={h['count']}\n   ...{json.loads(h['snippets'])[0]}...")


if __name__ == "__main__":
    c = sqlite3.connect(DB)
    strip_boilerplate(c)
    scan(c)
    report(c)
    show_hits(c)

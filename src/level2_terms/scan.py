"""Level 2 scanner: term hits and per-paper, per-theory flags for EVERY paper in the corpus.

DEFINITION OF `direct_mention` (cited in the demo; keep this docstring authoritative):
    A paper directly mentions theory T iff
      (a) a STRONG term of T occurs in its title, abstract, introduction, body or discussion
          (reference list and back matter such as acknowledgements never count), AND
      (b) the paper passes the domain_context rule: at least `domain_context_min` distinct domain_context words
          occur in those same sections.
    Abbreviations (GWT, IIT, PP ...) can never create a direct mention on their own. They are recorded as
    `abbreviation` when a strong term of the same theory occurs anywhere outside the reference list (confirmed)
    and `abbreviation_unconfirmed` otherwise. Because confirmation needs a strong term, a confirmed abbreviation
    adds no papers beyond (a)+(b); it only documents usage.
    A term listed under `needs_corroboration` in terms.yaml (the bare phrase "predictive processing") counts only if
    it is in the title/abstract or the paper also has another strong or close_term of the same theory in a counted
    section. Otherwise its hits are stored as tier `strong_uncorroborated` and the paper (if it passes the domain rule)
    gets `weak_mention=1`: not a direct mention, not in the silver set, but it HAS named the theory.
    `any_mention_level` = direct > weak > close > none; `names_theory_loosely` = direct OR weak OR close. A Level 3
    "never names the theory" claim must filter on names_theory_loosely = 0.
    close_term, adjacent, landmark_ref (reference list) and author_year (in-text citation) hits are stored but
    are NEVER direct mentions. `close_term_hit` / `adjacent_hit` additionally require the domain rule.
    `mention_strength` = total strong-term count in the counted sections (0 unless direct_mention).

usage: python -m src.level2_terms.scan [--rescan]
"""
import argparse
import json
import random
import re
import sys
from datetime import datetime, timezone
from itertools import groupby

from src import db
from src.level2_terms.terms import COUNTED_SECTIONS, SCAN_SECTIONS, Terms, TheoryPatterns, load_terms

SNIPPET_CHARS = 150
MAX_SNIPPETS = 3


def snippet(text: str, start: int, end: int) -> str:
    seg = text[max(0, start - SNIPPET_CHARS): end + SNIPPET_CHARS]
    return re.sub(r"\s+", " ", seg).strip()


def _add(hits: dict, key: tuple, text: str, m: re.Match) -> None:
    rec = hits.setdefault(key, {"count": 0, "snippets": []})
    rec["count"] += 1
    if len(rec["snippets"]) < MAX_SNIPPETS:
        rec["snippets"].append(snippet(text, m.start(), m.end()))


def domain_count(sections: dict[str, str], terms: Terms) -> int:
    seen = set()
    for sec in COUNTED_SECTIONS:
        seen.update(m.group(0).lower() for m in terms.domain_rx.finditer(sections.get(sec) or ""))
    return len(seen)


def scan_paper(sections: dict[str, str], refs: list[str], terms: Terms) -> tuple[list[dict], list[dict]]:
    """Pure function: (term_hit rows, paper_flags rows, one per theory). No DB access."""
    n_dom = domain_count(sections, terms)
    dom_ok = n_dom >= terms.domain_min
    rows, flags = [], []
    for th in terms.theories.values():
        hits: dict[tuple, dict] = {}
        for sec in SCAN_SECTIONS:
            text = sections.get(sec) or ""
            if not text:
                continue
            if th.main_rx:
                for m in th.main_rx.finditer(text):
                    term, tier = th.main_groups[m.lastgroup]
                    _add(hits, (term, tier, sec), text, m)
            if th.abbr_rx:
                for m in th.abbr_rx.finditer(text):
                    _add(hits, (th.abbr_groups[m.lastgroup], "abbreviation_raw", sec), text, m)
            for rx, years in th.intext_rx:
                if not any(y in text for y in years):
                    continue
                for m in rx.finditer(text):
                    lm = years[m.group("y")]
                    _add(hits, (lm.key, "author_year", sec), text, m)
        for rx_s, rx_y, lm in th.ref_rx:
            for ref in refs:
                if rx_y.search(ref) and rx_s.search(ref) and (not lm.title_hint or lm.title_hint.lower() in ref.lower()):
                    _add(hits, (lm.key, "landmark_ref", "references"), ref, rx_s.search(ref))
                    break
        if th.needs_corroboration:
            # a term in `needs_corroboration` counts only if it is in the title/abstract or the paper also has another
            # strong or close_term of the same theory in a counted section; otherwise its hits become
            # tier "strong_uncorroborated" (stored, never a direct mention)
            others = any(k[1] in ("strong", "close_term") and k[0] not in th.needs_corroboration
                         and k[2] in COUNTED_SECTIONS for k in hits)
            for term in th.needs_corroboration:
                ks = [k for k in hits if k[0] == term and k[1] == "strong"]
                if ks and not others and not any(k[2] in ("title", "abstract") for k in ks):
                    for k in ks:
                        hits[(k[0], "strong_uncorroborated", k[2])] = hits.pop(k)
        strong_anywhere = any(t == "strong" for (_, t, _s) in hits)
        for (term, tier, sec), rec in hits.items():
            if tier == "abbreviation_raw":
                tier = "abbreviation" if strong_anywhere else "abbreviation_unconfirmed"
            rows.append({"theory": th.key, "term": term, "tier": tier, "section": sec, "count": rec["count"],
                         "snippets": json.dumps(rec["snippets"]), "domain_ok": int(dom_ok)})
        counted = lambda tier: [(k, r) for k, r in hits.items() if k[1] == tier and k[2] in COUNTED_SECTIONS]
        strong_counted = counted("strong")
        n_strong = sum(r["count"] for _, r in strong_counted)
        direct = n_strong > 0 and dom_ok
        weak = bool(dom_ok and not direct and counted("strong_uncorroborated"))
        close = bool(dom_ok and counted("close_term"))
        flags.append({
            "theory": th.key, "direct_mention": int(direct), "weak_mention": int(weak),
            "any_mention_level": "direct" if direct else "weak" if weak else "close" if close else "none",
            "names_theory_loosely": int(direct or weak or close), "mention_strength": n_strong if direct else 0,
            "title_or_abstract_hit": int(direct and any(k[2] in ("title", "abstract") for k, _ in strong_counted)),
            "strong_blocked_by_domain": 0 if dom_ok else n_strong,
            "close_term_hit": int(close),
            "adjacent_hit": int(dom_ok and bool(counted("adjacent"))),
            "abbrev_confirmed": sum(r["count"] for k, r in hits.items() if k[1] == "abbreviation_raw") if strong_anywhere else 0,
            "abbrev_unconfirmed": 0 if strong_anywhere else sum(r["count"] for k, r in hits.items() if k[1] == "abbreviation_raw"),
            "cites_landmark": len({k[0] for k in hits if k[1] == "landmark_ref"}),
            "cites_author_year": len({k[0] for k in hits if k[1] == "author_year"}),
            "domain_n": n_dom, "domain_ok": int(dom_ok),
        })
    return rows, flags


def corpus_pmcids(conn) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT pmcid FROM corpus_membership ORDER BY pmcid")]


def _load(conn, pmcid: str) -> tuple[dict, list[str]]:
    secs = {r["section"]: r["text"] for r in conn.execute("SELECT section, text FROM paper_sections WHERE pmcid=?", (pmcid,))}
    refs = [r[0] for r in conn.execute("SELECT raw_text FROM paper_refs WHERE pmcid=? ORDER BY idx", (pmcid,))]
    return secs, refs


def run(conn, terms: Terms, rescan: bool = False) -> dict:
    done = {} if rescan else {r[0]: r[1] for r in conn.execute("SELECT pmcid, terms_hash FROM scan_log")}
    stats = {"scanned": 0, "skipped": 0, "no_text": 0}
    db.migrate_paper_flags(conn)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for i, pmcid in enumerate(corpus_pmcids(conn), 1):
        if done.get(pmcid) == terms.terms_hash:
            stats["skipped"] += 1
            continue
        secs, refs = _load(conn, pmcid)
        for tbl in ("term_hits", "paper_flags"):
            conn.execute(f"DELETE FROM {tbl} WHERE pmcid=?", (pmcid,))
        if not any(secs.get(s) for s in COUNTED_SECTIONS):
            p = conn.execute("SELECT fetch_status, fetch_error, parse_status, parse_error FROM papers WHERE pmcid=?",
                             (pmcid,)).fetchone()
            note = (f"no text: fetch={p['fetch_status']} {p['fetch_error'] or ''} parse={p['parse_status']} "
                    f"{p['parse_error'] or ''}" if p else "no papers row").strip()
            print(f"[no_text] {pmcid}: {note}", file=sys.stderr)
            conn.execute("INSERT OR REPLACE INTO scan_log VALUES (?,?,?,?,?)", (pmcid, terms.terms_hash, now, "no_text", note))
            stats["no_text"] += 1
            continue
        rows, flags = scan_paper(secs, refs, terms)
        conn.executemany("INSERT INTO term_hits VALUES (:pmcid,:theory,:term,:tier,:section,:count,:snippets,:domain_ok)",
                         [{**r, "pmcid": pmcid} for r in rows])
        cols = ("pmcid,theory,direct_mention,weak_mention,any_mention_level,names_theory_loosely,mention_strength,"
                "title_or_abstract_hit,strong_blocked_by_domain,close_term_hit,adjacent_hit,abbrev_confirmed,"
                "abbrev_unconfirmed,cites_landmark,cites_author_year,domain_n,domain_ok")
        conn.executemany(f"INSERT INTO paper_flags ({cols}) VALUES ({','.join(':' + c for c in cols.split(','))})",
                         [{**f, "pmcid": pmcid} for f in flags])
        conn.execute("INSERT OR REPLACE INTO scan_log VALUES (?,?,?,?,?)", (pmcid, terms.terms_hash, now, "ok", None))
        stats["scanned"] += 1
        if i % 500 == 0:
            conn.commit()
            print(f"  ...{i} papers", file=sys.stderr)
    conn.commit()
    return stats


def sanity(conn) -> None:
    q = lambda sql, *a: conn.execute(sql, a).fetchall()
    print("\n== scan sanity ==")
    print("scan_log:", dict(q("SELECT status, COUNT(*) FROM scan_log GROUP BY 1")))
    print("papers in corpus:", len(corpus_pmcids(conn)), "| papers with flags:", q("SELECT COUNT(DISTINCT pmcid) FROM paper_flags")[0][0])
    for r in q("""SELECT theory, SUM(direct_mention) d, SUM(close_term_hit) c, SUM(weak_mention) w, SUM(adjacent_hit) a, SUM(strong_blocked_by_domain>0) b,
                  SUM(cites_landmark>0) cl, SUM(cites_author_year>0) ay FROM paper_flags GROUP BY theory"""):
        print(f"  {r['theory']:28} direct={r['d']:5} close={r['c']:5} adjacent={r['a']:5} domain-blocked={r['b']:4} "
              f"cites_landmark={r['cl']:5} author_year={r['ay']:5}")
    print("random direct-mention hits:")
    rows = q("""SELECT h.pmcid, h.theory, h.term, h.section, h.snippets FROM term_hits h JOIN paper_flags f USING(pmcid, theory)
                WHERE h.tier='strong' AND f.direct_mention=1""")
    for r in random.Random(1).sample(rows, min(5, len(rows))):
        print(f"  {r['pmcid']} {r['theory']} [{r['term']}/{r['section']}] …{json.loads(r['snippets'])[0][:200]}…")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rescan", action="store_true")
    args = ap.parse_args()
    conn = db.connect()
    terms = load_terms()
    print("scan:", run(conn, terms, args.rescan))
    sanity(conn)

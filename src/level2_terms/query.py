"""Level 2 query API (the Streamlit UI calls this directly).

    get_mentions("Global Workspace Theory", 1995, 2015, min_strength=1, limit=50)

`theory` may be the terms.yaml key ("global_workspace") or its display name. Only papers with direct_mention=1
(strong term + domain_context rule, see scan.py) are returned, sorted by mention strength, then title/abstract
hits, then year. Each result carries title, year, journal, strong-term counts per section, snippets, the corpus
part(s) the paper belongs to, and the weak signals (close/adjacent/landmark) that are NOT mentions.
"""
import json
from pathlib import Path

from src import db


def resolve_theory(conn, theory: str) -> str:
    keys = {r[0] for r in conn.execute("SELECT DISTINCT theory FROM paper_flags")}
    if theory in keys:
        return theory
    from src.level2_terms.terms import load_terms
    return load_terms().by_name(theory).key


def get_mentions(theory: str, year_min: int = 1995, year_max: int = 2015, min_strength: int = 1,
                 limit: int | None = None, db_path: Path | None = None, max_snippets: int = 3) -> list[dict]:
    conn = db.connect(db_path) if db_path else db.connect()
    key = resolve_theory(conn, theory)
    sql = """SELECT p.pmcid, p.pmid, p.doi, p.title, p.year, p.journal, f.mention_strength, f.title_or_abstract_hit,
                    f.close_term_hit, f.adjacent_hit, f.cites_landmark, f.cites_author_year,
                    (SELECT GROUP_CONCAT(DISTINCT part) FROM corpus_membership m WHERE m.pmcid=p.pmcid) AS parts
             FROM paper_flags f JOIN papers p USING(pmcid)
             WHERE f.theory=? AND f.direct_mention=1 AND f.mention_strength>=? AND p.year BETWEEN ? AND ?
             ORDER BY f.mention_strength DESC, f.title_or_abstract_hit DESC, p.year, p.pmcid"""
    args = [key, min_strength, year_min, year_max]
    if limit:
        sql += " LIMIT ?"
        args.append(limit)
    out = []
    for r in conn.execute(sql, args).fetchall():
        rec = dict(r)
        rec["parts"] = (rec["parts"] or "").split(",")
        by_section, terms, snips = {}, {}, []
        for h in conn.execute("""SELECT term, section, count, snippets FROM term_hits
                                 WHERE pmcid=? AND theory=? AND tier='strong' AND domain_ok=1
                                 ORDER BY count DESC""", (rec["pmcid"], key)):
            by_section[h["section"]] = by_section.get(h["section"], 0) + h["count"]
            terms[h["term"]] = terms.get(h["term"], 0) + h["count"]
            for s in json.loads(h["snippets"]):
                if len(snips) < max_snippets:
                    snips.append({"term": h["term"], "section": h["section"], "text": s})
        rec.update(mentions_by_section=by_section, mentions_by_term=terms, snippets=snips)
        out.append(rec)
    return out


def direct_mention_ids(theory: str, db_path: Path | None = None) -> set[str]:
    """PMCIDs flagged direct_mention for a theory: the exclusion set for Level 3."""
    conn = db.connect(db_path) if db_path else db.connect()
    key = resolve_theory(conn, theory)
    return {r[0] for r in conn.execute("SELECT pmcid FROM paper_flags WHERE theory=? AND direct_mention=1", (key,))}


def names_theory_ids(theory: str, db_path: Path | None = None) -> set[str]:
    """PMCIDs that name the theory at all: direct OR weak (uncorroborated bare phrase) OR close-term mention.
    Level 3 must filter on this (not direct_mention_ids) before claiming a paper "never mentions" the theory."""
    conn = db.connect(db_path) if db_path else db.connect()
    key = resolve_theory(conn, theory)
    return {r[0] for r in conn.execute("SELECT pmcid FROM paper_flags WHERE theory=? AND names_theory_loosely=1", (key,))}

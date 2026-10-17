"""SQLite schema and connection helper."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "excavator.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS theories (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL UNIQUE,
    loc_url          TEXT,
    description_text TEXT
);

CREATE TABLE IF NOT EXISTS loc_references (
    id                INTEGER PRIMARY KEY,
    theory_id         INTEGER NOT NULL REFERENCES theories(id),
    raw_text          TEXT NOT NULL,
    parsed_title      TEXT,
    parsed_authors    TEXT,
    parsed_year       INTEGER,
    parsed_journal    TEXT,
    doi               TEXT,
    pmcid             TEXT,
    pmid              TEXT,
    resolution_status TEXT CHECK (resolution_status IN
        ('resolved_fulltext','resolved_no_fulltext','doi_only','unresolved','non_article')),
    resolution_source TEXT,
    notes             TEXT,
    source_url        TEXT,
    match_score       REAL,
    resolve_notes     TEXT,
    UNIQUE (theory_id, raw_text)
);
CREATE TABLE IF NOT EXISTS papers (
    pmcid        TEXT PRIMARY KEY,
    pmid         TEXT, doi TEXT, title TEXT, year INTEGER, journal TEXT, abstract TEXT, license TEXT,
    source       TEXT,                      -- Europe PMC source flag (MED / PMC / ...)
    xml_path     TEXT,
    xml_source   TEXT,                      -- s3 (AWS PMC open data) | europepmc
    fetch_status TEXT NOT NULL DEFAULT 'pending',   -- pending | ok | failed
    fetch_error  TEXT,
    parse_status TEXT,                      -- NULL | ok | failed
    parse_error  TEXT,
    n_refs INTEGER, n_body_chars INTEGER, has_intro INTEGER, has_discussion INTEGER
);
CREATE TABLE IF NOT EXISTS paper_sections (
    pmcid TEXT NOT NULL REFERENCES papers(pmcid),
    section TEXT NOT NULL,                  -- title | abstract | introduction | body | discussion | back_matter
    text TEXT NOT NULL,
    PRIMARY KEY (pmcid, section)
);
CREATE TABLE IF NOT EXISTS paper_refs (    -- reference lists, never merged into section text
    pmcid TEXT NOT NULL REFERENCES papers(pmcid),
    idx INTEGER NOT NULL, raw_text TEXT NOT NULL,
    PRIMARY KEY (pmcid, idx)
);
CREATE TABLE IF NOT EXISTS corpus_membership (
    pmcid TEXT NOT NULL REFERENCES papers(pmcid),
    part TEXT NOT NULL CHECK (part IN ('seed','candidate','background','random')),
    tag  TEXT NOT NULL,                     -- theory (seed/candidate), topic (background), year (random)
    PRIMARY KEY (pmcid, part, tag)
);
CREATE TABLE IF NOT EXISTS search_log (
    part TEXT NOT NULL, tag TEXT NOT NULL, query TEXT NOT NULL,
    total_hits INTEGER, enumerated INTEGER, sampled INTEGER, cap INTEGER, run_at TEXT,
    PRIMARY KEY (part, tag, query)
);
-- Level 2 (see src/level2_terms/scan.py for the definitions)
CREATE TABLE IF NOT EXISTS term_hits (
    pmcid TEXT NOT NULL, theory TEXT NOT NULL,          -- theory = key in terms.yaml
    term TEXT NOT NULL,
    tier TEXT NOT NULL,       -- strong | abbreviation | abbreviation_unconfirmed | close_term | adjacent | landmark_ref | author_year
    section TEXT NOT NULL,    -- title | abstract | introduction | body | discussion | back_matter | references
    count INTEGER NOT NULL,
    snippets TEXT,            -- JSON list, up to 3
    domain_ok INTEGER NOT NULL,
    PRIMARY KEY (pmcid, theory, term, tier, section)
);
CREATE INDEX IF NOT EXISTS ix_term_hits_theory ON term_hits(theory, tier);
CREATE TABLE IF NOT EXISTS paper_flags (    -- one row per paper per theory: every scanned paper gets a row
    pmcid TEXT NOT NULL, theory TEXT NOT NULL,
    direct_mention INTEGER NOT NULL,         -- strong hit in title/abstract/intro/body/discussion AND domain_ok
    mention_strength INTEGER NOT NULL,       -- total strong-term count in those sections (0 unless direct_mention)
    title_or_abstract_hit INTEGER NOT NULL,
    strong_blocked_by_domain INTEGER NOT NULL,   -- strong hits that failed the domain_context rule
    close_term_hit INTEGER NOT NULL, adjacent_hit INTEGER NOT NULL,     -- counted sections and domain_ok
    abbrev_confirmed INTEGER NOT NULL, abbrev_unconfirmed INTEGER NOT NULL,
    cites_landmark INTEGER NOT NULL,         -- distinct landmark works found in the reference list
    cites_author_year INTEGER NOT NULL,      -- distinct landmark surname+year found as in-text citations
    domain_n INTEGER NOT NULL, domain_ok INTEGER NOT NULL,
    weak_mention INTEGER NOT NULL DEFAULT 0,       -- needs_corroboration term only, uncorroborated (not a direct mention)
    any_mention_level TEXT NOT NULL DEFAULT 'none',  -- direct | weak | close | none (that precedence)
    names_theory_loosely INTEGER NOT NULL DEFAULT 0, -- direct OR weak OR close: Level 3 "never names the theory" filter
    PRIMARY KEY (pmcid, theory)
);
CREATE VIEW IF NOT EXISTS multi_theory_papers AS     -- papers with a direct mention of more than one theory
    SELECT pmcid, COUNT(*) AS n_theories, GROUP_CONCAT(theory) AS theories FROM paper_flags
    WHERE direct_mention=1 GROUP BY pmcid HAVING COUNT(*)>1;
CREATE TABLE IF NOT EXISTS scan_log (
    pmcid TEXT PRIMARY KEY, terms_hash TEXT, scanned_at TEXT, status TEXT, note TEXT   -- status: ok | no_text
);
CREATE TABLE IF NOT EXISTS term_counts_by_year (    -- Europe PMC server-side counts, OA full text
    theory TEXT NOT NULL, year INTEGER NOT NULL, hits INTEGER NOT NULL, total_oa INTEGER NOT NULL,
    rate_per_10k REAL NOT NULL, query TEXT, PRIMARY KEY (theory, year)
);
"""


def migrate_paper_flags(conn: sqlite3.Connection) -> None:
    have = {r["name"] for r in conn.execute("PRAGMA table_info(paper_flags)")}
    for col, ddl in (("weak_mention", "INTEGER NOT NULL DEFAULT 0"),
                     ("any_mention_level", "TEXT NOT NULL DEFAULT 'none'"),
                     ("names_theory_loosely", "INTEGER NOT NULL DEFAULT 0")):
        if col not in have:
            conn.execute(f"ALTER TABLE paper_flags ADD COLUMN {col} {ddl}")
    conn.commit()


def migrate_corpus_membership(conn: sqlite3.Connection) -> None:
    """Add the nullable-in-spirit `window` column (prompt 07). Existing rows get '1995-2015'. Idempotent."""
    have = {r["name"] for r in conn.execute("PRAGMA table_info(corpus_membership)")}
    if "window" not in have:
        conn.execute("ALTER TABLE corpus_membership ADD COLUMN window TEXT DEFAULT '1995-2015'")
    conn.execute("UPDATE corpus_membership SET window='1995-2015' WHERE window IS NULL")
    conn.commit()


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    migrate_corpus_membership(conn)
    have = {r["name"] for r in conn.execute("PRAGMA table_info(loc_references)")}
    for col, typ in (("source_url", "TEXT"), ("match_score", "REAL"), ("resolve_notes", "TEXT"),
                     ("oa_status", "TEXT"),        # gold|hybrid|bronze|green|closed|not_found; NULL = not yet checked
                     ("fulltext_url", "TEXT"), ("fulltext_kind", "TEXT"),   # kind: pdf | landing
                     ("fulltext_source", "TEXT"),  # unpaywall | openalex
                     ("oa_host_type", "TEXT"), ("oa_license", "TEXT"), ("oa_version", "TEXT"),
                     ("abstract", "TEXT"), ("oa_notes", "TEXT")):
        if col not in have:   # migrate DBs created before the column existed
            conn.execute(f"ALTER TABLE loc_references ADD COLUMN {col} {typ}")
    if "xml_source" not in {r["name"] for r in conn.execute("PRAGMA table_info(papers)")}:
        conn.execute("ALTER TABLE papers ADD COLUMN xml_source TEXT")
    return conn

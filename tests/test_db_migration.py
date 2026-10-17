import sqlite3

from src import db


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(db.SCHEMA)
    return c


def test_window_migration_is_idempotent_and_defaults_old_rows():
    c = _conn()
    c.execute("INSERT INTO papers(pmcid) VALUES ('PMC1')")
    c.execute("INSERT INTO corpus_membership VALUES ('PMC1','candidate','GWT')")
    db.migrate_corpus_membership(c)
    db.migrate_corpus_membership(c)          # second run must be a no-op
    cols = [r["name"] for r in c.execute("PRAGMA table_info(corpus_membership)")]
    assert cols.count("window") == 1
    assert c.execute("SELECT window FROM corpus_membership").fetchone()[0] == "1995-2015"
    c.execute("INSERT INTO corpus_membership VALUES ('PMC1','background','x','2016-2025')")
    db.migrate_corpus_membership(c)
    assert sorted(r[0] for r in c.execute("SELECT window FROM corpus_membership")) == ["1995-2015", "2016-2025"]

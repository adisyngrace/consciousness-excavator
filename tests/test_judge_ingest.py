import json
import sqlite3

from src.judge.ingest import ingest, parse_packet, validate

PACKET = """# Batch 01

**Theory:** Test (test_theory)

**Core claims:**
- **t-c1:** first claim.
- **t-c2:** second claim.

---

### Item X001

**Title:** A title
**Year:** 2010

**Abstract:** Some   abstract
with a line break.

**Passage 1 (body):** passage text here.

### Item X002

**Title:** Other
**Year:** 2011

**Abstract:** (no abstract available)

**Passage 1 (body):** more text.
"""


def good(**kw):
    j = {"item_id": "X001", "verdict": "R", "confidence": "high", "claim_ids": ["t-c1"], "reason": "r",
         "evidence": "Some abstract with a line break.", "names_theory_in_text": False, "better_fit_theory": None}
    j.update(kw)
    return j


def test_parse_packet():
    p = parse_packet(PACKET)
    assert p["theory"] == "test_theory" and p["claim_ids"] == {"t-c1", "t-c2"} and set(p["items"]) == {"X001", "X002"}


def test_valid_and_whitespace_normalised():
    assert validate(good(), parse_packet(PACKET)) == []


def test_failures():
    p = parse_packet(PACKET)
    assert any("verbatim" in e for e in validate(good(evidence="not in packet"), p))
    assert any("words" in e for e in validate(good(evidence=" ".join(["a"] * 21)), p))
    assert any("verdict" in e for e in validate(good(verdict="X"), p))
    assert any("confidence" in e for e in validate(good(confidence="very"), p))
    assert any("empty" in e for e in validate(good(claim_ids=[]), p))
    assert any("not R" in e for e in validate(good(verdict="G"), p))
    assert any("unknown claim" in e for e in validate(good(claim_ids=["zz"]), p))
    assert any("not in packet" in e for e in validate(good(item_id="Q"), p))
    assert any("better_fit" in e for e in validate(good(better_fit_theory="Nope"), p))
    j = good()
    del j["reason"]
    assert any("keys" in e for e in validate(j, p))
    assert any("keys" in e for e in validate({**good(), "extra": 1}, p))


def test_ingest_loads_and_lists_failures(tmp_path):
    (tmp_path / "packets").mkdir()
    (tmp_path / "judgments").mkdir()
    (tmp_path / "packets" / "batch_01.md").write_text(PACKET)
    (tmp_path / "judgments" / "batch_01.json").write_text(json.dumps([good(better_fit_theory="Panpsychism")]))
    db = tmp_path / "t.db"
    n, fails = ingest(tmp_path, db)
    assert n == 1 and fails == [("X002", "item has no judgment")]
    row = sqlite3.connect(db).execute("SELECT item_id, theory, pmcid, verdict, claim_ids, flags FROM judgments").fetchone()
    assert row == ("X001", "test_theory", None, "R", '["t-c1"]', '["better_fit:Panpsychism"]')
    n, fails = ingest(tmp_path, db)  # idempotent
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM judgments").fetchone()[0] == 1

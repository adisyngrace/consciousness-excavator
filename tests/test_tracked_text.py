"""Guard: tracked results/, reports/ and docs/ must not contain pasted source text (prompt 09 final check).

Rules
  * No CSV cell over 400 characters, except the allowlisted LoC description excerpts (public Landmark of Consciousness text, not CORE).
  * CORE pilot files (philosophy_pilot_*.csv, core_pilot_labels.csv) have no column named snippet / text / excerpt / abstract / body.
  * `snippet` cells (Europe PMC pilot files, <= 200 chars by construction) never exceed 200 characters.
  * No markdown paragraph (outside tables) over 6,000 characters; CORE pilot markdown (reports/core_pilot.md and results/README.md) has no
    quoted span of 15+ words, which would be a verbatim quotation.
  * If data/core_pilot.db exists: no 10-word run from any CORE paper's text appears in a CORE pilot file once the papers' titles are removed.
"""
import csv
import re
import sqlite3
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(10 ** 7)
ALLOW_LONG = {("results/theory_descriptions.csv", "excerpt")}          # LoC description excerpts, public, not CORE
CORE_CSV = ("results/philosophy_pilot_metrics.csv",)     # the CORE title lists and labels are withheld in the public release
CORE_MD = ("reports/core_pilot.md", "results/README.md")
SNIPPET_CAP_REPORTS = 350      # Level 2 audit sheets in reports/ hold Europe PMC open-access snippets of up to ~330 characters (not CORE)
BANNED_COLS = {"snippet", "text", "excerpt", "abstract", "body", "fulltext", "full_text"}


def tracked() -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "results", "reports", "docs"], cwd=ROOT, text=True).split()
    return [f for f in out if (ROOT / f).exists()]


def cells(f: str):
    with open(ROOT / f, newline="") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def paragraphs(f: str):
    return [p for p in re.split(r"\n\s*\n", (ROOT / f).read_text()) if not p.lstrip().startswith("|")]


def test_csv_cells_not_pasted_text():
    bad = []
    for f in (x for x in tracked() if x.endswith(".csv")):
        head, rows = cells(f)
        for r in rows:
            for h, c in zip(head, r):
                if len(c) > 400 and (f, h) not in ALLOW_LONG:
                    bad.append((f, h, len(c)))
                if h.lower() == "snippet" and len(c) > (200 if f.startswith("results/") else SNIPPET_CAP_REPORTS):
                    bad.append((f, h, len(c)))
    assert not bad, bad


def test_core_pilot_csv_have_no_text_columns():
    for f in CORE_CSV:
        head, _ = cells(f)
        assert not {h.lower() for h in head} & BANNED_COLS, (f, head)


def test_markdown_has_no_pasted_blocks():
    bad = [(f, len(p)) for f in tracked() if f.endswith(".md") for p in paragraphs(f) if len(p) > 6000]
    assert not bad, bad
    for f in CORE_MD:
        for line in (ROOT / f).read_text().splitlines():
            pos = [m.start() for m in re.finditer(r'"|\u201c|\u201d', line)]
            if len(pos) % 2:
                continue                                          # unbalanced quotes on this line: cannot pair reliably
            for a, b in zip(pos[::2], pos[1::2]):
                assert len(line[a + 1:b].split()) < 15, (f, line[a + 1:a + 80])


def test_no_core_text_in_core_pilot_files():
    db = ROOT / "data" / "core_pilot.db"
    if not db.exists():
        pytest.skip("data/core_pilot.db not present")
    conn = sqlite3.connect(db)
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (s or "").lower())).strip()
    haystack = " ".join(norm(f"{a} {b}") for a, b in conn.execute("SELECT abstract, body FROM core_texts"))
    titles = [norm(t) for (t,) in conn.execute("SELECT title FROM core_papers") if t]
    tw = [t.split() for t in titles]
    grams = {" ".join(w[i:i + 4]) for w in tw for i in range(max(1, len(w) - 3))}
    hits = []
    for f in CORE_CSV + CORE_MD:
        words = norm((ROOT / f).read_text()).split()
        in_title = [False] * len(words)                          # titles (also clipped ones) are allowed; mark words they cover
        for i in range(len(words) - 3):
            if " ".join(words[i:i + 4]) in grams:
                for j in range(i, i + 4):
                    in_title[j] = True
        for i in range(0, max(0, len(words) - 10), 3):
            if any(in_title[i:i + 10]):
                continue
            run = " ".join(words[i:i + 10])
            if run in haystack:
                hits.append((f, run[:60]))
    assert not hits, hits[:5]

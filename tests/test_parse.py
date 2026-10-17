from pathlib import Path

import pytest

from src.parse import parse_page

FIX = Path(__file__).parent / "fixtures"
# Saved LoC pages are third-party text and are not published; tests that need them are skipped.
needs_fixture = pytest.mark.skipif(not FIX.exists(), reason="fixture not published")


def load(slug):
    return parse_page((FIX / f"{slug}.html").read_text())


def by_start(refs, start):
    return next(r for r in refs if r.raw_text.startswith(start))


@needs_fixture
def test_champagne_quoted_article_with_doi():
    desc, refs = load("champagne-s-semiotic-account")
    assert 13 <= len(refs) <= 14
    r = by_start(refs, "Champagne, M. (2009)")
    assert r.year == 2009
    assert r.authors == "Champagne, M."
    assert r.title.startswith("Explaining the Qualitative Dimension")
    assert r.journal == "Dialogue: Canadian Philosophical Review"
    assert r.doi == "10.1017/s0012217309090088"
    assert not r.notes
    assert "Four Ages of Understanding" not in desc  # reference list excluded


@needs_fixture
def test_champagne_book_flagged_not_dropped():
    _, refs = load("champagne-s-semiotic-account")
    r = by_start(refs, "Deely, J. N. (2001)")
    assert r.title == "Four Ages of Understanding"
    assert "book" in r.notes and r.doi is None


@needs_fixture
def test_year_range_uses_first_year():
    _, refs = load("champagne-s-semiotic-account")
    assert by_start(refs, "Peirce, C. S. (1931").year == 1931


@needs_fixture
def test_peirce_chapter_and_book_and_nd():
    _, refs = load("peirce-s-phaneroscopic-semiotics")
    assert len(refs) == 16
    assert "book" in by_start(refs, "Hookway, C. (1992)").notes
    assert "book_chapter" in by_start(refs, "Peirce, C. S. (1904)").notes
    nd = by_start(refs, "Peirce, C. S. (n.d.)")
    assert nd.year is None and any("n.d." in n for n in nd.notes)


@needs_fixture
def test_gwt_structured_entries():
    desc, refs = load("baars-s-and-dehaene-s-global-workspace-theory")
    assert len(refs) == 10
    r = by_start(refs, "Baars, 1988")
    assert r.year == 1988 and r.title == "A Cognitive Theory of Consciousness"
    assert "book" in r.notes
    assert "Google Scholar" not in r.raw_text
    assert "Core Claim" in desc  # Key Takeaways included


@needs_fixture
def test_iit_doi_from_link_and_article_fields():
    _, refs = load("tononi-s-integrated-information-theory")
    assert len(refs) == 14
    r = by_start(refs, "Tononi & Koch, 2015")
    assert r.doi == "10.1098/rstb.2014.0167"
    assert r.year == 2015
    assert r.title == "Consciousness: here, there and everywhere?"
    assert r.journal.startswith("Phil. Trans. R. Soc. B")
    assert "non_article" not in " ".join(r.notes)


@needs_fixture
def test_nature_news_flagged_nonarticle_but_kept():
    _, refs = load("tononi-s-integrated-information-theory")
    r = by_start(refs, "Lenharo, 2023a")
    assert r.doi == "10.1038/d41586-023-02120-8"   # DOI present, still kept


@needs_fixture
def test_label_style_page():
    _, refs = load("sebastian-s-predictive-machine")
    assert len(refs) == 7
    r = by_start(refs, "Friston, 2010")
    assert r.year == 2010
    assert r.title is None and any("unparsed" in n for n in r.notes)


@pytest.mark.parametrize("slug", ["champagne-s-semiotic-account", "peirce-s-phaneroscopic-semiotics",
                                  "baars-s-and-dehaene-s-global-workspace-theory",
                                  "tononi-s-integrated-information-theory", "sebastian-s-predictive-machine"])
@needs_fixture
def test_every_ref_has_raw_text_and_is_unique(slug):
    _, refs = load(slug)
    assert refs and all(r.raw_text for r in refs)
    assert len({r.raw_text for r in refs}) == len(refs)


def test_journal_name_trimmed():
    from src.parse import journal_name
    assert journal_name("Cognition, 79 , pp. 1-37") == "Cognition"
    assert journal_name("Entropy, 21 (12) , p. 1160") == "Entropy"
    assert journal_name("Phil. Trans. R. Soc. B, 370, Article 20140167") == "Phil. Trans. R. Soc. B"
    assert journal_name("Nature") == "Nature"
    assert journal_name(None) is None


@needs_fixture
def test_quoted_title_chapter_not_journal():
    _, refs = load("champagne-s-semiotic-account")
    r = by_start(refs, "Champagne, M. (2024)")
    assert "book_chapter" in r.notes and r.journal is None


@needs_fixture
def test_notes_not_duplicated():
    _, refs = load("tononi-s-integrated-information-theory")
    for r in refs:
        assert len(r.notes) == len(set(r.notes))

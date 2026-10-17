from src.resolve import fulltext_available, score_candidate


def item(title, year, doi="10.1/x"):
    return {"DOI": doi, "title": [title] if isinstance(title, str) else title,
            "issued": {"date-parts": [[year]]}}


def test_accepts_matching_title_and_year():
    c = score_candidate(item("Consciousness: here, there and everywhere?", 2015),
                        "Consciousness: here, there and everywhere?", 2015, "raw")
    assert c and not c.reason and c.score > 95


def test_accepts_year_off_by_one_online_first():
    c = score_candidate(item("Why does space feel the way it does", 2020),
                        "Why does space feel the way it does?", 2019, "raw")
    assert not c.reason


def test_rejects_year_mismatch():
    c = score_candidate(item("Consciousness: here, there and everywhere?", 2008),
                        "Consciousness: here, there and everywhere?", 2015, "raw")
    assert "year_mismatch" in c.reason


def test_rejects_different_title():
    c = score_candidate(item("Integrated information in the brain", 2015),
                        "Consciousness: here, there and everywhere?", 2015, "raw")
    assert "title_similarity" in c.reason


def test_subtitle_split_in_crossref_still_matches():
    c = score_candidate(item(["Whatever next", "Predictive brains, situated agents"], 2013),
                        "Whatever next? Predictive brains, situated agents", 2013, "raw")
    assert not c.reason


def test_no_parsed_title_uses_raw_text_and_is_stricter():
    raw = "Clark, 2013. Andy Clark, Whatever next? Predictive brains, situated agents, and the future of cognitive science."
    ok = score_candidate(item("Whatever next? Predictive brains, situated agents, and the future of cognitive science", 2013),
                         None, 2013, raw)
    assert not ok.reason
    short = score_candidate(item("Whatever", 2013), None, 2013, raw)   # too short to trust
    assert short.reason


def test_missing_title_or_doi_ignored():
    assert score_candidate({"DOI": "10.1/x"}, "t", 2000, "") is None
    assert score_candidate({"title": ["t"]}, "t", 2000, "") is None


def test_fulltext_requires_pmcid_and_open_access():
    assert fulltext_available({"pmcid": "PMC1", "isOpenAccess": "Y", "inEPMC": "Y"})
    assert not fulltext_available({"pmcid": "PMC1", "isOpenAccess": "N", "inEPMC": "Y"})
    assert not fulltext_available({"pmid": "1", "isOpenAccess": "Y", "inEPMC": "N"})

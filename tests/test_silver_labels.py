from src.level2_terms.labels import paper_repetition, per_term, wilson
from src.level2_terms.silver import CONSC_RX


def test_wilson_small_n_is_wide():
    lo, hi = wilson(3, 3)
    assert 0.4 < lo < 0.5 and hi == 1.0
    assert wilson(0, 0) == (0.0, 1.0)


def test_consciousness_vocab_matches_variants_not_aware():
    txt = "Consciousness, unconscious priming, awareness, qualia, subjective experience; we were aware of it."
    assert len(CONSC_RX.findall(txt)) == 5


def test_per_term_excludes_undecided_from_precision_and_dedupes_papers():
    rows = [{"theory": "t", "pmcid": "P1", "term": "x", "label": "Y", "note": "weak mention"},
            {"theory": "t", "pmcid": "P2", "term": "x", "label": "?", "note": ""},
            {"theory": "t", "pmcid": "P1", "term": "y", "label": "N", "note": ""}]
    d = per_term(rows)
    assert d[("t", "x")]["Y"] == 1 and d[("t", "x")]["?"] == 1 and d[("t", "x")]["weak"] == 1
    assert paper_repetition(rows) == [("P1", 2, {"t": 2})]

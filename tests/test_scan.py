import json

import pytest

from src.level2_terms.mask import PLACEHOLDER, leaks, mask_text
from src.level2_terms.scan import scan_paper
from src.level2_terms.terms import load_terms

T = load_terms()
CTX = "The brain and neural cortex support cognition and perception."      # >= 2 domain_context words
WS = "global_workspace"


def run(sections, refs=()):
    rows, flags = scan_paper({"title": "", **sections}, list(refs), T)
    return rows, {f["theory"]: f for f in flags}


def tiers(rows, theory, tier):
    return [r for r in rows if r["theory"] == theory and r["tier"] == tier]


def test_strong_term_with_context_is_direct_mention():
    rows, fl = run({"body": f"{CTX} We apply global workspace theory here."})
    assert fl[WS]["direct_mention"] == 1 and fl[WS]["mention_strength"] == 1


def test_longest_term_wins_no_double_count():
    rows, fl = run({"body": f"{CTX} global workspace theory and the global workspace."})
    assert fl[WS]["mention_strength"] == 2
    assert {r["term"] for r in tiers(rows, WS, "strong")} == {"global workspace theory", "global workspace"}


def test_abbreviation_alone_is_unconfirmed_and_not_direct():
    rows, fl = run({"body": f"{CTX} The IIT campus in Kharagpur."})
    assert tiers(rows, "integrated_information", "abbreviation_unconfirmed")
    assert not tiers(rows, "integrated_information", "abbreviation")
    assert fl["integrated_information"]["direct_mention"] == 0
    assert fl["integrated_information"]["abbrev_unconfirmed"] == 1


def test_abbreviation_confirmed_by_strong_term_and_case_sensitive():
    rows, fl = run({"body": f"{CTX} Integrated information theory (IIT) and iit."})
    assert tiers(rows, "integrated_information", "abbreviation")[0]["count"] == 1   # 'iit' lowercase ignored
    assert fl["integrated_information"]["direct_mention"] == 1


@pytest.mark.parametrize("variant", ["free energy principle", "free-energy principle", "Free-Energy Principle",
                                     "free‐energy principles"])
def test_hyphen_case_plural_variants(variant):
    rows, fl = run({"body": f"{CTX} Under the {variant} the brain minimises surprise."})
    assert fl["predictive_processing_fep"]["direct_mention"] == 1


def test_reference_list_only_is_not_a_mention_but_is_landmark():
    refs = ["Tononi G. An information integration theory of consciousness. BMC Neurosci. 2004;5:42.",
            "Smith J. Global workspace theory revisited. 2009."]
    rows, fl = run({"body": CTX + " Nothing relevant."}, refs)
    assert fl[WS]["direct_mention"] == 0 and not tiers(rows, WS, "strong")
    assert fl["integrated_information"]["cites_landmark"] == 1
    assert fl["integrated_information"]["direct_mention"] == 0


def test_in_text_author_year_is_weak_and_never_direct():
    rows, fl = run({"body": f"{CTX} As argued (Tononi and Koch, 2015) and Dehaene et al. 2001."})
    assert fl["integrated_information"]["cites_author_year"] == 1
    assert fl[WS]["cites_author_year"] == 1
    assert fl["integrated_information"]["direct_mention"] == 0


def test_bare_surname_does_not_count():
    rows, fl = run({"body": f"{CTX} Koch and Clark and Friston discussed it."})
    assert all(f["cites_author_year"] == 0 for f in fl.values())


def test_generic_words_do_not_count():
    rows, fl = run({"body": f"{CTX} Information integration in the workspace; free energy and prediction error "
                            "in a global setting."})
    assert not any(r["tier"] in ("strong", "close_term") for r in rows)
    assert all(f["direct_mention"] == 0 for f in fl.values())


def test_strong_term_without_domain_context_does_not_count():
    rows, fl = run({"body": "We compute the free energy principle for the global workspace theory in software."})
    assert fl["predictive_processing_fep"]["direct_mention"] == 0
    assert fl["predictive_processing_fep"]["strong_blocked_by_domain"] == 1
    assert tiers(rows, "predictive_processing_fep", "strong")[0]["domain_ok"] == 0


def test_close_term_and_adjacent_never_direct():
    rows, fl = run({"abstract": f"{CTX} Predictive coding and the Markov blanket; ignition and conscious access."})
    f = fl["predictive_processing_fep"]
    assert f["close_term_hit"] == 1 and f["direct_mention"] == 0
    assert fl[WS]["adjacent_hit"] == 1 and fl[WS]["direct_mention"] == 0


def test_back_matter_hit_does_not_count():
    rows, fl = run({"body": CTX, "back_matter": "We thank the panpsychism group."})
    assert fl["panpsychism"]["direct_mention"] == 0


def test_title_or_abstract_flag():
    rows, fl = run({"title": "Panpsychism and the brain", "body": CTX})
    assert fl["panpsychism"]["title_or_abstract_hit"] == 1


def test_snippets_capped_and_normalised():
    rows, _ = run({"body": CTX + " " + " x\n y ".join(["panpsychism"] * 6)})
    r = tiers(rows, "panpsychism", "strong")[0]
    assert r["count"] == 6 and len(json.loads(r["snippets"])) == 3 and "\n" not in r["snippets"]


# ---- masking -------------------------------------------------------------------------------------------------
def test_mask_blanks_direct_close_and_abbreviations_but_not_adjacent():
    txt = "Global workspace theory (GWT), predictive-coding, the Markov blanket and ignition; integrated information."
    out = mask_text(txt, terms=T)
    assert out.count(PLACEHOLDER) == 4
    assert "ignition" in out and "integrated information" in out
    assert leaks(out, terms=T) == []


def test_mask_single_theory_leaves_others():
    out = mask_text("panpsychism and active inference", theories=["panpsychism"], terms=T)
    assert out == f"{PLACEHOLDER} and active inference"


def test_mask_author_year_opt_in():
    txt = "see Tononi et al. 2016"
    assert mask_text(txt, terms=T) == txt
    assert PLACEHOLDER in mask_text(txt, terms=T, mask_author_year=True)


PP = "predictive_processing_fep"


def test_bare_predictive_processing_uncorroborated_is_weak_not_direct():
    rows, fl = run({"body": f"{CTX} Predictive processing aids sentence comprehension."})
    assert fl[PP]["direct_mention"] == 0 and fl[PP]["weak_mention"] == 1
    assert fl[PP]["any_mention_level"] == "weak" and fl[PP]["names_theory_loosely"] == 1
    assert tiers(rows, PP, "strong_uncorroborated") and not tiers(rows, PP, "strong")


def test_bare_predictive_processing_in_abstract_or_with_other_term_is_direct():
    _, fl = run({"abstract": f"{CTX} Predictive processing in the brain."})
    assert fl[PP]["direct_mention"] == 1 and fl[PP]["weak_mention"] == 0
    _, fl = run({"body": f"{CTX} Predictive processing and the free energy principle."})
    assert fl[PP]["direct_mention"] == 1


def test_predictive_machine_is_close_term_and_corroborates():
    rows, fl = run({"body": f"{CTX} The brain is a predictive machine."})
    assert fl[PP]["direct_mention"] == 0 and fl[PP]["close_term_hit"] == 1 and fl[PP]["any_mention_level"] == "close"
    _, fl = run({"body": f"{CTX} Predictive processing; the brain is a predictive machine."})
    assert fl[PP]["direct_mention"] == 1


def test_information_integration_theory_is_iit_strong_and_none_level_default():
    _, fl = run({"body": f"{CTX} The information integration theory of consciousness (Tononi, 2004)."})
    assert fl["integrated_information"]["direct_mention"] == 1
    _, fl = run({"body": CTX})
    assert fl[PP]["any_mention_level"] == "none" and fl[PP]["names_theory_loosely"] == 0

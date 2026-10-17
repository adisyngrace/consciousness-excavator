from src.eval.mask import leaks_for_theory, mask_for_theory

G = "global_workspace"


def test_terms_deleted_without_token():
    out = mask_for_theory("According to global workspace theory (GWT), access is broadcast.", G)
    assert "[" not in out and "global" not in out.lower() and "GWT" not in out
    assert out.startswith("According to") and "access is broadcast." in out


def test_citation_variants_removed():
    for s in ("as shown (Dehaene and Naccache, 2001) here", "as in Dehaene et al. (2001) here", "see Baars, 1988; Dehaene 2003 here"):
        out = mask_for_theory(s, G)
        assert "Dehaene" not in out and "Baars" not in out and "Naccache" not in out, out
        assert "here" in out and "()" not in out


def test_possessive_and_bare_surname():
    out = mask_for_theory("Baars's idea and Dehaene's model", G)
    assert "Baars" not in out and "Dehaene" not in out and "idea" in out


def test_ambiguous_surname_only_in_citations():
    t = "champagne_semiotic"
    assert "Short" in mask_for_theory("Short sentences are fine.", t)
    assert "Short" not in mask_for_theory("as argued (Short, 2007) earlier", t)


def test_other_theory_untouched_and_leak_check():
    out = mask_for_theory("Integrated information theory and global workspace theory", G)
    assert "Integrated information theory" in out and "global workspace" not in out
    assert leaks_for_theory(out, G) == []


def test_citation_list_tidied():
    out = mask_for_theory("online correction (Friston et al., 2010; Friston, 2011; Adams et al., 2012) is assumed", "predictive_processing_fep")
    assert out == "online correction (Adams et al., 2012) is assumed", out


def test_enclosing_paren_kept():
    out = mask_for_theory("through a global workspace or a central executive (Dehaene et al., 1998; Baddeley, 2003; Baars, 2005). Next.", "global_workspace")
    assert out == "through a or a central executive (Baddeley, 2003). Next.", out
    assert mask_for_theory("as in Baars et al. (1998) and more", "global_workspace") == "as in and more"
    assert mask_for_theory("claims (Dehaene, 2001)", "global_workspace").strip() == "claims"

from src.corpus.build_core import norm_doi, norm_title, split_refs


def test_split_refs_cuts_last_heading_in_tail():
    text = "Intro text. " * 200 + "\nReferences\n" + "Smith 2001. " * 50
    body, refs, split = split_refs(text)
    assert split and refs.startswith("References") and "Smith" not in body


def test_split_refs_ignores_early_heading():
    text = "References\n" + "word " * 1000
    assert split_refs(text)[2] is False


def test_normalisers():
    assert norm_doi("https://doi.org/10.1/ABC") == "10.1/abc"
    assert norm_title("The  Mind: A-Study!") == "themindastudy"


def test_clean_title_unescapes():
    from src.eval.core_pilot import clean_title
    assert clean_title("11. \\u3cem\\u3eDreamers\\u3c/em\\u3e &amp; more") == "11. Dreamers & more"


def test_clean_title_two_digit_escapes_and_mojibake():
    from src.eval.core_pilot import clean_title
    assert clean_title("Children\\u27s &quot;X&quot; \\u3cem\\u3eR\\u3c/em\\u3e") == 'Children\'s "X" R'
    assert clean_title("Clip â€œYURAâ€ news") == "Clip “YURA” news"

import pytest
from pathlib import Path

from src.corpus.jats import classify_section, parse_jats

from lxml import etree

FIX = Path(__file__).parent / "fixtures"


def _art(inner, back=""):
    return f"""<article><front><article-meta>
      <article-id pub-id-type="pmid">123</article-id><article-id pub-id-type="doi">10.1/ABC</article-id>
      <title-group><article-title>A <i>test</i> title</article-title></title-group>
      <pub-date pub-type="epub"><year>2009</year></pub-date>
      <abstract><p>Abstract mentions workspace.</p></abstract></article-meta></front>
      <body>{inner}</body>{back}</article>""".encode()


def test_reflist_in_back_is_extracted_and_not_in_text():
    xml = _art("<sec sec-type='intro'><title>Introduction</title><p>Intro text.</p></sec>"
               "<sec><title>Results</title><p>Result text.</p></sec>"
               "<sec sec-type='discussion'><title>Discussion</title><p>Disc text.</p></sec>",
               "<back><ack><p>Thanks.</p></ack><ref-list><ref><label>1</label><mixed-citation>Tononi G (2004) Cites IIT.</mixed-citation></ref></ref-list></back>")
    p = parse_jats(xml)
    assert p.sections["introduction"].endswith("Intro text.")
    assert "Result text." in p.sections["body"] and "Disc text." in p.sections["discussion"]
    assert p.sections["back_matter"] == "Thanks."
    assert p.refs == ["Tononi G (2004) Cites IIT."]
    assert "Tononi" not in " ".join(p.sections.values())


def test_reflist_inside_body_section_is_still_separated():
    xml = _art("<sec><title>Results</title><p>Body.</p></sec>"
               "<sec sec-type='ref-list'><title>References</title><ref-list><ref><mixed-citation>Baars B (1988).</mixed-citation></ref></ref-list></sec>")
    p = parse_jats(xml)
    assert p.refs == ["Baars B (1988)."]
    assert "Baars" not in p.sections["body"] + p.sections["back_matter"]


def test_metadata_and_inline_markup():
    p = parse_jats(_art("<sec><title>Methods</title><p>x</p></sec>"))
    assert p.meta["title"] == "A test title"
    assert p.meta["doi"] == "10.1/abc" and p.meta["pmid"] == "123" and p.meta["year"] == 2009
    assert p.sections["abstract"] == "Abstract mentions workspace."


def test_tables_and_figures_are_dropped():
    p = parse_jats(_art("<sec><title>R</title><p>Real.</p><table-wrap><p>Table junk</p></table-wrap><fig><caption><p>Fig junk</p></caption></fig></sec>"))
    assert "junk" not in p.sections["body"]


def test_results_and_discussion_stays_body_but_plain_discussion_is_discussion():
    def sec(title, st=None):
        return etree.fromstring(f"<sec{' sec-type=%r' % st if st else ''}><title>{title}</title><p>x</p></sec>")
    assert classify_section(sec("Results and Discussion")) == "body"
    assert classify_section(sec("4. Discussion")) == "discussion"
    assert classify_section(sec("Conclusions")) == "discussion"
    assert classify_section(sec("Background")) == "introduction"
    assert classify_section(sec("Acknowledgments")) == "back_matter"
    assert classify_section(sec("Competing interests")) == "back_matter"
    assert classify_section(sec("Whatever", "intro")) == "introduction"


@pytest.mark.skipif(not (FIX / "pmc_plos_reflist_in_body.xml").exists(), reason="fixture not published")
def test_real_plos_article_with_reflist_in_body():
    p = parse_jats((FIX / "pmc_plos_reflist_in_body.xml").read_bytes())
    assert len(p.refs) == 73
    assert p.has_intro and p.sections["introduction"].startswith("Introduction")
    assert "References" not in p.sections["body"][-300:]
    assert p.sections["abstract"] and p.meta["year"] == 2014
    assert "Building high-level features using large scale unsupervised learning" in " ".join(p.refs)
    assert "Building high-level features using large scale" not in p.sections["body"]   # cited titles live only in refs

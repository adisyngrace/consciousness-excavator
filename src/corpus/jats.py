"""Parse Europe PMC / PMC JATS full-text XML into abstract, intro, body, discussion, back matter + references.

Verified structure (see scripts/s0_struct.py survey, 21 articles 1995-2015):
  * the reference list lives in <back><ref-list> in about half the articles, and as a <sec> containing
    a <ref-list> INSIDE <body> in the other half -- so refs are always extracted first, then every
    ref-list is stripped from the text that gets scanned;
  * sec-type is usually present but inconsistent, so sections are classified by sec-type then title regex;
  * tables, figures and supplementary-material are dropped from the text (captions included).
"""
import re
from dataclasses import dataclass, field

from lxml import etree

XLINK = "{http://www.w3.org/1999/xlink}"
DROP = ("ref-list", "table-wrap", "fig", "fig-group", "supplementary-material", "object-id", "graphic", "media")

BACK_TYPES = {"ack", "ref-list", "supplementary-material", "data-availability", "coi-statement", "author-contributions",
              "funding", "abbreviations", "supplementary-materials", "associated-data", "notes", "app", "appendix"}
BACK_TITLE = re.compile(r"acknowledg|funding|conflicts? of interest|competing|author'?s?'? contribution|supplement|"
                        r"associated data|abbreviations?|disclosure|data availability|ethics|note added|appendix|"
                        r"supporting information|financial support|footnotes?|^\W*references?\W*$|authors'? information|"
                        r"additional files?|declarations?|availability of", re.I)
INTRO_TITLE = re.compile(r"^\W*(\d+[\.\)]?\s*)?(introduction|background|overview)\b", re.I)
DISC_TITLE = re.compile(r"^\W*(\d+[\.\)]?\s*)?(general\s+)?(discussion|conclusions?|concluding remarks?)\W*$", re.I)


@dataclass
class Parsed:
    meta: dict = field(default_factory=dict)
    sections: dict = field(default_factory=dict)
    refs: list = field(default_factory=list)

    @property
    def has_intro(self) -> bool:
        return bool(self.sections.get("introduction"))

    @property
    def has_discussion(self) -> bool:
        return bool(self.sections.get("discussion"))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _text(el) -> str:
    return _norm("".join(el.itertext()))


def _block_text(el) -> str:
    """Section titles and paragraphs in document order, one per line."""
    parts = []
    for node in el.iter("title", "p", "list-item"):
        if node.tag == "p" and node.getparent() is not None and node.getparent().tag == "list-item":
            continue   # list-item text is taken whole, avoids double counting
        t = _text(node)
        if t:
            parts.append(t)
    return "\n".join(parts)


def classify_section(sec) -> str:
    st = (sec.get("sec-type") or "").lower()
    title = _text(sec.find("title")) if sec.find("title") is not None else ""
    if st in BACK_TYPES or BACK_TITLE.search(title):
        return "back_matter"
    if st == "intro" or INTRO_TITLE.search(title):
        return "introduction"
    if st in ("discussion", "conclusions", "conclusion") or DISC_TITLE.search(title):
        return "discussion"
    return "body"


def _meta(root, refs_n: int) -> dict:
    def aid(kind):
        el = root.find(f".//article-meta/article-id[@pub-id-type='{kind}']")
        return _norm(el.text) if el is not None and el.text else None
    lic = root.find(".//permissions/license")
    year = None
    for pt in ("ppub", "epub", "collection", "pub"):
        d = root.find(f".//article-meta/pub-date[@pub-type='{pt}']")
        if d is None:
            d = root.find(f".//article-meta/pub-date[@date-type='{pt}']")
        if d is not None and d.findtext("year"):
            year = int(d.findtext("year")); break
    if year is None:
        d = root.find(".//article-meta/pub-date")
        year = int(d.findtext("year")) if d is not None and (d.findtext("year") or "").isdigit() else None
    title_el = root.find(".//article-meta/title-group/article-title")
    jt = root.find(".//journal-meta//journal-title")
    return dict(pmid=aid("pmid"), doi=(aid("doi") or "").lower() or None, pmcid=aid("pmcid") or aid("pmc"),
                title=_text(title_el) if title_el is not None else None,
                journal=_text(jt) if jt is not None else None, year=year,
                license=(lic.get(XLINK + "href") or _text(lic)[:300]) if lic is not None else None, n_refs=refs_n)


def parse_jats(xml: bytes) -> Parsed:
    root = etree.fromstring(xml)
    if root.tag != "article":
        inner = root.find(".//article")
        root = inner if inner is not None else root
    refs = []
    for ref in root.iter("ref"):
        for lab in ref.findall("label"):
            lab.getparent().remove(lab)
        t = _text(ref)
        if t:
            refs.append(t)
    meta = _meta(root, len(refs))
    abstracts = [_block_text(a) or _text(a) for a in root.findall(".//article-meta/abstract")
                 if a.get("abstract-type") not in ("graphical", "toc")]
    etree.strip_elements(root, *DROP, with_tail=False)

    buckets = {"introduction": [], "body": [], "discussion": [], "back_matter": []}
    body = root.find("body")
    if body is not None:
        for child in body:
            if child.tag == "sec":
                buckets[classify_section(child)].append(_block_text(child))
            elif child.tag == "p":
                buckets["body"].append(_text(child))
    back = root.find("back")
    if back is not None:
        buckets["back_matter"].extend(_block_text(c) or _text(c) for c in back)
    sections = {k: "\n".join(t for t in v if t) for k, v in buckets.items()}
    sections["title"] = meta["title"] or ""
    sections["abstract"] = "\n".join(a for a in abstracts if a)
    return Parsed(meta=meta, sections=sections, refs=refs)

"""Parse a Landscape of Consciousness theory page into description text and references.

Two reference layouts exist on the site:
  A  plain-text <p> citations under a "References" heading inside div.sanity-content
  B  structured <div> entries inside section#reference-section
"""
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

UI_LABELS = {"google scholar", "view at publisher", "view  at publisher", "view in scopus",
             "view pdf", "view article", "crossref", "journal", "pubmed", "view at pubmed"}
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>|]+", re.I)
YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})[a-z]?\b")
PUBLISHER_RE = re.compile(r"\b(Press|Books|Publishers?|Publishing|Verlag|Routledge|Springer|Wiley|"
                          r"Blackwell|Penguin|Basic Books|Bloomsbury|Imprint|Academic)\b", re.I)
NONARTICLE_HOSTS = {"wikipedia.org": "wikipedia", "closertotruth.com": "video/site",
                    "plato.stanford.edu": "encyclopedia", "nautil.us": "magazine",
                    "templetonworldcharity.org": "web page"}


@dataclass
class Ref:
    raw_text: str
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    notes: list[str] = field(default_factory=list)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _doi_from(text: str, hrefs: list[str]) -> str | None:
    for src in [*hrefs, text]:
        m = DOI_RE.search(src or "")
        if m:
            return m.group(0).rstrip(".,;)").lower()
    return None


def _flag_nonarticle(ref: Ref, hrefs: list[str], has_vol_pages: bool) -> None:
    for h in hrefs:
        for host, why in NONARTICLE_HOSTS.items():
            if host in h and f"non_article:{why}" not in ref.notes:
                ref.notes.append(f"non_article:{why}")
    venue = ref.journal or ""
    if not has_vol_pages and PUBLISHER_RE.search(venue):
        ref.notes.append("book")
    elif not has_vol_pages and not ref.doi and venue and not re.search(r"\d", venue) and ref.journal:
        ref.notes.append("non_article:no_volume_or_pages")


JOURNAL_CUT_RE = re.compile(r"\s*(?:,\s*(?=\d|Article|vol)|\s+\d+\s*\(|\s+\d+\s*$|\.\s*$)", re.I)


def journal_name(venue: str | None) -> str | None:
    """Best-effort journal/publisher name: the venue string up to the first volume/page token."""
    if not venue:
        return None
    return JOURNAL_CUT_RE.split(venue, maxsplit=1)[0].strip(" ,.;") or venue


def description_text(soup: BeautifulSoup) -> str:
    """Main article body (sanity-content, References block removed) + Key Takeaways bullets."""
    parts = []
    kt = soup.find(lambda t: t.name == "h2" and t.get_text(strip=True) == "Key Takeaways")
    if kt:
        box = kt
        while box is not None and not box.find("ul"):
            box = box.parent
        box = box or kt.parent
        parts.append(_clean(box.get_text(" ", strip=True)))
    sc = soup.find("div", class_="sanity-content")
    if sc:
        body = BeautifulSoup(str(sc), "lxml")
        hdr = next((h for h in body.find_all(["h2", "h3"]) if h.get_text(strip=True) == "References"), None)
        if hdr:
            for el in list(hdr.find_all_next()):
                el.decompose()
            hdr.decompose()
        parts.append(_clean(body.get_text(" ", strip=True)))
    return "\n\n".join(p for p in parts if p)


def _parse_format_b(entry) -> Ref:
    spans = entry.find_all("span", recursive=False)
    label = _clean(spans[0].get_text()) if spans else ""
    authors = _clean(spans[1].get_text()) if len(spans) > 1 else None
    sub = entry.find("div", class_="pl-4")
    kids = sub.find_all("div", recursive=False) if sub else []
    title = _clean(kids[0].get_text()) if kids else None
    venue = _clean(kids[1].get_text()) if len(kids) > 2 or (len(kids) > 1 and not kids[1].find("a")) else None
    anchors = entry.find_all("a")
    hrefs = [a.get("href", "") for a in anchors]
    kept = [_clean(a.get_text()) for a in anchors if _clean(a.get_text()).lower() not in UI_LABELS]
    raw = " | ".join(x for x in [label, authors, title, venue, *kept] if x)
    ym = YEAR_RE.search(label)
    ref = Ref(raw_text=raw, title=title, authors=authors.strip(" ,") if authors else None,
              year=int(re.match(r"\d{4}", ym.group(0)).group(0)) if ym else None, journal=journal_name(venue),
              doi=_doi_from(raw, hrefs))
    has_vol = bool(venue and re.search(r"\d", venue))
    _flag_nonarticle(ref, hrefs, has_vol)
    if not title:
        ref.notes.append("parse:no_title")
    return ref


YEAR_PAREN_RE = re.compile(r"\((\d{4})[a-z]?(?:\s*[\u2013-]\s*\d{2,4})?\)")


def _parse_format_a(p) -> Ref:
    """Plain-text citation. Handles quoted-title style (Champagne), APA with <em> titles or
    journals (Peirce) and the 'Label, 2010. Authors, Title. Venue' style (Sebastian)."""
    raw = _clean(p.get_text(" ", strip=True))
    raw = re.sub(r"\s+([,.;:)])", r"\1", raw)
    hrefs = [a.get("href", "") for a in p.find_all("a")]
    em = p.find("em")
    em_text = _clean(em.get_text()) if em else None
    ref = Ref(raw_text=raw, doi=_doi_from(raw, hrefs))
    has_vol = bool(re.search(r"\bvol\.|\bpp?\.|\bno\.\s*\d|\d+\(\d+\)|,\s*\d+,\s*\d+", raw))

    strong = p.find("strong")
    if strong:  # label style
        label = _clean(strong.get_text())
        ym = YEAR_RE.search(label)
        ref.year = int(re.match(r"\d{4}", ym.group(0)).group(0)) if ym else None
        ref.notes.append("parse:label_style_fields_unparsed")
        _flag_nonarticle(ref, hrefs, has_vol)
        return ref

    ym = YEAR_PAREN_RE.search(raw)
    if ym:
        ref.year = int(ym.group(1))
        ref.authors = raw[: ym.start()].strip(" ,")
    elif "(n.d.)" in raw:
        ref.authors = raw.split("(n.d.)")[0].strip(" ,")
        ref.notes.append("parse:no_year(n.d.)")
    else:
        ref.notes.append("parse:no_year")
    rest = raw[ym.end():].lstrip(". ") if ym else raw
    qm = re.search(r"[\u201c\"](.+?)[\u201d\"]", raw)
    if qm:                                  # quoted title; <em> is the journal
        ref.title, ref.journal = qm.group(1).strip(" .,"), em_text
        if re.match(r"\s*In\s", raw[qm.end():]):
            ref.journal = None
            ref.notes.append("book_chapter")
        else:
            _flag_nonarticle(ref, hrefs, has_vol)
    elif em_text and rest.startswith(em_text):   # italic right after year: a book/report
        ref.title = em_text
        ref.notes.append("book")
    elif re.search(r"\bIn\s.+\(Eds?\.\)", rest):      # chapter in an edited volume
        ref.title = re.split(r"\.\s+In\s", rest, maxsplit=1)[0].strip(" .")
        ref.notes.append("book_chapter")
    elif em_text:                           # plain title, italic journal
        ref.title = rest.split(em_text)[0].strip(" .,")
        ref.journal = em_text
        _flag_nonarticle(ref, hrefs, has_vol)
    else:
        ref.title = re.split(r"\.\s", rest, maxsplit=1)[0].strip(" .")
        ref.notes.append("parse:no_markup_title_approx")
        _flag_nonarticle(ref, hrefs, has_vol)
    return ref


def parse_references(soup: BeautifulSoup) -> list[Ref]:
    refs: list[Ref] = []
    sec = soup.find("section", id="reference-section")
    if sec:
        box = sec.find("div", class_="space-y-4")
        refs += [_parse_format_b(e) for e in (box.find_all("div", recursive=False) if box else [])]
    sc = soup.find("div", class_="sanity-content")
    hdr = next((h for h in (sc.find_all(["h2", "h3"]) if sc else []) if h.get_text(strip=True) == "References"), None)
    if hdr:
        for el in hdr.find_all_next():
            if el.name in ("h2", "h3"):
                break
            if el.name == "p" and el.get_text(strip=True):
                refs.append(_parse_format_a(el))
    return refs


def parse_page(html: str) -> tuple[str, list[Ref]]:
    soup = BeautifulSoup(html, "lxml")
    return description_text(soup), parse_references(soup)

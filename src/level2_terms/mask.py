"""Term-masking utility for the Level 3 term-masked retrieval test.

Blanks, in a paper's text, every strong term and close_term (and, by default, every abbreviation such as GWT/IIT,
which would leak the theory just as well) of the chosen theories. Matching uses exactly the scanner's regexes, so
anything the scanner would count is masked. NOT masked by default: `adjacent` terms (they are legitimate
conceptual signal for Level 3), in-text author-year citations (opt in with mask_author_year=True) and the
reference list (callers should not embed it anyway).

    mask_text(text, theories=None)        theories=None masks every theory's terms
    mask_sections(sections, ...)          dict of section -> masked text
    mask_paper(conn, pmcid, ...)          load from SQLite and mask
    leaks(text, ...)                      remaining maskable hits (should be [] after masking)
"""
import re

from src.level2_terms.terms import Terms, load_terms, term_regex, _wrap

PLACEHOLDER = "[MASK]"
_cache: dict[tuple, tuple[re.Pattern | None, re.Pattern | None, re.Pattern | None]] = {}


def _compile(terms: Terms, theories: tuple, tiers: tuple, abbreviations: bool, author_year: bool):
    ck = (terms.terms_hash, theories, tiers, abbreviations, author_year)
    if ck in _cache:
        return _cache[ck]
    keys = theories or tuple(terms.theories)
    words, abbrs, cites = set(), set(), []
    for k in keys:
        th = terms.theories[k]
        words.update(term for term, tier in th.main_groups.values() if tier in tiers)
        if abbreviations:
            abbrs.update(th.abbr_groups.values())
        if author_year:
            cites += [rx.pattern.replace("(?P<y>", "(?:") for rx, _ in th.intext_rx]
    w = sorted(words, key=len, reverse=True)
    rx_w = re.compile(_wrap("|".join(term_regex(t) for t in w)), re.I) if w else None
    rx_a = re.compile(_wrap("|".join(re.escape(a) for a in sorted(abbrs, key=len, reverse=True)))) if abbrs else None
    rx_c = re.compile("|".join(f"(?:{c})" for c in cites), re.I) if cites else None
    _cache[ck] = (rx_w, rx_a, rx_c)
    return _cache[ck]


def mask_text(text: str, theories: list[str] | None = None, terms: Terms | None = None, tiers=("strong", "close_term"),
              abbreviations: bool = True, mask_author_year: bool = False, replacement: str = PLACEHOLDER) -> str:
    terms = terms or load_terms()
    rxs = _compile(terms, tuple(theories or ()), tuple(tiers), abbreviations, mask_author_year)
    for rx in rxs:
        if rx is not None:
            text = rx.sub(replacement, text)
    return text


def mask_sections(sections: dict[str, str], **kw) -> dict[str, str]:
    kw.setdefault("terms", load_terms())
    return {k: mask_text(v, **kw) for k, v in sections.items()}


def mask_paper(conn, pmcid: str, **kw) -> dict[str, str]:
    secs = {r["section"]: r["text"] for r in conn.execute("SELECT section, text FROM paper_sections WHERE pmcid=?", (pmcid,))}
    return mask_sections(secs, **kw)


def leaks(text: str, theories: list[str] | None = None, terms: Terms | None = None, **kw) -> list[str]:
    """Maskable hits still present in `text` (empty list = fully masked)."""
    terms = terms or load_terms()
    kw.pop("replacement", None)
    tiers = kw.get("tiers", ("strong", "close_term"))
    rxs = _compile(terms, tuple(theories or ()), tuple(tiers), kw.get("abbreviations", True), kw.get("mask_author_year", False))
    return [m.group(0) for rx in rxs if rx is not None for m in rx.finditer(text)]

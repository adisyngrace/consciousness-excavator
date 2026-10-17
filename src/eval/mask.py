"""Step 1 of prompt 05: neutral masking of a theory's terms and landmark authors in a positive paper's text.

Masking = DELETION (no [MASK] token, which would be a distinctive artifact the encoder could pick up on). Removed:
  * the theory's strong, close_term and abbreviation terms (the weak tier is a subset of strong), using the Level 2
    regexes so anything the scanner counts is removed;
  * the theory's landmark author surnames (terms.yaml `landmark_refs`), including in-text citations such as
    "Dehaene and Naccache, 2001", "(Naccache and Dehaene, 2001)", "Baars et al. (1998)" and possessives ("Baars's").
    Surnames that are ordinary English words (AMBIGUOUS_BARE) are removed only inside citations.
Leftover punctuation (empty brackets, doubled spaces, space before a comma) is tidied; `leaks` re-checks.

    mask_for_theory(text, "global_workspace")  ->  masked text
    leaks_for_theory(text, "global_workspace") ->  list of remaining hits ([] expected)
"""
import re
from functools import lru_cache

from src.level2_terms import mask as l2mask
from src.level2_terms.terms import load_terms

AMBIGUOUS_BARE = {"Short"}
_NAME = r"[A-Z][\w’'\-]+"
_YEAR = r"(?:1[89]\d\d|20[0-2]\d)[a-z]?"


@lru_cache(maxsize=None)
def _surnames(theory: str) -> tuple[str, ...]:
    return tuple(sorted({lm.surname for lm in load_terms().theories[theory].landmarks}, key=len, reverse=True))


@lru_cache(maxsize=None)
def _patterns(theory: str) -> tuple[re.Pattern | None, re.Pattern | None]:
    names = _surnames(theory)
    if not names:
        return None, None
    esc = lambda ns: "|".join(re.escape(n).replace("ø", "[øo]") for n in ns)
    bare = [n for n in names if n not in AMBIGUOUS_BARE]
    amb = [n for n in names if n in AMBIGUOUS_BARE]
    tail = rf"(?:\s+(?:and|&)\s+{_NAME})?(?:\s+et\s+al\.?)?"
    ys = rf"{_YEAR}(?:\s*[,;]\s*{_YEAR})*"
    year = rf"(?:\s*,\s*{ys}|\s*\(\s*{ys}\s*\))"          # "Baars, 1988"  or  "Baars (1988)"; never eats an enclosing ")"
    pre = rf"(?:(?<!\w){_NAME}\s+(?:and|&)\s+)?"
    sn = lambda ns: rf"(?<!\w)(?:{esc(ns)})(?:ean|ian)?(?:['’]s)?(?!\w)"
    parts = []
    if bare:
        parts.append(rf"{pre}{sn(bare)}{tail}(?:{year})?")
    if amb:
        parts.append(rf"{pre}{sn(amb)}{tail}{year}")      # ambiguous surnames: only with a year
    return re.compile("|".join(parts)), None


def _tidy(text: str) -> str:
    text = re.sub(r"\(\s*[,;]?\s*\)|\[\s*[,;]?\s*\]", "", text)           # emptied brackets
    text = re.sub(r"\(\s*(?:[,;]\s*)+", "(", text)
    text = re.sub(r"(?:\s*[,;])+\s*\)", ")", text)
    text = re.sub(r"([,;])(?:\s*[,;])+", r"\1", text)
    text = re.sub(r"\s+([,.;:)\]])", r"\1", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    return re.sub(r"[ \t]{2,}", " ", text)


def mask_for_theory(text: str, theory: str) -> str:
    out = l2mask.mask_text(text, [theory], replacement="")
    cite_rx, bare_rx = _patterns(theory)
    if cite_rx:
        out = cite_rx.sub("", out)       # citations incl. unambiguous bare surnames (cite pattern covers sn alone)
    if bare_rx:
        out = bare_rx.sub("", out)
    return _tidy(out)


def leaks_for_theory(text: str, theory: str) -> list[str]:
    found = l2mask.leaks(text, [theory])
    names = [n for n in _surnames(theory) if n not in AMBIGUOUS_BARE]
    if names:
        rx = re.compile(rf"(?<!\w)(?:{'|'.join(re.escape(n).replace('ø', '[øo]') for n in names)})(?!\w)")
        found += [m.group(0) for m in rx.finditer(text)]
    return found

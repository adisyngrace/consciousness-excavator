"""Load src/terms.yaml and compile it into regexes shared by the scanner, the masking utility and the query API.

Matching rules (documented once, here):
  * strong / close_term / adjacent terms: case-insensitive, whole word. Spaces and hyphens in a term match each
    other ("free energy principle" = "free-energy principle"), a trailing plural "s"/"es" is optional, "'" matches
    both apostrophes, and theater/theatre are interchangeable.
  * abbreviations: case-sensitive, whole word.
  * All strong + close_term + adjacent terms of one theory go into ONE alternation, longest term first, so a span
    is attributed to its longest term ("global workspace theory", not also "global workspace") and a strong term
    never double-counts as an adjacent one ("integrated information theory" vs "integrated information").
  * excluded_generic terms are never compiled: they are never counted.
"""
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TERMS_PATH = Path(__file__).resolve().parents[1] / "terms.yaml"
COUNTED_SECTIONS = ("title", "abstract", "introduction", "body", "discussion")   # where a hit can count
SCAN_SECTIONS = COUNTED_SECTIONS + ("back_matter",)                                 # back matter: recorded only
TIERS_MAIN = ("strong", "close_term", "adjacent")

_SEP = r"[\s\-‐-―]+"
_VARIANTS = (("theater", r"theat(?:er|re)"),)


def term_regex(term: str, plural: bool = True) -> str:
    """Regex source (no flags, no boundaries) for one term."""
    tokens = [t for t in re.split(r"[\s\-‐-―]+", term.strip()) if t]
    out = []
    for i, tok in enumerate(tokens):
        rx = re.escape(tok).replace("'", "['’]")
        for plain, alt in _VARIANTS:
            if tok.lower() == plain:
                rx = alt
        if plural and i == len(tokens) - 1 and not tok.lower().endswith("s"):
            rx += r"(?:s|es)?"
        out.append(rx)
    return _SEP.join(out)


def _wrap(alts: str) -> str:
    return rf"(?<!\w)(?:{alts})(?!\w)"


@dataclass
class Landmark:
    surname: str
    year: int
    title_hint: str | None = None

    @property
    def key(self) -> str:
        return f"{self.surname} {self.year}"


@dataclass
class TheoryPatterns:
    key: str
    name: str
    main_rx: re.Pattern | None
    main_groups: dict[str, tuple[str, str]]          # group name -> (term, tier)
    abbr_rx: re.Pattern | None
    abbr_groups: dict[str, str]
    landmarks: list[Landmark]
    ref_rx: list[tuple[re.Pattern, re.Pattern, Landmark]] = field(default_factory=list)    # (surname, year, lm)
    intext_rx: list[tuple[re.Pattern, dict[str, Landmark]]] = field(default_factory=list)   # per surname
    strong_terms: list[str] = field(default_factory=list)
    needs_corroboration: set[str] = field(default_factory=set)


@dataclass
class Terms:
    theories: dict[str, TheoryPatterns]
    domain_rx: re.Pattern
    domain_min: int
    terms_hash: str

    def by_name(self, name: str) -> TheoryPatterns:
        if name in self.theories:
            return self.theories[name]
        for t in self.theories.values():
            if t.name == name:
                return t
        raise KeyError(f"unknown theory {name!r}")


def _surname_rx(surname: str) -> str:
    return re.escape(surname).replace("ø", "[øo]")


def _compile_theory(key: str, spec: dict) -> TheoryPatterns:
    entries: list[tuple[str, str]] = []
    for tier in TIERS_MAIN:
        entries += [(t, tier) for t in spec.get(tier) or []]
    entries.sort(key=lambda e: -len(e[0]))
    groups, alts = {}, []
    for i, (term, tier) in enumerate(entries):
        g = f"g{i}"
        groups[g] = (term, tier)
        alts.append(f"(?P<{g}>{term_regex(term)})")
    main = re.compile(_wrap("|".join(alts)), re.I) if alts else None

    abbrs = sorted(spec.get("abbreviation") or [], key=len, reverse=True)
    agroups = {f"a{i}": a for i, a in enumerate(abbrs)}
    abbr = re.compile(_wrap("|".join(f"(?P<{g}>{re.escape(a)})" for g, a in agroups.items()))) if abbrs else None

    lms = [Landmark(str(d["surname"]), int(d["year"]), d.get("title_hint")) for d in spec.get("landmark_refs") or []]
    ref_rx = [(re.compile(_wrap(_surname_rx(lm.surname)), re.I),
               re.compile(rf"(?<!\d){lm.year}[a-z]?(?![\d])"), lm) for lm in lms]
    by_surname: dict[str, dict[str, Landmark]] = {}
    for lm in lms:
        by_surname.setdefault(lm.surname, {})[str(lm.year)] = lm
    intext = []
    for sn, years in by_surname.items():
        cite = (rf"(?<!\w){_surname_rx(sn)}(?!\w)(?:\s+(?:and|&)\s+[A-Z][\w’'\-]+)?(?:\s+et\s+al\.?)?"
                rf"[\s,;(\[]{{0,3}}(?P<y>{'|'.join(years)})[a-z]?(?!\d)")
        intext.append((re.compile(cite, re.I), years))
    return TheoryPatterns(key, spec.get("name", key), main, groups, abbr, agroups, lms, ref_rx, intext,
                          list(spec.get("strong") or []), set(spec.get("needs_corroboration") or []))


def load_terms(path: Path = TERMS_PATH) -> Terms:
    raw = path.read_text()
    doc = yaml.safe_load(raw)
    theories = {k: _compile_theory(k, v) for k, v in doc["theories"].items()}
    dom = sorted(set(doc["domain_context"]), key=len, reverse=True)
    domain_rx = re.compile(_wrap("|".join(re.escape(w) for w in dom)), re.I)
    return Terms(theories, domain_rx, int(doc.get("domain_context_min", 2)), hashlib.sha256(raw.encode()).hexdigest()[:16])

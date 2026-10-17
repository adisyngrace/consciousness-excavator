"""Silver sets: Level 2 direct-mention papers per theory, in the subsets the evaluation and report use.

  all            direct_mention = 1 (the definition in scan.py)
  exclusive      direct mention of this theory and of no other theory (overlap papers removed)
  primary        strong term in the title or abstract, OR >= PRIMARY_MIN_STRENGTH strong-term mentions
  consciousness  silver papers that also use consciousness/awareness vocabulary: in the title or abstract, OR
                 >= CONSC_MIN occurrences in the text (stricter subset; motivated by predictive processing, whose
                 direct mentions are mostly computational neuroscience)
  consciousness_any   >= 1 occurrence (lenient version of the same)
Reference lists and back matter are never searched.
"""
import re

from src import db
from src.level2_terms.terms import COUNTED_SECTIONS

PRIMARY_MIN_STRENGTH = 3
CONSC_MIN = 3
CONSC_RX = re.compile(r"(?<!\w)(?:(?:un|non)?conscious(?:ness)?|awareness|sentien(?:ce|t)|phenomenal|qualia|"
                      r"subjective\s+experiences?)(?!\w)", re.I)    # bare "aware" omitted: far too generic
_cache: dict[str, tuple[int, int]] = {}


def consciousness_counts(conn, pmcid: str) -> tuple[int, int]:
    """(occurrences in title+abstract, occurrences in all counted sections)."""
    if pmcid not in _cache:
        ta = total = 0
        for r in conn.execute("SELECT section, text FROM paper_sections WHERE pmcid=?", (pmcid,)):
            if r["section"] in COUNTED_SECTIONS:
                n = len(CONSC_RX.findall(r["text"]))
                total += n
                ta += n if r["section"] in ("title", "abstract") else 0
        _cache[pmcid] = (ta, total)
    return _cache[pmcid]


def silver(conn, theory_key: str, subset: str = "all") -> set[str]:
    rows = conn.execute("""SELECT f.pmcid, f.mention_strength, f.title_or_abstract_hit,
        (SELECT COUNT(*) FROM paper_flags g WHERE g.pmcid=f.pmcid AND g.direct_mention=1) AS n_theories
        FROM paper_flags f WHERE f.theory=? AND f.direct_mention=1""", (theory_key,)).fetchall()
    out = set()
    for r in rows:
        if subset == "all":
            keep = True
        elif subset == "exclusive":
            keep = r["n_theories"] == 1
        elif subset == "primary":
            keep = bool(r["title_or_abstract_hit"]) or r["mention_strength"] >= PRIMARY_MIN_STRENGTH
        elif subset in ("consciousness", "consciousness_any"):
            ta, tot = consciousness_counts(conn, r["pmcid"])
            keep = (ta > 0 or tot >= CONSC_MIN) if subset == "consciousness" else tot >= 1
        else:
            raise ValueError(subset)
        if keep:
            out.add(r["pmcid"])
    return out

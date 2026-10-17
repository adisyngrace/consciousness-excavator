"""Level 1, step 3: resolve each LoC reference to DOI / PMCID / PMID and a status.

Per reference:
  1. no DOI on the page -> Crossref bibliographic search, accepted only if title similarity and
     year both agree (score stored in match_score)
  2. any DOI -> Europe PMC lookup for PMCID/PMID and open-access full-text availability
Statuses: resolved_fulltext | resolved_no_fulltext | doi_only | unresolved | non_article
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass

from rapidfuzz import fuzz

from src import db, http

CROSSREF = "https://api.crossref.org/works"
EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TITLE_MIN = 88          # token_sort_ratio, parsed title vs Crossref title
RAW_MIN = 92            # partial_ratio of Crossref title inside raw text (when no parsed title)
RAW_MIN_NOYEAR = 95
STRONG_NONARTICLE = ("video/site", "wikipedia", "encyclopedia", "magazine", "web page")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (s or "").lower())).strip()


@dataclass
class Candidate:
    doi: str
    title: str
    year: int | None
    score: float
    reason: str = ""


def _cand_year(item: dict) -> int | None:
    for k in ("issued", "published", "published-print", "published-online", "created"):
        parts = (item.get(k) or {}).get("date-parts") or [[None]]
        if parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def score_candidate(item: dict, title: str | None, year: int | None, raw: str) -> Candidate | None:
    titles = item.get("title") or []
    if not titles or not item.get("DOI"):
        return None
    full = ": ".join(titles) if len(titles) > 1 else titles[0]
    cy = _cand_year(item)
    if title:
        score = max(fuzz.token_sort_ratio(norm(title), norm(t)) for t in (titles[0], full))
        need = TITLE_MIN
    else:
        score = fuzz.partial_ratio(norm(titles[0]), norm(raw)) if len(norm(titles[0])) >= 15 else 0
        need = RAW_MIN if year else RAW_MIN_NOYEAR
    reason = ""
    if score < need:
        reason = f"title_similarity {score:.0f}<{need}"
    elif year and cy and abs(year - cy) > 1:
        reason = f"year_mismatch {year} vs {cy}"
    return Candidate(item["DOI"].lower(), full, cy, float(score), reason)


def crossref_lookup(raw: str, title: str | None, year: int | None, email: str) -> tuple[Candidate | None, str]:
    query = raw.replace(" | ", ", ")
    r = http.get(CROSSREF, params={"query.bibliographic": query[:600], "rows": 5, "mailto": email,
                                   "select": "DOI,title,issued,published,type"})
    if r["status"] != 200:
        return None, f"crossref_http_{r['status']}"
    items = json.loads(r["text"])["message"]["items"]
    if not items:
        return None, "crossref_no_results"
    cands = [c for c in (score_candidate(i, title, year, raw) for i in items) if c]
    if not cands:
        return None, "crossref_results_without_title"
    ok = [c for c in cands if not c.reason]
    if ok:
        return max(ok, key=lambda c: c.score), ""
    best = max(cands, key=lambda c: c.score)
    return None, f"crossref_rejected: best '{best.title[:60]}' ({best.year}) {best.reason}"


def europepmc_lookup(doi: str) -> tuple[dict | None, str]:
    r = http.get(EUROPEPMC, params={"query": f'DOI:"{doi}"', "format": "json", "resultType": "lite", "pageSize": 5})
    if r["status"] != 200:
        return None, f"europepmc_http_{r['status']}"
    for hit in json.loads(r["text"]).get("resultList", {}).get("result", []):
        if (hit.get("doi") or "").lower() == doi.lower():
            return hit, ""
    return None, "europepmc_not_found"


def fulltext_available(hit: dict) -> bool:
    return bool(hit.get("pmcid")) and hit.get("isOpenAccess") == "Y" and \
        "Y" in (hit.get("inEPMC"), hit.get("inPMC"))


def resolve_row(row, email: str) -> dict:
    """Returns column updates for one loc_references row."""
    notes = (row["notes"] or "")
    why: list[str] = []
    doi, source, score = row["doi"], None, None
    if doi:
        source = "loc_page"
    elif any(f"non_article:{k}" in notes for k in STRONG_NONARTICLE):
        return dict(resolution_status="non_article", resolution_source="loc_page", match_score=None,
                    resolve_notes="skipped Crossref: " + next(n for n in notes.split("; ") if n.startswith("non_article")))
    else:
        cand, reason = crossref_lookup(row["raw_text"], row["parsed_title"], row["parsed_year"], email)
        if cand:
            doi, source, score = cand.doi, "crossref", cand.score
        else:
            why.append(reason)

    out = dict(doi=doi, resolution_source=source, match_score=score, pmcid=None, pmid=None)
    if doi:
        hit, reason = europepmc_lookup(doi)
        if hit:
            out["pmcid"], out["pmid"] = hit.get("pmcid"), hit.get("pmid")
            out["resolution_status"] = "resolved_fulltext" if fulltext_available(hit) else "resolved_no_fulltext"
            why.append(f"europepmc: OA={hit.get('isOpenAccess')} inEPMC={hit.get('inEPMC')} src={hit.get('source')}")
            if not (out["pmcid"] or out["pmid"]):
                out["resolution_status"] = "doi_only"   # indexed (e.g. preprint) but no PMC/PubMed ID
        else:
            out["resolution_status"] = "doi_only"
            why.append(reason)
    else:
        bookish = re.search(r"\bbook\b|book_chapter|non_article", notes)
        out["resolution_status"] = "non_article" if bookish else "unresolved"
        out["resolution_source"] = None
    out["resolve_notes"] = "; ".join(why) or None
    return out


def run(force: bool = False, limit: int | None = None) -> None:
    conn = db.connect()
    email = http.os.getenv("CONTACT_EMAIL", "")
    if not email:
        sys.exit("CONTACT_EMAIL missing from .env (needed for the Crossref polite pool)")
    where = "" if force else "WHERE resolution_status IS NULL"
    rows = conn.execute(f"SELECT * FROM loc_references {where} ORDER BY id").fetchall()[:limit]
    print(f"resolving {len(rows)} references")
    for i, row in enumerate(rows, 1):
        upd = resolve_row(row, email)
        cols = ", ".join(f"{k}=?" for k in upd)
        conn.execute(f"UPDATE loc_references SET {cols} WHERE id=?", (*upd.values(), row["id"]))
        conn.commit()
        if i % 20 == 0:
            print(f"  {i}/{len(rows)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-resolve rows that already have a status")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    run(a.force, a.limit)

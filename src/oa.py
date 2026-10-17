"""Level 1 addendum: open-access full-text discovery for every reference that has a DOI.

Unpaywall is the primary source (publisher + repository copies, e.g. PhilArchive, arXiv, OSF, Zenodo).
OpenAlex is the fallback for the OA link and the source of abstracts (backup seeds).
Resolution statuses are NOT changed; results go in separate columns. Idempotent: only rows with
oa_status IS NULL are processed (use --force to redo).
"""
import argparse
import json
import os
import sys

from src import db, http

UNPAYWALL = "https://api.unpaywall.org/v2/"
OPENALEX = "https://api.openalex.org/works/doi:"


def pick_location(unpaywall: dict) -> tuple[str | None, str | None, dict | None]:
    """(url, kind, location): a PDF link from any location (best first) else the best landing page."""
    best = unpaywall.get("best_oa_location") or {}
    locs = [best, *(unpaywall.get("oa_locations") or [])]
    for loc in locs:
        if loc and loc.get("url_for_pdf"):
            return loc["url_for_pdf"], "pdf", loc
    if best.get("url"):
        return best["url"], "landing", best
    return None, None, None


def abstract_from_index(idx: dict | None) -> str | None:
    if not idx:
        return None
    words = {pos: w for w, positions in idx.items() for pos in positions}
    return " ".join(words[i] for i in sorted(words)) or None


def check_doi(doi: str, email: str) -> dict:
    out = dict(oa_status=None, fulltext_url=None, fulltext_kind=None, fulltext_source=None,
               oa_host_type=None, oa_license=None, oa_version=None, abstract=None)
    notes = []

    u = http.get(UNPAYWALL + doi, params={"email": email})
    if u["status"] == 200:
        data = json.loads(u["text"])
        url, kind, loc = pick_location(data)
        out["oa_status"] = data.get("oa_status") or ("closed" if not data.get("is_oa") else "unknown")
        if url:
            out.update(fulltext_url=url, fulltext_kind=kind, fulltext_source="unpaywall",
                       oa_host_type=loc.get("host_type"), oa_license=loc.get("license"), oa_version=loc.get("version"))
    elif u["status"] == 404:
        notes.append("unpaywall: DOI not found")
    else:
        raise RuntimeError(f"unpaywall HTTP {u['status']}")

    o = http.get(OPENALEX + doi, params={"mailto": email,
                 "select": "open_access,best_oa_location,locations,abstract_inverted_index"})
    if o["status"] == 200:
        w = json.loads(o["text"])
        out["abstract"] = abstract_from_index(w.get("abstract_inverted_index"))
        if not out["fulltext_url"]:
            for loc in [w.get("best_oa_location"), *(w.get("locations") or [])]:
                if loc and loc.get("is_oa") and (loc.get("pdf_url") or loc.get("landing_page_url")):
                    out.update(fulltext_url=loc.get("pdf_url") or loc["landing_page_url"],
                               fulltext_kind="pdf" if loc.get("pdf_url") else "landing",
                               fulltext_source="openalex", oa_host_type=(loc.get("source") or {}).get("type"),
                               oa_license=loc.get("license"), oa_version=loc.get("version"))
                    out["oa_status"] = (w.get("open_access") or {}).get("oa_status") or out["oa_status"] or "unknown"
                    break
    elif o["status"] == 404:
        notes.append("openalex: DOI not found")
    else:
        raise RuntimeError(f"openalex HTTP {o['status']}")

    if out["oa_status"] is None:
        out["oa_status"] = "not_found"
    out["oa_notes"] = "; ".join(notes) or None
    return out


def run(force: bool = False, limit: int | None = None) -> None:
    email = os.getenv("CONTACT_EMAIL") or sys.exit("CONTACT_EMAIL missing from .env")
    conn = db.connect()
    where = "doi IS NOT NULL" + ("" if force else " AND oa_status IS NULL")
    rows = conn.execute(f"SELECT id, doi FROM loc_references WHERE {where} ORDER BY id").fetchall()[:limit]
    print(f"checking OA for {len(rows)} DOIs")
    failures = 0
    for i, row in enumerate(rows, 1):
        try:
            upd = check_doi(row["doi"], email)
        except Exception as e:   # leave oa_status NULL so a re-run retries it
            failures += 1
            print(f"  FAIL id={row['id']} doi={row['doi']}: {e}", file=sys.stderr)
            continue
        cols = ", ".join(f"{k}=?" for k in upd)
        conn.execute(f"UPDATE loc_references SET {cols} WHERE id=?", (*upd.values(), row["id"]))
        conn.commit()
        if i % 20 == 0:
            print(f"  {i}/{len(rows)}")
    print(f"done, {failures} failures")


if __name__ == "__main__":
    import src.http  # noqa: F401  (loads .env)
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    run(a.force, a.limit)

"""Level 1, step 4: write reports/level1_resolution.md from the DB."""
from pathlib import Path

from src import db

OUT = Path(__file__).resolve().parent.parent / "reports" / "level1_resolution.md"
STATUSES = ["resolved_fulltext", "resolved_no_fulltext", "doi_only", "unresolved", "non_article"]
RESOLVED = ("resolved_fulltext", "resolved_no_fulltext", "doi_only")   # has a DOI
WINDOWS = [(1995, 2015), (1995, 2020), (1995, 2025)]
MIN_SEEDS = 15


def has_fulltext(r) -> bool:
    """Open full text by either route: Europe PMC OA, or an OA PDF link from Unpaywall/OpenAlex."""
    return r["resolution_status"] == "resolved_fulltext" or r["fulltext_kind"] == "pdf"


def reason(row) -> str:
    r = row["resolve_notes"] or ""
    if "year_mismatch" in r:
        return "Crossref found a same-title work in a different year (likely a reprint/edition): " + r.split("crossref_rejected: ")[-1][:90]
    if "title_similarity" in r:
        if "personal communication" in row["raw_text"].lower():
            return "personal communication, not a published work"
        return "no Crossref title close enough (likely not indexed, e.g. old/preprint/grey literature): " + r.split("best ")[-1][:90]
    return r or "no reason recorded"


def build() -> str:
    c = db.connect()
    L = ["# Level 1 resolution report", "",
         "Source: Landscape of Consciousness pages pooled per theory (see `src/config.py`). "
         "IDs from page DOIs, Crossref (title similarity + year) and Europe PMC; open-access copies from Europe PMC, Unpaywall and OpenAlex (DOI lookups only).", ""]
    summary = []
    for t in c.execute("SELECT id, name FROM theories ORDER BY id"):
        rows = c.execute("SELECT * FROM loc_references WHERE theory_id=?", (t["id"],)).fetchall()
        n = len(rows)
        cnt = {s: sum(r["resolution_status"] == s for r in rows) for s in STATUSES}
        ft = cnt["resolved_fulltext"]
        with_doi = sum(cnt[s] for s in RESOLVED)
        articleish = n - cnt["non_article"]
        L += [f"## {t['name']}", "", f"**Total references: {n}** (from {len({r['source_url'] for r in rows})} LoC pages)", "",
              "| Status | Count |", "|---|---|", *[f"| {s} | {cnt[s]} |" for s in STATUSES], "",
              f"- Open-access full text in Europe PMC: **{ft}** = {ft / n:.0%} of all references, "
              f"{ft / articleish:.0%} of non-`non_article` references, {ft / with_doi:.0%} of those with a DOI" if with_doi else "- no DOIs",
              f"- With any DOI: {with_doi} ({with_doi / n:.0%}); with PMID or PMCID: "
              f"{sum(bool(r['pmid'] or r['pmcid']) for r in rows)}",
              f"- Resolved via: page DOI {sum(r['resolution_source'] == 'loc_page' and r['doi'] is not None for r in rows)}, "
              f"Crossref {sum(r['resolution_source'] == 'crossref' for r in rows)}", ""]
        pdf = [r for r in rows if r["fulltext_kind"] == "pdf"]
        landing = [r for r in rows if r["fulltext_kind"] == "landing"]
        both = [r for r in rows if has_fulltext(r)]
        hosts = {}
        for r in pdf:
            hosts[r["oa_host_type"] or "?"] = hosts.get(r["oa_host_type"] or "?", 0) + 1
        L += ["Open-access full-text discovery (Europe PMC + Unpaywall/OpenAlex):", "",
              f"- **Full-text seeds (Europe PMC OA *or* OA PDF link): {len(both)}**",
              f"  - Europe PMC OA full text: {ft}; OA PDF link: {len(pdf)} ({', '.join(f'{k} {v}' for k, v in hosts.items()) or 'none'}); "
              f"overlap {len([r for r in pdf if r['resolution_status'] == 'resolved_fulltext'])}",
              f"  - Landing page only (not counted as seed): {len(landing)}",
              f"  - DOIs with no OA copy found: {sum(1 for r in rows if r['doi'] and not r['fulltext_url'])}",
              f"- Abstracts available (OpenAlex): {sum(bool(r['abstract']) for r in rows)} "
              f"({sum(bool(r['abstract']) and not has_fulltext(r) for r in rows)} of them for refs with no full text)", ""]
        # year distribution
        res = [r for r in rows if r["resolution_status"] in RESOLVED]
        fts = both
        L += ["Year distribution (parsed year from the LoC entry):", "",
              "| Window | Resolved (has DOI) | Full-text seeds |", "|---|---|---|"]
        for lo, hi in WINDOWS:
            f = lambda rs: sum(r["parsed_year"] is not None and lo <= r["parsed_year"] <= hi for r in rs)
            L.append(f"| {lo}-{hi} | {f(res)} | {f(fts)} |")
        L.append(f"| year missing | {sum(r['parsed_year'] is None for r in res)} | {sum(r['parsed_year'] is None for r in fts)} |")
        decades = {}
        for r in res:
            if r["parsed_year"]:
                d = r["parsed_year"] // 10 * 10
                decades[d] = decades.get(d, 0) + 1
        L += ["", "By decade (resolved): " + ", ".join(f"{d}s: {k}" for d, k in sorted(decades.items())), ""]
        # unresolved examples
        un = [r for r in rows if r["resolution_status"] == "unresolved"]
        L += [f"### Unresolved examples ({len(un)} unresolved in total; showing up to 10)", ""]
        L += [f"- `{r['raw_text'][:110]}` — {reason(r)}" for r in un[:10]] or ["- none"]
        na = [r for r in rows if r["resolution_status"] == "non_article"][:5]
        L += ["", "Sample `non_article` (books, chapters, videos, news; kept, not searched for full text):", ""]
        L += [f"- `{r['raw_text'][:100]}` — {r['notes'] or 'no DOI found'}" for r in na] or ["- none"]
        L.append("")
        flag = len(both) < MIN_SEEDS
        L += [f"> **{'FLAG' if flag else 'OK'}: {len(both)} full-text seed papers"
              f"{' (< ' + str(MIN_SEEDS) + '); needs backup seeds (abstracts, descriptions)' if flag else ''}.**", ""]
        summary.append((t["name"], n, len(both), ft, sum(bool(r['abstract']) and not has_fulltext(r) for r in rows), with_doi, flag))
    head = ["## Summary", "", "| Theory | Refs | Full-text seeds (any OA route) | of which Europe PMC | Extra abstract-only seeds | With DOI | Needs backup seeds |", "|---|---|---|---|---|---|---|"]
    head += [f"| {a} | {b} | {c_} | {d} | {e} | {f} | {'YES' if g else 'no'} |" for a, b, c_, d, e, f, g in summary]
    return "\n".join(L[:4] + head + [""] + L[4:])


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    text = build()
    OUT.write_text(text)
    print(text)

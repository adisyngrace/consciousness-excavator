"""Step 6: write reports/level2_terms.md (and reports/level2_overlap_papers.csv).

Precision comes from YOUR hand labels in reports/precision_audit_labels.csv (see labels.py); nothing is invented
or auto-applied. The original 83-hit sample is reports/level2_precision_audit.csv (not regenerated).
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from src import db
from src.level2_terms.labels import paper_repetition, per_term, per_theory_unique, read_labels, wilson
from src.level2_terms.silver import CONSC_MIN, PRIMARY_MIN_STRENGTH, silver
from src.level2_terms.terms import load_terms

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "level2_terms.md"
AUDIT = ROOT / "reports" / "level2_precision_audit.csv"
OVERLAP = ROOT / "reports" / "level2_overlap_papers.csv"
PARTS = ["seed", "candidate", "background", "random"]
AUDIT_N = 20


def per_term_hits(conn, key: str) -> list[tuple]:
    return conn.execute("""SELECT h.term, COUNT(DISTINCT h.pmcid) papers, SUM(h.count) total FROM term_hits h
                           JOIN paper_flags f ON f.pmcid=h.pmcid AND f.theory=h.theory
                           WHERE h.theory=? AND h.tier='strong' AND f.direct_mention=1 GROUP BY h.term
                           ORDER BY papers DESC""", (key,)).fetchall()


def build(conn) -> str:
    terms = load_terms()
    q = lambda sql, *a: conn.execute(sql, a).fetchall()
    n_corpus = q("SELECT COUNT(DISTINCT pmcid) FROM corpus_membership")[0][0]
    n_scanned = q("SELECT COUNT(DISTINCT pmcid) FROM paper_flags")[0][0]
    L = ["# Level 2: direct term mentions (1995-2015 corpus)", "",
         f"Corpus papers: **{n_corpus}**. Scanned with text: **{n_scanned}**. "
         f"No-text papers (logged, flags absent): **{n_corpus - n_scanned}**. terms.yaml hash `{terms.terms_hash}`.", "",
         "`direct_mention` = a strong term in title/abstract/intro/body/discussion AND >= "
         f"{terms.domain_min} distinct domain_context words (see `src/level2_terms/scan.py`). Close-term, adjacent, "
         "landmark-reference and in-text author-year hits are never mentions.", ""]
    nt = q("SELECT pmcid, note FROM scan_log WHERE status='no_text'")
    if nt:
        L += ["No-text papers: " + "; ".join(f"{r['pmcid']} ({r['note'][:60]})" for r in nt[:25]), ""]

    # ---- overview ----
    L += ["## 1. Overview per theory", "",
          "| Theory | direct_mention | by title/abstract | strong blocked by domain rule | close_term | adjacent | cites landmark (refs) | in-text author-year |",
          "|---|---|---|---|---|---|---|---|"]
    for k, th in terms.theories.items():
        r = q("""SELECT SUM(direct_mention), SUM(title_or_abstract_hit), SUM(strong_blocked_by_domain>0), SUM(close_term_hit),
                 SUM(adjacent_hit), SUM(cites_landmark>0), SUM(cites_author_year>0) FROM paper_flags WHERE theory=?""", k)[0]
        L.append(f"| {th.name} | " + " | ".join(str(x or 0) for x in r) + " |")

    # ---- direct mentions by part ----
    L += ["", "## 2. Direct-mention papers by corpus part", "",
          "A paper can sit in several parts. Share = flagged / papers in that part.", "",
          "| Theory | " + " | ".join(PARTS) + " |", "|---|" + "---|" * len(PARTS)]
    part_n = {p: q("SELECT COUNT(DISTINCT pmcid) FROM corpus_membership WHERE part=?", p)[0][0] for p in PARTS}
    for k, th in terms.theories.items():
        cells = []
        for p in PARTS:
            n = q("""SELECT COUNT(DISTINCT f.pmcid) FROM paper_flags f JOIN corpus_membership m ON m.pmcid=f.pmcid
                     WHERE f.theory=? AND f.direct_mention=1 AND m.part=?""", k, p)[0][0]
            cells.append(f"{n} ({100 * n / part_n[p]:.1f}%)" if part_n[p] else "0")
        L.append(f"| {th.name} | " + " | ".join(cells) + " |")
    L.append("| *papers in part* | " + " | ".join(str(part_n[p]) for p in PARTS) + " |")

    # ---- seed recall ----
    L += ["", "## 3. Seed recall", "",
          "Fraction of Level 1 seed papers in the corpus (part `seed`) that directly mention their own theory. "
          "Seeds that do not are early Level 3 examples."]
    tag_of = {th.name: k for k, th in terms.theories.items()}
    exp = q("""SELECT t.name, COUNT(*) FROM loc_references r JOIN theories t ON t.id=r.theory_id
               WHERE r.resolution_status='resolved_fulltext' AND r.parsed_year BETWEEN 1995 AND 2015 GROUP BY t.name""")
    L += ["", "Level 1 `resolved_fulltext` refs dated 1995-2015: " + (", ".join(f"{n}: {c}" for n, c in exp) or "none") +
          ". CLAUDE.md quotes 11 in total; check this against the `seed` rows below if the numbers disagree.", "",
          "| Theory | seeds in corpus | directly mention own theory | recall |", "|---|---|---|---|"]
    notmention = []
    for name, k in tag_of.items():
        seeds = q("SELECT DISTINCT pmcid FROM corpus_membership WHERE part='seed' AND tag=?", name)
        hit = 0
        for s in seeds:
            f = q("SELECT direct_mention FROM paper_flags WHERE pmcid=? AND theory=?", s[0], k)
            if f and f[0][0]:
                hit += 1
            else:
                p = q("SELECT title, year FROM papers WHERE pmcid=?", s[0])[0]
                notmention.append(f"- {name}: {s[0]} ({p['year']}) {p['title']}")
        L.append(f"| {name} | {len(seeds)} | {hit} | {f'{hit / len(seeds):.0%}' if seeds else 'n/a'} |")
    L += ["", "Seeds that do NOT directly mention their theory:", ""] + (notmention or ["- none"])

    # ---- strength distribution + primary subset ----
    sub = lambda k, name: silver(conn, k, name)
    L += ["", "## 4. Mention strength and the primary subset", "",
          "Strength = total strong-term mentions in title/abstract/intro/body/discussion. **Primary** = strong term in the "
          f"title or abstract, OR >= {PRIMARY_MIN_STRENGTH} strong-term mentions.", "",
          "| Theory | silver set (n) | strength 1 | 2 | 3-4 | 5-9 | 10-29 | 30+ | median | in title/abstract | primary (n) | primary % |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, th in terms.theories.items():
        s_ = sorted(r[0] for r in q("SELECT mention_strength FROM paper_flags WHERE theory=? AND direct_mention=1", k))
        b = Counter("1" if x == 1 else "2" if x == 2 else "3-4" if x <= 4 else "5-9" if x <= 9 else "10-29" if x <= 29 else "30+" for x in s_)
        ta = q("SELECT SUM(title_or_abstract_hit) FROM paper_flags WHERE theory=? AND direct_mention=1", k)[0][0] or 0
        pr = len(sub(k, "primary"))
        L.append(f"| {th.name} | {len(s_)} | " + " | ".join(str(b[c]) for c in ("1", "2", "3-4", "5-9", "10-29", "30+")) +
                 f" | {s_[len(s_) // 2] if s_ else '-'} | {ta} | {pr} | {100 * pr / len(s_):.0f}% |" if s_ else f"| {th.name} | 0 |")
    L += ["", "> **Panpsychism (n = 17) and Champagne's semiotic account (n = 3): the silver set is too small for "
          "quantitative claims.** Report recall/AUC for them as descriptive counts only, and treat any percentage as "
          "anecdotal. Champagne's three papers use the Peircean sense of the terms and none is about consciousness; "
          "that theory is effectively absent from the 1995-2015 open-access biomedical corpus.", ""]

    # ---- abbreviation noise ----
    L += ["## 5. Abbreviation ambiguity", "",
          "Papers using an abbreviation with no strong term of the same theory in the paper (`unconfirmed`, removed by the "
          "rule) versus confirmed. Per-abbreviation snippets to label: `reports/abbreviation_audit.md`.", "",
          "| Theory | abbreviations | papers confirmed | papers unconfirmed |", "|---|---|---|---|"]
    for k, th in terms.theories.items():
        if not th.abbr_groups:
            continue
        c = q("SELECT SUM(abbrev_confirmed>0), SUM(abbrev_unconfirmed>0) FROM paper_flags WHERE theory=?", k)[0]
        L.append(f"| {th.name} | {', '.join(th.abbr_groups.values())} | {c[0] or 0} | {c[1] or 0} |")

    # ---- overlap ----
    names = {k: t.name for k, t in terms.theories.items()}
    L += ["", "## 6. Overlap between theories", ""]
    multi = q("SELECT pmcid, n_theories, theories FROM multi_theory_papers ORDER BY n_theories DESC, pmcid")
    anyd = q("SELECT COUNT(DISTINCT pmcid) FROM paper_flags WHERE direct_mention=1")[0][0]
    L += [f"Corpus papers with direct_mention for **more than one** theory: **{len(multi)}** "
          f"({100 * len(multi) / n_scanned:.2f}% of {n_scanned} scanned; {100 * len(multi) / anyd:.1f}% of the {anyd} papers "
          "with any direct mention). They are flagged in the SQL view `multi_theory_papers` and listed in "
          "`reports/level2_overlap_papers.csv`.", "",
          "Pairwise counts:", "", "| | " + " | ".join(t.name.split()[0] for t in terms.theories.values()) + " |",
          "|---|" + "---|" * len(terms.theories)]
    for a, ta in terms.theories.items():
        cells = [str(q("""SELECT COUNT(*) FROM paper_flags x JOIN paper_flags y ON x.pmcid=y.pmcid
                          WHERE x.theory=? AND y.theory=? AND x.direct_mention=1 AND y.direct_mention=1""", a, b)[0][0])
                 for b in terms.theories]
        L.append(f"| {ta.name} | " + " | ".join(cells) + " |")
    L += ["", "Silver set with and without the overlapping papers:", "",
          "| Theory | silver set (all) | overlap papers | exclusive (overlap removed) | primary, exclusive |", "|---|---|---|---|---|"]
    for k, th in terms.theories.items():
        al, ex = sub(k, "all"), sub(k, "exclusive")
        L.append(f"| {th.name} | {len(al)} | {len(al) - len(ex)} | {len(ex)} | {len(ex & sub(k, 'primary'))} |")
    L += ["", "Overlap papers:", "", "| PMCID | year | theories (strength) | title |", "|---|---|---|---|"]
    ov_rows = []
    for m in multi:
        p = q("SELECT title, year FROM papers WHERE pmcid=?", m["pmcid"])[0]
        det = ", ".join(f"{names[r['theory']].split()[0]} ({r['mention_strength']})" for r in
                        q("SELECT theory, mention_strength FROM paper_flags WHERE pmcid=? AND direct_mention=1", m["pmcid"]))
        L.append(f"| {m['pmcid']} | {p['year']} | {det} | {p['title'][:80]} |")
        ov_rows.append({"pmcid": m["pmcid"], "year": p["year"], "n_theories": m["n_theories"], "theories": det, "title": p["title"]})
    with OVERLAP.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pmcid", "year", "n_theories", "theories", "title"])
        w.writeheader()
        w.writerows(ov_rows)

    # ---- consciousness-relevant subset ----
    L += ["", "## 7. Consciousness-relevant subset", "",
          "Most predictive-processing direct mentions are computational neuroscience, not consciousness science. The stricter "
          "subset keeps silver papers that use consciousness/awareness vocabulary (conscious(ness), unconscious, "
          f"awareness, sentience, phenomenal, qualia, subjective experience; bare 'aware' excluded) in the title/abstract OR "
          f">= {CONSC_MIN} times in the text. 'Any' is the lenient version (>= 1 occurrence). Computed for every theory for comparison.", "",
          "| Theory | silver set | consciousness-relevant (strict) | % | consciousness vocabulary, any | % |", "|---|---|---|---|---|---|"]
    for k, th in terms.theories.items():
        al, st, an = sub(k, "all"), sub(k, "consciousness"), sub(k, "consciousness_any")
        pc = lambda n: f"{100 * n / len(al):.0f}%" if al else "-"
        L.append(f"| {th.name} | {len(al)} | {len(st)} | {pc(len(st))} | {len(an)} | {pc(len(an))} |")
    k = "predictive_processing_fep"
    L += ["", f"Predictive Processing / FEP: the **PRIMARY** consciousness-relevant subset is the strict definition "
          f"(title/abstract, or >= {CONSC_MIN} occurrences): **{len(sub(k, 'consciousness'))}** of {len(sub(k, 'all'))} silver papers "
          f"({len(sub(k, 'consciousness') & sub(k, 'primary'))} also primary by strength). SECONDARY: lenient (>= 1 occurrence) "
          f"**{len(sub(k, 'consciousness_any'))}** and the full silver set **{len(sub(k, 'all'))}**. Report all three.", ""]

    # ---- weak mentions ----
    L += ["## 7b. Weak mentions and `any_mention_level`", "",
          "Bare \"predictive processing\" (`needs_corroboration`) counts as a direct mention only in the title/abstract or with another "
          "strong/close term of the theory. Otherwise the paper is `weak_mention` (not in the silver set, but it HAS named the theory). "
          "`any_mention_level` = direct > weak > close > none; `names_theory_loosely` = direct OR weak OR close. A Level 3 \"never names "
          "the theory\" claim must use `names_theory_loosely = 0` (`query.names_theory_ids`).", "",
          "| Theory | direct | weak | close-term only | names theory loosely (any) |", "|---|---|---|---|---|"]
    for k2, th in terms.theories.items():
        lv = dict(q("SELECT any_mention_level, COUNT(*) FROM paper_flags WHERE theory=? GROUP BY 1", k2))
        L.append(f"| {th.name} | {lv.get('direct', 0)} | {lv.get('weak', 0)} | {lv.get('close', 0)} | "
                 f"{q('SELECT SUM(names_theory_loosely) FROM paper_flags WHERE theory=?', k2)[0][0] or 0} |")
    L.append("")

    # ---- precision from labels ----
    L += ["## 8. Precision audit (hand labels)", "",
          "Source: `reports/precision_audit_labels.csv` (Y = true positive, N = false positive, ? = undecided and excluded "
          "from precision; weak mentions count as Y). Each (paper, term) appears once, so per-term n is already unique papers. "
          "The sample was stratified so every strong term with hits was drawn at least once, then topped up at random: "
          "it is NOT a random sample of all hits, so these are diagnostics, not population precision estimates. "
          "Wilson 95% interval shown because every n here is tiny; no term has enough labels to certify 80%.", ""]
    lab_rows = read_labels()
    pt = per_term(lab_rows)
    for k, th in terms.theories.items():
        L += [f"### {th.name}", "", "| strong term | papers (corpus) | audited n | Y | N | ? | weak (in Y) | precision | Wilson 95% |",
              "|---|---|---|---|---|---|---|---|---|"]
        ph = {r["term"]: r for r in per_term_hits(conn, k)}
        for t in th.strong_terms:
            d = pt.get((k, t))
            r = ph.get(t)
            if not d:
                L.append(f"| {t} | {r['papers'] if r else 0} | 0 | | | | | not audited | |")
                continue
            n = d["Y"] + d["N"]
            lo, hi = wilson(d["Y"], n)
            L.append(f"| {t} | {r['papers'] if r else 0} | {len(d['papers'])} | {d['Y']} | {d['N']} | {d['?']} | {d['weak']} | "
                     f"{d['Y'] / n:.0%} | {lo:.0%}-{hi:.0%} |" if n else
                     f"| {t} | {r['papers'] if r else 0} | {len(d['papers'])} | 0 | 0 | {d['?']} | 0 | undecided | |")
        up = per_theory_unique(lab_rows).get(k, {})
        yes = sum(1 for v in up.values() if v == {"Y"})
        no = sum(1 for v in up.values() if "N" in v)
        und = sum(1 for v in up.values() if "?" in v and "N" not in v)
        n_hits = sum(1 for r in lab_rows if r["theory"] == k)
        lo, hi = wilson(yes, yes + no)
        L += ["", f"Theory level, de-duplicated by paper: {n_hits} audited hits = **{len(up)} unique papers**; "
              f"{yes} Y, {no} N, {und} undecided; precision {yes}/{yes + no} = {yes / (yes + no):.0%} (Wilson 95% {lo:.0%}-{hi:.0%}).", ""
              if yes + no else f"Theory level: {n_hits} hits, no decided labels.", ""]
    rep = paper_repetition(lab_rows)
    L += ["**The audit sample over-represents a few papers** (hits per paper across all theories; 83 audited hits come from "
          f"{len({r['pmcid'] for r in lab_rows})} unique papers):", "",
          "| PMCID | audited hits | by theory |", "|---|---|---|"]
    L += [f"| {p} | {n} | {', '.join(f'{t} {c}' for t, c in d.items())} |" for p, n, d in rep]
    L += ["", "PMC4387509 alone supplies 9 of the 83 rows (5 IIT, 4 panpsychism); PMC3502201 supplies 4 of panpsychism's 20, "
          "PMC4014402 3 of IIT's 20. Read theory-level precision per unique paper, not per row.", ""]

    # ---- trends ----
    L += ["", "## 9. Server-side trend (Europe PMC, OA full text, strong phrases)", "",
          "Hits (per 10,000 OA full-text papers that year). Phrase counts without the domain rule: an upper bound on "
          "direct mentions. 2024-2025 are incomplete in PMC.", ""]
    keys = list(terms.theories)
    yrs = [r[0] for r in q("SELECT DISTINCT year FROM term_counts_by_year ORDER BY year")]
    if yrs:
        L += ["| Year | OA papers | " + " | ".join(terms.theories[k].name.split()[0] for k in keys) + " |",
              "|---|---|" + "---|" * len(keys)]
        for y in yrs:
            tot = q("SELECT total_oa FROM term_counts_by_year WHERE year=? LIMIT 1", y)[0][0]
            cells = []
            for k in keys:
                r = q("SELECT hits, rate_per_10k FROM term_counts_by_year WHERE theory=? AND year=?", k, y)
                cells.append(f"{r[0][0]} ({r[0][1]:.2f})" if r else "-")
            L.append(f"| {y} | {tot} | " + " | ".join(cells) + " |")
    else:
        L.append("(run `python -m src.level2_terms.trends` first)")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    conn = db.connect()
    text = build(conn)
    OUT.write_text(text)
    print(text)

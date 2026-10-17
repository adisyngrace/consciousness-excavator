"""Step 1 checkpoint summary: sizes per part, year distribution, section coverage, random samples."""
import random
from pathlib import Path

PARTS = ["seed", "candidate", "background", "random"]
BINS = [(1995, 1999), (2000, 2004), (2005, 2009), (2010, 2012), (2013, 2015)]
OUT = Path(__file__).resolve().parents[2] / "reports" / "corpus_step1.md"
SUBSTANTIVE = 2000   # chars of intro+body+discussion for a paper to count as a real full text, not a stub


def print_stats(conn) -> None:
    L = ["# Corpus build, Step 1 summary (1995-2015)", ""]
    q = lambda sql, *a: conn.execute(sql, a).fetchall()
    total = q("SELECT COUNT(DISTINCT pmcid) FROM corpus_membership")[0][0]
    L += [f"**Distinct papers in corpus: {total}**", "", "| Part | Papers | Downloaded OK | Failed | Parsed OK |", "|---|---|---|---|---|"]
    for part in PARTS:
        r = q("""SELECT COUNT(DISTINCT p.pmcid), SUM(p.fetch_status='ok'), SUM(p.fetch_status='failed'), SUM(p.parse_status='ok')
                 FROM papers p WHERE p.pmcid IN (SELECT pmcid FROM corpus_membership WHERE part=?)""", part)[0]
        L.append(f"| {part} | {r[0]} | {r[1] or 0} | {r[2] or 0} | {r[3] or 0} |")
    multi = q("SELECT COUNT(*) FROM (SELECT pmcid FROM corpus_membership GROUP BY pmcid HAVING COUNT(DISTINCT part)>1)")[0][0]
    L += ["", f"Papers in more than one part: {multi}", "", "### Per tag", "", "| Part | Tag | Papers | Total hits found | Cap |", "|---|---|---|---|---|"]
    for r in q("""SELECT m.part, m.tag, COUNT(*) n, s.total_hits, s.cap FROM corpus_membership m
                  LEFT JOIN search_log s ON s.part=m.part AND s.tag=m.tag AND s.query IN ('UNION','level1:resolved_fulltext') OR
                       (s.part=m.part AND s.tag=m.tag AND m.part IN ('background','random'))
                  WHERE m.part!='random' GROUP BY m.part, m.tag ORDER BY m.part, m.tag"""):
        L.append(f"| {r['part']} | {r['tag']} | {r['n']} | {r['total_hits']} | {r['cap']} |")
    L += ["", "(random sample: one stratum per year; per-year quotas in `search_log`)", "", "### Year distribution (papers)", "",
          "| Part | " + " | ".join(f"{a}-{b}" for a, b in BINS) + " |", "|---|" + "---|" * len(BINS)]
    for part in PARTS:
        cells = []
        for a, b in BINS:
            cells.append(str(q("""SELECT COUNT(DISTINCT p.pmcid) FROM papers p JOIN corpus_membership m USING(pmcid)
                                 WHERE m.part=? AND p.year BETWEEN ? AND ?""", part, a, b)[0][0]))
        L.append(f"| {part} | " + " | ".join(cells) + " |")
    # fetch failures
    fails = q("SELECT fetch_error, COUNT(*) n FROM papers WHERE fetch_status='failed' AND pmcid IN (SELECT pmcid FROM corpus_membership) GROUP BY fetch_error ORDER BY n DESC")
    L += ["", "### Download failures", ""] + ([f"- {r['n']} x {r['fetch_error']}" for r in fails] or ["- none"])
    pend = q("SELECT COUNT(DISTINCT p.pmcid) FROM papers p JOIN corpus_membership m USING(pmcid) WHERE p.fetch_status='pending'")[0][0]
    if pend:
        L.append(f"- {pend} papers still pending download")
    pf = q("SELECT parse_error, COUNT(*) n FROM papers WHERE parse_status='failed' AND pmcid IN (SELECT pmcid FROM corpus_membership) GROUP BY parse_error")
    L += ["", "### Parse failures", ""] + ([f"- {r['n']} x {r['parse_error']}" for r in pf] or ["- none"])
    # section coverage
    r = q(f"""SELECT COUNT(*) n, SUM(has_intro) i, SUM(has_discussion) d, SUM(has_intro AND has_discussion) both_,
              SUM(n_refs>0) refs FROM papers WHERE parse_status='ok' AND n_body_chars>={SUBSTANTIVE} AND pmcid IN (SELECT pmcid FROM corpus_membership)""")[0]
    a = q("SELECT COUNT(*) n, SUM(n_body_chars<?) stubs FROM papers WHERE parse_status='ok' AND pmcid IN (SELECT pmcid FROM corpus_membership)", SUBSTANTIVE)[0]
    L += ["", "### Section detection", "",
          f"- Parsed papers: {a['n']}, of which {a['stubs']} are stubs (<{SUBSTANTIVE} chars of text; errata, letters, titles-only)",
          f"- Among the {r['n']} substantive papers: introduction identified **{(r['i'] or 0) / max(r['n'], 1):.0%}**, "
          f"discussion/conclusion identified **{(r['d'] or 0) / max(r['n'], 1):.0%}**, both {(r['both_'] or 0) / max(r['n'], 1):.0%}, "
          f"reference list extracted {(r['refs'] or 0) / max(r['n'], 1):.0%}"]
    for part in PARTS:
        r = q("""SELECT COUNT(*) n, AVG(has_intro) i, AVG(has_discussion) d FROM papers p WHERE parse_status='ok' AND n_body_chars>=?
                 AND pmcid IN (SELECT pmcid FROM corpus_membership WHERE part=?)""", SUBSTANTIVE, part)[0]
        if r["n"]:
            L.append(f"  - {part}: n={r['n']}, intro {r['i']:.0%}, discussion {r['d']:.0%}")
    # samples
    rows = q("SELECT pmcid FROM papers WHERE parse_status='ok' AND n_body_chars>=? AND pmcid IN (SELECT pmcid FROM corpus_membership) ORDER BY pmcid", SUBSTANTIVE)
    L += ["", "### 5 random papers", ""]
    for pm in random.Random(11).sample([r[0] for r in rows], min(5, len(rows))):
        p = q("SELECT title, year, journal FROM papers WHERE pmcid=?", pm)[0]
        sec = {r["section"]: r["text"] for r in q("SELECT section, text FROM paper_sections WHERE pmcid=?", pm)}
        parts = [r["part"] + ":" + r["tag"] for r in q("SELECT part, tag FROM corpus_membership WHERE pmcid=?", pm)]
        body = (sec.get("body") or sec.get("introduction") or "").replace("\n", " ")
        L += [f"- **{pm}** ({p['year']}, {p['journal']}) [{', '.join(parts)}]", f"  - {p['title']}", f"  - body: \"{body[:300]}\""]
    text = "\n".join(L)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(text)
    print(text)

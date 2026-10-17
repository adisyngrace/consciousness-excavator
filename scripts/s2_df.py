"""Estimate document frequency of every term in terms.yaml across the corpus (approximate; the real scanner is Step 3)."""
import re, sys, time
from pathlib import Path
import yaml
from src import db

T = yaml.safe_load(open("src/terms.yaml"))["theories"]
SCAN = ("title", "abstract", "introduction", "body", "discussion")      # never back_matter / references
HY = re.compile(r"[-‐-―]")
norm = lambda s: HY.sub(" ", s.lower())

c = db.connect()
n_papers = c.execute("select count(distinct pmcid) from corpus_membership").fetchone()[0]
phr = {}      # (theory, tier, term) -> [any, tiab]
rx = {}       # case-sensitive regexes for abbreviations and authors
for th, d in T.items():
    for tier in ("strong", "excluded_generic"):
        for term in d[tier]:
            phr[(th, tier, term)] = [0, 0]
    for tier in ("abbreviation", "author"):
        for term in d[tier]:
            rx[(th, tier, term)] = [re.compile(r"\b" + re.escape(term) + r"\b"), 0, 0]   # any, confirmed(strong in same paper)
strong_norm = {th: [norm(t) for t in d["strong"]] for th, d in T.items()}
strong_papers = {th: 0 for th in T}
t0 = time.time()
rows = c.execute("""select s.pmcid, s.section, s.text from paper_sections s
                    where s.pmcid in (select pmcid from corpus_membership) and s.section in ('title','abstract','introduction','body','discussion')
                    order by s.pmcid""")
cur, parts = None, {}
def flush():
    if cur is None: return
    full_raw = "\n".join(parts.get(s, "") for s in SCAN)
    full = norm(full_raw)
    tiab = norm(parts.get("title", "") + "\n" + parts.get("abstract", ""))
    for (th, tier, term), v in phr.items():
        k = norm(term)
        if k in full:
            v[0] += 1
            if k in tiab: v[1] += 1
    for th in T:
        if any(k in full for k in strong_norm[th]):
            strong_papers[th] += 1
    sp = {th: any(k in full for k in strong_norm[th]) for th in T}
    for (th, tier, term), v in rx.items():
        if v[0].search(full_raw):
            v[1] += 1
            if sp[th]: v[2] += 1
for pmcid, section, text in rows:
    if pmcid != cur:
        flush(); cur, parts = pmcid, {}
    parts[section] = text
flush()

L = [f"# Term document frequencies (approximate, {n_papers} corpus papers, references excluded)", "",
     "Substring estimate for phrases; case-sensitive whole-word regex for abbreviations and authors. "
     "The real scanner (Step 3) is stricter, so treat these as upper bounds.", ""]
for th, d in T.items():
    L += [f"## {d['name']}  (papers with any strong term: {strong_papers[th]})", "", "| Tier | Term | Papers | In title/abstract | Note |", "|---|---|---|---|---|"]
    for tier in ("strong", "excluded_generic"):
        for term in d[tier]:
            a, b = phr[(th, tier, term)]
            L.append(f"| {tier} | {term} | {a} | {b} | |")
    for tier in ("abbreviation", "author"):
        for term in d[tier]:
            _, a, conf = rx[(th, tier, term)]
            note = f"confirmed by a strong term in {conf} of them" if tier == "abbreviation" else ""
            L.append(f"| {tier} | {term} | {a} | | {note} |")
    L.append("")
Path("reports/terms_df.md").write_text("\n".join(L))
print(f"scanned in {time.time()-t0:.0f}s")
print("\n".join(L))

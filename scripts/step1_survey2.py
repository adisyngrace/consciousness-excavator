import collections, random, re, sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from src import http
BASE = "https://loc.closertotruth.com/theory/"
random.seed(2)
for s in sys.argv[1:]:
    soup = BeautifulSoup(http.get(BASE + s)["text"], "lxml")
    sec = soup.find("section", id="reference-section")
    print(f"\n=== {s}")
    # description location
    sc = soup.find("div", class_="sanity-content")
    print("sanity-content div:", bool(sc), "| chars:", len(sc.get_text(' ', strip=True)) if sc else 0,
          "| <p> in it:", len(sc.find_all('p')) if sc else 0)
    if sec:
        refs = sec.find("div", class_="space-y-4").find_all("div", recursive=False)
        doms = collections.Counter()
        with_doi = 0
        for r in refs:
            hrefs = [a.get("href","") for a in r.find_all("a")]
            labels = [a.get_text(strip=True) for a in r.find_all("a")]
            doms.update(labels)
            with_doi += any("doi.org" in h for h in hrefs)
        print(f"format B: {len(refs)} refs; with doi.org link: {with_doi}; link-button labels: {dict(doms)}")
        for r in random.sample(refs, min(3, len(refs))):
            print("  •", r.get_text(" | ", strip=True)[:240])
    else:
        print("format B section: absent")
    fn = soup.find(lambda t: t.name in ("h2","h3") and t.get_text(strip=True) == "Footnotes")
    print("has Footnotes heading:", bool(fn))

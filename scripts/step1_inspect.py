import re, sys
from bs4 import BeautifulSoup
from src import http

BASE = "https://loc.closertotruth.com/theory/"
SLUGS = sys.argv[1:]
for s in SLUGS:
    r = http.get(BASE + s)
    soup = BeautifulSoup(r["text"], "lxml")
    h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    heads = [(h.name, h.get_text(" ", strip=True)[:70]) for h in soup.find_all(["h2", "h3"])]
    text = soup.get_text(" ", strip=True)
    print(f"\n=== {s}  status={r['status']} bytes={len(r['text'])} title={soup.title.string if soup.title else None!r}")
    print("h1:", h1)
    print("h2/h3:", heads[:25])
    print("n <li>:", len(soup.find_all("li")), " n doi links:", len(re.findall(r"doi\.org/10\.", r["text"])),
          " 'Reference' mentions:", len(re.findall(r"[Rr]eferences?", text)))

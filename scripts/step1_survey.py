import random, re, sys
from bs4 import BeautifulSoup
from src import http
BASE = "https://loc.closertotruth.com/theory/"
random.seed(1)
for s in sys.argv[1:]:
    soup = BeautifulSoup(http.get(BASE + s)["text"], "lxml")
    hdrs = [h for h in soup.find_all(["h2","h3"]) if h.get_text(strip=True) == "References"]
    h = hdrs[-1]
    items, stop = [], False
    for el in h.find_all_next():
        if el.name in ("h2","h3") and el is not h: break
        if el.name in ("p","li") and not el.find_parent(["p","li"]):
            items.append(el)
    txt = [i.get_text(" ", strip=True) for i in items]
    doi = [t for i,t in zip(items,txt) if i.find("a", href=re.compile("doi.org"))]
    print(f"\n=== {s}: {len(items)} items after 'References' ({len(hdrs)} such headings); {len(doi)} with DOI link; container={h.parent.name}.{(h.parent.get('class') or [''])[0]}")
    for t in random.sample(txt, min(3, len(txt))):
        print("  •", t[:260])

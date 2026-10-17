from bs4 import BeautifulSoup
from src import http
for s in ["baars-s-and-dehaene-s-global-workspace-theory", "champagne-s-semiotic-account"]:
    soup = BeautifulSoup(http.get("https://loc.closertotruth.com/theory/" + s)["text"], "lxml")
    print("==", s)
    for h in soup.find_all(["h2", "h3"])[:6]:
        anc = [(p.name, (p.get("class") or [""])[0][:22]) for p in h.parents][:3]
        print("  ", h.name, repr(h.get_text(strip=True)[:35]), "<-", anc)
    sc = soup.find("div", class_="sanity-content")
    print("  sanity-content starts:", sc.get_text(" ", strip=True)[:160])

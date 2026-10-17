import sys
from bs4 import BeautifulSoup
from src import http
BASE = "https://loc.closertotruth.com/theory/"
s = sys.argv[1]
soup = BeautifulSoup(http.get(BASE + s)["text"], "lxml")
hdr = [h for h in soup.find_all(["h2","h3"]) if h.get_text(strip=True) == "References"][-1]
print("header parent:", hdr.parent.name, hdr.parent.get("class"))
n = 0
for sib in hdr.next_siblings:
    if getattr(sib, "name", None) in ("h2",): break
    if getattr(sib, "name", None):
        print(f"--- <{sib.name} class={sib.get('class')}> children={len(list(sib.children))}")
        print(str(sib)[:int(sys.argv[2])])
        n += 1
        if n >= 3: break

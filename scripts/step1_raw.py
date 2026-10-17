import sys
from bs4 import BeautifulSoup
from src import http
soup = BeautifulSoup(http.get("https://loc.closertotruth.com/theory/" + sys.argv[1])["text"], "lxml")
h = [h for h in soup.find_all(["h2","h3"]) if h.get_text(strip=True) == "References"][-1]
sec = h.parent
print("section:", sec.name, sec.get("class"), "| direct children:", [(c.name, (c.get("class") or [""])[0][:25]) for c in sec.find_all(recursive=False)][:8])
print(str(sec)[:int(sys.argv[2])])

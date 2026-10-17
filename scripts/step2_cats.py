from bs4 import BeautifulSoup
from src import http
B = "https://loc.closertotruth.com/theory/"
for s in ["champagne-s-semiotic-account","baars-s-and-dehaene-s-global-workspace-theory","tononi-s-integrated-information-theory","panpsychisms-overview","predictive-theories-top-down","friston-s-free-energy-principle-and-active-inference"]:
    soup = BeautifulSoup(http.get(B+s)["text"], "lxml")
    h = soup.find(lambda t: t.name=="h2" and t.get_text(strip=True)=="Categories")
    cont = h.parent
    print("==", s, [a.get_text(strip=True) for a in cont.find_all("a")][:12])

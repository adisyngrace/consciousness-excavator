import json, re, random
from lxml import etree
from src import http
S = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
random.seed(3)
ids = []
for span in ("[1995 TO 2004]", "[2005 TO 2009]", "[2010 TO 2015]"):
    r = json.loads(http.get(S + "search", params={"query": f'"attention" AND OPEN_ACCESS:y AND HAS_FT:y AND PUB_YEAR:{span}', "format": "json", "resultType": "lite", "pageSize": 100})["text"])
    res = [x for x in r["resultList"]["result"] if x.get("pmcid")]
    ids += [(span, x["pmcid"], x.get("pubYear"), x.get("source")) for x in random.sample(res, 7)]
INTRO = re.compile(r"^\W*(\d+\W*)?(introduction|background)\b", re.I)
DISC = re.compile(r"^\W*(\d+\W*)?(general )?(discussion|conclusions?|summary and discussion)\b", re.I)
rows = []
for span, pm, yr, src in ids:
    x = http.get(S + f"{pm}/fullTextXML")
    if x["status"] != 200:
        rows.append((span, pm, yr, "HTTP %s" % x["status"])); continue
    root = etree.fromstring(x["text"].encode())
    body = root.find("body")
    titles = [(s.findtext("title") or "").strip() for s in (body.findall("sec") if body is not None else [])]
    back = root.find("back")
    reflist = root.find(".//ref-list")
    rows.append((span, pm, yr, dict(
        body=body is not None, nsec=len(titles), sec_types=sum(1 for s in body.findall("sec") if s.get("sec-type")) if body is not None else 0,
        intro=any(INTRO.search(t) for t in titles), disc=any(DISC.search(t) for t in titles),
        back=back is not None, reflist_in="back" if reflist is not None and reflist.getparent().tag == "back" else ("body" if reflist is not None else "none"),
        nrefs=len(root.findall(".//ref")), abstract=root.find(".//abstract") is not None, kb=len(x["text"]) // 1000)))
for r in rows: print(r)
ok = [r[3] for r in rows if isinstance(r[3], dict)]
n = len(ok)
print(f"\n{n} articles: body {sum(o['body'] for o in ok)}, has Introduction/Background title {sum(o['intro'] for o in ok)}, "
      f"Discussion/Conclusion title {sum(o['disc'] for o in ok)}, <back> present {sum(o['back'] for o in ok)}, "
      f"ref-list in back {sum(o['reflist_in']=='back' for o in ok)} / in body {sum(o['reflist_in']=='body' for o in ok)} / none {sum(o['reflist_in']=='none' for o in ok)}, "
      f"sec-type attr used {sum(o['sec_types']>0 for o in ok)}, abstract {sum(o['abstract'] for o in ok)}")

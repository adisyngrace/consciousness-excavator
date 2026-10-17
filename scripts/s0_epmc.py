import json, sys
from src import http
S = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
def hits(q, **kw):
    r = http.get(S, params={"query": q, "format": "json", "resultType": "lite", "pageSize": kw.get("n", 1)})
    j = json.loads(r["text"])
    return j.get("hitCount"), j.get("resultList", {}).get("result", [])
for q in sys.argv[1:]:
    n, res = hits(q)
    print(f"{n:>9}  {q}")

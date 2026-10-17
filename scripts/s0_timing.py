import os, time, requests
from dotenv import load_dotenv
load_dotenv()
ua = {"User-Agent": os.environ["USER_AGENT"]}
S = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
r = requests.get(S + "search", params={"query": '"global workspace theory" AND OPEN_ACCESS:y AND HAS_FT:y AND PUB_YEAR:[1995 TO 2015]', "format": "json", "resultType": "lite", "pageSize": 8}, headers=ua).json()
ids = [x["pmcid"] for x in r["resultList"]["result"] if x.get("pmcid")]
t = time.time(); sz = 0
for i in ids:
    x = requests.get(f"{S}{i}/fullTextXML", headers=ua); sz += len(x.content)
n = len(ids)
print(f"{n} articles, {time.time()-t:.1f}s total, {(time.time()-t)/n:.2f}s each, avg {sz/n/1e3:.0f} KB")
print("rate-limit headers:", {k: v for k, v in x.headers.items() if "rate" in k.lower() or "limit" in k.lower()})
p = requests.get(S + "search", params={"query": "panpsychism AND OPEN_ACCESS:y", "format": "json", "resultType": "lite", "pageSize": 1000, "cursorMark": "*"}, headers=ua).json()
print("pageSize=1000 returned", len(p["resultList"]["result"]), "| nextCursorMark present:", "nextCursorMark" in p)

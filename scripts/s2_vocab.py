import math, re, collections
from src import db
c = db.connect()
STOP = set("the of and a to in is that it as for with on by this be are or an from at which their its not can has have more than but also these they such what when into how about one all other between through who been may only both was were his her them our we if so any each most some there while within without out over under".split())
texts = {r["name"]: r["description_text"] for r in c.execute("select name, description_text from theories")}
def grams(t):
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]+", t)
    low = [w.lower() for w in toks]
    out = collections.Counter()
    for i, w in enumerate(low):
        if w not in STOP and len(w) > 3:
            out[w] += 1
        if i + 1 < len(low) and low[i] not in STOP and low[i + 1] not in STOP and len(low[i]) > 2 and len(low[i + 1]) > 2:
            out[low[i] + " " + low[i + 1]] += 1
    return out
G = {k: grams(v) for k, v in texts.items()}
df = collections.Counter(g for cnt in G.values() for g in cnt)
for name, cnt in G.items():
    scored = sorted(((n * math.log(5 / df[g]), g, n) for g, n in cnt.items() if n >= 3 and df[g] <= 2), reverse=True)[:45]
    print(f"\n== {name} ({len(texts[name])} chars)\n  " + "; ".join(f"{g} ({n})" for _, g, n in scored))

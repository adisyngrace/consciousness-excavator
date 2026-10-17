"""Step 0 of prompt 06: build the blind judging set and packets.

Per theory: V4 top 30 (1995-2015, names_theory_loosely = 0) plus, for GWT and PP, the BM25 top 30 (same pool/eligibility),
union, 10% repeats (seed), shuffle (seed), batches of 10 -> data/judge/packets/batch_NN.md. Packets carry no score, rank,
corpus part or method. Method membership goes to data/judge/method_membership.csv (do not open before Step 4).
Passages: the 2 chunks with the highest V4 chunk score (max over the theory's components of unweighted z), same rule for
every item; abstract-section chunks are skipped because the abstract is already shown.
usage: python -m src.judge.build
"""
import csv
import json
import random

import numpy as np
import yaml

from src.eval.run_dev import SHORT
from src.eval.scoring import THEORIES, bank, build_pool
from src.level3_concepts.make_profiles import PROFILES

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2] / "data" / "judge"
SEED = 20261012
TOP, BATCH = 30, 10
BM25_THEORIES = {"global_workspace", "predictive_processing_fep"}
PROFILE_FILE = {"champagne_semiotic": "champagne", "global_workspace": "gwt", "integrated_information": "iit",
                "panpsychism": "panpsychism", "predictive_processing_fep": "predictive_processing"}
PREFIX = {"champagne_semiotic": "CH", "global_workspace": "GW", "integrated_information": "II", "panpsychism": "PA", "predictive_processing_fep": "PP"}


def top_papers(bk, pool, t: str, variant: str, k: int) -> list[str]:
    s = pool.scores[variant]
    idx = np.array([i for i, p in enumerate(pool.papers) if bk.flag.get((p, t), 1) == 0])
    idx = idx[np.argsort(-s[idx], kind="stable")][:k]
    return [str(pool.papers[i]) for i in idx]


def passages(bk, chunk_ids: np.ndarray, t: str, pmcid: str) -> list[dict]:
    ix = bk.ix
    rows = np.where((ix.pmcid == pmcid) & (ix.section != "abstract"))[0]
    sel = np.where(ix.ctheory == t)[0]
    sc = ix.z[np.ix_(rows, sel)].max(1)
    out = []
    for j in np.argsort(-sc, kind="stable")[:2]:
        text = ix.conn.execute("SELECT text FROM chunks WHERE chunk_id=?", (int(chunk_ids[rows[j]]),)).fetchone()[0]
        out.append({"section": str(ix.section[rows[j]]), "text": " ".join(text.split())})
    return out


def layout(items: list[dict], reps: list[dict], rng: random.Random) -> list[dict]:
    """Shuffle originals, insert repeats at random places; redraw until every repeat is in a LATER batch than its original."""
    for _ in range(10000):
        seq = list(items)
        rng.shuffle(seq)
        for r in reps:
            seq.insert(rng.randrange(len(seq) + 1), r)
        batch = {(i["pmcid"], bool(i["repeat_of"])): n // BATCH for n, i in enumerate(seq)}
        if all(batch[(r["pmcid"], True)] > batch[(r["pmcid"], False)] for r in reps):
            return seq
    raise RuntimeError("no valid layout")


def claims(t: str) -> list[dict]:
    return yaml.safe_load((PROFILES / f"{PROFILE_FILE[t]}.yaml").read_text())["core_claims"]


def packet(item: dict, n: int) -> str:
    ps = "\n\n".join(f"**Passage {i} ({p['section']}):** {p['text']}" for i, p in enumerate(item["passages"], 1))
    return f"### Item {item['item_id']}\n\n**Title:** {item['title']}\n**Year:** {item['year']}\n\n**Abstract:** {item['abstract'] or '(no abstract available)'}\n\n{ps}\n"


def main() -> None:
    bk = bank()
    conn = bk.ix.conn
    chunk_ids = np.array([r[0] for r in conn.execute("SELECT chunk_id FROM chunks ORDER BY chunk_id")])
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "packets").mkdir(exist_ok=True)
    member, counts, placement, bno = [], [], [], 0
    for t in THEORIES:
        pool = build_pool(t, False)
        m: dict[str, set] = {}
        for p in top_papers(bk, pool, t, "V4", TOP):
            m.setdefault(p, set()).add("V4")
        if t in BM25_THEORIES:
            for p in top_papers(bk, pool, t, "BM25", TOP):
                m.setdefault(p, set()).add("BM25")
        papers = sorted(m)
        rng = random.Random(f"{SEED}-{t}")
        items = []
        for p in papers:
            r = conn.execute("SELECT title, year, abstract FROM papers WHERE pmcid=?", (p,)).fetchone()
            items.append({"pmcid": p, "title": r["title"], "year": r["year"], "abstract": r["abstract"], "passages": passages(bk, chunk_ids, t, p), "repeat_of": ""})
        reps = [dict(i) for i in rng.sample(items, round(0.1 * len(items)))]
        for r in reps:
            r["repeat_of"] = r["pmcid"]
        allit = layout(items, reps, rng)
        placement.append((t, [(next(n for n, i in enumerate(allit) if i["pmcid"] == r["pmcid"] and not i["repeat_of"]) // BATCH + 1 + bno,
                               next(n for n, i in enumerate(allit) if i["pmcid"] == r["pmcid"] and i["repeat_of"]) // BATCH + 1 + bno) for r in reps]))
        for n, it in enumerate(allit, 1):
            it["item_id"] = f"{PREFIX[t]}{n:03d}"
            member.append({"item_id": it["item_id"], "theory": t, "pmcid": it["pmcid"], "methods": "+".join(sorted(m[it["pmcid"]])), "is_repeat": int(bool(it["repeat_of"]))})
        cl = "\n".join(f"- **{c['id']}:** {c['text']}" for c in claims(t))
        for b in range(0, len(allit), BATCH):
            bno += 1
            chunk = allit[b:b + BATCH]
            head = f"# Batch {bno:02d}\n\n**Theory:** {SHORT[t]} ({t})\n\n**Core claims:**\n{cl}\n\n---\n\n"
            (ROOT / "packets" / f"batch_{bno:02d}.md").write_text(head + "\n".join(packet(i, 0) for i in chunk))
        counts.append((t, len(items), len(reps), sum("V4" in v for v in m.values()), sum("BM25" in v for v in m.values()), sum(len(v) == 2 for v in m.values())))
    with open(ROOT / "method_membership.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "theory", "pmcid", "methods", "is_repeat"])
        w.writeheader()
        w.writerows(member)
    print("theory, unique items, repeats, V4, BM25, both")
    for c in counts:
        print(*c)
    print("batches:", bno)
    print("repeat placement (original batch -> repeat batch), global batch numbers:")
    for t, pl in placement:
        print(t, "repeats:", len(pl), "later:", sum(b > a for a, b in pl), "same:", sum(a == b for a, b in pl), "earlier:", sum(b < a for a, b in pl), sorted(pl))


if __name__ == "__main__":
    main()

"""Steps 4-5 of prompt 06: analysis of the blind judgments (blindness is over), report and exports.

Reads data/project.db (judgments), data/judge/method_membership.csv, reports/labeling_sheet.csv, the V4/BM25 ranks
(recomputed with the Step 0 code, no tuning), writes reports/level3_judge.md, results/judgments.csv (pmcid filled,
NO method column) and data/judge/judgments_final.csv (same plus is_repeat). Fills judgments.pmcid in the DB.
Sensitivity: PP014 was revised R -> G during judging (data/judge/notes_revisions.md); every headline number is also
computed with the original verdict.
usage: python -m src.judge.analyze
"""
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
JD = ROOT / "data" / "judge"
SEED = 20261012
NBOOT = 10000
KS = (10, 20, 30)
NAME = {"champagne_semiotic": "Champagne", "global_workspace": "GWT", "integrated_information": "IIT",
        "panpsychism": "Panpsychism", "predictive_processing_fep": "Predictive processing"}
SHEET = {"Champagne": "champagne_semiotic", "GWT": "global_workspace", "IIT": "integrated_information",
         "Panpsychism": "panpsychism", "PP": "predictive_processing_fep"}
THEORY_FULL = {"Champagne's semiotic account": "champagne_semiotic", "Global Workspace Theory": "global_workspace",
               "Integrated Information Theory": "integrated_information", "Panpsychism": "panpsychism",
               "Predictive Processing / Free Energy Principle": "predictive_processing_fep"}
REVISION = {"item": "PP014", "original": ("R", "low", ["predictive_processing-c4"])}
V = ["R", "G", "O"]


def kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in set(a) | set(b)) / n ** 2
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def ranks() -> dict[tuple[str, str], list[str]]:
    from src.eval.scoring import THEORIES, bank, build_pool
    from src.judge.build import BM25_THEORIES, TOP, top_papers
    bk = bank()
    out = {}
    for t in THEORIES:
        pool = build_pool(t, False)
        out[(t, "V4")] = top_papers(bk, pool, t, "V4", TOP)
        if t in BM25_THEORIES:
            out[(t, "BM25")] = top_papers(bk, pool, t, "BM25", TOP)
    return out


def load():
    conn = sqlite3.connect(ROOT / "data" / "project.db")
    conn.row_factory = sqlite3.Row
    mem = {r["item_id"]: r for r in csv.DictReader(open(JD / "method_membership.csv"))}
    jud = {}
    for r in conn.execute("SELECT * FROM judgments"):
        d = dict(r)
        d["pmcid"] = mem[d["item_id"]]["pmcid"]
        d["is_repeat"] = int(mem[d["item_id"]]["is_repeat"])
        d["claim_ids"] = json.loads(d["claim_ids"])
        d["flags"] = json.loads(d["flags"])
        jud[d["item_id"]] = d
    ex = sqlite3.connect(ROOT / "data" / "excavator.db")
    ex.row_factory = sqlite3.Row
    paper = {r["pmcid"]: dict(r) for r in ex.execute(
        "SELECT p.pmcid, p.title, p.year, p.abstract, (SELECT part FROM corpus_membership c WHERE c.pmcid=p.pmcid) part FROM papers p")}
    return conn, mem, jud, paper


def revised(jud: dict, original: bool) -> dict:
    if not original:
        return jud
    j = {k: dict(v) for k, v in jud.items()}
    v, c, ids = REVISION["original"]
    j[REVISION["item"]].update(verdict=v, confidence=c, claim_ids=list(ids))
    return j


def boot(x: np.ndarray, rng) -> tuple[float, float, float]:
    m = x.mean()
    s = rng.choice(x, size=(NBOOT, len(x))).mean(1)
    return m, *np.percentile(s, [2.5, 97.5])


def fmt(t: tuple) -> str:
    return f"{100 * t[0]:.0f}% [{100 * t[1]:.0f}, {100 * t[2]:.0f}]"


def table(head: list[str], rows: list[list]) -> str:
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]) + "\n"


def by_pmcid(jud: dict) -> dict:
    """(theory, pmcid) -> original (non-repeat) judgment."""
    return {(j["theory"], j["pmcid"]): j for j in jud.values() if not j["is_repeat"]}


def analyse(jud: dict, rk: dict, paper: dict, mem: dict, sheet: list[dict]) -> dict:
    """All numbers for one version of the verdicts."""
    bp = by_pmcid(jud)
    rng = np.random.default_rng(SEED)
    res: dict = {}
    # 1. V4 distribution and R share
    dist, share = {}, {}
    for t in NAME:
        js = [bp[(t, p)] for p in rk[(t, "V4")]]
        dist[t] = Counter(j["verdict"] for j in js)
        share[t] = {k: sum(j["verdict"] == "R" for j in js[:k]) / min(k, len(js)) for k in KS}
    res["dist"], res["share"] = dist, share
    # 2. V4 vs BM25 (R share at k, bootstrap) and difference
    cmp = {}
    for t in ("global_workspace", "predictive_processing_fep"):
        row = {}
        for m in ("V4", "BM25"):
            x = np.array([bp[(t, p)]["verdict"] == "R" for p in rk[(t, m)]], float)
            row[m] = {k: boot(x[:k], rng) for k in KS}
            row[m]["x"] = x
        row["diff"] = {}
        for k in KS:
            a, b = row["V4"]["x"][:k], row["BM25"]["x"][:k]
            d = rng.choice(a, (NBOOT, len(a))).mean(1) - rng.choice(b, (NBOOT, len(b))).mean(1)
            row["diff"][k] = (a.mean() - b.mean(), *np.percentile(d, [2.5, 97.5]))
        cmp[t] = row
    res["cmp"] = cmp
    # 3. consistency
    by_p = defaultdict(dict)
    for j in jud.values():
        by_p[(j["theory"], j["pmcid"])][j["is_repeat"]] = j
    pairs = [(d[0], d[1]) for d in by_p.values() if 0 in d and 1 in d]
    a, b = [p[0]["verdict"] for p in pairs], [p[1]["verdict"] for p in pairs]
    ar, br = [x == "R" for x in a], [y == "R" for y in b]
    res["cons"] = dict(n=len(pairs), agree=sum(x == y for x, y in zip(a, b)) / len(pairs), kappa=kappa(a, b),
                       agree_r=sum(x == y for x, y in zip(ar, br)) / len(pairs),
                       kappa_r=kappa([str(x) for x in ar], [str(y) for y in br]),
                       disagree=[(p[0]["item_id"], p[1]["item_id"], p[0]["verdict"], p[1]["verdict"]) for p in pairs if p[0]["verdict"] != p[1]["verdict"]])
    # 4. hand labels
    lab, miss = [], []
    for r in sheet:
        if r["label"] not in V:
            continue
        j = bp.get((SHEET[r["theory"]], r["pmcid"]))
        if j is None:
            miss.append(r)
        else:
            lab.append((r["label"], j["verdict"], r))
    res["lab"] = dict(pairs=lab, missing=miss,
                      cm=Counter((h, jv) for h, jv, _ in lab),
                      agree=np.mean([h == jv for h, jv, _ in lab]) if lab else float("nan"),
                      kappa=kappa([h for h, _, _ in lab], [jv for _, jv, _ in lab]) if lab else float("nan"),
                      kappa_r=kappa([str(h == "R") for h, _, _ in lab], [str(jv == "R") for _, jv, _ in lab]) if lab else float("nan"))
    # 5. corpus part (V4 list, non-repeat) and abstract presence
    part = defaultdict(lambda: [0, 0])
    for t in NAME:
        for p in rk[(t, "V4")]:
            c = part[paper[p]["part"]]
            c[0] += 1
            c[1] += bp[(t, p)]["verdict"] == "R"
    res["part"] = dict(part)
    part_t = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for t in NAME:
        for p in rk[(t, "V4")]:
            c = part_t[t][paper[p]["part"]]
            c[0] += 1
            c[1] += bp[(t, p)]["verdict"] == "R"
    res["part_t"] = {t: dict(v) for t, v in part_t.items()}
    # 6. flags
    nt = [j["item_id"] for j in jud.values() if "names_theory_in_text" in j["flags"]]
    conf = Counter()
    bf_items = []
    for j in jud.values():
        for f in j["flags"]:
            if f.startswith("better_fit:"):
                conf[(j["theory"], THEORY_FULL[f.split(":", 1)[1]])] += 1
                bf_items.append(j)
    res["flags"] = dict(names=nt, conf=conf, n_bf=len(bf_items),
                        bf_verdict=Counter(j["verdict"] for j in bf_items))
    return res


def no_abstract(rk, paper, mem) -> dict:
    out = {}
    for (t, m), ps in rk.items():
        out[(t, m)] = sum(not (paper[p]["abstract"] or "").strip() for p in ps)
    return out


def write_csvs(jud: dict, mem: dict, conn) -> None:
    cols = ["item_id", "theory", "pmcid", "verdict", "confidence", "claim_ids", "reason", "evidence", "flags"]
    ordered = sorted(jud.values(), key=lambda j: j["item_id"])
    for path, extra in ((ROOT / "results" / "judgments.csv", []), (JD / "judgments_final.csv", ["is_repeat"])):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols + extra)
            for j in ordered:
                w.writerow([j["item_id"], j["theory"], j["pmcid"], j["verdict"], j["confidence"], json.dumps(j["claim_ids"]),
                            j["reason"], j["evidence"], json.dumps(j["flags"])] + [j[e] for e in extra])
    conn.executemany("UPDATE judgments SET pmcid=? WHERE item_id=?", [(j["pmcid"], j["item_id"]) for j in jud.values()])
    conn.commit()


def exports(jud: dict, rk: dict, paper: dict) -> str:
    bp = by_pmcid(jud)
    out = ""
    order = {"high": 0, "medium": 1, "low": 2}
    for t in NAME:
        rs = [(order[bp[(t, p)]["confidence"]], i, p) for i, p in enumerate(rk[(t, "V4")]) if bp[(t, p)]["verdict"] == "R"]
        rs.sort()
        out += f"\n#### {NAME[t]} ({len(rs)} R-judged in the V4 top 30; best {min(10, len(rs))} shown)\n\n"
        rows = []
        for _, i, p in rs[:10]:
            j = bp[(t, p)]
            rows.append([p, paper[p]["title"].replace("|", "/"), paper[p]["year"], j["confidence"], ", ".join(j["claim_ids"]),
                         j["reason"].replace("|", "/"), f"\"{j['evidence']}\""])
        out += table(["pmcid", "title", "year", "conf.", "claims", "reason", "evidence"], rows) if rows else "None.\n"
    return out


def main() -> None:
    conn, mem, jud, paper = load()
    rk = ranks()
    lines = [l for l in csv.reader(open(ROOT / "reports" / "labeling_sheet.csv")) if len(l) > 1]  # skips a stray one-cell title line
    sheet = [dict(zip(lines[0], l)) for l in lines[1:]]
    cur, orig = analyse(revised(jud, False), rk, paper, mem, sheet), analyse(revised(jud, True), rk, paper, mem, sheet)
    na = no_abstract(rk, paper, mem)
    write_csvs(jud, mem, conn)
    md = report(jud, rk, paper, mem, sheet, cur, orig, na)
    (ROOT / "reports" / "level3_judge.md").write_text(md)
    print(md)


def report(jud, rk, paper, mem, sheet, cur, orig, na) -> str:
    bp = by_pmcid(jud)
    o = f"# Level 3 LLM judge (prompt 06, Steps 4-5)\n\n"
    o += ("Claude Code judged 209 unique items (230 judgments incl. 21 repeats) from packets only, blind to method, rank, score, corpus part and "
          "to the hand labels. Blindness ended at Step 4. Nothing here was used to change profiles, terms or the selected variant (V4). "
          "Verdicts: R relevant conceptual neighbor, G generic consciousness/neuroscience, O off-topic. "
          "All numbers use the **revised** PP014 verdict (G) unless marked; section 8 repeats the headline numbers with the original (R).\n\n")
    # 1
    o += "## 1. Verdict distribution, V4 top 30 per theory\n\n"
    rows = []
    for t in NAME:
        d = cur["dist"][t]
        s = cur["share"][t]
        rows.append([NAME[t], d["R"], d["G"], d["O"]] + [f"{100 * s[k]:.0f}% ({round(s[k] * k)}/{k})" for k in KS])
    o += table(["Theory", "R", "G", "O", "R share top 10", "top 20", "top 30"], rows)
    tot = sum((cur["dist"][t] for t in NAME), Counter())
    o += f"\nAll theories: R {tot['R']}, G {tot['G']}, O {tot['O']} of {sum(tot.values())}.\n\n"
    # 2
    o += "## 2. V4 versus BM25 (GWT and predictive processing)\n\n"
    o += ("The judge was blind to the method: packets have the same format for every item and carry no method, rank or score. "
          "R share of the top k of each method's list (k = 10, 20, 30), with 95% bootstrap CI (10,000 resamples of the papers, "
          f"seed {SEED}). n is small (10 to 30 papers), so the intervals are wide. The difference is V4 minus BM25 (independent resamples). "
          "In predictive processing one paper is in both lists.\n\n")
    rows = []
    for t in ("global_workspace", "predictive_processing_fep"):
        for m in ("V4", "BM25"):
            rows.append([NAME[t], m] + [fmt(cur["cmp"][t][m][k]) for k in KS])
        rows.append([NAME[t], "V4 - BM25"] + [f"{100 * cur['cmp'][t]['diff'][k][0]:+.0f} pts [{100 * cur['cmp'][t]['diff'][k][1]:+.0f}, {100 * cur['cmp'][t]['diff'][k][2]:+.0f}]" for k in KS])
    o += table(["Theory", "Method", "R share top 10", "top 20", "top 30"], rows)
    o += "\nItems with no abstract (packet says \"no abstract available\"), by list:\n\n"
    rows = [[NAME[t], m, na[(t, m)], len(ps)] for (t, m), ps in rk.items()]
    o += table(["Theory", "Method", "No abstract", "Items"], rows)
    wa = {k: [bp[(k[0], p)]["verdict"] for p in ps if (paper[p]["abstract"] or "").strip()] for k, ps in rk.items()}
    na_r = sum(bp[(k[0], p)]["verdict"] == "R" for k, ps in rk.items() for p in ps if not (paper[p]["abstract"] or "").strip())
    n_v4 = sum(v for (t, m), v in na.items() if m == "V4")
    n_bm = sum(v for (t, m), v in na.items() if m == "BM25")
    o += (f"\nV4 lists: {n_v4} of 150 items have no abstract ({100 * n_v4 / 150:.0f}%); BM25 lists: {n_bm} of 60 ({100 * n_bm / 60:.0f}%). "
          f"Of all {sum(na.values())} list entries without an abstract, {na_r} were judged R. For GWT and predictive processing alone, V4 has "
          f"{na[('global_workspace', 'V4')] + na[('predictive_processing_fep', 'V4')]} of 60 without an abstract and BM25 has {n_bm} of 60. "
          "Could this bias the comparison? A packet without an abstract has only the title and two passages, so the judge is more likely to give G or O (almost all such items were G or O), "
          "which lowers a list's R share. In the V4-versus-BM25 comparison, BM25 has more of them (5 of 60 vs 1 of 60), so if anything the missing abstracts handicap BM25, "
          "by at most a few papers, and 4 of its 5 are predictive processing items, where the two methods tie. They cannot explain the GWT gap (1 such item in BM25's GWT list, judged R). "
"It is not a controlled test: the missing-abstract items also differ in other ways.\n\n")
    # 3
    c = cur["cons"]
    o += "## 3. Judge consistency on repeated items\n\n"
    o += (f"{c['n']} repeated papers, judged under new item ids in a later batch. Three-way verdict agreement {100 * c['agree']:.0f}% "
          f"({round(c['agree'] * c['n'])}/{c['n']}), Cohen's kappa {c['kappa']:.2f}. R versus not-R: agreement {100 * c['agree_r']:.0f}%, kappa {c['kappa_r']:.2f}. "
          "Disagreements (original, repeat, verdicts): " + ("; ".join(f"{a}/{b} {x}->{y}" for a, b, x, y in c["disagree"]) or "none") + ".\n\n")
    o += ("**The repeats were judged in the same Claude Code session as the originals, so they were not fully independent (the judge could remember "
          "the earlier item). The consistency figure is therefore an upper bound on the judge's true consistency.**\n\n")
    # 4
    l = cur["lab"]
    o += "## 4. Agreement with the hand labels\n\n"
    if not l["pairs"]:
        o += "The label column of `reports/labeling_sheet.csv` is empty; skipped.\n\n"
    else:
        n = len(l["pairs"])
        o += (f"{n} labelled rows of the sheet were matched to a judgment (theory and pmcid). {len(l['missing'])} labelled rows have no judgment "
              "(they are V5 picks that were not in the V4 or BM25 top 30, so they were never judged)"
              + (": " + ", ".join(f"{r['theory']} {r['variant']} rank {r['rank']} {r['pmcid']}" for r in l["missing"]) if l["missing"] else "") + ". ")
        o += f"Exact agreement {100 * l['agree']:.0f}% ({round(l['agree'] * n)}/{n}); Cohen's kappa (3 classes) {l['kappa']:.2f}; R versus not-R kappa {l['kappa_r']:.2f}.\n\n"
        o += "Confusion matrix (rows = your label, columns = judge):\n\n"
        o += table(["you \\ judge", "R", "G", "O", "total"], [[h] + [l["cm"][(h, jv)] for jv in V] + [sum(l["cm"][(h, jv)] for jv in V)] for h in V])
        dis = [(h, jv, r) for h, jv, r in l["pairs"] if h != jv]
        o += f"\nDisagreements ({len(dis)}):\n\n"
        o += table(["theory", "variant", "rank", "pmcid", "you", "judge", "judge conf.", "title"],
                   [[r["theory"], r["variant"], r["rank"], r["pmcid"], h, jv, bp[(SHEET[r["theory"]], r["pmcid"])]["confidence"], r["title"][:70].replace("|", "/")] for h, jv, r in dis])
        o += ("\nProvenance note: the git history records the labels as \"proposed by an AI assistant, reviewed by the user\". "
              "If so, they are not an independent human reference, and agreement with them partly measures agreement between two LLM-assisted judgments.\n\n")
    # 5
    o += "## 5. R share by corpus part (V4 top 30 lists)\n\n"
    rows = [[p, n, r, f"{100 * r / n:.0f}%"] for p, (n, r) in sorted(cur["part"].items())]
    o += table(["Corpus part", "Items", "R", "R share"], rows)
    o += "\nPer theory (items / R):\n\n"
    parts = sorted(cur["part"])
    o += table(["Theory"] + parts, [[NAME[t]] + [f"{cur['part_t'][t].get(p, [0, 0])[0]} / {cur['part_t'][t].get(p, [0, 0])[1]}" for p in parts] for t in NAME])
    nb = cur["part"]
    o += ("\nThe R share is not driven by the candidate pool: candidates (papers that the term-based Level 2 scan flagged as plausibly related but not direct mentions) "
          f"have a lower R share ({100 * nb['candidate'][1] / nb['candidate'][0]:.0f}%) than background papers ({100 * nb['background'][1] / nb['background'][0]:.0f}%). "
          "The background result comes mostly from GWT and predictive processing; for Champagne, IIT and panpsychism the candidate and background shares are both low and similar. "
          "No seed papers appear (they are excluded as direct mentions), and the two random-part items were both not R.\n\n")
    # 6
    f = cur["flags"]
    o += "## 6. Flags\n\n"
    o += f"- `names_theory_in_text` true: {len(f['names'])} items" + (f" ({', '.join(f['names'])})" if f["names"] else " (no exclusion leak seen in the packets)") + ".\n"
    o += ("  - PP059 (PMC4270100, predictive-processing V4 list; judged R, high) names \"free energy\" in its packet text. Level 2 treats bare \"free energy\" as a generic term "
          "(`excluded_generic`) and the paper has only a Friston 2010 citation, so it is correctly `names_theory_loosely = 0`; the judge flagged it as a possible exclusion leak. "
          "It is a case where a paper uses the theory's central concept under a different name, not a missed direct mention, but it should be kept out of any claim that these papers are free of the theory's vocabulary.\n")
    o += f"- `better_fit_theory` set: {f['n_bf']} judgments (verdicts: " + ", ".join(f"{k} {v}" for k, v in sorted(f["bf_verdict"].items())) + ").\n\n"
    o += "Confusion across theories (rows = theory the item was judged for, columns = better-fit theory):\n\n"
    ts = list(NAME)
    o += table(["judged for \\ better fit"] + [NAME[t] for t in ts], [[NAME[a]] + [f["conf"][(a, b)] or "" for b in ts] for a in ts])
    # 7
    o += "\n## 7. Exports for the app\n\nBest R-judged papers in each theory's V4 top 30, high confidence first, then medium, then low, ties by V4 rank. Full table: `data/judge/judgments_final.csv` and `results/judgments.csv`.\n"
    o += exports(jud, rk, paper)
    # 8
    o += "\n## 8. Sensitivity: the PP014 revision\n\n"
    o += ("PP014 (\"Homeostatic Plasticity and STDP: Keeping a Neuron's Cool in a Fluctuating World\") was first judged R (low, claim c4) and revised to G (low) "
          "before ingest, after PP023, PP035 and PP060 were judged G for the same reason (topic match without a parallel to the claim's content). "
          "Its repeat, PP049, was judged G independently. Notes: `data/judge/notes_revisions.md`. The revision was made while still blind, but it was a judgment call, "
          "so here are the headline numbers with each version.\n\n")
    rows = []
    for name, r in (("Revised (G)", cur), ("Original (R)", orig)):
        pp = r["cmp"]["predictive_processing_fep"]
        rows.append([name, r["dist"]["predictive_processing_fep"]["R"]] + [f"{100 * r['share']['predictive_processing_fep'][k]:.0f}%" for k in KS]
                    + [fmt(pp["V4"][30]), fmt(pp["BM25"][30]), f"{100 * pp['diff'][30][0]:+.0f} pts [{100 * pp['diff'][30][1]:+.0f}, {100 * pp['diff'][30][2]:+.0f}]",
                       f"{100 * r['cons']['agree']:.0f}% / {r['cons']['kappa']:.2f}", f"{100 * r['lab']['agree']:.0f}% / {r['lab']['kappa']:.2f}"])
    o += table(["PP014 verdict", "PP V4 R (of 30)", "PP V4 top 10", "top 20", "top 30", "PP V4 top-30 CI", "PP BM25 top-30 CI", "V4 - BM25 top 30", "repeat agreement / kappa", "label agreement / kappa"], rows)
    where = {m: (rk[("predictive_processing_fep", m)].index(by_pmcid(jud)[("predictive_processing_fep", next(j["pmcid"] for j in jud.values() if j["item_id"] == REVISION["item"]))]["pmcid"]) + 1)
             if next(j["pmcid"] for j in jud.values() if j["item_id"] == REVISION["item"]) in rk[("predictive_processing_fep", m)] else None
             for m in ("V4", "BM25")}
    o += f"\nPP014's position in the lists: V4 rank {where['V4']}, BM25 rank {where['BM25']}.\n"
    o += ("\nReading: the revision moves one paper out of predictive processing's V4 R list (12 vs 13 of 30). It changes the V4 top-20 and top-30 shares by 3 to 5 points, "
          "leaves the top-10 share unchanged, and the V4 versus BM25 difference stays inside the confidence interval either way (about zero). "
          "The repeat agreement under the original verdict is 20/21 (kappa 0.93), because PP014 and its repeat PP049 would disagree. "
          "Agreement with your labels is unaffected because PP014 is not on the labeling sheet. No conclusion changes.\n")
    # 9
    o += ("\n## 9. Caveats\n\nThe judge is an LLM and shares biases with other LLMs (for example towards papers that sound like the claim wording). "
          "It saw only the abstract and two passages per paper, not the full text, so low-confidence verdicts on thin packets are expected. "
          "It is not independent of the author of the profiles: the core-claims summaries that define the standard for R were LLM-drafted (then edited by the user) "
          "and the judge scored papers against them, which can favour papers that match the wording of those claims. Items judged R are a small, hand-sized sample; the V4-versus-BM25 "
          "intervals are wide and a difference inside them is not evidence either way. The repeats were judged in the same session and were not fully independent, so "
          "the consistency figure is an upper bound. Agreement with the hand labels is only as good as the small labelled sample allows (n above), the label sheet "
          "covers the top 10 per theory and not the top 30, and the labels were proposed by an AI assistant and reviewed by the user. "
          "The corpus is Europe PMC open access, so philosophy-heavy theories (panpsychism, Champagne) have thin coverage.\n")
    return o


if __name__ == "__main__":
    main()

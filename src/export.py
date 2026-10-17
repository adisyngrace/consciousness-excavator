"""Prompt 07 Step 6: small, tracked, app-ready CSV exports in results/. No embeddings, no full texts, snippets <= 200 chars,
nothing from CORE. Reads only finished tables and reports; nothing here tunes or selects anything.

usage: python -m src.export
"""
import csv
import json
import re
from pathlib import Path

import numpy as np

from src import db
from src.eval import late as EL
from src.eval.late import parse_old
from src.level2_terms import silver as S
from src.level2_terms.terms import COUNTED_SECTIONS
from src.level3_concepts import retrieve_window as RW

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
THEORIES = RW.THEORIES
NAME = {"champagne_semiotic": "Champagne", "global_workspace": "GWT", "integrated_information": "IIT", "panpsychism": "Panpsychism", "predictive_processing_fep": "PP"}
LOC_NAME = {"Champagne's semiotic account": "champagne_semiotic", "Global Workspace Theory": "global_workspace", "Integrated Information Theory": "integrated_information",
            "Panpsychism": "panpsychism", "Predictive Processing / Free Energy Principle": "predictive_processing_fep"}
SEC_ORDER = {s: i for i, s in enumerate(COUNTED_SECTIONS)}
WINDOW_NAMES = {(1995, 2015): "1995-2015", (1995, 2020): "1995-2020", (1995, 2025): "1995-2025"}
SAMPLE_CAP = {"1995-2015": "candidate pool <=2000/theory (cap not reached); background <=5000; random <=2000",
              "2016-2025": "candidate pool <=400/theory (reached for GWT, IIT, PP; not for Champagne, panpsychism); background <=3000; random 1000"}


def clip(s: str | None, n: int = 200) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def write(name: str, rows: list[dict]) -> None:
    RES.mkdir(exist_ok=True)
    with open(RES / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


# ---------------------------------------------------------------------------------------------------------
def level1(conn) -> list[dict]:
    rows = []
    for r in conn.execute("""SELECT t.name tname, r.* FROM loc_references r JOIN theories t ON t.id=r.theory_id ORDER BY t.id, r.id"""):
        pmc_xml = r["resolution_status"] == "resolved_fulltext"
        pdf = r["fulltext_kind"] == "pdf"
        rows.append({"theory": LOC_NAME[r["tname"]], "raw_reference": clip(r["raw_text"], 600), "parsed_title": r["parsed_title"] or "", "year": r["parsed_year"] or "",
                     "doi": r["doi"] or "", "pmcid": r["pmcid"] or "", "resolution_status": r["resolution_status"],
                     "oa_fulltext": "yes" if (pmc_xml or pdf) else "no",
                     "oa_route": "europe_pmc" if r["pmcid"] and pmc_xml else ("oa_pdf" if (pmc_xml or pdf) else "none")})
    return rows


def level2(conn) -> list[dict]:
    meta = {r["pmcid"]: r for r in conn.execute("SELECT pmcid, title, year, journal FROM papers")}
    win = {r[0]: r[1] for r in conn.execute("SELECT pmcid, MIN(window) FROM corpus_membership GROUP BY pmcid")}
    hits: dict[tuple[str, str], list] = {}
    for r in conn.execute("SELECT pmcid, theory, tier, section, count, snippets FROM term_hits WHERE tier IN ('strong','strong_uncorroborated','close_term') AND section!='back_matter' AND section!='references'"):
        hits.setdefault((r["pmcid"], r["theory"]), []).append(r)
    rows = []
    for f in conn.execute("SELECT pmcid, theory, direct_mention, weak_mention, any_mention_level, mention_strength FROM paper_flags WHERE any_mention_level!='none' ORDER BY theory, pmcid"):
        p, t, lvl = f["pmcid"], f["theory"], f["any_mention_level"]
        tiers = {"direct": ("strong",), "weak": ("strong_uncorroborated", "strong"), "close": ("close_term",)}[lvl]
        hs = sorted([h for h in hits.get((p, t), []) if h["tier"] in tiers], key=lambda h: SEC_ORDER.get(h["section"], 99))
        strength = f["mention_strength"] if lvl == "direct" else sum(h["count"] for h in hs)
        snip = ""
        for h in hs:
            sn = json.loads(h["snippets"] or "[]")
            if sn:
                snip = clip(sn[0])
                break
        w = win.get(p, "1995-2015")
        rows.append({"theory": t, "window": w, "pmcid": p, "title": meta[p]["title"] or "", "year": meta[p]["year"] or "", "journal": meta[p]["journal"] or "",
                     "mention_tier": lvl, "mention_strength": strength, "first_hit_section": hs[0]["section"] if hs else "", "snippet": snip,
                     "sample_cap": SAMPLE_CAP[w],
                     "sample_note": "capped/design sample of the open-access literature; counts here are NOT full totals (see window_trends.csv)"})
    return rows


def judgments() -> dict[tuple[str, str], dict]:
    mem = {r["item_id"]: r for r in csv.DictReader(open(ROOT / "data" / "judge" / "method_membership.csv"))}
    out = {}
    for r in csv.DictReader(open(RES / "judgments.csv")):
        if int(mem[r["item_id"]]["is_repeat"]):
            continue                                   # originals only; repeats are a consistency check
        out[(r["theory"], r["pmcid"])] = r
    return out


def level3_top() -> tuple[list[dict], dict]:
    cb = RW.combined()
    jud = judgments()
    rows, judged_in_1995_2015_top30 = [], {}
    for t in THEORIES:
        for (a, b), wn in WINDOW_NAMES.items():
            for r in RW.retrieve(t, a, b, 30):
                j = jud.get((t, r["pmcid"]))
                rows.append({"theory": t, "window": wn, "rank": r["rank"], "pmcid": r["pmcid"], "title": r["title"], "year": r["year"], "score_v4": round(r["score"], 4),
                             "corpus_part": r["corpus_part"], "best_claim_id": r["best_claim"], "best_claim_text": cb.claim_text.get(r["best_claim"], ""),
                             "snippet": clip(RW.snippet(r["chunk_id"], 400)), "other_theories_named": ";".join(r["names_other_theories"]),
                             "judged": "true" if j else "false", "judge_verdict": j["verdict"] if j else "", "judge_confidence": j["confidence"] if j else "",
                             "judge_reason": clip(j["reason"], 300) if j else "", "judge_evidence": clip(j["evidence"]) if j else ""})
                if wn == "1995-2015":
                    judged_in_1995_2015_top30[t] = judged_in_1995_2015_top30.get(t, 0) + bool(j)
    return rows, judged_in_1995_2015_top30


def trends(conn) -> list[dict]:
    return [{"theory": r["theory"], "year": r["year"], "hits": r["hits"], "total_oa_papers": r["total_oa"], "rate_per_10k": round(r["rate_per_10k"], 4)}
            for r in conn.execute("SELECT theory, year, hits, total_oa, rate_per_10k FROM term_counts_by_year ORDER BY theory, year")]


def parse_old_meta() -> dict:
    """n candidate-pool negatives per theory in the 1995-2015 test, from the report headers."""
    out = {}
    for ln in (ROOT / "reports" / "level3_eval_test.md").read_text().splitlines():
        m = re.match(r"## (\w+) \(.*?\): n positives = (\d+), negatives = (\d+), candidate-pool negatives = (\d+)", ln)
        if m:
            out[m.group(1)] = dict(n_pos=int(m.group(2)), n_neg=int(m.group(3)), n_cand=int(m.group(4)))
    return out


def parse_old_matrix() -> list[dict]:
    """V4 matrices of reports/level3_discriminability.md (1995-2015, all positives, no split)."""
    rows, cur, ns = [], None, None
    for ln in (ROOT / "reports" / "level3_discriminability.md").read_text().splitlines():
        m = re.match(r"## (V4|V5): (all negatives|candidate-pool negatives only)", ln)
        if m:
            cur = (m.group(1), "all_negatives" if m.group(2) == "all negatives" else "candidate_pool_only")
            continue
        if ln.startswith("## "):
            cur = None
        if cur and cur[0] == "V4" and ln.startswith("| row profile"):
            ns = [int(x) for x in re.findall(r"\(n=(\d+)\)", ln)]
        m = re.match(r"\| \*\*(\w+)\*\* \| (.*) \|$", ln)
        if cur and cur[0] == "V4" and m and ns:
            vals = [float(x.strip("*")) for x in m.group(2).split(" | ")]
            ri = [NAME[t] for t in THEORIES].index(m.group(1))
            for j, v in enumerate(vals):
                rows.append({"period": "1995-2015", "pool": cur[1], "variant": "V4", "row_profile": THEORIES[ri], "column_positives": THEORIES[j],
                             "n_column_positives": ns[j], "mean_percentile_rank": v, "is_diagonal": str(ri == j).lower()})
    return rows


def metrics(lt, pools, conn, judged_top30) -> tuple[list[dict], list[dict]]:
    res, _ = EL.evaluate(lt, pools, ())
    old, oldn = parse_old(ROOT / "reports" / "level3_eval_test.md"), parse_old_meta()
    jud = judgments()
    mem = {r["item_id"]: r for r in csv.DictReader(open(ROOT / "data" / "judge" / "method_membership.csv"))}
    tc = lambda t, a, b: conn.execute("SELECT SUM(hits), SUM(total_oa) FROM term_counts_by_year WHERE theory=? AND year BETWEEN ? AND ?", (t, a, b)).fetchone()
    loc = {r["name"]: r for r in conn.execute("""SELECT t.name, COUNT(*) refs, SUM(r.resolution_status='resolved_fulltext' OR r.fulltext_kind='pdf') ft,
        SUM(r.resolution_status='resolved_fulltext') pmc FROM loc_references r JOIN theories t ON t.id=r.theory_id GROUP BY t.name""")}
    early = {r[0] for r in conn.execute("SELECT pmcid FROM corpus_membership WHERE window='1995-2015'")}
    rows = []
    for t in THEORIES:
        o = old[NAME[t]]
        loc_r = next(v for k, v in loc.items() if LOC_NAME[k] == t)
        # R share of the V4 top 30 (1995-2015 window, the judged set): the judge file holds those items
        top30 = [r["pmcid"] for r in RW.retrieve(t, 1995, 2015, 30)]
        nj = [jud[(t, p)]["verdict"] for p in top30 if (t, p) in jud]
        h1, tot1 = tc(t, 1995, 2015)
        h2, tot2 = tc(t, 2016, 2025)
        h3, tot3 = tc(t, 1995, 2025)
        silver_1 = len(S.silver(conn, t, "exclusive") & early)
        row = {"theory": t, "loc_references": loc_r["refs"], "loc_fulltext_seeds_any_oa_route": loc_r["ft"], "loc_seeds_europe_pmc_xml": loc_r["pmc"],
               "strong_phrase_hits_1995_2015_server_side": h1, "rate_per_10k_1995_2015": round(10000 * h1 / tot1, 3),
               "strong_phrase_hits_2016_2025_server_side": h2, "rate_per_10k_2016_2025": round(10000 * h2 / tot2, 3),
               "strong_phrase_hits_1995_2025_server_side": h3,
               "mention_totals_source": "term_counts_by_year (full Europe PMC server-side counts, strong phrases, upper bound on direct mentions)",
               "silver_exclusive_1995_2015_corpus": silver_1, "silver_exclusive_2016_2025_capped_sample": len(lt.pos[t]),
               "silver_2016_2025_sample_cap": "400 candidates/theory" + (" (cap reached)" if t in ("global_workspace", "integrated_information", "predictive_processing_fep") else " (cap not reached)")}
        for v in ("V4", "BM25"):
            a, lo, hi = o["rows"][v]["cand"]
            c = res[t]["v"][v]["cand"]["auc"]
            row.update({f"{v}_cand_auc_1995_2015": a, f"{v}_cand_auc_1995_2015_ci_lo": lo, f"{v}_cand_auc_1995_2015_ci_hi": hi,
                        f"{v}_cand_auc_2016_2025": round(c[0], 3), f"{v}_cand_auc_2016_2025_ci_lo": round(c[1], 3), f"{v}_cand_auc_2016_2025_ci_hi": round(c[2], 3)})
        row.update({"cand_auc_1995_2015_n_positives": o["n"], "cand_auc_1995_2015_n_candidate_negatives": oldn[NAME[t]]["n_cand"],
                    "cand_auc_1995_2015_eval_set": "test half" if t in ("global_workspace", "predictive_processing_fep") else "all exclusive positives",
                    "cand_auc_2016_2025_n_positives": res[t]["n_pos"], "cand_auc_2016_2025_n_candidate_negatives": res[t]["n_cand"],
                    "judged_R_share_v4_top30_1995_2015": round(sum(v == "R" for v in nj) / len(nj), 3) if nj else "", "judged_n": len(nj),
                    "judge_note": "LLM judge, 1995-2015 V4 top 30 only; 2016-2025 papers are unjudged"})
        rows.append(row)
    # discriminability: 1995-2015 from the report, 2016-2025 recomputed (all years, V4)
    disc = parse_old_matrix()
    npos = {t: int(EL.masks(lt, pools[t][0], t, ())[0].sum()) for t in THEORIES}
    for restrict in (False, True):
        M = EL.matrix(lt, pools, (), restrict, "V4")
        for i, tr in enumerate(THEORIES):
            for j, tc_ in enumerate(THEORIES):
                disc.append({"period": "2016-2025", "pool": "candidate_pool_only" if restrict else "all_negatives", "variant": "V4", "row_profile": tr, "column_positives": tc_,
                             "n_column_positives": npos[tc_], "mean_percentile_rank": round(float(M[i, j]), 1), "is_diagonal": str(i == j).lower()})
    return rows, disc


def main() -> None:
    conn = db.connect()
    write("level1_references.csv", level1(conn))
    write("level2_mentions.csv", level2(conn))
    write("window_trends.csv", trends(conn))
    top, judged = level3_top()
    write("level3_top.csv", top)
    print("judged papers in 1995-2015 top 30 per theory:", judged)
    lt = EL.Late()
    pools = {t: EL.build_pool(lt, t) for t in THEORIES}
    summary, disc = metrics(lt, pools, conn, judged)
    write("summary_metrics.csv", summary)
    write("discriminability.csv", disc)


if __name__ == "__main__":
    main()

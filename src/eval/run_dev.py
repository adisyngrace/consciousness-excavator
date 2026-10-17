"""Step 3 of prompt 05: run every pre-registered variant on the DEV halves of GWT and PP (test halves are never read).

usage: python -m src.eval.run_dev      -> reports/level3_eval_dev.md
Selection rule (reports/eval_plan.md): highest mean AUC over the two dev sets; variants within 0.01 of the best are
tied and the lowest mean hub rate wins; BM25 is a baseline, not selectable.
"""
import json
from collections import Counter

import numpy as np

from src.eval import positives as P
from src.eval.metrics import summarize
from src.eval.scoring import THEORIES, VARIANTS, bank, build_pool

DEV = ["global_workspace", "predictive_processing_fep"]
SHORT = {"global_workspace": "GWT", "predictive_processing_fep": "PP", "integrated_information": "IIT", "panpsychism": "Panpsychism", "champagne_semiotic": "Champagne"}
HUB_K = 50


def eval_positives(splits: dict, t: str, which: str = "dev") -> list[str]:
    s = splits["split"].get(t)
    return s[which] if s else splits["positives"][t]


def masks(pool, bk, t: str, pos: list[str]):
    names0 = np.array([bk.flag.get((p, t), 1) == 0 for p in pool.papers])
    is_pos = np.isin(pool.papers, pos)
    return is_pos, names0 & ~is_pos


def fmt(x, pct=False) -> str:
    m, lo, hi = x
    return f"{m:.1f} [{lo:.1f}, {hi:.1f}]" if pct else f"{m:.3f} [{lo:.3f}, {hi:.3f}]"


def main() -> None:
    bk = bank()
    splits = json.loads((P.EVAL / "splits.json").read_text())
    pools = {t: build_pool(t, True) for t in THEORIES}
    unmasked = {t: build_pool(t, False) for t in DEV}
    pos_eval = {t: eval_positives(splits, t) for t in THEORIES}
    # ---- top-50 per theory per variant (pool = eligible negatives + eval positives), for the hub rate
    top: dict[str, dict[str, list[str]]] = {v: {} for v in VARIANTS}
    for t in THEORIES:
        pl = pools[t]
        is_pos, is_neg = masks(pl, bk, t, pos_eval[t])
        elig = np.where(is_pos | is_neg)[0]
        for v in VARIANTS:
            o = elig[np.argsort(-pl.scores[v][elig], kind="stable")][:HUB_K]
            top[v][t] = list(pl.papers[o])
    hub, hubcount = {}, {}
    for v in VARIANTS:
        cnt = Counter(p for t in THEORIES for p in top[v][t])
        hubcount[v] = cnt
        for t in THEORIES:
            hub[v, t] = float(np.mean([cnt[p] >= 3 for p in top[v][t]]))     # in own list + >= 2 other theories' lists
    # ---- metrics
    res, cand, mu = {}, {}, {}
    for t in DEV:
        pl, pu = pools[t], unmasked[t]
        is_pos, is_neg = masks(pl, bk, t, pos_eval[t])
        is_cand = is_neg & np.array([bk.part_of[p] == "candidate" for p in pl.papers])
        upos = np.isin(pu.papers, pos_eval[t])
        uneg = np.isin(pu.papers, pl.papers[is_neg])
        for v in VARIANTS:
            s = pl.scores[v]
            res[v, t] = summarize(s[is_pos], s[is_neg])
            cand[v, t] = summarize(s[is_pos], s[is_cand])
            su = pu.scores[v]
            ru = summarize(su[upos], su[uneg])
            mu[v, t] = {"auc_unmasked": ru["auc"], "auc_masked": res[v, t]["auc"],
                        "score_unmasked": float(su[upos].mean()), "score_masked": float(s[is_pos].mean()),
                        "neg_mean": float(s[is_neg].mean()), "neg_sd": float(s[is_neg].std())}
    # ---- selection
    mean_auc = {v: float(np.mean([res[v, t]["auc"][0] for t in DEV])) for v in VARIANTS}
    mean_hub = {v: float(np.mean([hub[v, t] for t in DEV])) for v in VARIANTS}
    cands = [v for v in VARIANTS if v != "BM25"]
    best = max(cands, key=lambda v: mean_auc[v])
    tied = [v for v in cands if mean_auc[best] - mean_auc[v] <= 0.01]
    chosen = min(tied, key=lambda v: mean_hub[v])
    beats_bm25 = {v: [res[v, t]["auc"][0] > res["BM25", t]["auc"][0] for t in DEV] for v in cands}
    # ---- mix
    mix = {}
    for t in THEORIES:
        pl = pools[t]
        is_pos, is_neg = masks(pl, bk, t, pos_eval[t])
        mix[t] = {"pos": Counter(bk.part_of[p] for p in pl.papers[is_pos]), "neg": Counter(bk.part_of[p] for p in pl.papers[is_neg])}
    L = ["# Level 3 evaluation: DEV results (prompt 05, Step 3)", "", "Pre-registered plan: `reports/eval_plan.md`. Test halves of GWT and PP were NOT read.", ""]
    summ = P.EVAL / "dev_summary.md"
    L += [summ.read_text() if summ.exists() else "_(summary pending)_", ""]
    L += ["## Selection rule applied", "",
          f"Mean dev AUC (GWT, PP): " + ", ".join(f"{v} {mean_auc[v]:.3f}" for v in VARIANTS) + ".", "",
          f"Best non-baseline: **{best}**; within 0.01 of it (tied): {', '.join(tied)}; mean hub rates of the tied: "
          + ", ".join(f"{v} {mean_hub[v]:.2f}" for v in tied) + f". **Rule selects: {chosen}.**", "",
          "BM25 loses to / beats each variant on dev AUC (GWT, PP): " + "; ".join(f"{v}: {'beats BM25' if all(b) else ('mixed' if any(b) else 'loses to BM25')}" for v, b in beats_bm25.items()) + ".", ""]
    L += ["## Notes on the metrics", "",
          "- AUC is the probability that a masked positive outscores a random negative; with negatives only, mean percentile rank equals 100 x AUC, so the two columns carry the same information (both kept as pre-registered).",
          "- Recall@k: share of positives whose rank among the negatives (1 + number of negatives scoring higher) is <= k. Chance = k / n_neg.",
          "- Negatives are *unlabeled*, not known irrelevant: genuine conceptual neighbours are scored as errors, so every number is a lower bound and the comparison between variants matters more than the absolute values.",
          "- 95% CIs: 2,000 bootstrap resamples of the positives (negatives fixed), seed 20261011.",
          "- Hub rate: share of the variant's top 50 for the theory that is also in the top 50 of >= 2 other theories (each theory's top 50 drawn from its own pool: eligible negatives + eval positives; GWT/PP use dev positives only; the other three use all their positives).", ""]
    L += ["## Corpus-part mix of positives and negatives (1995-2015)", "",
          "| theory | n pos | pos seed/cand/bg/rand | n neg | neg seed/cand/bg/rand | pos cand % | neg cand % |", "|---|---|---|---|---|---|---|"]
    parts = ("seed", "candidate", "background", "random")
    for t in THEORIES:
        p, n = mix[t]["pos"], mix[t]["neg"]
        sp, sn = sum(p.values()), sum(n.values())
        L.append(f"| {SHORT[t]}{' (dev)' if t in DEV else ''} | {sp} | {'/'.join(str(p[k]) for k in parts)} | {sn} | {'/'.join(str(n[k]) for k in parts)} | {100*p['candidate']/max(sp,1):.0f}% | {100*n['candidate']/max(sn,1):.0f}% |")
    L += ["", "Positives are drawn from the Level 2 silver set, so they over-represent the theory-term candidate pool; a variant that merely prefers candidate-pool papers gains an advantage on the all-negatives AUC. The candidate-only AUC below removes that.", ""]
    for t in DEV:
        r0 = res["V0", t]
        L += [f"## {SHORT[t]} dev (n positives = {r0['n_pos']}, n negatives = {r0['n_neg']}; candidate-pool negatives = {cand['V0', t]['n_neg']})", "",
              "| variant | AUC [95% CI] | recall@50 | recall@100 | recall@200 | mean pct rank [95% CI] | AUC vs candidate negatives only | hub rate |", "|---|---|---|---|---|---|---|---|"]
        for v in VARIANTS:
            r = res[v, t]
            L.append(f"| {v} | {fmt(r['auc'])} | {fmt(r['r50'])} | {fmt(r['r100'])} | {fmt(r['r200'])} | {fmt(r['mpr'], True)} | {fmt(cand[v, t]['auc'])} | {hub[v, t]:.2f} |")
        ch = r0["chance"]
        L.append(f"| *chance* | {ch['auc']:.3f} | {ch['r50']:.3f} | {ch['r100']:.3f} | {ch['r200']:.3f} | {ch['mpr']:.1f} | 0.500 | - |")
        L.append("")
    L += ["## Mask-artifact control (dev positives): masked vs unmasked text", "",
          "Same dev positives and same negatives; unmasked = original main-index chunks. Score columns are the variant's own units (mean over dev positives). `z-shift` expresses the masked-minus-unmasked mean score change in negative-pool SDs.", "",
          "| theory | variant | AUC unmasked | AUC masked | mean score unmasked | mean score masked | z-shift (SD of negatives) |", "|---|---|---|---|---|---|---|"]
    for t in DEV:
        for v in VARIANTS:
            m = mu[v, t]
            L.append(f"| {SHORT[t]} | {v} | {m['auc_unmasked'][0]:.3f} | {m['auc_masked'][0]:.3f} | {m['score_unmasked']:.3f} | {m['score_masked']:.3f} | {(m['score_masked'] - m['score_unmasked']) / m['neg_sd']:+.2f} |")
    L += ["", "## Most frequent hub papers (in the top 50 of several theories), per variant", ""]
    for v in VARIANTS:
        L.append(f"**{v}**: " + "; ".join(f"{p} ({c} theories) {bk.title.get(p, '')[:60]}" for p, c in hubcount[v].most_common(10) if c > 1) or "none")
        L.append("")
    (P.EVAL.parent.parent / "reports" / "level3_eval_dev.md").write_text("\n".join(L))
    json.dump({"chosen": chosen, "mean_auc": mean_auc, "mean_hub": mean_hub}, open(P.EVAL / "dev_selection.json", "w"), indent=1)
    print("chosen:", chosen, "\nmean AUC:", mean_auc, "\nmean hub:", mean_hub)


if __name__ == "__main__":
    main()

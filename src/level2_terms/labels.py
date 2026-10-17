"""Hand-labelled precision audit: reports/precision_audit_labels.csv and the per-term precision computed from it.

Labels are the user's (Y = true positive, N = false positive, ? = undecided; weak mentions are Y with a note).
`snippet_id` is the 1-based position in that theory's numbered list in the audit section of the Level 2 report
(same order as reports/level2_precision_audit.csv).
"""
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "reports" / "level2_precision_audit.csv"
LABELS = ROOT / "reports" / "precision_audit_labels.csv"
FIELDS = ["theory", "snippet_id", "pmcid", "term", "label", "note"]

# theory -> {snippet_id: (label, note)}; ids not listed default to ("Y", "")
OVERRIDES = {
    "global_workspace": {16: ("Y", "weak mention")},
    "integrated_information": {16: ("Y", "weak mention")},
    "panpsychism": {i: ("Y", "weak mention") for i in (9, 14, 16, 18)},
    "predictive_processing_fep": {
        4: ("N", "'predictive machine' (not the theory)"),
        10: ("N", "'predictive machine' (not the theory)"),
        11: ("?", "low-level LGN physiology; undecided"),
        18: ("Y", "weak mention"),
        20: ("N", "generic 'predictive processing' in a speech paper"),
    },
    "champagne_semiotic": {i: ("Y", "Peircean sense, but not about consciousness") for i in (1, 2, 3)},
}


def build_labels() -> list[dict]:
    seen, out = defaultdict(int), []
    for r in csv.DictReader(SAMPLE.open(encoding="utf-8")):
        seen[r["theory"]] += 1
        sid = seen[r["theory"]]
        lab, note = OVERRIDES.get(r["theory"], {}).get(sid, ("Y", ""))
        out.append({"theory": r["theory"], "snippet_id": sid, "pmcid": r["pmcid"], "term": r["term"], "label": lab, "note": note})
    return out


def write_labels() -> list[dict]:
    rows = build_labels()
    with LABELS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def read_labels() -> list[dict]:
    return list(csv.DictReader(LABELS.open(encoding="utf-8"))) if LABELS.exists() else []


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def per_term(rows: list[dict]) -> dict:
    """(theory, term) -> counts. Each (paper, term) appears once in the sample, so n_hits == n_papers per term;
    undecided ('?') is excluded from the precision denominator."""
    out = defaultdict(lambda: {"Y": 0, "N": 0, "?": 0, "weak": 0, "papers": set()})
    for r in rows:
        d = out[(r["theory"], r["term"])]
        d[r["label"]] += 1
        d["weak"] += "weak" in r["note"]
        d["papers"].add(r["pmcid"])
    return out


def per_theory_unique(rows: list[dict]) -> dict:
    """theory -> {pmcid: set(labels)}: dedupe by paper so a paper audited on several terms counts once."""
    out = defaultdict(lambda: defaultdict(set))
    for r in rows:
        out[r["theory"]][r["pmcid"]].add(r["label"])
    return out


def paper_repetition(rows: list[dict]) -> list[tuple]:
    """Papers appearing in more than one audit row (across all theories): (pmcid, n_rows, {theory: n})."""
    c = defaultdict(lambda: defaultdict(int))
    for r in rows:
        c[r["pmcid"]][r["theory"]] += 1
    return sorted(((p, sum(t.values()), dict(t)) for p, t in c.items() if sum(t.values()) > 1), key=lambda x: -x[1])

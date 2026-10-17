"""Step 3 of prompt 06: validate judgments against the rubric schema and the packets, load valid ones into SQLite.

Reads data/judge/packets/batch_NN.md and data/judge/judgments/batch_NN.json (never any results file).
Valid judgments go to table `judgments` in data/project.db; failures are printed with reasons and not loaded.
`pmcid` is left NULL here (the item -> paper map lives in the method-membership file, which stays closed until Step 4).
usage: python -m src.judge.ingest [--db PATH] [--judge-dir PATH]
"""
import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEYS = {"item_id", "verdict", "confidence", "claim_ids", "reason", "evidence", "names_theory_in_text", "better_fit_theory"}
VERDICTS = {"R", "G", "O"}
CONFIDENCE = {"high", "medium", "low"}
THEORY_NAMES = {"Champagne's semiotic account", "Global Workspace Theory", "Integrated Information Theory",
                "Panpsychism", "Predictive Processing / Free Energy Principle"}
MAX_EVIDENCE_WORDS = 20

SCHEMA = """CREATE TABLE IF NOT EXISTS judgments (
    item_id TEXT PRIMARY KEY, theory TEXT NOT NULL, pmcid TEXT, verdict TEXT NOT NULL, confidence TEXT NOT NULL,
    claim_ids TEXT NOT NULL, reason TEXT NOT NULL, evidence TEXT NOT NULL, flags TEXT NOT NULL)"""


def norm(s: str) -> str:
    return " ".join(s.split())


def parse_packet(text: str) -> dict:
    """-> {'theory': code, 'claim_ids': set, 'items': {item_id: normalized item text}}"""
    theory = re.search(r"\*\*Theory:\*\*.*\(([a-z_]+)\)", text).group(1)
    claim_ids = set(re.findall(r"^- \*\*([\w-]+):\*\*", text, re.M))
    parts = re.split(r"^### Item (\S+)\s*$", text, flags=re.M)
    items = {parts[i]: norm(parts[i + 1]) for i in range(1, len(parts), 2)}
    return {"theory": theory, "claim_ids": claim_ids, "items": items}


def validate(j: object, packet: dict) -> list[str]:
    """Return a list of problems (empty = valid)."""
    if not isinstance(j, dict):
        return ["not an object"]
    errs = []
    if set(j) != KEYS:
        errs.append(f"keys differ: missing {sorted(KEYS - set(j))} extra {sorted(set(j) - KEYS)}")
        return errs
    iid = j["item_id"]
    if iid not in packet["items"]:
        return [f"item_id {iid} not in packet"]
    if j["verdict"] not in VERDICTS:
        errs.append(f"bad verdict {j['verdict']!r}")
    if j["confidence"] not in CONFIDENCE:
        errs.append(f"bad confidence {j['confidence']!r}")
    c = j["claim_ids"]
    if not isinstance(c, list) or not all(isinstance(x, str) for x in c):
        errs.append("claim_ids not a list of strings")
    else:
        if j["verdict"] == "R" and not c:
            errs.append("verdict R but claim_ids empty")
        if j["verdict"] != "R" and c:
            errs.append("claim_ids non-empty but verdict not R")
        bad = [x for x in c if x not in packet["claim_ids"]]
        if bad:
            errs.append(f"unknown claim ids {bad}")
    for k in ("reason", "evidence"):
        if not isinstance(j[k], str) or not j[k].strip():
            errs.append(f"{k} empty or not a string")
    if not isinstance(j["names_theory_in_text"], bool):
        errs.append("names_theory_in_text not boolean")
    b = j["better_fit_theory"]
    if b is not None and b not in THEORY_NAMES:
        errs.append(f"better_fit_theory {b!r} not a theory name")
    ev = j["evidence"]
    if isinstance(ev, str) and ev.strip():
        if len(ev.split()) > MAX_EVIDENCE_WORDS:
            errs.append(f"evidence has {len(ev.split())} words (> {MAX_EVIDENCE_WORDS})")
        if norm(ev) not in packet["items"][iid]:
            errs.append("evidence not verbatim in packet")
    return errs


def flags_of(j: dict) -> list[str]:
    f = []
    if j["names_theory_in_text"]:
        f.append("names_theory_in_text")
    if j["better_fit_theory"]:
        f.append(f"better_fit:{j['better_fit_theory']}")
    return f


def ingest(judge_dir: Path, db: Path) -> tuple[int, list[tuple[str, str]]]:
    """Return (n_loaded, failures[(item_id or batch, problem)])."""
    failures, rows = [], []
    for pk in sorted((judge_dir / "packets").glob("batch_*.md")):
        packet = parse_packet(pk.read_text())
        jf = judge_dir / "judgments" / (pk.stem + ".json")
        if not jf.exists():
            failures.append((pk.stem, "judgment file missing"))
            continue
        try:
            data = json.loads(jf.read_text())
        except json.JSONDecodeError as e:
            failures.append((pk.stem, f"invalid JSON: {e}"))
            continue
        if not isinstance(data, list):
            failures.append((pk.stem, "top level is not a list"))
            continue
        seen = set()
        for j in data:
            iid = j.get("item_id", "?") if isinstance(j, dict) else "?"
            errs = validate(j, packet)
            if iid in seen:
                errs.append("duplicate item_id")
            seen.add(iid)
            if errs:
                failures.append((iid, "; ".join(errs)))
                continue
            rows.append((iid, packet["theory"], None, j["verdict"], j["confidence"], json.dumps(j["claim_ids"]),
                         j["reason"], j["evidence"], json.dumps(flags_of(j))))
        for iid in sorted(set(packet["items"]) - seen):
            failures.append((iid, "item has no judgment"))
    conn = sqlite3.connect(db)
    conn.execute(SCHEMA)
    ids = [r[0] for r in rows]
    conn.executemany("DELETE FROM judgments WHERE item_id=?", [(i,) for i in ids])
    conn.executemany("INSERT INTO judgments VALUES (?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    return len(rows), failures


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "project.db"))
    ap.add_argument("--judge-dir", default=str(ROOT / "data" / "judge"))
    a = ap.parse_args()
    n, failures = ingest(Path(a.judge_dir), Path(a.db))
    print(f"loaded {n} valid judgments into {a.db}")
    print(f"failures: {len(failures)}")
    for iid, why in failures:
        print(f"  {iid}: {why}")


if __name__ == "__main__":
    main()

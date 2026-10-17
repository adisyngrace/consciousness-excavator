"""Write results/theory_descriptions.csv: first two sentences of each theory's main LoC page, verbatim.

The main page is the first slug in src/config.THEORIES. The "Key Takeaways" box (a bullet summary, not prose) is skipped;
the excerpt starts at the first prose segment. Sentence split: ". " followed by a capital, excluding known initials/abbrevs.
"""
import csv
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FILES = ["champagne", "gwt", "iit", "panpsychism", "predictive_processing"]
BASE = "https://loc.closertotruth.com/theory/"
NO_SPLIT = ("S", "Dr", "St", "et al", "e.g", "i.e", "vs", "cf")


def first_sentences(text: str, n: int = 2) -> str:
    out, start = [], 0
    for m in re.finditer(r"([.!?])(?:[”\"’)\]]*)\s+(?=[A-Z“\"(\[])", text):
        before = text[start:m.start()].split()[-1] if text[start:m.start()].split() else ""
        if m.group(1) == "." and (before in NO_SPLIT or re.fullmatch(r"[A-Z]", before)):
            continue
        out.append(text[start:m.end()].strip())
        start = m.end()
        if len(out) == n:
            break
    return " ".join(out)


def main() -> None:
    rows = []
    for f in FILES:
        d = yaml.safe_load((ROOT / "profiles" / f"{f}.yaml").read_text())
        page = d["loc_description_pages"][0]
        seg = next(s for s in page["segments"] if not s["text"].startswith("Key Takeaways"))
        rows.append({"theory": d["key"], "theory_name": d["theory"], "excerpt": first_sentences(seg["text"]),
                     "source_url": BASE + page["slug"]})
    with open(ROOT / "results" / "theory_descriptions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r["theory"], "|", r["excerpt"], "|", r["source_url"], "\n")


if __name__ == "__main__":
    main()

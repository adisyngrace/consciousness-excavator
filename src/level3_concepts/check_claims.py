"""Term check for profile core claims against the FROZEN terms.yaml (uses the scanner's own regexes).

Forbidden in a claim: any strong / close_term / needs_corroboration term or abbreviation of ANY theory, theory names,
and author surnames (landmark surnames plus a manual list). `adjacent` terms are reported as info only.

usage: python -m src.level3_concepts.check_claims [dir]     (default profiles/claims_revised; files <stem>.yaml)
"""
import re
import sys
from pathlib import Path

import yaml

from src.level2_terms.terms import TERMS_PATH, load_terms
from src.level3_concepts.make_profiles import PROFILES

NAME_WORDS = ["global workspace", "integrated information", "information integration", "panpsychis", "predictive processing",
              "free energy", "free-energy", "semiotic account", "semiotics", "global neuronal", "predictive coding"]
AUTHORS = ["Peirce", "Champagne", "Baars", "Dehaene", "Naccache", "Changeux", "Sergent", "Tononi", "Koch", "Oizumi", "Balduzzi",
           "Chalmers", "Goff", "Strawson", "Nagasawa", "Kadić", "Starrett", "Wallace", "Faggin", "Mørch", "Harris", "Hunt", "Schooler",
           "Friston", "Clark", "Seth", "Gregory", "Llin", "Helmholtz", "Husserl", "Deely", "Searle", "Carroll", "Russell", "Leibniz", "Block", "Papineau"]


def check(text: str, terms, surnames: list[str]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {"forbidden": [], "adjacent": [], "name_or_author": []}
    for th in terms.theories.values():
        if th.main_rx:
            for m in th.main_rx.finditer(text):
                term, tier = th.main_groups[m.lastgroup]
                hits["adjacent" if tier == "adjacent" else "forbidden"].append(f"{th.key}:{tier}:{m.group(0)}")
        if th.abbr_rx:
            hits["forbidden"] += [f"{th.key}:abbreviation:{m.group(0)}" for m in th.abbr_rx.finditer(text)]
    low = text.lower()
    hits["name_or_author"] += [w for w in NAME_WORDS if w in low]
    hits["name_or_author"] += [a for a in AUTHORS + surnames if re.search(rf"(?<!\w){re.escape(a)}", text)]
    return hits


def landmark_surnames() -> list[str]:
    doc = yaml.safe_load(TERMS_PATH.read_text())
    out = set()
    for th in doc["theories"].values():
        for lm in th.get("landmark_refs") or []:
            for s in ([lm.get("surname")] if lm.get("surname") else []) + list(lm.get("surnames") or []):
                out.add(s)
    return sorted(x for x in out if x and len(x) > 3)


def main(folder: Path) -> int:
    terms, sn, bad = load_terms(), landmark_surnames(), 0
    for f in sorted(folder.glob("*.yaml")):
        for c in (yaml.safe_load(f.read_text()) or {}).get("core_claims", []):
            h = check(c["text"], terms, sn)
            n_sent = len(re.findall(r"[.!?](?:\s|$)", c["text"]))
            flag = "FAIL" if h["forbidden"] or h["name_or_author"] else "ok"
            bad += flag == "FAIL"
            extra = {k: v for k, v in h.items() if v}
            print(f"{flag:4} {c['id']:28} sentences={n_sent} {extra if extra else ''}")
    print(f"\n{bad} claim(s) with a forbidden term, theory name or author")
    return bad


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else PROFILES / "claims_revised")

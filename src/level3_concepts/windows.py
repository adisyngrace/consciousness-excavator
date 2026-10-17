"""Profile components: LoC description pages -> use_in_profile flags -> ~150-word windows -> equal per-theory cap.

`loc_description` in each profile YAML stays exactly as stored. `loc_description_pages` splits it at the `## slug`
sub-page boundaries into segments (paragraphs; the Peirce "Note on Placement" is its own segment), each with a
`use_in_profile` flag. Text is never deleted: a False flag only keeps it out of the windows.

Windows: per kept page, the kept segments are joined and cut into n = max(1, round(words/150)) equal windows (never
across pages). Every theory is then capped at the smallest theory's window count: the cap is shared evenly over the
theory's kept pages (water-filling, at least one per page when cap >= pages) and, inside a page, windows are picked at
evenly spaced positions.

Components and weights (profiles/config.yaml, weights multiply cosine similarity in Step 4): core_claim 1.0,
description_window 0.5, seed_abstract 0.5.

usage: python -m src.level3_concepts.windows [--apply-flags]     (prints window counts and the capped allocation)
"""
import argparse
import re
from pathlib import Path

import yaml

from src import db
from src.level3_concepts import make_profiles as mp   # registers the YAML literal-block representer

PROFILES = mp.PROFILES
TARGET_WORDS = 150
DROP_PAGES = {"koch-compares-integrated-information-theory-with-panpsychism",
              "faggin-s-quantum-information-based-panpsychism", "panpsychism-additional-theories",
              "ostendorf-s-predictive-pattern-driven-interface"}                  # user decision 2026-10-11
SPLIT_AT = {"peirce-s-phaneroscopic-semiotics": "A Note on Placement"}           # marker starts a separate segment
DROP_SEGMENTS = {("peirce-s-phaneroscopic-semiotics", "note-on-placement")}
DEFAULT_WEIGHTS = {"core_claim": 1.0, "description_window": 0.5, "seed_abstract": 0.5}


def split_pages(desc: str) -> list[dict]:
    parts = re.split(r"(?m)^## (\S+)\n", desc)
    pages = []
    for slug, body in zip(parts[1::2], parts[2::2]):
        body = body.strip()
        segs, marker = [], SPLIT_AT.get(slug)
        if marker and marker in body:
            head, tail = body.split(marker, 1)
            texts = [("body", head.strip()), ("note-on-placement", (marker + tail).strip())]
        else:
            texts = [(f"p{i}", t.strip()) for i, t in enumerate(body.split("\n"), 1) if t.strip()]
        for sid, t in texts:
            segs.append({"id": sid, "use_in_profile": (slug, sid) not in DROP_SEGMENTS, "text": t})
        pages.append({"slug": slug, "chars": len(body), "use_in_profile": slug not in DROP_PAGES, "segments": segs})
    return pages


def apply_flags(stem: str) -> None:
    """Add/refresh loc_description_pages in profiles/<stem>.yaml (flags re-derived from the decisions above)."""
    p = PROFILES / f"{stem}.yaml"
    d = yaml.safe_load(p.read_text())
    d["loc_description_pages"] = split_pages(d["loc_description"])
    p.write_text(yaml.dump(d, sort_keys=False, allow_unicode=True, width=110))


def page_windows(page: dict) -> list[str]:
    if not page["use_in_profile"]:
        return []
    w = " ".join(s["text"] for s in page["segments"] if s["use_in_profile"]).split()
    if not w:
        return []
    n = max(1, round(len(w) / TARGET_WORDS))
    size = len(w) / n
    return [" ".join(w[round(i * size):round((i + 1) * size)]) for i in range(n)]


def allocate(avail: list[int], cap: int) -> list[int]:
    """Share `cap` windows evenly over pages (water-filling), never more than a page has."""
    alloc = [0] * len(avail)
    left = min(cap, sum(avail))
    while left > 0:
        open_ = [i for i, a in enumerate(avail) if alloc[i] < a]
        share, extra = divmod(left, len(open_))
        order = sorted(open_, key=lambda i: avail[i] - alloc[i], reverse=True)   # remainder goes to the roomiest pages
        for rank, i in enumerate(order):
            give = min(share + (1 if rank < extra else 0), avail[i] - alloc[i])
            alloc[i] += give
            left -= give
        if share == 0 and extra == 0:
            break
    return alloc


def pick(n_avail: int, k: int) -> list[int]:
    if k >= n_avail:
        return list(range(n_avail))
    return sorted({round((i + 0.5) * n_avail / k - 0.5) for i in range(k)})


def capped_windows(pages_by_theory: dict[str, list[dict]], cap: int | None = None) -> tuple[int, dict[str, list[tuple[str, int, str]]]]:
    """-> (cap, {stem: [(slug, window_index, text)]})."""
    full = {s: [(pg["slug"], page_windows(pg)) for pg in pages if pg["use_in_profile"]] for s, pages in pages_by_theory.items()}
    cap = cap or min(sum(len(w) for _, w in v) for v in full.values())
    out = {}
    for stem, pw in full.items():
        alloc = allocate([len(w) for _, w in pw], cap)
        out[stem] = [(slug, j, w[j]) for (slug, w), k in zip(pw, alloc) for j in pick(len(w), k)]
    return cap, out


def theory_stems() -> list[str]:
    return [stem for _, (_, stem) in mp.THEORIES.items()]


def load_profile(stem: str) -> dict:
    return yaml.safe_load((PROFILES / f"{stem}.yaml").read_text())


def load_weights() -> dict:
    p = PROFILES / "config.yaml"
    return {**DEFAULT_WEIGHTS, **(yaml.safe_load(p.read_text()).get("weights", {}) if p.exists() else {})}


def components(cap_windows: dict[str, list[tuple[str, int, str]]]) -> dict[str, list[dict]]:
    """Profile components per theory: claims (query-prefixed at embedding time), capped description windows, seed abstracts."""
    w = load_weights()
    out = {}
    for stem in theory_stems():
        d = load_profile(stem)
        comps = [{"id": c["id"], "kind": "core_claim", "weight": w["core_claim"], "text": c["text"]} for c in d["core_claims"]]
        comps += [{"id": f"{stem}-w{i}:{slug}#{j}", "kind": "description_window", "weight": w["description_window"], "text": t}
                  for i, (slug, j, t) in enumerate(cap_windows[stem], 1)]
        comps += [{"id": f"{stem}-s{i}", "kind": "seed_abstract", "weight": w["seed_abstract"], "text": s["text"]}
                  for i, s in enumerate(d.get("seed_passages") or [], 1)]
        out[stem] = comps
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-flags", action="store_true")
    args = ap.parse_args()
    if args.apply_flags:
        for stem in theory_stems():
            apply_flags(stem)
    pages = {s: load_profile(s)["loc_description_pages"] for s in theory_stems()}
    cap, capped = capped_windows(pages)
    print(f"{'theory':24} pages kept/total  words kept  windows(uncapped) -> capped (cap={cap})")
    for stem, pgs in pages.items():
        kept = [p for p in pgs if p["use_in_profile"]]
        words = sum(len(" ".join(s["text"] for s in p["segments"] if s["use_in_profile"]).split()) for p in kept)
        nw = sum(len(page_windows(p)) for p in kept)
        print(f"{stem:24} {len(kept):2}/{len(pgs):2}            {words:6}      {nw:3} -> {len(capped[stem])}")
    print("\nallocation per page (capped windows):")
    for stem, ws in capped.items():
        c = {}
        for slug, _, _ in ws:
            c[slug] = c.get(slug, 0) + 1
        print(f"  {stem}: {c}")
    print("\ndropped:", [(s, p['slug']) for s, pgs in pages.items() for p in pgs if not p["use_in_profile"]],
          "| dropped segments:", [(p['slug'], g['id']) for pgs in pages.values() for p in pgs for g in p['segments'] if not g['use_in_profile']])

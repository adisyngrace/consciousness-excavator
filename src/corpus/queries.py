"""Search definitions for the 1995-2015 corpus.

The theory phrases here are a DRAFT used only to pull the candidate pool. The authoritative term lists
live in src/terms.yaml (Step 2); re-running the candidate stage after editing them is cheap because
XML already on disk is never re-downloaded.
"""
YEARS = (1995, 2015)
BASE = f"OPEN_ACCESS:y AND HAS_FT:y AND PUB_YEAR:[{YEARS[0]} TO {YEARS[1]}]"

# Quoted phrases only: Europe PMC expands unquoted terms (stemming/synonyms).
# Deliberately omitted as too generic (checked 1995-2015 OA hit counts):
#   "integrated information" (813 hits, mostly multisensory integration), "prescission" (923 hits, almost all
#   PreScission protease in methods sections), bare "attention"/"prediction"/"information".
THEORY_QUERIES = {
    "Champagne's semiotic account": [
        '"Peircean"', '"semiotic theory"', '"semiotic account"', '"phaneroscopy"', '("Peirce" AND "consciousness")',
    ],
    "Global Workspace Theory": [
        '"global workspace"', '"global neuronal workspace"', '"global neuronal workspace theory"',
    ],
    "Integrated Information Theory": [
        '"integrated information theory"',
    ],
    "Panpsychism": [
        '"panpsychism"', '"panpsychist"', '"panpsychic"', '"micropsychism"', '"cosmopsychism"', '"panprotopsychism"',
    ],
    "Predictive Processing / Free Energy Principle": [
        '"free energy principle"', '"predictive processing"', '"predictive coding"', '"active inference"',
        '"Bayesian brain"', '"predictive brain"',
    ],
}

# Adjacent-topic pool (title/abstract mention only), excluding papers that name any theory phrase above.
BACKGROUND_TOPICS = {
    "prediction error": 'RAW:((TITLE:"prediction error" OR ABSTRACT:"prediction error") AND (TITLE:brain OR ABSTRACT:brain OR TITLE:neural OR ABSTRACT:neural OR TITLE:dopamine OR ABSTRACT:dopamine OR TITLE:cortex OR ABSTRACT:cortex OR TITLE:perception OR ABSTRACT:perception OR TITLE:cognitive OR ABSTRACT:cognitive OR TITLE:learning OR ABSTRACT:learning))',
    "hierarchical Bayesian inference": '("hierarchical Bayesian" OR "Bayesian inference")',
    # tightened after a title audit: bare "attention", "emergence" and "prediction error" matched everyday senses
    # (alcoholic liver disease, drug resistance, pharmacokinetics); RAW: = used verbatim, not title/abstract-wrapped.
    "attention": 'RAW:(TITLE:"selective attention" OR ABSTRACT:"selective attention" OR TITLE:"attentional" OR ABSTRACT:"attentional" OR TITLE:"visual attention" OR ABSTRACT:"visual attention" OR TITLE:"spatial attention" OR ABSTRACT:"spatial attention" OR TITLE:"sustained attention" OR ABSTRACT:"sustained attention" OR TITLE:"attention network" OR ABSTRACT:"attention network" OR TITLE:"attentional blink" OR ABSTRACT:"attentional blink")',
    "working memory": '"working memory"',
    "perceptual awareness": '("perceptual awareness" OR "visual awareness" OR "conscious perception")',
    "binocular rivalry": '"binocular rivalry"',
    "anesthesia": '("anesthesia" OR "anaesthesia" OR "anesthetic")',
    "semiotics": '("semiotics" OR "semiotic")',
    "symbol grounding": '"symbol grounding"',
    # semiotics-adjacent (added at Step 2 checkpoint): sign/meaning theory and phenomenology that never name the
    # theory. Bare "semiotic(s)" is already above; "sign" alone is far too generic so only compound phrases here.
    "biosemiotics": '("biosemiotics" OR "biosemiotic" OR "semiosis" OR "zoosemiotics")',
    "Peirce sign theory": '(("Peirce" OR "Peircean") AND ("sign" OR "icon" OR "interpretant" OR "pragmatism" OR "abduction"))',
    "phenomenology": '("phenomenology" OR "phenomenological" OR "Husserl")',
    "meaning and representation": '("intentionality" OR "mental representation" OR "representational content" OR "symbolic representation")',
    "information integration": '("information integration" OR "integration of information")',
    "emergence": 'RAW:(TITLE:"emergent properties" OR ABSTRACT:"emergent properties" OR TITLE:"emergent property" OR ABSTRACT:"emergent property" OR TITLE:"strong emergence" OR ABSTRACT:"strong emergence" OR TITLE:"weak emergence" OR ABSTRACT:"weak emergence" OR TITLE:"downward causation" OR ABSTRACT:"downward causation" OR TITLE:"emergentism" OR ABSTRACT:"emergentism" OR TITLE:"emergence of consciousness" OR ABSTRACT:"emergence of consciousness")',
    "mind-body": '("mind-body" OR "mind body problem" OR "mind-brain")',
}

# Random distractors: neuroscience/psychology/medicine by title/abstract keyword (MeSH filtering proved
# unreliable for 1995-2015 OA records: sparse indexing and inconsistent OR behaviour).
FIELD_WORDS = ["brain", "cognitive", "neural", "neuron*", "psycholog*", "behavio*", "psychiatr*", "mental",
               "clinical", "patients", "disease", "therapy", "cortex"]
RANDOM_FILTER = "(" + " OR ".join(f"(TITLE:{w} OR ABSTRACT:{w})" for w in FIELD_WORDS) + ")"


def tiab(expr: str) -> str:
    """Restrict a phrase or OR-group of phrases to title/abstract (RAW:... is passed through unchanged)."""
    if expr.startswith("RAW:"):
        return expr[4:]
    parts = [p for p in expr.strip("()").split(" OR ")]
    return "(" + " OR ".join(f"TITLE:{p} OR ABSTRACT:{p}" for p in parts) + ")"


def theory_phrase_exclusion() -> str:
    phrases = [p for ps in THEORY_QUERIES.values() for p in ps if " AND " not in p]
    return "NOT (" + " OR ".join(phrases) + ")"

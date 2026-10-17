"""Step 1 of prompt 04: write profiles/<theory>.yaml, profiles/generic_consciousness.yaml, profiles/other_theories.yaml.

Profile inputs are limited to: the LoC description (as stored), core claims (drafted from the description and seed
abstracts, edited by hand afterwards), and abstract-only seed passages. Never silver-set or loosely-naming papers.
Refuses to overwrite an existing file (hand edits!) unless --force.

usage: python -m src.level3_concepts.make_profiles [--force]
"""
import argparse
from pathlib import Path

import yaml

from src import db

PROFILES = Path(__file__).resolve().parents[2] / "profiles"
WINDOW = (1995, 2015)
# theory db id -> terms.yaml key, file stem
THEORIES = {1: ("champagne_semiotic", "champagne"), 2: ("global_workspace", "gwt"), 3: ("integrated_information", "iit"),
            4: ("panpsychism", "panpsychism"), 5: ("predictive_processing_fep", "predictive_processing")}

D, S = "description", "seed abstract"
CLAIMS: dict[str, list[tuple[str, str]]] = {
    "champagne_semiotic": [
        ("A felt quality (what a color or a pain is like) can be pulled apart from every causal and inferential relation it figures in only in thought, never in fact. This act of mental separation (prescission) shows what can and cannot be inferred from the quality alone.", D),
        ("Signs have three kinds of vehicle, not two: type, token and tone. A tone is a bare quality considered before any instance or meaning is attached, and admitting it as a category stops experiential qualities from looking explanatorily anomalous.", D),
        ("Reference to another person's experience can work through resemblance (iconicity) rather than causal contact or convention, so one can grasp what an experience is like without having been exposed to its cause.", D + " + 2014 Champagne abstract"),
        ("The 'hard problem' is dissolved, not solved: the distinction between quality and function is legitimate, but it generates a puzzle only when it is reified into a separate kind of thing or a separate module of the mind.", D + " + 2009 Champagne abstract"),
        ("Qualities are mind-involving without being mind-dependent: isolating a quality is something humans do, but what results when the isolation is done properly is not up to them.", D),
        ("Explanation should rest on third-person elements that can be detected and checked, with no appeal to introspection; science explains the mechanisms, and philosophy justifies the persistent sense that something is left over.", D),
        ("Reality is layered by sign-action: regular (law-like) sign relations subsume actual events, which subsume mere possibilities such as qualities. Tracking which layer a case sits at gives a way to treat consciousness without a separate metaphysical substance.", D + " + 2015 Champagne abstract"),
        ("Habit makes perception efficient but makes us perceive what we expect rather than what is given. A disciplined looking (phaneroscopy) that suspends practical and technological automatisms lets appearances be observed in their qualitative, resistant and mediating aspects.", D),
    ],
    "global_workspace": [
        ("Many specialised processors (perception, memory, evaluation, language, motor control) run in parallel and unconsciously. A piece of information is conscious when it wins a competition for access to a shared, limited-capacity workspace.", D),
        ("The winning content is broadcast to the whole set of processors, so it becomes globally available for attention, memory, verbal report and action, while competing and conflicting contents are inhibited.", D),
        ("In the brain this is implemented by a network of long-range excitatory cortical neurons, dense in prefrontal, temporoparietal and cingulate regions and linked with thalamocortical loops. The content of a conscious percept is carried by the sustained, amplified activity ('ignition') of a subset of these neurons.", D),
        ("Three empirical regularities frame the theory: a great deal of processing happens without awareness, attention is a prerequisite for awareness, and awareness is needed for specific tasks such as holding information over time, combining operations in novel ways, and spontaneously generating intentional behavior.", D),
        ("The prefrontal cortex is thought to coordinate and sustain the broadcast. A newer, brain-based version treats the whole cortex as a flexibly recruited oscillatory system in which an arbitrary prefrontal versus non-prefrontal division is misleading.", D),
        ("Conscious access is temporally flexible: sensory information can be held in a shared network and accessed when it becomes relevant, so attention directed to a location after a stimulus has gone can bring that earlier stimulus into awareness.", D),
        ("Predictions that broadcast marks both the onset and the end of an experience, centered on prefrontal cortex, were only partly borne out in adversarial tests. Broadcast was seen at onset but not at offset, and only some aspects of consciousness were found in prefrontal cortex.", D),
    ],
    "integrated_information": [
        ("The theory starts from the essential properties of experience (it exists intrinsically, is structured, is specific, is unified and is definite) and asks what a physical system must be like to account for each property, in terms of its cause-effect power on itself.", D),
        ("Every experience is specific: it is what it is by differing from all alternative experiences, so the physical substrate must specify a particular cause-effect repertoire that distinguishes its present state from other possible states.", D),
        ("Every experience is unified, so the substrate's cause-effect structure must be irreducible: it cannot be partitioned into non-interdependent parts without loss. The amount of this irreducibility is measured by a quantity, phi, and degrees of consciousness covary with it.", D),
        ("Every experience is definite in content and in spatio-temporal grain, so only the set of elements whose cause-effect structure is maximally irreducible is the substrate; overlapping or larger and smaller sets are excluded.", D),
        ("Each experience is identical to the maximally irreducible structure of concepts that the substrate specifies, a shape in an abstract 'qualia space' whose mathematical properties match the properties of the experience.", D),
        ("Consciousness is an intrinsic property of how a physical system is organised and what it can constrain in its own past and future, not of what it computes. A simulation or purely feed-forward arrangement that merely reproduces the function is not thereby conscious, and brains are not the only possible substrate.", D),
        ("Experience is unique and there is an enormous number of distinct experiences, yet each is apprehended as a whole. Taking both facts seriously and casting them in the language of information over states and their interrelations, rather than the material the system is made of, is what yields the theory.", D),
    ],
    "panpsychism": [
        ("Experience (or a precursor of experience) is a primitive, non-reducible feature of the fundamental constituents of physical reality, as basic as fields and particles, rather than something that appears only in brains.", D),
        ("Physics describes how fundamental entities relate to each other but not what they are in themselves; panpsychism proposes that the intrinsic nature of those entities is experiential, which puts consciousness inside the physical world and gives it a causal role.", D),
        ("Richer minds arise when micro-level experiential properties combine under the right conditions. How many micro-subjects or properties add up to one unified macro-experience, or how a cosmic mind is divided into individual ones, is the central unsolved problem (the combination problem).", D),
        ("Proposed combination mechanisms include synchronised oscillation or resonance among micro-conscious elements, with electromagnetic fields serving to bind them into larger units.", D),
        ("The motivation is the hard problem: if consciousness is not to be explained away, nature must be conceived more broadly, so a view is sought that sits between reductive materialism and mind-body dualism.", D + " + 1995 and 2003 Chalmers abstracts"),
        ("A realistic materialist who takes consciousness to be a real physical phenomenon must hold that matter is not wholly non-conscious in its ultimate nature, because something cannot come from what is wholly non-something.", D + " + 2009 Strawson abstract"),
        ("The view comes in several forms that differ in what is fundamental: experience in the smallest particles (micropsychism), in the universe as a whole (cosmopsychism), or in a field or in fundamental monads.", D),
        ("Objections: consciousness seems to come in discrete units with boundaries, causal closure of physics leaves no room for extra mental influences, and the claim may be untestable.", D),
    ],
    "predictive_processing_fep": [
        ("The brain does not passively receive sensory signals. It continuously generates predictions about the causes of its sensory input and top-down signals carry these predictions, while bottom-up signals carry only the mismatches (prediction errors).", D),
        ("Perception, learning and action all come from one operation: adjusting internal models or the world so that prediction error is minimised. This is an approximation to Bayesian inference, in which prior expectations are combined with sensory evidence.", D + " + 2005 Friston abstract"),
        ("The internal model is hierarchical, so that higher levels supply context-sensitive priors to lower levels. This predicts reciprocal cortical connections, an asymmetry between forward and backward connections, and effects such as repetition suppression and the mismatch negativity.", S + " (2005 Friston)"),
        ("Organisms stay alive by keeping their states within a narrow set of low-surprise attractor states (homeostasis). Minimising the difference between expected and actual sensory states, i.e. free energy or surprise, is the formal expression of this self-maintenance.", D),
        ("Consciousness is treated as a process of inference, not as a thing. Experience is the brain's best guess about the causes of its sensations, and awareness is thought to facilitate flexible prediction about future states and to ground selfhood and action.", D),
        ("The precision (expected reliability) assigned to predictions and to errors controls their weighting, and a higher level that sets precision across all layers could account for attention and for flexible, general-purpose agency.", D),
        ("Prediction may not by itself explain consciousness; it may only underpin perception. Related reentry accounts say that recurrent top-down signalling is itself the conscious state.", D),
        ("The brain is a prediction engine that evolved for survival in mobile creatures, which must anticipate the outcome of each movement. The predictive brain can be part of larger loops of body, tools and environment rather than being confined to the skull.", D),
    ],
}

GENERIC = [
    "Consciousness research studies awareness: the state of being awake and responsive, and the content of subjective experience, such as seeing, hearing, feeling pain or having a thought.",
    "Researchers measure consciousness mainly by subjective report, such as asking participants whether they saw a stimulus, how clearly, and how confident they are, and by behavioural indicators in infants, animals and patients who cannot speak.",
    "Experimenters compare aware and unaware conditions while keeping the stimulus the same, using masking, binocular rivalry, change blindness, attentional blink and threshold-level stimuli, and ask which brain measures differ with report.",
    "Studies of the neural correlates of consciousness record fMRI, EEG, MEG and single-neuron activity in cortex and thalamus to find the brain activity associated with conscious perception, and what separates it from unconscious processing.",
    "Sleep, general anesthesia and sedation reduce or abolish consciousness, and brain activity changes in characteristic ways, for example slow waves, reduced connectivity and loss of responsiveness, as awareness fades and returns.",
    "Disorders of consciousness such as coma, the vegetative state or unresponsive wakefulness, and the minimally conscious state are assessed at the bedside and with brain imaging and EEG, to detect covert awareness in patients who cannot respond.",
    "Philosophers and scientists discuss the relationship between subjective experience and the physical brain, the distinction between phenomenal experience and access to information for report, and whether consciousness can be studied objectively.",
]


def _lit(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|" if ("\n" in data or len(data) > 160) else None)


yaml.add_representer(str, _lit)


def seed_passages(conn, tid: int) -> list[dict]:
    rows = conn.execute("""SELECT parsed_year, raw_text, parsed_title, parsed_authors, pmcid, resolution_status, fulltext_kind, abstract
        FROM loc_references WHERE theory_id=? AND parsed_year BETWEEN ? AND ? AND abstract IS NOT NULL AND abstract != ''
        ORDER BY parsed_year""", (tid, *WINDOW)).fetchall()
    out = []
    for r in rows:
        if r["pmcid"] and conn.execute("SELECT 1 FROM papers WHERE pmcid=?", (r["pmcid"],)).fetchone():
            continue   # in-corpus seeds are silver-set papers: excluded from profiles entirely
        label = (r["parsed_title"] or "").strip() or r["raw_text"][:90]
        out.append({"source": f"{(r['parsed_authors'] or '').strip()} ({r['parsed_year']}) {label}".strip()[:200],
                    "route": f"{r['resolution_status']}; full text via {r['fulltext_kind'] or 'none'} (not extracted)",
                    "use": "profile-only (abstract; not in corpus)", "text": r["abstract"].strip()})
    return out


# user decision 2026-10-11: these four abstracts are dropped from profiles and kept under `excluded_seeds`
EXCLUDED = {("Chalmers", "2003"): "abstract is only a chapter table of contents",
            ("Verlinde", "2011"): "physics paper (entropic gravity), off-topic for the profile",
            ("Deely", "2001"): "generic book blurb",
            ("Buzs", "2006"): "book blurb on brain oscillations, only marginal to the theory"}


def split_excluded(seeds: list[dict]) -> tuple[list[dict], list[dict]]:
    keep, ex = [], []
    for s in seeds:
        why = next((r for (name, yr), r in EXCLUDED.items() if name in s["source"] and f"({yr})" in s["source"]), None)
        (ex if why else keep).append({**s, "reason_excluded": why} if why else s)
    return keep, ex


def build(force: bool) -> None:
    conn = db.connect()
    PROFILES.mkdir(exist_ok=True)
    for tid, (key, stem) in THEORIES.items():
        path = PROFILES / f"{stem}.yaml"
        if path.exists() and not force:
            print(f"skip (exists): {path.name}")
            continue
        name, desc = conn.execute("SELECT name, description_text FROM theories WHERE id=?", (tid,)).fetchone()
        seeds = seed_passages(conn, tid)
        seeds, excluded = split_excluded(seeds)
        doc = {"theory": name, "key": key, "status": "DRAFT, core_claims to be edited by hand",
               "loc_description": desc.strip(),
               "core_claims": [{"id": f"{stem}-c{i}", "text": t, "source": src} for i, (t, src) in enumerate(CLAIMS[key], 1)],
               "seed_passages": seeds or []}
        if excluded:
            doc["excluded_seeds"] = excluded
        if not seeds:
            doc["seed_passages_note"] = "none: no abstract-only or OA-PDF seed with an abstract in 1995-2015 (in-corpus seeds are silver and excluded)"
        path.write_text(yaml.dump(doc, sort_keys=False, allow_unicode=True, width=110))
        print(f"wrote {path.name}: {len(CLAIMS[key])} claims, {len(seeds)} seed passages")
    p = PROFILES / "generic_consciousness.yaml"
    if force or not p.exists():
        p.write_text(yaml.dump({"profile": "generic_consciousness", "note": "neutral, no theory-specific claims; subtracted in contrastive scoring",
                                "paragraphs": GENERIC}, sort_keys=False, allow_unicode=True, width=110))
    p = PROFILES / "other_theories.yaml"
    if force or not p.exists():
        keys = [k for k, _ in THEORIES.values()]
        p.write_text(yaml.dump({"note": "cross-theory contrast: for each theory, the other four profiles (resolved by key at scoring time)",
                                "others": {k: [x for x in keys if x != k] for k in keys}}, sort_keys=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    build(ap.parse_args().force)

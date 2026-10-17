# Level 3 LLM judge (prompt 06, Steps 4-5)

Claude Code judged 209 unique items (230 judgments incl. 21 repeats) from packets only, blind to method, rank, score, corpus part and to the hand labels. Blindness ended at Step 4. Nothing here was used to change profiles, terms or the selected variant (V4). Verdicts: R relevant conceptual neighbor, G generic consciousness/neuroscience, O off-topic. All numbers use the **revised** PP014 verdict (G) unless marked; section 8 repeats the headline numbers with the original (R).

## 1. Verdict distribution, V4 top 30 per theory

| Theory | R | G | O | R share top 10 | top 20 | top 30 |
|---|---|---|---|---|---|---|
| Champagne | 5 | 20 | 5 | 20% (2/10) | 20% (4/20) | 17% (5/30) |
| GWT | 16 | 3 | 11 | 60% (6/10) | 55% (11/20) | 53% (16/30) |
| IIT | 6 | 13 | 11 | 20% (2/10) | 25% (5/20) | 20% (6/30) |
| Panpsychism | 5 | 18 | 7 | 20% (2/10) | 20% (4/20) | 17% (5/30) |
| Predictive processing | 12 | 7 | 11 | 60% (6/10) | 45% (9/20) | 40% (12/30) |

All theories: R 44, G 61, O 45 of 150.

## 2. V4 versus BM25 (GWT and predictive processing)

The judge was blind to the method: packets have the same format for every item and carry no method, rank or score. R share of the top k of each method's list (k = 10, 20, 30), with 95% bootstrap CI (10,000 resamples of the papers, seed 20261012). n is small (10 to 30 papers), so the intervals are wide. The difference is V4 minus BM25 (independent resamples). In predictive processing one paper is in both lists.

| Theory | Method | R share top 10 | top 20 | top 30 |
|---|---|---|---|---|
| GWT | V4 | 60% [30, 90] | 55% [35, 75] | 53% [37, 70] |
| GWT | BM25 | 40% [10, 70] | 30% [10, 50] | 27% [13, 43] |
| GWT | V4 - BM25 | +20 pts [-20, +60] | +25 pts [-5, +55] | +27 pts [+3, +50] |
| Predictive processing | V4 | 60% [30, 90] | 45% [25, 65] | 40% [23, 57] |
| Predictive processing | BM25 | 50% [20, 80] | 45% [25, 65] | 43% [27, 60] |
| Predictive processing | V4 - BM25 | +10 pts [-30, +50] | +0 pts [-30, +30] | -3 pts [-27, +20] |

Items with no abstract (packet says "no abstract available"), by list:

| Theory | Method | No abstract | Items |
|---|---|---|---|
| Champagne | V4 | 4 | 30 |
| GWT | V4 | 0 | 30 |
| GWT | BM25 | 1 | 30 |
| IIT | V4 | 4 | 30 |
| Panpsychism | V4 | 4 | 30 |
| Predictive processing | V4 | 1 | 30 |
| Predictive processing | BM25 | 4 | 30 |

V4 lists: 13 of 150 items have no abstract (9%); BM25 lists: 5 of 60 (8%). Of all 18 list entries without an abstract, 2 were judged R. For GWT and predictive processing alone, V4 has 1 of 60 without an abstract and BM25 has 5 of 60. Could this bias the comparison? A packet without an abstract has only the title and two passages, so the judge is more likely to give G or O (almost all such items were G or O), which lowers a list's R share. In the V4-versus-BM25 comparison, BM25 has more of them (5 of 60 vs 1 of 60), so if anything the missing abstracts handicap BM25, by at most a few papers, and 4 of its 5 are predictive processing items, where the two methods tie. They cannot explain the GWT gap (1 such item in BM25's GWT list, judged R). It is not a controlled test: the missing-abstract items also differ in other ways.

## 3. Judge consistency on repeated items

21 repeated papers, judged under new item ids in a later batch. Three-way verdict agreement 100% (21/21), Cohen's kappa 1.00. R versus not-R: agreement 100%, kappa 1.00. Disagreements (original, repeat, verdicts): none.

**The repeats were judged in the same Claude Code session as the originals, so they were not fully independent (the judge could remember the earlier item). The consistency figure is therefore an upper bound on the judge's true consistency.**

## 4. Agreement with the hand labels

55 labelled rows of the sheet were matched to a judgment (theory and pmcid). 15 labelled rows have no judgment (they are V5 picks that were not in the V4 or BM25 top 30, so they were never judged): GWT V5 rank 1 PMC2902469, GWT V5 rank 2 PMC3681776, GWT V5 rank 3 PMC4302175, GWT V5 rank 5 PMC3484139, GWT V5 rank 6 PMC4124985, GWT V5 rank 9 PMC3700976, GWT V5 rank 10 PMC3907788, PP V5 rank 2 PMC4520615, PP V5 rank 3 PMC2914651, PP V5 rank 5 PMC4169184, PP V5 rank 6 PMC4563025, PP V5 rank 7 PMC2232470, PP V5 rank 8 PMC2700262, PP V5 rank 9 PMC3435273, PP V5 rank 10 PMC3748415. Exact agreement 65% (36/55); Cohen's kappa (3 classes) 0.44; R versus not-R kappa 0.55.

Confusion matrix (rows = your label, columns = judge):

| you \ judge | R | G | O | total |
|---|---|---|---|---|
| R | 16 | 6 | 0 | 22 |
| G | 6 | 15 | 6 | 27 |
| O | 0 | 1 | 5 | 6 |

Disagreements (19):

| theory | variant | rank | pmcid | you | judge | judge conf. | title |
|---|---|---|---|---|---|---|---|
| Champagne | V4 | 2 | PMC4243501 | R | G | medium | Problems with theories that equate consciousness with information or i |
| Champagne | V4 | 6 | PMC4460548 | G | R | low | Artworks as dichotomous objects: implications for the scientific study |
| Champagne | V4 | 7 | PMC3510409 | R | G | low | Cyberspace as a new arena for terroristic propaganda: an updated exami |
| Champagne | V4 | 10 | PMC3151447 | O | G | low | Notes on a Few Issues in the Philosophy of Psychiatry* |
| GWT | V4 | 2 | PMC4172090 | R | G | medium | Evidence of weak conscious experiences in the exclusion task |
| GWT | V4 | 5 | PMC4883148 | G | R | medium | Computational cognitive modelling of action awareness: prior and retro |
| GWT | V4 | 8 | PMC3876278 | G | O | high | Prefrontal cortex activation during story encoding/retrieval: a multi- |
| GWT | V5 | 7 | PMC4383541 | G | R | low | Keep Calm and Carry On: Improved Frustration Tolerance and Processing  |
| GWT | V5 | 8 | PMC4677100 | G | R | low | Working Memory in the Service of Executive Control Functions |
| IIT | V4 | 3 | PMC3958532 | G | O | medium | Naturalizing Sense of Agency with a Hierarchical Event-Control Approac |
| IIT | V4 | 5 | PMC3096919 | G | O | high | Body Awareness: a phenomenological inquiry into the common ground of m |
| Panpsychism | V4 | 1 | PMC4037890 | R | G | medium | Medicine and Mind-Body Dualism: A Reply to Mehta's Critique |
| Panpsychism | V4 | 3 | PMC4625076 | G | O | medium | The social neuroscience and the theory of integrative levels |
| Panpsychism | V4 | 4 | PMC4270171 | G | O | medium | Tuning pathological brain oscillations with neurofeedback: a systems n |
| Panpsychism | V4 | 6 | PMC4014402 | G | R | low | From the Phenomenology to the Mechanisms of Consciousness: Integrated  |
| Panpsychism | V4 | 8 | PMC3341650 | R | G | medium | Consciousness regained? Philosophical arguments for and against reduct |
| Panpsychism | V4 | 10 | PMC4530257 | G | O | medium | Pedagogical tools to explore Cartesian mind-body dualism in the classr |
| PP | V4 | 2 | PMC2876988 | G | R | high | Dopamine signals for reward value and risk: basic and recent data |
| PP | V4 | 7 | PMC4559402 | R | G | low | A Self-Organising Model of Thermoregulatory Huddling |

Provenance note: the git history records the labels as "proposed by an AI assistant, reviewed by the user". If so, they are not an independent human reference, and agreement with them partly measures agreement between two LLM-assisted judgments.

## 5. R share by corpus part (V4 top 30 lists)

| Corpus part | Items | R | R share |
|---|---|---|---|
| background | 88 | 30 | 34% |
| candidate | 60 | 14 | 23% |
| random | 2 | 0 | 0% |

Per theory (items / R):

| Theory | background | candidate | random |
|---|---|---|---|
| Champagne | 13 / 2 | 17 / 3 | 0 / 0 |
| GWT | 25 / 14 | 5 / 2 | 0 / 0 |
| IIT | 12 / 3 | 17 / 3 | 1 / 0 |
| Panpsychism | 14 / 2 | 16 / 3 | 0 / 0 |
| Predictive processing | 24 / 9 | 5 / 3 | 1 / 0 |

The R share is not driven by the candidate pool: candidates (papers that the term-based Level 2 scan flagged as plausibly related but not direct mentions) have a lower R share (23%) than background papers (34%). The background result comes mostly from GWT and predictive processing; for Champagne, IIT and panpsychism the candidate and background shares are both low and similar. No seed papers appear (they are excluded as direct mentions), and the two random-part items were both not R.

## 6. Flags

- `names_theory_in_text` true: 1 items (PP059).
  - PP059 (PMC4270100, predictive-processing V4 list; judged R, high) names "free energy" in its packet text. Level 2 treats bare "free energy" as a generic term (`excluded_generic`) and the paper has only a Friston 2010 citation, so it is correctly `names_theory_loosely = 0`; the judge flagged it as a possible exclusion leak. It is a case where a paper uses the theory's central concept under a different name, not a missed direct mention, but it should be kept out of any claim that these papers are free of the theory's vocabulary.
- `better_fit_theory` set: 35 judgments (verdicts: G 22, O 8, R 5).

Confusion across theories (rows = theory the item was judged for, columns = better-fit theory):

| judged for \ better fit | Champagne | GWT | IIT | Panpsychism | Predictive processing |
|---|---|---|---|---|---|
| Champagne |  | 1 | 2 | 1 | 2 |
| GWT |  |  | 1 |  | 7 |
| IIT |  | 2 |  | 1 | 5 |
| Panpsychism |  | 1 | 3 |  | 2 |
| Predictive processing | 1 | 4 | 2 |  |  |

## 7. Exports for the app

Best R-judged papers in each theory's V4 top 30, high confidence first, then medium, then low, ties by V4 rank. Full table: `data/judge/judgments_final.csv` and `results/judgments.csv`.

#### Champagne (5 R-judged in the V4 top 30; best 5 shown)

| pmcid | title | year | conf. | claims | reason | evidence |
|---|---|---|---|---|---|---|
| PMC2865004 | Designing informative warning signals: Effects of indicator type, modality, and task demand on recognition speed and accuracy | 2009 | high | champagne-c3, champagne-c2 | It applies Peirce's icon/index/symbol distinctions, including resemblance-based signs and a tripartite signification relation involving the interpreter. | "signification is a tripartite relation between signal, referent, and person/cogniser" |
| PMC3787248 | Extracting salient sublexical units from written texts: “Emophon,” a corpus-based approach to phonological iconicity | 2013 | medium | champagne-c3 | It uses Peirce's icon, a sign whose form resembles and shares qualities with its referent, paralleling reference by resemblance rather than convention or causal contact. | "its form is similar to, and shares qualities with its referent" |
| PMC4460548 | Artworks as dichotomous objects: implications for the scientific study of aesthetic experience | 2015 | low | champagne-c2 | It treats representations as having a material vehicle and an evoked meaning present together, paralleling the sign vehicle versus meaning distinction. | "Most forms of representation in which material is organized so as to evoke something other than itself" |
| PMC3485814 | Components of aesthetic experience: aesthetic fascination, aesthetic appraisal, and aesthetic emotion | 2012 | low | champagne-c8 | It says aesthetic experience arises when everyday pragmatic meaning is suspended, paralleling suspension of practical automatisms to observe appearances. | "only when they lose their everyday pragmatic meaning (as bicycle parts) and transcend into the new symbolic level of reality" |
| PMC4661186 | The Natural Emergence of (Bio)Semiosic Phenomena | 2015 | low | champagne-c7 | It models meaning as a Peircean sign-object-interpretant process and argues the resulting phenomena are real and irreducible, loosely paralleling the layered sign-process view that counts such phenomena as real. | "The theory can be represented as a triad that resembles the semiotic triad proposed by Peirce" |

#### GWT (16 R-judged in the V4 top 30; best 10 shown)

| pmcid | title | year | conf. | claims | reason | evidence |
|---|---|---|---|---|---|---|
| PMC4005968 | I can see clearly now: the effects of age and perceptual load on inattentional blindness | 2014 | high | gwt-c4 | It shows awareness of unattended stimuli depends on attentional capacity, directly paralleling attention as a prerequisite for awareness. | "According to Load Theory, awareness levels are determined by the availability of attentional capacity." |
| PMC3110775 | Task-Irrelevant Blindsight and the Impact of Invisible Stimuli | 2011 | high | gwt-c4 | It shows invisible stimuli in blind fields guide behaviour and affect attention, and considers attention as selecting for awareness, matching processing without awareness and attention as a prerequisite. | "stimuli presented within regions of absolute cortical blindness can both guide forced-choice behavior when they are task-relevant" |
| PMC2864967 | Measuring unconscious cognition: Beyond the zero-awareness criterion | 2008 | high | gwt-c4 | It argues for measuring unconscious processing directly, such as feedforward priming without recurrent processing, paralleling the observation that considerable processing occurs without awareness. | "Feedforward tasks such as this might thus be used to measure the time-course of unconscious processing directly" |
| PMC3260467 | Attentional Routes to Conscious Perception | 2012 | high | gwt-c4 | It reviews evidence that spatial attention is a necessary step for reportable visual experience, directly paralleling attention being a prerequisite for awareness. | "appear instead to be a necessary, although not sufficient, step in the development of reportable visual experiences" |
| PMC4189413 | Isolating neural correlates of conscious perception from neural correlates of reporting one's perception | 2014 | medium | gwt-c4 | It presents inattentional-blindness evidence that attention is necessary for conscious perception and separates report-related processing from the percept, paralleling attention as a prerequisite for awareness. | "there is no such thing as awareness in the absence of attention; i.e., attention is necessary for conscious perception." |
| PMC4883148 | Computational cognitive modelling of action awareness: prior and retrospective | 2015 | medium | gwt-c4 | It models actions prepared unconsciously and notes that deviating from a habitual task seems to require awareness, paralleling processing without awareness and awareness needed for novel combinations. | "actions that are prepared without being conscious at any point in time" |
| PMC4023070 | Intralaminar and medial thalamic influence on cortical synchrony, information transmission and cognition | 2014 | medium | gwt-c3, gwt-c5 | It proposes that thalamo-cortical loops linking prefrontal and fronto-parietal cortex synchronise cortical circuits for large-scale integration bearing on consciousness, paralleling the thalamocortical oscillatory system. | "Such a thalamic-mediated synchronization mechanism may give rise to large-scale integration of information across multiple cortical circuits" |
| PMC3895618 | Altered network properties of the fronto-parietal network and the thalamus in impaired consciousness☆ | 2014 | medium | gwt-c3, gwt-c5 | It tests a model in which consciousness depends on fronto-parietal connectivity modulated by the thalamus, paralleling the widely connected prefrontal-parietal network with thalamocortical loops. | "Recovery of consciousness has been associated with connectivity in the frontal cortex and parietal regions modulated by the thalamus." |
| PMC2955690 | Cross-approximate entropy of cortical local field potentials quantifies effects of anesthesia - a pilot study in rats | 2010 | medium | gwt-c3 | It frames anaesthetic unconsciousness as loss of local-global long-range cortical communication in thalamocortical networks, paralleling long-range connections that tie processors together for conscious content. | "this local-global wiring is necessary for subjective experiences" |
| PMC3345872 | Iconic memory requires attention | 2012 | medium | gwt-c4 | It concludes that phenomenal consciousness depends heavily on attention, paralleling attention as a prerequisite for awareness. | "phenomenal consciousness, like access consciousness, depends heavily on attention" |

#### IIT (6 R-judged in the V4 top 30; best 6 shown)

| pmcid | title | year | conf. | claims | reason | evidence |
|---|---|---|---|---|---|---|
| PMC4430458 | Stimulus Set Meaningfulness and Neurophysiological Differentiation: A Functional Magnetic Resonance Imaging Study | 2015 | high | iit-c3, iit-c2 | It measures phi-star and differentiation of brain responses, defining integration as how well the whole predicts its future beyond independent parts, matching irreducibility and differentiation of experience. | "how much better the current state of a system as a whole predicts its future state" |
| PMC331407 | Measuring information integration | 2003 | high | iit-c3, iit-c2 | It defines phi as the minimum effective information exchanged across a partition and ties informative, unified experience to a repertoire of states, directly matching irreducibility and differentiation requirements. | "The capacity to integrate information, or Φ, is given by the minimum amount of effective information" |
| PMC4387919 | What makes you think you are conscious? An agnosticist manifesto | 2015 | medium | iit-c3 | It argues the unity of experience despite disunity of content is afforded by intrinsic brain dynamics rather than separate specialised parts, paralleling unity that cannot be reduced to independent parts. | "the view that the experience of unity is afforded by the intrinsic, multiscale brain dynamics" |
| PMC3786226 | The embodied transcendental: a Kantian perspective on neurophenomenology | 2013 | low | iit-c1 | It starts from the invariant structure of lived experience and argues brain organisation shares that structure, loosely paralleling translating experience's essential properties into requirements on the physical system. | "the former and the latter share the same transcendental structure" |
| PMC3599657 | The nature of “internal sensations” of higher brain functions may be derived from the design rules for artificial machines that can produce them | 2012 | low | iit-c6 | It holds that internal sensations should be tested by replicating mechanisms in physical electronic systems rather than only modelling them, loosely paralleling the view that implementation, not simulated function, matters and the substrate need not be biological. | "the gold standard of replicating the models in physical systems starts exhibiting some of these properties" |
| PMC3653222 | A Commentary On De Sousa's “Towards An Integrative Theory Of Consciousness” | 2013 | low | iit-c3 | It argues from the phenomenology of unified experience against treating consciousness as independent unbound modules, loosely paralleling unity that is not reducible to independent parts. | "Why are we conscious only of the integrated percepts?" |

#### Panpsychism (5 R-judged in the V4 top 30; best 5 shown)

| pmcid | title | year | conf. | claims | reason | evidence |
|---|---|---|---|---|---|---|
| PMC2823620 | Psychosomatic medicine and the philosophy of life | 2010 | medium | panpsychism-c5 | It rejects both materialist reduction and dualism, proposing a unified account of reality that keeps subjective experience and the physical together, paralleling revising nature to avoid reduction and a separate mental realm. | "our theory must reintegrate psyche with soma such that no component of the whole is short-changed" |
| PMC2702101 | Rhythms of Consciousness: Binocular Rivalry Reveals Large-Scale Oscillatory Network Dynamics Mediating Visual Perception | 2009 | medium | panpsychism-c4 | It proposes that unified perceptual experience arises from transient gamma-synchronous assemblies binding distributed neural populations, paralleling synchronised oscillation as a binding mechanism for combining units. | "Consciousness has been proposed to emerge from functionally integrated large-scale ensembles of gamma-synchronous neural populations" |
| PMC4158773 | On habit and the mind-body problem. The view of Felix Ravaisson | 2014 | medium | panpsychism-c1 | It reports a view in which nature itself is a kind of obscured consciousness or sleepy will, placing experience-like qualities in nature rather than only in brains. | "nature is a kind of obscured consciousness, or sleepy will" |
| PMC3837243 | Quantized visual awareness | 2013 | medium | panpsychism-c3 | It posits elementary quanta of awareness that are integrated into a unified percept by recurrent processing, paralleling micro-level experiential units combining into a larger unified experience. | "are not integrated into a conscious experience until recurrent processing from centers like V4 or V5 select the appropriate qualia" |
| PMC4014402 | From the Phenomenology to the Mechanisms of Consciousness: Integrated Information Theory 3.0 | 2014 | low | panpsychism-c3 | It specifies when elements combine into a complex that generates an experience and even holds that simple systems can be minimally conscious, loosely paralleling how micro-level parts combine into larger experience, though it grounds this in causal structure. | "simple systems can be minimally conscious; complicated systems can be unconscious" |

#### Predictive processing (12 R-judged in the V4 top 30; best 10 shown)

| pmcid | title | year | conf. | claims | reason | evidence |
|---|---|---|---|---|---|---|
| PMC4270100 | Homeostatic reinforcement learning for integrating reward collection and physiological stability | 2014 | high | predictive_processing-c4 | It argues organisms stay within a restricted set of physiological states and that minimising deviation from setpoints is equivalent to minimising surprise, directly matching homeostatic self-maintenance as surprise minimisation. | "We propose that our notion of drive is equivalent to surprise as utilized in the free energy" |
| PMC2876988 | Dopamine signals for reward value and risk: basic and recent data | 2010 | high | predictive_processing-c1, predictive_processing-c6 | It describes storing predictions in higher centres and computing the discrepancy between event and prediction as an error, with dopamine error responses scaled by risk, paralleling error-only signalling and reliability scaling. | "The discrepancy between the actual event and its prediction is called an event prediction error." |
| PMC3459842 | Risk-Sensitivity in Bayesian Sensorimotor Integration | 2012 | high | predictive_processing-c2, predictive_processing-c6 | It tests Bayesian sensorimotor integration of prior expectation and sensory evidence, with risk sensitivity depending on the imprecision of model predictions, paralleling inference with priors and reliability weighting. | "weigh all possibilities based on prior expectation and sensory evidence" |
| PMC3792359 | From self-assessment to frustration, a small step toward autonomy in robotic navigation | 2013 | high | predictive_processing-c1, predictive_processing-c2 | It builds a controller that learns expected sensations from actions, uses prediction error from surprising events as the feedback signal, and alters behaviour to test expectations, paralleling error-driven revision and action. | "Prediction error, coming from surprising events, provides a measure of the quality of the underlying sensory-motor contingencies." |
| PMC4147392 | T-type calcium channels promote predictive homeostasis of input-output relations in thalamocortical neurons of lateral geniculate nucleus | 2014 | high | predictive_processing-c1, predictive_processing-c4 | It tests a theory of predictive homeostasis in which neurons predict their inputs and signal prediction error while holding excitability at a homeostatic level, paralleling error signalling and homeostatic self-maintenance. | "A general theory views the function of all neurons as prediction" |
| PMC3315009 | Sense of agency in health and disease: A review of cue integration approaches☆ | 2012 | high | predictive_processing-c2, predictive_processing-c6 | It frames the sense of agency as Bayesian integration of cues weighted by reliability, with persistent error signalling and priors explaining delusions, paralleling inference with priors and precision weighting. | "describing a simple framework of this integration based on Bayesian principles" |
| PMC4010728 | The meaning of spikes from the neuron’s point of view: predictive homeostasis generates the appearance of randomness | 2014 | high | predictive_processing-c1, predictive_processing-c4 | It treats a neuron's excitability as an expectation and a spike as a prediction error, with predictive homeostasis keeping the expectation accurate, paralleling error-only upward signalling and homeostatic self-maintenance. | "Therefore excitability is an expectation of EPSG amplitude and a spike is generated only when EPSG amplitude exceeds its expectation" |
| PMC4214225 | The interplay of plasticity and adaptation in neural circuits: a generative model | 2014 | medium | predictive_processing-c2 | It shows a recurrent circuit becomes a generative model whose spontaneous states sample the prior distribution of stimuli, paralleling an internal model embodying Bayesian priors. | "The neural circuit is able to generate spontaneous patterns of activity that reproduce exactly the probability distribution of experienced stimuli." |
| PMC3318766 | What failure in collective decision-making tells us about metacognition | 2012 | medium | predictive_processing-c6 | It treats collective perceptual decisions as combining information weighted by reliability, with shared confidence conveying reliability, paralleling precision weighting. | "observers convey the reliability of their individual perceptions by communicating their confidence" |
| PMC4221218 | The neural underpinnings of an optimal exploitation of social information under uncertainty | 2014 | medium | predictive_processing-c6, predictive_processing-c2 | It tests Bayes-optimal combination of information sources weighted by their reliabilities, paralleling combining priors with evidence and precision weighting, though in social decisions rather than perception. | "weights information from individual and social sources based on their respective reliabilities" |

## 8. Sensitivity: the PP014 revision

PP014 ("Homeostatic Plasticity and STDP: Keeping a Neuron's Cool in a Fluctuating World") was first judged R (low, claim c4) and revised to G (low) before ingest, after PP023, PP035 and PP060 were judged G for the same reason (topic match without a parallel to the claim's content). Its repeat, PP049, was judged G independently. Notes: `data/judge/notes_revisions.md`. The revision was made while still blind, but it was a judgment call, so here are the headline numbers with each version.

| PP014 verdict | PP V4 R (of 30) | PP V4 top 10 | top 20 | top 30 | PP V4 top-30 CI | PP BM25 top-30 CI | V4 - BM25 top 30 | repeat agreement / kappa | label agreement / kappa |
|---|---|---|---|---|---|---|---|---|---|
| Revised (G) | 12 | 60% | 45% | 40% | 40% [23, 57] | 43% [27, 60] | -3 pts [-27, +20] | 100% / 1.00 | 65% / 0.44 |
| Original (R) | 13 | 60% | 50% | 43% | 43% [27, 60] | 43% [27, 60] | +0 pts [-23, +23] | 95% / 0.93 | 65% / 0.44 |

PP014's position in the lists: V4 rank 20, BM25 rank None.

Reading: the revision moves one paper out of predictive processing's V4 R list (12 vs 13 of 30). It changes the V4 top-20 and top-30 shares by 3 to 5 points, leaves the top-10 share unchanged, and the V4 versus BM25 difference stays inside the confidence interval either way (about zero). The repeat agreement under the original verdict is 20/21 (kappa 0.93), because PP014 and its repeat PP049 would disagree. Agreement with your labels is unaffected because PP014 is not on the labeling sheet. No conclusion changes.

## 9. Caveats

The judge is an LLM and shares biases with other LLMs (for example towards papers that sound like the claim wording). It saw only the abstract and two passages per paper, not the full text, so low-confidence verdicts on thin packets are expected. It is not independent of the author of the profiles: the core-claims summaries that define the standard for R were LLM-drafted (then edited by the user) and the judge scored papers against them, which can favour papers that match the wording of those claims. Items judged R are a small, hand-sized sample; the V4-versus-BM25 intervals are wide and a difference inside them is not evidence either way. The repeats were judged in the same session and were not fully independent, so the consistency figure is an upper bound. Agreement with the hand labels is only as good as the small labelled sample allows (n above), the label sheet covers the top 10 per theory and not the top 30, and the labels were proposed by an AI assistant and reviewed by the user. The corpus is Europe PMC open access, so philosophy-heavy theories (panpsychism, Champagne) have thin coverage.

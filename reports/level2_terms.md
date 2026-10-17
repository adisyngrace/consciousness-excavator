# Level 2: direct term mentions (1995-2015 corpus)

Corpus papers: **7794**. Scanned with text: **7793**. No-text papers (logged, flags absent): **1**. terms.yaml hash `be1cf889c6c24f00`.

`direct_mention` = a strong term in title/abstract/intro/body/discussion AND >= 2 distinct domain_context words (see `src/level2_terms/scan.py`). Close-term, adjacent, landmark-reference and in-text author-year hits are never mentions.

No-text papers: PMC4975114 (no text: fetch=ok  parse=ok)

## 1. Overview per theory

| Theory | direct_mention | by title/abstract | strong blocked by domain rule | close_term | adjacent | cites landmark (refs) | in-text author-year |
|---|---|---|---|---|---|---|---|
| Champagne's semiotic account | 3 | 0 | 0 | 0 | 40 | 4 | 6 |
| Global Workspace Theory | 173 | 26 | 0 | 0 | 86 | 115 | 166 |
| Integrated Information Theory | 39 | 12 | 0 | 0 | 54 | 48 | 66 |
| Panpsychism | 17 | 2 | 0 | 0 | 3 | 27 | 37 |
| Predictive Processing / Free Energy Principle | 200 | 62 | 3 | 647 | 0 | 242 | 350 |

## 2. Direct-mention papers by corpus part

A paper can sit in several parts. Share = flagged / papers in that part.

| Theory | seed | candidate | background | random |
|---|---|---|---|---|
| Champagne's semiotic account | 0 (0.0%) | 3 (0.3%) | 0 (0.0%) | 0 (0.0%) |
| Global Workspace Theory | 0 (0.0%) | 172 (17.0%) | 1 (0.0%) | 0 (0.0%) |
| Integrated Information Theory | 2 (66.7%) | 37 (3.7%) | 2 (0.0%) | 0 (0.0%) |
| Panpsychism | 1 (33.3%) | 17 (1.7%) | 0 (0.0%) | 0 (0.0%) |
| Predictive Processing / Free Energy Principle | 1 (33.3%) | 200 (19.8%) | 0 (0.0%) | 0 (0.0%) |
| *papers in part* | 3 | 1009 | 4891 | 1907 |

## 3. Seed recall

Fraction of Level 1 seed papers in the corpus (part `seed`) that directly mention their own theory. Seeds that do not are early Level 3 examples.

Level 1 `resolved_fulltext` refs dated 1995-2015: Integrated Information Theory: 2, Predictive Processing / Free Energy Principle: 1. CLAUDE.md quotes 11 in total; check this against the `seed` rows below if the numbers disagree.

| Theory | seeds in corpus | directly mention own theory | recall |
|---|---|---|---|
| Champagne's semiotic account | 0 | 0 | n/a |
| Global Workspace Theory | 0 | 0 | n/a |
| Integrated Information Theory | 2 | 2 | 100% |
| Panpsychism | 0 | 0 | n/a |
| Predictive Processing / Free Energy Principle | 1 | 1 | 100% |

Seeds that do NOT directly mention their theory:

- none

## 4. Mention strength and the primary subset

Strength = total strong-term mentions in title/abstract/intro/body/discussion. **Primary** = strong term in the title or abstract, OR >= 3 strong-term mentions.

| Theory | silver set (n) | strength 1 | 2 | 3-4 | 5-9 | 10-29 | 30+ | median | in title/abstract | primary (n) | primary % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Champagne's semiotic account | 3 | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0% |
| Global Workspace Theory | 173 | 78 | 29 | 31 | 17 | 16 | 2 | 2 | 26 | 69 | 40% |
| Integrated Information Theory | 39 | 20 | 5 | 4 | 4 | 4 | 2 | 1 | 12 | 15 | 38% |
| Panpsychism | 17 | 8 | 2 | 2 | 2 | 3 | 0 | 2 | 2 | 7 | 41% |
| Predictive Processing / Free Energy Principle | 200 | 78 | 31 | 24 | 20 | 38 | 9 | 2 | 62 | 102 | 51% |

> **Panpsychism (n = 17) and Champagne's semiotic account (n = 3): the silver set is too small for quantitative claims.** Report recall/AUC for them as descriptive counts only, and treat any percentage as anecdotal. Champagne's three papers use the Peircean sense of the terms and none is about consciousness; that theory is effectively absent from the 1995-2015 open-access biomedical corpus.

## 5. Abbreviation ambiguity

Papers using an abbreviation with no strong term of the same theory in the paper (`unconfirmed`, removed by the rule) versus confirmed. Per-abbreviation snippets to label: `reports/abbreviation_audit.md`.

| Theory | abbreviations | papers confirmed | papers unconfirmed |
|---|---|---|---|
| Global Workspace Theory | GNWT, GWT, GNW | 23 | 2 |
| Integrated Information Theory | IIT | 13 | 2 |
| Predictive Processing / Free Energy Principle | FEP, PP, PC | 21 | 551 |

## 6. Overlap between theories

Corpus papers with direct_mention for **more than one** theory: **25** (0.32% of 7793 scanned; 6.2% of the 402 papers with any direct mention). They are flagged in the SQL view `multi_theory_papers` and listed in `reports/level2_overlap_papers.csv`.

Pairwise counts:

| | Champagne's | Global | Integrated | Panpsychism | Predictive |
|---|---|---|---|---|---|
| Champagne's semiotic account | 3 | 0 | 0 | 0 | 0 |
| Global Workspace Theory | 0 | 173 | 17 | 6 | 2 |
| Integrated Information Theory | 0 | 17 | 39 | 8 | 2 |
| Panpsychism | 0 | 6 | 8 | 17 | 0 |
| Predictive Processing / Free Energy Principle | 0 | 2 | 2 | 0 | 200 |

Silver set with and without the overlapping papers:

| Theory | silver set (all) | overlap papers | exclusive (overlap removed) | primary, exclusive |
|---|---|---|---|---|
| Champagne's semiotic account | 3 | 0 | 3 | 0 |
| Global Workspace Theory | 173 | 20 | 153 | 56 |
| Integrated Information Theory | 39 | 22 | 17 | 7 |
| Panpsychism | 17 | 10 | 7 | 3 |
| Predictive Processing / Free Energy Principle | 200 | 3 | 197 | 102 |

Overlap papers:

| PMCID | year | theories (strength) | title |
|---|---|---|---|
| PMC3814086 | 2013 | Global (2), Integrated (1), Predictive (2) | Consciousness in humans and non-human animals: recent advances and future direct |
| PMC4037891 | 2014 | Global (2), Integrated (2), Panpsychism (1) | What Explains Consciousness? Or…What Consciousness Explains? |
| PMC4091309 | 2014 | Global (2), Integrated (1), Panpsychism (3) | The measurement of consciousness: a framework for the scientific study of consci |
| PMC4518274 | 2015 | Global (3), Integrated (4), Panpsychism (1) | Consciousness: individuated information in action |
| PMC4574706 | 2015 | Global (1), Integrated (11), Panpsychism (13) | The Problem with Phi: A Critique of Integrated Information Theory |
| PMC2996305 | 2010 | Global (3), Integrated (2) | Changes in Resting Neural Connectivity during Propofol Sedation |
| PMC3010745 | 2010 | Global (1), Integrated (1) | Brain Connectivity in Pathological and Pharmacological Coma |
| PMC3199212 | 2011 | Global (3), Integrated (1) | Lateral Information Processing by Spiking Neurons: A Theoretical Model of the Ne |
| PMC3298966 | 2012 | Global (15), Integrated (1) | Consciousness and the Prefrontal Parietal Network: Insights from Attention, Work |
| PMC3651967 | 2013 | Global (7), Integrated (3) | Sleep Neuroimaging and Models of Consciousness |
| PMC3653219 | 2013 | Global (9), Panpsychism (1) | Towards An Integrative Theory Of Consciousness: Part 1 (Neurobiological And Cogn |
| PMC3653222 | 2013 | Global (3), Panpsychism (1) | A Commentary On De Sousa's “Towards An Integrative Theory Of Consciousness” |
| PMC3664777 | 2013 | Global (10), Integrated (2) | Global Workspace Dynamics: Cortical “Binding and Propagation” Enables Conscious  |
| PMC3712269 | 2013 | Global (21), Integrated (9) | General and specific consciousness: a first-order representationalist approach |
| PMC3909994 | 2014 | Integrated (1), Predictive (1) | The entropic brain: a theory of conscious states informed by neuroimaging resear |
| PMC3912322 | 2014 | Integrated (5), Panpsychism (4) | An integration of integrated information theory with fundamental physics |
| PMC4010789 | 2014 | Global (2), Integrated (1) | The consciousness state space (CSS)—a unifying model for consciousness and self |
| PMC4045549 | 2013 | Integrated (1), Panpsychism (1) | The Mind-Brain Relationship as a Mathematical Problem |
| PMC4066704 | 2014 | Global (1), Integrated (1) | Top-down mechanisms of anesthetic-induced unconsciousness |
| PMC4243501 | 2014 | Integrated (1), Panpsychism (2) | Problems with theories that equate consciousness with information or information |
| PMC4354375 | 2015 | Global (1), Integrated (1) | Across the consciousness continuum—from unresponsive wakefulness to sleep |
| PMC4387509 | 2015 | Integrated (36), Panpsychism (18) | Consciousness: here, there and everywhere? |
| PMC4460809 | 2015 | Global (10), Predictive (1) | Thalamocortical Dysrhythmia: A Theoretical Update in Tinnitus |
| PMC4550793 | 2015 | Global (11), Integrated (6) | A unified 3D default space consciousness model combining neurological and physio |
| PMC6089087 | 2015 | Global (10), Integrated (5) | Are we ever aware of concepts? A critical question for the Global Neuronal Works |

## 7. Consciousness-relevant subset

Most predictive-processing direct mentions are computational neuroscience, not consciousness science. The stricter subset keeps silver papers that use consciousness/awareness vocabulary (conscious(ness), unconscious, awareness, sentience, phenomenal, qualia, subjective experience; bare 'aware' excluded) in the title/abstract OR >= 3 times in the text. 'Any' is the lenient version (>= 1 occurrence). Computed for every theory for comparison.

| Theory | silver set | consciousness-relevant (strict) | % | consciousness vocabulary, any | % |
|---|---|---|---|---|---|
| Champagne's semiotic account | 3 | 1 | 33% | 1 | 33% |
| Global Workspace Theory | 173 | 147 | 85% | 155 | 90% |
| Integrated Information Theory | 39 | 38 | 97% | 39 | 100% |
| Panpsychism | 17 | 16 | 94% | 16 | 94% |
| Predictive Processing / Free Energy Principle | 200 | 58 | 29% | 98 | 49% |

Predictive Processing / FEP: the **PRIMARY** consciousness-relevant subset is the strict definition (title/abstract, or >= 3 occurrences): **58** of 200 silver papers (32 also primary by strength). SECONDARY: lenient (>= 1 occurrence) **98** and the full silver set **200**. Report all three.

## 7b. Weak mentions and `any_mention_level`

Bare "predictive processing" (`needs_corroboration`) counts as a direct mention only in the title/abstract or with another strong/close term of the theory. Otherwise the paper is `weak_mention` (not in the silver set, but it HAS named the theory). `any_mention_level` = direct > weak > close > none; `names_theory_loosely` = direct OR weak OR close. A Level 3 "never names the theory" claim must use `names_theory_loosely = 0` (`query.names_theory_ids`).

| Theory | direct | weak | close-term only | names theory loosely (any) |
|---|---|---|---|---|
| Champagne's semiotic account | 3 | 0 | 0 | 3 |
| Global Workspace Theory | 173 | 0 | 0 | 173 |
| Integrated Information Theory | 39 | 0 | 0 | 39 |
| Panpsychism | 17 | 0 | 0 | 17 |
| Predictive Processing / Free Energy Principle | 200 | 43 | 492 | 735 |

## 8. Precision audit (hand labels)

Source: `reports/precision_audit_labels.csv` (Y = true positive, N = false positive, ? = undecided and excluded from precision; weak mentions count as Y). Each (paper, term) appears once, so per-term n is already unique papers. The sample was stratified so every strong term with hits was drawn at least once, then topped up at random: it is NOT a random sample of all hits, so these are diagnostics, not population precision estimates. Wilson 95% interval shown because every n here is tiny; no term has enough labels to certify 80%.

### Champagne's semiotic account

| strong term | papers (corpus) | audited n | Y | N | ? | weak (in Y) | precision | Wilson 95% |
|---|---|---|---|---|---|---|---|---|
| phaneroscopy | 0 | 0 | | | | | not audited | |
| phaneroscopic | 0 | 0 | | | | | not audited | |
| phaneron | 0 | 0 | | | | | not audited | |
| Peircean semiotics | 2 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| Peirce's semiotics | 0 | 0 | | | | | not audited | |
| semiotic account of consciousness | 0 | 0 | | | | | not audited | |
| semiotic theory of consciousness | 0 | 0 | | | | | not audited | |
| semiotic account of phenomenal consciousness | 0 | 0 | | | | | not audited | |
| qualisign | 0 | 0 | | | | | not audited | |
| synechism | 0 | 0 | | | | | not audited | |
| firstness | 1 | 1 | 1 | 0 | 0 | 0 | 100% | 21%-100% |

Theory level, de-duplicated by paper: 3 audited hits = **3 unique papers**; 3 Y, 0 N, 0 undecided; precision 3/3 = 100% (Wilson 95% 44%-100%).


### Global Workspace Theory

| strong term | papers (corpus) | audited n | Y | N | ? | weak (in Y) | precision | Wilson 95% |
|---|---|---|---|---|---|---|---|---|
| global workspace theory | 53 | 4 | 4 | 0 | 0 | 0 | 100% | 51%-100% |
| global workspace | 132 | 7 | 7 | 0 | 0 | 1 | 100% | 65%-100% |
| global neuronal workspace | 37 | 3 | 3 | 0 | 0 | 0 | 100% | 44%-100% |
| global neuronal workspace theory | 10 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| neuronal workspace | 8 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| global playground | 0 | 0 | | | | | not audited | |
| theater of consciousness | 0 | 0 | | | | | not audited | |
| theatre of consciousness | 0 | 0 | | | | | not audited | |
| conscious access hypothesis | 4 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |

Theory level, de-duplicated by paper: 20 audited hits = **19 unique papers**; 19 Y, 0 N, 0 undecided; precision 19/19 = 100% (Wilson 95% 83%-100%).


### Integrated Information Theory

| strong term | papers (corpus) | audited n | Y | N | ? | weak (in Y) | precision | Wilson 95% |
|---|---|---|---|---|---|---|---|---|
| integrated information theory | 18 | 8 | 8 | 0 | 0 | 1 | 100% | 68%-100% |
| integrated information theory of consciousness | 6 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| information integration theory | 17 | 0 | | | | | not audited | |
| cause-effect structure | 2 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| intrinsic cause-effect power | 1 | 1 | 1 | 0 | 0 | 0 | 100% | 21%-100% |
| maximally irreducible conceptual structure | 3 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| cause-effect repertoire | 6 | 3 | 3 | 0 | 0 | 0 | 100% | 44%-100% |
| IIT 3.0 | 4 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| IIT 4.0 | 0 | 0 | | | | | not audited | |

Theory level, de-duplicated by paper: 20 audited hits = **12 unique papers**; 12 Y, 0 N, 0 undecided; precision 12/12 = 100% (Wilson 95% 76%-100%).


### Panpsychism

| strong term | papers (corpus) | audited n | Y | N | ? | weak (in Y) | precision | Wilson 95% |
|---|---|---|---|---|---|---|---|---|
| panpsychism | 16 | 10 | 10 | 0 | 0 | 4 | 100% | 72%-100% |
| panpsychist | 6 | 4 | 4 | 0 | 0 | 0 | 100% | 51%-100% |
| panpsychists | 1 | 1 | 1 | 0 | 0 | 0 | 100% | 21%-100% |
| panpsychic | 1 | 1 | 1 | 0 | 0 | 0 | 100% | 21%-100% |
| panpsychistic | 0 | 0 | | | | | not audited | |
| micropsychism | 0 | 0 | | | | | not audited | |
| micropsychist | 0 | 0 | | | | | not audited | |
| cosmopsychism | 0 | 0 | | | | | not audited | |
| cosmopsychist | 0 | 0 | | | | | not audited | |
| panprotopsychism | 0 | 0 | | | | | not audited | |
| panprotopsychist | 0 | 0 | | | | | not audited | |
| panexperientialism | 2 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| combination problem | 2 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| constitutive panpsychism | 0 | 0 | | | | | not audited | |
| monadic panpsychism | 0 | 0 | | | | | not audited | |

Theory level, de-duplicated by paper: 20 audited hits = **12 unique papers**; 12 Y, 0 N, 0 undecided; precision 12/12 = 100% (Wilson 95% 76%-100%).


### Predictive Processing / Free Energy Principle

| strong term | papers (corpus) | audited n | Y | N | ? | weak (in Y) | precision | Wilson 95% |
|---|---|---|---|---|---|---|---|---|
| free energy principle | 94 | 4 | 4 | 0 | 0 | 1 | 100% | 51%-100% |
| predictive processing | 54 | 4 | 2 | 1 | 1 | 0 | 67% | 21%-94% |
| predictive mind | 1 | 1 | 1 | 0 | 0 | 0 | 100% | 21%-100% |
| active inference | 94 | 7 | 7 | 0 | 0 | 0 | 100% | 65%-100% |
| prediction error minimization | 19 | 2 | 2 | 0 | 0 | 0 | 100% | 34%-100% |
| beautiful loop | 0 | 0 | | | | | not audited | |

Theory level, de-duplicated by paper: 20 audited hits = **19 unique papers**; 15 Y, 3 N, 1 undecided; precision 15/18 = 83% (Wilson 95% 61%-94%).


**The audit sample over-represents a few papers** (hits per paper across all theories; 83 audited hits come from 62 unique papers):

| PMCID | audited hits | by theory |
|---|---|---|
| PMC4387509 | 9 | integrated_information 5, panpsychism 4 |
| PMC3502201 | 4 | panpsychism 4 |
| PMC4014402 | 3 | integrated_information 3 |
| PMC4574706 | 3 | integrated_information 1, panpsychism 2 |
| PMC3912322 | 3 | integrated_information 1, panpsychism 2 |
| PMC2771980 | 2 | global_workspace 2 |
| PMC4270440 | 2 | integrated_information 2 |
| PMC4233945 | 2 | integrated_information 2 |
| PMC4064703 | 2 | predictive_processing_fep 2 |

PMC4387509 alone supplies 9 of the 83 rows (5 IIT, 4 panpsychism); PMC3502201 supplies 4 of panpsychism's 20, PMC4014402 3 of IIT's 20. Read theory-level precision per unique paper, not per row.


## 9. Server-side trend (Europe PMC, OA full text, strong phrases)

Hits (per 10,000 OA full-text papers that year). Phrase counts without the domain rule: an upper bound on direct mentions. 2024-2025 are incomplete in PMC.

| Year | OA papers | Champagne's | Global | Integrated | Panpsychism | Predictive |
|---|---|---|---|---|---|---|
| 1995 | 3907 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 1996 | 4063 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 1997 | 4399 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 1998 | 4553 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 1999 | 4939 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 1 (2.02) | 0 (0.00) |
| 2000 | 5714 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2001 | 7093 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2002 | 7746 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2003 | 8981 | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2004 | 13299 | 0 (0.00) | 1 (0.75) | 1 (0.75) | 0 (0.00) | 0 (0.00) |
| 2005 | 17270 | 0 (0.00) | 3 (1.74) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2006 | 24002 | 0 (0.00) | 2 (0.83) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2007 | 28859 | 0 (0.00) | 5 (1.73) | 0 (0.00) | 1 (0.35) | 2 (0.69) |
| 2008 | 45032 | 0 (0.00) | 6 (1.33) | 1 (0.22) | 0 (0.00) | 3 (0.67) |
| 2009 | 60500 | 0 (0.00) | 9 (1.49) | 1 (0.17) | 1 (0.17) | 5 (0.83) |
| 2010 | 81639 | 0 (0.00) | 13 (1.59) | 1 (0.12) | 1 (0.12) | 9 (1.10) |
| 2011 | 110828 | 0 (0.00) | 29 (2.62) | 0 (0.00) | 7 (0.63) | 19 (1.71) |
| 2012 | 150481 | 2 (0.13) | 30 (1.99) | 4 (0.27) | 3 (0.20) | 45 (2.99) |
| 2013 | 186528 | 0 (0.00) | 25 (1.34) | 1 (0.05) | 6 (0.32) | 51 (2.73) |
| 2014 | 223868 | 0 (0.00) | 33 (1.47) | 10 (0.45) | 6 (0.27) | 61 (2.72) |
| 2015 | 252293 | 1 (0.04) | 31 (1.23) | 7 (0.28) | 7 (0.28) | 82 (3.25) |
| 2016 | 276180 | 0 (0.00) | 44 (1.59) | 17 (0.62) | 12 (0.43) | 111 (4.02) |
| 2017 | 315205 | 2 (0.06) | 33 (1.05) | 14 (0.44) | 12 (0.38) | 109 (3.46) |
| 2018 | 355962 | 2 (0.06) | 44 (1.24) | 36 (1.01) | 18 (0.51) | 190 (5.34) |
| 2019 | 415138 | 3 (0.07) | 53 (1.28) | 38 (0.92) | 12 (0.29) | 209 (5.03) |
| 2020 | 598386 | 2 (0.03) | 77 (1.29) | 50 (0.84) | 24 (0.40) | 319 (5.33) |
| 2021 | 751407 | 4 (0.05) | 107 (1.42) | 68 (0.90) | 45 (0.60) | 506 (6.73) |
| 2022 | 850767 | 3 (0.04) | 103 (1.21) | 75 (0.88) | 42 (0.49) | 643 (7.56) |
| 2023 | 774915 | 10 (0.13) | 114 (1.47) | 88 (1.14) | 38 (0.49) | 634 (8.18) |
| 2024 | 772437 | 9 (0.12) | 108 (1.40) | 77 (1.00) | 32 (0.41) | 763 (9.88) |
| 2025 | 921079 | 5 (0.05) | 151 (1.64) | 104 (1.13) | 36 (0.39) | 1039 (11.28) |

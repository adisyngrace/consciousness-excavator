# Profiles

Landscape of Consciousness (LoC) description text and paper abstracts were removed from these files for licensing reasons
(they are third-party text). What remains: core claims (written and edited by the author), ids, sources, routes, excluded-seed
reasons (no text), the weights in `config.yaml`, and the generic and cross-theory contrast profiles.

`src/level3_concepts/make_profiles.py` regenerates the removed LoC and abstract text from the scraped pages (`python -m src.level1_extract`
first, then `python -m src.level3_concepts.make_profiles --force`; it needs network access and the pipeline database, which are not included).
`make_profiles.py` writes draft claims, so after regenerating, restore the approved core claims from `claims_revised/`.

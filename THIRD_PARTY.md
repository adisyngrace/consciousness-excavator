# Third-party data and what is not included

## Sources
| Source | Used for | Notes |
|---|---|---|
| Landscape of Consciousness (Robert Lawrence Kuhn; Closer To Truth), https://loc.closertotruth.com/ | Theory descriptions and reference lists | Page text is not redistributed. `results/theory_descriptions.csv` has two attributed sentences per theory with the source URL. Follow the site's terms for any further reuse. |
| Europe PMC / PubMed Central open access (REST API) | The full-text corpus and per-year counts | Papers keep their own licences. Only titles, ids, years, scores, counts and short snippets (at most 150 characters) are included. |
| Crossref | Reference string to DOI resolution | Level 1 only. |
| Unpaywall | Open-access copies of DOIs not in PMC | Level 1 only. |
| OpenAlex | Discovery only (DOI and open-access lookups) | No citation graph is used. |
| CORE (core.ac.uk) | Exploratory philosophy pilot (Champagne, panpsychism) | The API returns no licence field and CORE's terms limit the data to machine processing. CORE text is never published. Cite CORE using the citation on core.ac.uk. |
| BAAI bge-base-en-v1.5 | Embedding model | Downloaded at run time; weights are not included. |

## Not included
- Full texts of papers (PMC and CORE), embeddings, the SQLite database and HTTP caches.
- Landscape of Consciousness page text, saved LoC pages and paper abstracts (removed from `profiles/*.yaml`).
- CORE title, link and id lists and CORE hand labels, withheld pending CORE's response.
- Test fixtures holding saved pages or paper text.

## Licence
No LICENSE file is included: all rights reserved for now.

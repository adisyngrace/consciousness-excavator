# Judge rubric (prompt 06)

You are judging whether a paper is a conceptual neighbor of a theory of consciousness. Each batch file gives one theory with its core claims (each with an id), then up to 10 items. Each item has a title, year, abstract and two passages from the paper. Judge every item from the packet text alone.

## The five theories (for `better_fit_theory`)
Short neutral descriptions, drawn from the core claims in each theory's profile. The batch file's claim list is the standard for R; these lines are only for deciding whether another theory fits clearly better.
- **Champagne's semiotic account:** felt qualities can be separated from their causal and inferential relations only in thought, and a Peircean sign typology (type, token and tone) with reference by resemblance lets qualities be explained without positing a separate mental realm, dissolving rather than solving the hard problem.
- **Global Workspace Theory:** many specialised processors work in parallel and compete, and the winning content is broadcast across the brain, becoming available at once to attention, memory, report and action; that brain-wide availability is what makes one aware of it.
- **Integrated Information Theory:** the essential properties of experience (intrinsic, specific, unified, definite, structured) are translated into requirements on a physical system's cause-effect structure, and consciousness is identified with a maximally irreducible structure measured by phi, not with what the system computes.
- **Panpsychism:** experience or a precursor of it is a primitive feature of the fundamental constituents of physical reality, so richer minds arise from the combination of micro-level experience, and the central difficulty is how many small subjects or properties form one unified experience.
- **Predictive Processing / Free Energy Principle:** the brain continuously generates top-down predictions about the causes of its sensory input, with bottom-up signals carrying prediction errors weighted by precision, and perception, learning and action all work by minimising the mismatch, which also expresses how organisms keep themselves in stable, low-surprise states.

## Rules
- Use only the text in the packet. Do not use outside knowledge about the paper, its authors or its citations. If the packet is too thin to decide (no abstract, passages off the point), give your best verdict with `confidence` = "low".
- Judge each item independently. Do not compare items, do not look for patterns across a batch, and do not try to guess how the item was selected.
- The question is whether the paper's own content parallels a specific core claim of the theory. It is not whether the paper is a good paper, or whether you would cite it.

## Verdicts
- **R, relevant conceptual neighbor.** The paper's own content, as shown in the packet, makes a claim, uses a mechanism or addresses a problem that parallels a specific core claim of the theory, even in different words. Name the claim id(s) in `claim_ids`. The parallel must be to the claim's content, not just its topic.
- **G, generic.** About consciousness, awareness or general neuroscience, but with no specific parallel to a core claim. The same brain region, the same task or paradigm, or "consciousness" in general is not enough.
- **O, off-topic.** Unrelated to the theory's ideas.
- **Champagne's semiotic account:** R requires a parallel to sign, meaning, interpretation, or the phenomenology of qualities (claims c1-c8). "Communication" or "language" alone is not enough.

## Output
For each batch, write a JSON list, one object per item, with exactly these keys:
- `item_id`: the id shown in the packet
- `verdict`: "R", "G" or "O"
- `confidence`: "high", "medium" or "low"
- `claim_ids`: list of claim ids that the paper parallels; empty unless verdict is R
- `reason`: one sentence naming the specific parallel (R) or why there is none (G, O)
- `evidence`: a quote of at most 20 words copied exactly from that item's packet (title, abstract or passages), character for character; for R, the text that carries the parallel
- `names_theory_in_text`: true only if the packet text actually names the theory or its standard abbreviation, which should not happen
- `better_fit_theory`: the name of another of the five theories (Champagne's semiotic account, Global Workspace Theory, Integrated Information Theory, Panpsychism, Predictive Processing / Free Energy Principle) if the paper clearly fits it better than this one, else null

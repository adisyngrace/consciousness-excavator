"""Streamlit viewer for the Consciousness Theory Literature Excavator. Reads only the tables in results/."""
from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import data  # noqa: E402

JUDGE_LABEL = "LLM judge (Claude), blind to ranking; checked against my labels on a sample"
VERDICT_TEXT = {"R": "Judged a conceptual neighbor of the theory",
                "G": "Judged generic consciousness / neuroscience, not specific to the theory",
                "O": "Judged off-topic"}
FOOTER = ("Data: PubMed Central open-access papers via Europe PMC; theory descriptions and reference lists from the "
          "Landscape of Consciousness (Closer To Truth). Judge verdicts come from an LLM and are not ground truth.")
LIMITS = [
    "**Open access only.** Only papers with free full text are searched. Coverage leans toward neuroscience, "
    "psychology and medicine; philosophy-heavy theories (panpsychism, Champagne) are thin.",
    "**Negatives are unlabeled.** In the tests, \"not a positive\" means the paper does not name the theory, not that it "
    "is known to be irrelevant. Scores are lower bounds.",
    "**The judge is an LLM.** Its verdicts are not ground truth. Agreement with my hand labels on a sample was moderate "
    "(kappa 0.44).",
    "**Small samples.** Champagne, IIT and panpsychism have few direct-mention papers in 1995-2015; treat their numbers "
    "as exploratory.",
    "**Candidate-pool confound.** Test positives mostly come from papers already found by theory queries, so the "
    "candidate-only AUC is the more informative number.",
    "**2016-2025 is a capped sample.** Lists for those years are a sample of at most 400 candidates per theory. Totals "
    "and trends come from full Europe PMC counts. 2024-2025 are incomplete in PMC.",
    "**Not a forecast.** The concept profiles come from current LoC text, so the 2016-2025 test shows whether the method "
    "generalizes to later papers, not that it predicted them.",
    "**Only 1995-2015 was judged.** Papers from later years in the conceptual-associations lists are marked \"not judged\".",
]


@st.cache_data
def tables() -> dict[str, pd.DataFrame]:
    return data.load_all()


def pmc_link(pmcid: str) -> str:
    return data.pmc_url(pmcid)


def header(theory: str, d: dict) -> None:
    desc = data.description(theory, d)
    st.title(desc["theory_name"])
    st.markdown(f"> {desc['excerpt']}")
    st.caption(f"Excerpt from the [Landscape of Consciousness page]({desc['source_url']}) (verbatim).")
    c = data.exclusive_counts(theory, d)
    a = f"**{c['n_1995_2015']}** in 1995-2015" + (" (exploratory)" if c["exploratory_1995_2015"] else "")
    b = f"**{c['n_2016_2025']}** in the 2016-2025 sample" + (" (exploratory)" if c["exploratory_2016_2025"] else "")
    st.info(f"Papers that name this theory and no other: {a}, {b}. The 2016-2025 figure is a capped sample "
            f"({c['cap_note']}), not a total.")


def tab_references(theory: str, d: dict) -> None:
    s = data.reference_summary(theory, d)
    st.markdown(f"**{s['total']} references.** {s['non_article']} are books, videos or web pages (not journal "
                f"articles). {s['open_fulltext']} have free full text ({s['europe_pmc_fulltext']} in Europe PMC, the "
                f"rest as open PDFs).")
    st.caption("Reference lists are as listed on the Landscape of Consciousness; many entries are books or videos.")
    r = data.references(theory, d).copy()
    r["DOI"] = r.doi.map(lambda x: f"https://doi.org/{x}" if x else None)
    r["Open full text"] = r.oa_fulltext.map({"yes": "yes", "no": "no"}) + r.oa_route.map(
        lambda x: "" if x == "none" else f" ({x.replace('_', ' ')})")
    r["Status"] = r.resolution_status.str.replace("_", " ")
    r["Year"] = r.year.astype("Int64")
    r["Title"] = r.parsed_title.where(r.parsed_title != "", r.raw_reference.str.slice(0, 120))
    st.dataframe(r[["Title", "Year", "DOI", "Status", "Open full text"]], hide_index=True, width="stretch",
                 column_config={"DOI": st.column_config.LinkColumn("DOI", display_text="open")})


def trend_chart(theory: str, window: str, d: dict) -> alt.Chart:
    t = data.trends(theory, d)
    end = data.WINDOWS[window]
    base = alt.Chart(t).encode(x=alt.X("year:Q", axis=alt.Axis(format="d"), title="Year"))
    band = alt.Chart(pd.DataFrame({"a": [1994.5], "b": [end + 0.5]})).mark_rect(opacity=0.12).encode(x="a:Q", x2="b:Q")
    line = base.mark_line(point=True).encode(
        y=alt.Y("rate_per_10k:Q", title="Papers naming the theory per 10,000 open-access papers"),
        tooltip=["year", "hits", "total_oa_papers", "rate_per_10k"])
    incomplete = alt.Chart(pd.DataFrame({"a": [2023.5], "b": [2025.5]})).mark_rect(opacity=0.15, color="gray").encode(
        x="a:Q", x2="b:Q")
    return (band + incomplete + line).properties(height=260)


def tab_mentions(theory: str, window: str, d: dict) -> None:
    st.markdown("Papers whose full text names the theory (strong phrase plus cognitive-science context). "
                "Reference lists are never counted.")
    if data.includes_capped_sample(window):
        st.warning("This view includes 2016-2025 papers. That list is a **capped sample**, not a complete list. "
                   "Totals come from the full Europe PMC counts in the chart below.")
    st.altair_chart(trend_chart(theory, window, d), width="stretch")
    st.caption("Rate of open-access papers matching a strong phrase of the theory (full server-side counts). Blue band: "
               "selected window. Grey band: 2024-2025, incomplete in PMC, so the rate is an upper bound.")
    c1, c2 = st.columns(2)
    tiers = c1.multiselect("Mention tier", ["direct", "weak", "close"], default=["direct"],
                           help="direct: names the theory; weak: a term that needs corroboration appeared alone; "
                                "close: only a closely related term.")
    mx = int(data.mentions(theory, window, d=d).mention_strength.max() or 1) if len(
        data.mentions(theory, window, d=d)) else 1
    min_s = c2.slider("Minimum mention strength (hits)", 0, max(mx, 1), 0)
    m = data.mentions(theory, window, tiers or None, min_s, d)
    if m.empty:
        st.info("No papers match these filters in this window.")
        return
    st.markdown(f"**{len(m)} papers shown** (window {window}).")
    v = m.copy()
    v["Link"] = v.pmcid.map(pmc_link)
    v = v.rename(columns={"title": "Title", "year": "Year", "mention_tier": "Tier", "mention_strength": "Hits",
                          "first_hit_section": "First seen in"})
    st.dataframe(v[["Title", "Year", "Tier", "Hits", "First seen in", "Link"]], hide_index=True, width="stretch",
                 column_config={"Link": st.column_config.LinkColumn("Link", display_text="PMC")})
    with st.expander("Read the snippet for a paper"):
        pick = st.selectbox("Paper", list(range(len(m))), format_func=lambda i: f"{m.title[i][:90]} ({m.year[i]})",
                            key=f"snip_{theory}_{window}")
        st.write(f"...{m.snippet[pick]}...")
        st.caption(f"{m.pmcid[pick]} · {m.journal[pick]} · first seen in {m.first_hit_section[pick]}")


def card(row: pd.Series) -> None:
    with st.container(border=True):
        st.markdown(f"**#{row['rank']}  [{row.title}]({pmc_link(row.pmcid)})** ({row.year})")
        st.markdown(f"Parallels claim `{row.best_claim_id}`: {row.best_claim_text}")
        st.caption(f"Closest passage: ...{row.snippet}...")
        if row.other_theories_named:
            names = [data.THEORIES.get(x, x) for x in row.other_theories_named.split(";") if x]
            st.caption("Also names: " + ", ".join(names))
        else:
            st.caption("Names none of the five theories.")
        if row.judged == "true":
            st.markdown(f"**{VERDICT_TEXT[row.judge_verdict]}** (confidence: {row.judge_confidence})")
            st.markdown(f"Reason: {row.judge_reason}")
            st.markdown(f"> {row.judge_evidence}")
            st.caption(JUDGE_LABEL)
        else:
            st.markdown("**Not judged.** This says nothing about whether the paper is relevant.")


def tab_concepts(theory: str, window: str, d: dict) -> None:
    st.markdown("Papers whose text is close in meaning to the theory's core claims but that **never name the "
                "theory**. Top 30 by embedding similarity (method V4).")
    if window == "1995-2015":
        n = data.headline_count(theory, d)
        st.success(f"**{n} of 30** papers the judge rated as conceptual neighbors of this theory never name it.")
        st.caption(JUDGE_LABEL + ".")
    else:
        c = data.judge_counts(theory, window, d)
        st.warning(f"Only papers from 1995-2015 were judged. In this window {c['judged']} of {c['shown']} are judged "
                   f"(the rest, including every paper after 2015, are **not judged**).")
    only = st.checkbox("Show judged-relevant papers only", key=f"only_{theory}_{window}")
    t = data.top_papers(theory, window, only, d)
    if t.empty:
        st.info("No papers to show with this filter in this window.")
        return
    for _, row in t.iterrows():
        card(row)


def tab_eval(theory: str, d: dict) -> None:
    st.subheader("Headline numbers, all five theories")
    st.dataframe(data.seeds_and_silver(d).assign(theory=lambda x: x.theory.map(data.THEORIES)).rename(
        columns={"theory": "Theory"}), hide_index=True, width="stretch",
        column_config={"Judged relevant share (V4 top 30)": st.column_config.NumberColumn(format="%.2f")})
    st.caption("Judged relevant share = share of the 30 top V4 papers the LLM judge rated a conceptual neighbor "
               "(1995-2015 only). 2016-2025 counts are a capped sample.")
    st.subheader("Does the method beat keyword ranking? (term-masked test)")
    st.markdown("Theory names are blanked out of known papers; we ask whether each method still ranks them above other "
                "candidate papers. AUC: 0.5 is chance, 1.0 is perfect. V4 = this tool's embedding score; BM25 = keyword "
                "ranking. 95% confidence intervals in brackets.")
    m = data.metrics(d)
    m["Theory"] = m.theory.map(data.THEORIES)
    m["V4"] = m.apply(lambda r: f"{r.V4:.2f} [{r.V4_lo:.2f}, {r.V4_hi:.2f}]", axis=1)
    m["BM25"] = m.apply(lambda r: f"{r.BM25:.2f} [{r.BM25_lo:.2f}, {r.BM25_hi:.2f}]", axis=1)
    m["Note"] = m.exploratory.map({True: "exploratory (n < 20)", False: ""})
    m = m.rename(columns={"period": "Period", "n_positives": "n"})
    st.dataframe(m[["Theory", "Period", "n", "V4", "BM25", "Note"]], hide_index=True, width="stretch")
    st.caption("Candidate-only AUC (the more informative one). 1995-2015 and 2016-2025 use different negative pools, so "
               "compare them loosely. Overlapping intervals mean no clear difference.")
    st.subheader("Does each theory's profile find its own papers? (V4, candidate pool)")
    period = st.radio("Period", ["1995-2015", "2016-2025"], horizontal=True, key="disc_period")
    mat = data.discriminability(period, d=d)
    if not mat.empty:
        long = mat.reset_index().melt(id_vars="row_profile", var_name="positives", value_name="rank")
        for c in ("row_profile", "positives"):
            long[c] = long[c].map(data.THEORIES)
        base = alt.Chart(long).encode(x=alt.X("positives:N", title="Papers of theory (columns)"),
                                      y=alt.Y("row_profile:N", title="Profile of theory (rows)"))
        heat = base.mark_rect().encode(color=alt.Color("rank:Q", scale=alt.Scale(scheme="blues"),
                                                       title="Mean percentile"))
        txt = base.mark_text().encode(text=alt.Text("rank:Q", format=".0f"))
        st.altair_chart((heat + txt).properties(height=300), width="stretch")
    st.caption("V4, candidate pool. Each cell is the mean percentile rank (100 = best, 50 = chance) of a column theory's "
               "papers under a row theory's profile. Champagne, IIT and panpsychism remain the most confusable group "
               "while the diagonal is the column maximum.")
    st.subheader("Limits")
    for x in LIMITS:
        st.markdown(f"- {x}")


def main() -> None:
    st.set_page_config(page_title="Consciousness Theory Literature Excavator", layout="wide")
    try:
        d = tables()
    except data.DataError as e:
        st.error(str(e))
        st.stop()
    with st.sidebar:
        st.header("Choose")
        theory = st.radio("Theory", list(data.THEORIES), format_func=data.THEORIES.get, key="theory")
        window = st.radio("Window", list(data.WINDOWS), key="window")
        with st.expander("About this tool"):
            st.markdown("Finds literature tied to five theories of consciousness at three levels: (1) the references on "
                        "each Landscape of Consciousness page, (2) papers that name the theory, and (3) papers close in "
                        "meaning to the theory that never name it. This app only displays saved results.")
    header(theory, d)
    t1, t2, t3, t4 = st.tabs(["References", "Direct mentions", "Conceptual associations", "Evaluation and limits"])
    with t1:
        tab_references(theory, d)
    with t2:
        tab_mentions(theory, window, d)
    with t3:
        tab_concepts(theory, window, d)
    with t4:
        tab_eval(theory, d)
    st.divider()
    st.caption(FOOTER)


main()

import shutil

import pytest

from app import data


def test_load_all_has_every_table():
    d = data.load_all()
    assert set(d) == set(data.REQUIRED)
    assert all(len(v) > 0 for v in d.values())


def test_missing_file_gives_clear_error(tmp_path):
    with pytest.raises(data.DataError, match="Missing file"):
        data.load_all.__wrapped__(tmp_path)


def test_missing_column_gives_clear_error(tmp_path):
    for f in data.REQUIRED:
        shutil.copy(data.RESULTS / f, tmp_path / f)
    p = tmp_path / "window_trends.csv"
    p.write_text(p.read_text().replace("rate_per_10k", "rate", 1))
    with pytest.raises(data.DataError, match="rate_per_10k"):
        data.load_all.__wrapped__(tmp_path)


def test_mentions_filter_on_year_not_label():
    m95 = data.mentions("global_workspace", "1995-2015")
    m20 = data.mentions("global_workspace", "1995-2020")
    m25 = data.mentions("global_workspace", "1995-2025")
    assert m95.year.max() <= 2015 and m20.year.max() <= 2020
    assert len(m95) <= len(m20) <= len(m25)
    assert (m25.year > 2020).any()


def test_mentions_tier_and_strength_filters():
    m = data.mentions("global_workspace", "1995-2025", tiers=["direct"], min_strength=3)
    assert set(m.mention_tier) == {"direct"} and (m.mention_strength >= 3).all()


def test_empty_result_is_an_empty_frame():
    assert data.mentions("champagne_semiotic", "1995-2015", tiers=["close"]).empty
    assert data.top_papers("panpsychism", "1995-2015").shape[0] == 30
    assert data.top_papers("panpsychism", "1995-2025", judged_relevant_only=True).judged.eq("true").all()


def test_capped_sample_flag():
    assert not data.includes_capped_sample("1995-2015")
    assert data.includes_capped_sample("1995-2020") and data.includes_capped_sample("1995-2025")


def test_unjudged_rows_have_no_verdict_and_post_2015_unjudged():
    for th in data.THEORIES:
        for w in data.WINDOWS:
            t = data.top_papers(th, w)
            assert (t[t.judged == "false"].judge_verdict == "").all()
            assert (t[t.year > 2015].judged == "false").all()
        c = data.judge_counts(th, "1995-2015")
        assert c["judged"] == 30 and c["R"] + c["G"] + c["O"] == 30


def test_headline_matches_summary_share():
    s = data.load_all()["summary_metrics.csv"].set_index("theory")
    for th in data.THEORIES:
        assert round(data.headline_count(th) / 30, 3) == pytest.approx(float(s.loc[th, "judged_R_share_v4_top30_1995_2015"]), abs=1e-3)


def test_exploratory_flags():
    assert data.exclusive_counts("champagne_semiotic")["exploratory_1995_2015"]
    assert not data.exclusive_counts("global_workspace")["exploratory_1995_2015"]
    assert data.exclusive_counts("champagne_semiotic")["n_1995_2015"] == 3


def test_unknown_theory_and_window():
    with pytest.raises(KeyError):
        data.top_papers("nope", "1995-2015")
    with pytest.raises(KeyError):
        data.mentions("panpsychism", "2000-2001")


def test_reference_summary_and_trends_and_matrix():
    s = data.reference_summary("global_workspace")
    assert s["total"] == 12 and s["open_fulltext"] == 3   # 13 in the full list; one personal communication removed from the public release
    assert len(data.trends("panpsychism")) == 31
    mat = data.discriminability("1995-2015")
    assert mat.shape == (5, 5)
    for col in mat.columns:
        assert mat[col].idxmax() == col
    assert len(data.metrics()) == 10

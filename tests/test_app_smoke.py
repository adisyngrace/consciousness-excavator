import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")

from pathlib import Path  # noqa: E402

from app import data  # noqa: E402

APP = str(Path(__file__).resolve().parent.parent / "app" / "app.py")


@pytest.mark.parametrize("theory", list(data.THEORIES))
@pytest.mark.parametrize("window", list(data.WINDOWS))
def test_every_theory_and_window_renders(theory, window):
    at = st_testing.AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    at.radio(key="theory").set_value(theory)
    at.radio(key="window").set_value(window).run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.title[0].value == data.THEORIES[theory]
    assert not at.error


def test_judged_only_filter_and_empty_state():
    at = st_testing.AppTest.from_file(APP, default_timeout=60).run()
    at.radio(key="theory").set_value("champagne_semiotic").run()
    at.checkbox(key="only_champagne_semiotic_1995-2015").check().run()
    assert not at.exception

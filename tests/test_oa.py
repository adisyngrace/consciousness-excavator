from src.oa import abstract_from_index, pick_location


def test_prefers_pdf_from_any_location_over_landing_page():
    data = {"best_oa_location": {"url": "https://x/landing", "url_for_pdf": None},
            "oa_locations": [{"url": "https://repo/landing", "url_for_pdf": "https://repo/paper.pdf"}]}
    url, kind, loc = pick_location(data)
    assert (url, kind) == ("https://repo/paper.pdf", "pdf")


def test_landing_page_when_no_pdf():
    url, kind, _ = pick_location({"best_oa_location": {"url": "https://x/landing", "url_for_pdf": None}})
    assert (url, kind) == ("https://x/landing", "landing")


def test_closed_access():
    assert pick_location({"best_oa_location": None, "oa_locations": []}) == (None, None, None)


def test_abstract_reconstruction_orders_words():
    assert abstract_from_index({"world": [1], "Hello": [0], "again": [2, 3]}) == "Hello world again again"
    assert abstract_from_index(None) is None

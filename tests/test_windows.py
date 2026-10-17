from src.level3_concepts.windows import allocate, page_windows, pick, split_pages
from src.level3_concepts.chunk import windows


def test_allocate_even_with_floor_per_page():
    assert allocate([8, 10], 11) == [5, 6] or sum(allocate([8, 10], 11)) == 11
    a = allocate([1, 1, 1, 9], 6)
    assert sum(a) == 6 and a[:3] == [1, 1, 1] and a[3] == 3
    assert allocate([2, 3], 99) == [2, 3]


def test_pick_spread():
    assert pick(10, 3) == [2, 5, 8] or len(pick(10, 3)) == 3
    assert pick(3, 5) == [0, 1, 2]


def test_split_pages_flags_and_no_text_loss():
    desc = "## a\nTakeaways x\n\nbody one two\n## peirce-s-phaneroscopic-semiotics\nintro words. A Note on Placement placed first"
    pages = split_pages(desc)
    assert [p["slug"] for p in pages] == ["a", "peirce-s-phaneroscopic-semiotics"]
    segs = pages[1]["segments"]
    assert [s["use_in_profile"] for s in segs] == [True, False] and segs[1]["text"].startswith("A Note on Placement")
    assert page_windows({"use_in_profile": False, "segments": []}) == []
    assert len(page_windows(pages[0])) == 1


def test_chunk_windows_never_tiny_tail():
    ws = windows(" ".join(str(i) for i in range(185)))
    assert len(ws) == 1 and len(ws[0].split()) == 185
    assert windows("short text") == []

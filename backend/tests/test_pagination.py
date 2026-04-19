from app.utils.pagination import paginate


def test_paginate_calculates_pages_correctly():
    result = paginate(items=list(range(10)), total=25, page=1, size=10)
    assert result.pages == 3


def test_paginate_returns_correct_metadata():
    result = paginate(items=list(range(10)), total=25, page=2, size=10)
    assert result.total == 25
    assert result.page == 2
    assert result.size == 10


def test_paginate_preserves_items():
    items = ["a", "b", "c"]
    result = paginate(items=items, total=3, page=1, size=10)
    assert list(result.items) == ["a", "b", "c"]


def test_paginate_empty_result():
    result = paginate(items=[], total=0, page=1, size=10)
    assert result.total == 0
    assert result.pages == 0
    assert list(result.items) == []


def test_paginate_last_page_with_remainder():
    result = paginate(items=list(range(5)), total=25, page=3, size=10)
    assert result.pages == 3

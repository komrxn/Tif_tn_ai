import json
from pathlib import Path

import pytest

BUILD = Path(__file__).parent.parent / "data" / "build"


@pytest.fixture(scope="module")
def chunks():
    path = BUILD / "chunks.json"
    if not path.exists():
        pytest.skip("chunks.json not built yet")
    return json.loads(path.read_text(encoding="utf-8"))


def test_chunk_count_in_range(chunks):
    assert 1_900 < len(chunks) < 2_010


def test_primary_code_coverage(chunks):
    with_primary = sum(1 for c in chunks if c["primary_code"])
    pct = with_primary / len(chunks) * 100
    assert pct >= 95, f"Only {pct:.1f}% have primary_code"


def test_no_empty_text(chunks):
    for c in chunks:
        assert len(c["text"].strip()) >= 100


def test_page_nums_unique(chunks):
    nums = [c["page_num"] for c in chunks]
    assert len(nums) == len(set(nums))


def test_sorted_by_page_num(chunks):
    nums = [c["page_num"] for c in chunks]
    assert nums == sorted(nums)

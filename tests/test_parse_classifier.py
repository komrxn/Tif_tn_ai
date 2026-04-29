import json
from pathlib import Path

import pytest

BUILD = Path(__file__).parent.parent / "data" / "build"


@pytest.fixture(scope="module")
def records():
    path = BUILD / "classifier.json"
    if not path.exists():
        pytest.skip("classifier.json not built yet")
    return json.loads(path.read_text(encoding="utf-8"))


def test_minimum_record_count(records):
    assert len(records) >= 10_000


def test_no_duplicate_codes(records):
    codes = [r["code"] for r in records]
    assert len(codes) == len(set(codes))


def test_target_code_exists(records):
    by_code = {r["code"]: r for r in records}
    row = by_code.get("0101210000")
    assert row is not None
    assert any(w in row["name_ru"] for w in ("племенные", "чистопородные"))


def test_all_codes_digits_only(records):
    for r in records:
        assert r["code"].isdigit(), f"Non-digit code: {r['code']}"


def test_levels_are_valid(records):
    valid = {2, 4, 6, 8, 10}
    for r in records:
        assert r["level"] in valid, f"Bad level {r['level']} for {r['code']}"


def test_parents_exist(records):
    codes = {r["code"] for r in records}
    missing = [
        r["code"] for r in records if r["parent"] and r["parent"] not in codes and r["level"] > 2
    ]
    # Allow a small number of orphans due to PDF layout issues
    assert len(missing) < 50, f"Too many orphans: {len(missing)}, sample: {missing[:5]}"

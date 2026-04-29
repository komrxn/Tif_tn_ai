import json
from pathlib import Path

import pytest

BUILD = Path(__file__).parent.parent / "data" / "build"


@pytest.fixture(scope="module")
def records():
    path = BUILD / "duties.json"
    if not path.exists():
        pytest.skip("duties.json not built yet")
    return json.loads(path.read_text(encoding="utf-8"))


def test_minimum_record_count(records):
    assert len(records) >= 1500


def test_all_codes_valid(records):
    for r in records:
        c = r["code"]
        assert c.isdigit() and len(c) in (4, 6, 8, 10), f"Bad duty code: {c}"


def test_compound_rate_kg(records):
    kg_rows = [r for r in records if r["min_per_kg_usd"] is not None]
    assert len(kg_rows) > 50, "Expected many kg-floor entries"
    for r in kg_rows:
        assert r["duty_pct"] is not None
        assert r["min_per_kg_usd"] > 0


def test_raw_text_preserved(records):
    for r in records:
        assert r["raw_text_uz"], f"Missing raw_text_uz for {r['code']}"


def test_specific_code_0403(records):
    by_code = {r["code"]: r for r in records}
    row = by_code.get("0403")
    assert row is not None
    assert row["duty_pct"] == 20.0
    assert row["min_per_kg_usd"] == pytest.approx(0.3)

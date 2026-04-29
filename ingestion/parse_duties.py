"""Parse ПК-181.md → data/build/duties.json

Each logical entry has 1-N codes sharing one name + rate.
Multi-code entries are exploded into separate rows.
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
MD_PATH = DATA_DIR / "ПК-181.md"
OUT_PATH = DATA_DIR / "build" / "duties.json"

# A code line is ONLY digits + optional trailing comma; nothing else
_CODE_LINE_RE = re.compile(r"^\d+,?\s*$")
# USD floor amount extraction
_USD_RE = re.compile(r"(\d+[,.]?\d*)\s*АҚШ долларидан")
# Header lines to skip
_HEADER_LINES = {
    "ТИФ ТНнинг 2022 йилги таҳрири",
    "Товар номи",
    "Импорт божхона божи ставкаси",
    "(товарнинг божхона қийматига нисбатан %да ёки ўлчов бирлиги учун АҚШ долларида)",
}


def _parse_rate(raw: str) -> tuple[float | None, float | None, float | None, float | None]:
    """Return (duty_pct, min_per_kg_usd, min_per_unit_usd, min_per_liter_usd)."""
    raw = raw.strip()
    pct_m = re.match(r"^(\d+(?:[,.]\d+)?)", raw)
    duty_pct = float(pct_m.group(1).replace(",", ".")) if pct_m else None

    usd_m = _USD_RE.search(raw)
    if not usd_m:
        return duty_pct, None, None, None

    usd_val = float(usd_m.group(1).replace(",", "."))

    if "килограмм" in raw:
        return duty_pct, usd_val, None, None
    if "литр" in raw:
        return duty_pct, None, None, usd_val
    if "дона" in raw:
        # "ҳар 1000 донаси учун X АҚШ" → store per-unit
        if "1000 дона" in raw:
            return duty_pct, None, round(usd_val / 1000, 6), None
        return duty_pct, None, usd_val, None

    return duty_pct, None, None, None


def _clean_code(raw: str) -> str:
    return raw.strip().rstrip(",").strip()


def parse() -> list[dict]:
    text = MD_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    records: list[dict] = []
    codes: list[str] = []
    name: str | None = None

    # States: "codes" | "got_name"
    state = "codes"

    def emit(rate_raw: str) -> None:
        if not codes or name is None:
            return
        pct, kg, unit, liter = _parse_rate(rate_raw)
        for raw_c in codes:
            c = _clean_code(raw_c)
            if c.isdigit() and len(c) in (4, 6, 8, 10):
                records.append(
                    {
                        "code": c,
                        "name_uz": name,
                        "duty_pct": pct,
                        "min_per_kg_usd": kg,
                        "min_per_unit_usd": unit,
                        "min_per_liter_usd": liter,
                        "raw_text_uz": rate_raw.strip(),
                    }
                )

    for raw_line in lines:
        line = raw_line.strip()

        if not line or line in _HEADER_LINES:
            continue

        if state == "codes":
            if _CODE_LINE_RE.match(line):
                codes.append(line)
            else:
                # Not a code — it's the name
                name = line
                state = "got_name"

        elif state == "got_name":
            # First non-blank line after name is the rate
            emit(line)
            codes = []
            name = None
            state = "codes"

    # Handle trailing entry without a trailing blank line
    # (shouldn't happen in practice but guard anyway)

    return records


def validate(records: list[dict]) -> None:
    assert len(records) >= 1500, f"Too few duty records: {len(records)}"
    codes = [r["code"] for r in records]
    for c in codes:
        assert len(c) in (4, 6, 8, 10) and c.isdigit(), f"Bad code: {c}"
    logger.info("Validation passed. Total duty rows: %d", len(records))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Parsing %s", MD_PATH)
    records = parse()
    validate(records)

    OUT_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote %d records to %s", len(records), OUT_PATH)

    # Show compound rate sample
    compound = next((r for r in records if r["min_per_kg_usd"] is not None), None)
    if compound:
        print("Compound rate sample:", json.dumps(compound, ensure_ascii=False, indent=2))

    # Rate type distribution
    total = len(records)
    has_kg = sum(1 for r in records if r["min_per_kg_usd"])
    has_unit = sum(1 for r in records if r["min_per_unit_usd"])
    has_liter = sum(1 for r in records if r["min_per_liter_usd"])
    print(
        f"Total: {total}  with_kg_floor: {has_kg}"
        f"  with_unit_floor: {has_unit}  with_liter_floor: {has_liter}"
    )


if __name__ == "__main__":
    main()

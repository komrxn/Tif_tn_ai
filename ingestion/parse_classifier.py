"""Parse TN-ved_rus.pdf → data/build/classifier.json

Flat list of {code, name_ru, parent, level, section, group_code, unit}.
Codes are always digit-only strings: 2, 4, 6, 8, or 10 chars.
"""

import json
import logging
import re
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
PDF_PATH = DATA_DIR / "TN-ved_rus.pdf"
OUT_PATH = DATA_DIR / "build" / "classifier.json"

# Matches code at start: 4 digits + optional groups of 2-3 digits + optional last digit
# Single space separates code from description (pdfplumber normalises whitespace).
_CODE_LINE_RE = re.compile(r"^(\d{4}(?:\s\d{2}(?:\s\d{2,3}(?:\s\d)?)?)?)\s(.+)$")
_SECTION_RE = re.compile(r"РАЗДЕЛ\s+([IVXLC]+)")
_GROUP_HEADER_RE = re.compile(r"^ГРУППА\s+(\d{2})\s*$")
_GROUP_ANY_RE = re.compile(r"ГРУППА\s+(\d{2})")

# Multi-line: group name follows group header on next non-blank line
_KNOWN_UNITS = {"шт", "кг", "л", "м2", "м3", "г", "пар", "м", "кар", "Ки", "100шт", "1000шт"}

# Skip pages 1–21 (convention text, units table)
_SKIP_BEFORE = 21


def _strip_code(raw: str) -> str:
    return re.sub(r"\s+", "", raw)


def _level(code: str) -> int:
    n = len(code)
    if n <= 2:
        return 2
    if n <= 4:
        return 4
    if n <= 6:
        return 6
    if n <= 8:
        return 8
    return 10


def _find_parent(code: str, known: set[str]) -> str | None:
    prefixes = [code[:8], code[:6], code[:4], code[:2]]
    for p in prefixes:
        if p and p != code and p in known:
            return p
    return None


def _extract_unit(rest: str) -> tuple[str, str | None]:
    """Split 'description unit' → (description, unit|None)."""
    tokens = rest.split()
    if not tokens:
        return rest, None
    # Check last 2 tokens as compound unit first
    if len(tokens) >= 2:
        compound = tokens[-2] + tokens[-1]
        if compound in _KNOWN_UNITS:
            return " ".join(tokens[:-2]).strip(), compound
    if tokens[-1] in _KNOWN_UNITS:
        return " ".join(tokens[:-1]).strip(), tokens[-1]
    return rest, None


def _clean_name(raw: str) -> str:
    return re.sub(r"^[\s–\-]+", "", raw).strip()


def parse() -> list[dict]:
    records: list[dict] = []
    group_names: dict[str, str] = {}  # group_code → name
    current_section: str | None = None
    current_group: str | None = None

    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        logger.info("PDF has %d pages, parsing from page %d", total, _SKIP_BEFORE + 1)

        for page_idx in range(_SKIP_BEFORE, total):
            page = pdf.pages[page_idx]
            text = page.extract_text(layout=False) or ""
            lines = text.splitlines()

            # Scan for section/group headers
            for li, line in enumerate(lines):
                sec_m = _SECTION_RE.search(line)
                if sec_m:
                    current_section = sec_m.group(1)

                grp_m = _GROUP_ANY_RE.search(line)
                if grp_m:
                    g = grp_m.group(1).zfill(2)
                    current_group = g
                    # Try to grab group name from next non-blank line
                    for nxt in lines[li + 1 :]:
                        nxt = nxt.strip()
                        if nxt and not nxt.startswith("Приме") and not nxt.startswith("РАЗДЕЛ"):
                            if g not in group_names:
                                group_names[g] = nxt
                            break

            # Parse code rows
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                m = _CODE_LINE_RE.match(line)
                if not m:
                    continue

                raw_code, rest = m.group(1), m.group(2)
                code = _strip_code(raw_code)

                if not code.isdigit() or len(code) < 4:
                    continue

                raw_name, unit = _extract_unit(rest)
                name = _clean_name(raw_name)
                if not name:
                    continue

                records.append(
                    {
                        "code": code,
                        "name_ru": name,
                        "parent": None,
                        "level": _level(code),
                        "section": current_section,
                        "group_code": current_group,
                        "unit": unit,
                    }
                )

    # Synthesise 2-digit group entries so 4-digit codes have a valid parent
    for g, name in group_names.items():
        records.append(
            {
                "code": g,
                "name_ru": name,
                "parent": None,
                "level": 2,
                "section": None,
                "group_code": g,
                "unit": None,
            }
        )

    # Deduplicate: keep first occurrence per code
    seen: dict[str, dict] = {}
    for r in records:
        if r["code"] not in seen:
            seen[r["code"]] = r
    records = list(seen.values())

    # Assign parents
    known = {r["code"] for r in records}
    for r in records:
        r["parent"] = _find_parent(r["code"], known)

    return records


def validate(records: list[dict]) -> None:
    codes = {r["code"] for r in records}
    assert len(records) >= 10_000, f"Too few records: {len(records)}"
    assert len(codes) == len(records), f"Duplicate codes: {len(records) - len(codes)}"
    target = next((r for r in records if r["code"] == "0101210000"), None)
    assert target is not None, "0101210000 not found"
    assert any(w in target["name_ru"] for w in ("племенные", "чистопородные", "племен")), (
        f"Unexpected name for 0101210000: {target['name_ru']}"
    )

    orphans = [r for r in records if r["parent"] and r["parent"] not in codes and r["level"] > 2]
    if orphans:
        logger.warning(
            "%d codes have missing parents (sample: %s)",
            len(orphans),
            [o["code"] for o in orphans[:5]],
        )
    logger.info("Validation passed. Total codes: %d", len(records))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Parsing %s", PDF_PATH)
    records = parse()
    validate(records)

    OUT_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote %d records to %s", len(records), OUT_PATH)

    sample = next((r for r in records if r["code"] == "0101210000"), records[0])
    print(json.dumps(sample, ensure_ascii=False, indent=2))

    # Level distribution
    from collections import Counter

    dist = Counter(r["level"] for r in records)
    print("Level distribution:", dict(sorted(dist.items())))


if __name__ == "__main__":
    main()

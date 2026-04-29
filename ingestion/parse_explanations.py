"""Parse Poyasneniya/*.pdf → data/build/chunks.json

1 file = 1 chunk. Uses ProcessPoolExecutor + pdftotext subprocess.
Extracts primary_code, related_codes, section, group from text header.
"""

import json
import logging
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from os import cpu_count
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
POYASNENIYA_DIR = DATA_DIR / "Poyasneniya"
OUT_PATH = DATA_DIR / "build" / "chunks.json"

_SECTION_RE = re.compile(r"Раздел\s+([IVXLC]+)\s+Группа\s+(\d+)", re.IGNORECASE)
_SECTION_ONLY_RE = re.compile(r"Раздел\s+([IVXLC]+)", re.IGNORECASE)
_GROUP_RE = re.compile(r"Группа\s+(\d+)", re.IGNORECASE)
# 4-digit primary code (first match in text)
_PRIMARY_RE = re.compile(r"\b(\d{4})\b")
# All 4, 6, or 10-digit codes mentioned
_ALL_CODES_RE = re.compile(r"\b(\d{10}|\d{6}|\d{4})\b")
_MIN_CHARS = 100


def _pdf_text(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["pdftotext", str(path), "-"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None


def _parse_file(path: Path) -> dict | None:
    text = _pdf_text(path)
    if not text or len(text.strip()) < _MIN_CHARS:
        return None

    page_num = int(re.search(r"page_(\d+)", path.stem).group(1))  # type: ignore[union-attr]

    section: str | None = None
    group_code: str | None = None

    # Check header (first 3 lines) for section+group
    header = "\n".join(text.splitlines()[:3])
    sm = _SECTION_RE.search(header)
    if sm:
        section = sm.group(1).upper()
        group_code = sm.group(2).zfill(2)
    else:
        sm2 = _SECTION_ONLY_RE.search(header)
        if sm2:
            section = sm2.group(1).upper()
        gm = _GROUP_RE.search(header)
        if gm:
            group_code = gm.group(1).zfill(2)

    # primary_code: first 4-digit code in text
    pm = _PRIMARY_RE.search(text)
    primary_code = pm.group(1) if pm else None
    if primary_code is None and group_code:
        primary_code = group_code

    related_codes = list(dict.fromkeys(_ALL_CODES_RE.findall(text)))

    return {
        "page_num": page_num,
        "text": text.strip(),
        "primary_code": primary_code,
        "related_codes": related_codes,
        "section": section,
        "group_code": group_code,
    }


def _worker(path_str: str) -> dict | None:
    return _parse_file(Path(path_str))


def parse() -> list[dict]:
    pdfs = sorted(POYASNENIYA_DIR.glob("page_*.pdf"))
    assert pdfs, f"No PDFs found in {POYASNENIYA_DIR}"
    logger.info("Parsing %d PDFs with %d workers", len(pdfs), cpu_count())

    chunks: list[dict] = []
    workers = min(cpu_count() or 4, 8)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_worker, str(p)): p for p in pdfs}
        for done, fut in enumerate(as_completed(futures), start=1):
            result = fut.result()
            if result:
                chunks.append(result)
            if done % 200 == 0:
                logger.info("  %d / %d processed", done, len(pdfs))

    chunks.sort(key=lambda c: c["page_num"])
    return chunks


def validate(chunks: list[dict]) -> None:
    assert 1_900 < len(chunks) < 2_010, f"Unexpected chunk count: {len(chunks)}"
    has_primary = sum(1 for c in chunks if c["primary_code"])
    pct = has_primary / len(chunks) * 100
    assert pct >= 95, f"Only {pct:.1f}% chunks have primary_code"
    logger.info("Validation passed. Chunks: %d, primary_code coverage: %.1f%%", len(chunks), pct)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    chunks = parse()
    validate(chunks)

    OUT_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote %d chunks to %s", len(chunks), OUT_PATH)
    meta = {k: v for k, v in chunks[0].items() if k != "text"}
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"text[:200]: {chunks[0]['text'][:200]!r}")


if __name__ == "__main__":
    main()

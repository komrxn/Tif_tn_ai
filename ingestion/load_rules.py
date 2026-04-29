"""Concatenate Rules_tn_ved/*.pdf → data/build/rules.txt via pdftotext."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
RULES_DIR = DATA_DIR / "Rules_tn_ved"
OUT_PATH = DATA_DIR / "build" / "rules.txt"

_PAGE_SEP = "\n\n---\n\n"


def load() -> str:
    pdfs = sorted(RULES_DIR.glob("page_*.pdf"))
    assert pdfs, f"No PDFs found in {RULES_DIR}"
    logger.info("Found %d rule PDFs", len(pdfs))

    parts: list[str] = []
    for pdf in pdfs:
        result = subprocess.run(
            ["pdftotext", str(pdf), "-"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdftotext failed for {pdf}: {result.stderr}")
        parts.append(result.stdout.strip())

    return _PAGE_SEP.join(parts)


def validate(text: str) -> None:
    assert "ПРАВИЛО 1" in text or "Правило 1" in text, "Rule 1 marker not found"
    assert 5_000 <= len(text) <= 100_000, f"Unexpected rules length: {len(text)}"
    logger.info("Validation passed. Rules text: %d chars", len(text))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    text = load()
    validate(text)

    OUT_PATH.write_text(text, encoding="utf-8")
    logger.info("Wrote rules to %s", OUT_PATH)
    print(text[:400])


if __name__ == "__main__":
    main()

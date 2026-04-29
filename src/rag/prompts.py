"""Assemble per-query context block from retrieval hits + classifier metadata."""

import logging

from src.db.client import get_db
from src.rag.retriever import ChunkHit

logger = logging.getLogger(__name__)

_MAX_CONTEXT_CHARS = 12_000  # ~3000 tokens


async def _fetch_classifier_rows(codes: list[str]) -> dict[str, dict]:
    if not codes:
        return {}
    db = await get_db()
    rows = await db.query(
        "SELECT code, name_ru, parent, level, unit FROM codes WHERE code IN $codes",
        {"codes": codes},
    )
    return {r["code"]: r for r in rows}


def _format_hit(hit: ChunkHit, classifier: dict[str, dict]) -> str:
    parts = []
    if hit.primary_code:
        meta = classifier.get(hit.primary_code)
        if meta:
            parts.append(f"[{hit.primary_code}] {meta.get('name_ru', '')}")
    # Clip text to avoid bloat; keep the first 800 chars of dense explanation pages
    parts.append(hit.text[:800])
    return "\n".join(parts)


async def build_context(hits: list[ChunkHit]) -> str:
    # Collect all codes to look up
    all_codes: list[str] = []
    for h in hits:
        if h.primary_code:
            all_codes.append(h.primary_code)
        all_codes.extend(h.related_codes[:4])
    all_codes = list(dict.fromkeys(all_codes))  # deduplicate, preserve order

    classifier = await _fetch_classifier_rows(all_codes)

    sections: list[str] = []
    total = 0
    for i, hit in enumerate(hits):
        block = _format_hit(hit, classifier)
        if total + len(block) > _MAX_CONTEXT_CHARS:
            logger.debug("Context cap hit after %d/%d chunks", i, len(hits))
            break
        sections.append(block)
        total += len(block)

    return "\n\n---\n\n".join(sections)

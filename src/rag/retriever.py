import logging
from dataclasses import dataclass

from src.ai.embeddings import embed
from src.db.client import get_db

logger = logging.getLogger(__name__)


@dataclass
class ChunkHit:
    page_num: int
    text: str
    primary_code: str | None
    related_codes: list[str]
    score: float
    section: str | None
    group_code: str | None


async def retrieve(query: str, top_k: int = 8) -> list[ChunkHit]:
    vec = await embed(query)
    db = await get_db()

    rows = await db.query(
        f"""
        SELECT id, text, primary_code, related_codes, page_num, section, group_code,
               vector::similarity::cosine(embedding, $q) AS score
        FROM chunks
        WHERE embedding <|{top_k},COSINE|> $q
        ORDER BY score DESC
        """,
        {"q": vec},
    )

    hits = []
    for r in rows:
        hits.append(
            ChunkHit(
                page_num=r.get("page_num", 0),
                text=r.get("text", ""),
                primary_code=r.get("primary_code"),
                related_codes=r.get("related_codes", []),
                score=r.get("score", 0.0),
                section=r.get("section"),
                group_code=r.get("group_code"),
            )
        )

    logger.debug("Retrieved %d chunks for query %r", len(hits), query[:60])
    return hits

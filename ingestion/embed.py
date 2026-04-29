"""Embed chunks.json → chunks_embedded.json using text-embedding-3-large.

Batches 100 texts per request. SHA256-keyed disk cache to skip re-embedding.
"""

import asyncio
import hashlib
import json
import logging
from pathlib import Path

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
CHUNKS_PATH = DATA_DIR / "build" / "chunks.json"
OUT_PATH = DATA_DIR / "build" / "chunks_embedded.json"
CACHE_PATH = DATA_DIR / "build" / "embed_cache.json"

MODEL = "text-embedding-3-large"
DIMENSIONS = 1536
BATCH_SIZE = 100
BATCH_SLEEP_S = 0.1


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


async def embed_all(chunks: list[dict]) -> list[dict]:
    client = AsyncOpenAI(timeout=60.0)

    # Load cache
    cache: dict[str, list[float]] = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        logger.info("Loaded %d cached embeddings", len(cache))

    to_embed = [(i, c) for i, c in enumerate(chunks) if _sha(c["text"]) not in cache]
    logger.info("%d chunks need embedding (cached: %d)", len(to_embed), len(chunks) - len(to_embed))

    total_tokens = 0
    batches = [to_embed[i : i + BATCH_SIZE] for i in range(0, len(to_embed), BATCH_SIZE)]

    for bi, batch in enumerate(batches):
        texts = [c["text"] for _, c in batch]
        resp = await client.embeddings.create(
            model=MODEL,
            input=texts,
            dimensions=DIMENSIONS,
        )
        total_tokens += resp.usage.total_tokens
        for (_, chunk), emb_obj in zip(batch, resp.data, strict=True):
            cache[_sha(chunk["text"])] = emb_obj.embedding

        logger.info("Batch %d/%d done, tokens so far: %d", bi + 1, len(batches), total_tokens)

        # Persist cache every batch so reruns skip done work
        CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")

        if bi < len(batches) - 1:
            await asyncio.sleep(BATCH_SLEEP_S)

    # Attach embeddings to chunks
    result = []
    for chunk in chunks:
        key = _sha(chunk["text"])
        result.append({**chunk, "embedding": cache[key]})

    cost_usd = total_tokens / 1_000_000 * 0.13  # $0.13/M tokens for text-embedding-3-large
    logger.info("Done. Total tokens: %d, estimated cost: $%.4f", total_tokens, cost_usd)
    print(f"tokens_used={total_tokens}  estimated_cost=${cost_usd:.4f}")

    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    logger.info("Loaded %d chunks", len(chunks))

    result = asyncio.run(embed_all(chunks))

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %d embedded chunks to %s", len(result), OUT_PATH)


if __name__ == "__main__":
    main()

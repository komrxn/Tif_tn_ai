"""Phase 2 validation: retriever smoke test + golden set.

Requires SurrealDB running at SURREAL_URL and OPENAI_API_KEY set.
Skip if either is missing.
"""

import asyncio
import os

import pytest

# Skip entire module if no live services
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def db_ready():
    """Verify SurrealDB has data loaded."""
    from src.db.client import get_db

    db = await get_db()
    rows = await db.query("SELECT count() FROM chunks GROUP ALL")
    count = rows[0]["count"] if rows else 0
    if count < 1000:
        pytest.skip(f"SurrealDB chunks count too low: {count}")
    return count


async def test_retriever_returns_hits(db_ready: int):
    assert db_ready > 0
    from src.rag.retriever import retrieve

    hits = await retrieve("свежие яблоки", top_k=5)
    assert len(hits) >= 1
    assert all(h.score > 0.0 for h in hits)
    assert all(h.text for h in hits)


async def test_retriever_primary_code_populated(db_ready: int):
    assert db_ready > 0
    from src.rag.retriever import retrieve

    hits = await retrieve("пшеница твёрдая зерно")
    with_code = [h for h in hits if h.primary_code]
    assert len(with_code) >= 1


async def test_golden_set(db_ready: int):
    assert db_ready > 0
    from src.ai.llm import classify
    from src.rag.prompts import build_context
    from src.rag.retriever import retrieve
    from tests.golden_set import GOLDEN

    passed = 0
    results = []
    for query, expected_prefix in GOLDEN:
        hits = await retrieve(query, top_k=8)
        context = await build_context(hits)
        result = await classify(query, context, "ru")
        ok = result.code is not None and result.code.startswith(expected_prefix)
        if ok:
            passed += 1
        results.append((query, expected_prefix, result.code, ok))

    print(f"\nGolden set: {passed}/{len(GOLDEN)}")
    for q, exp, got, ok in results:
        mark = "✓" if ok else "✗"
        print(f"  {mark} {q!r:40s} expected={exp} got={got}")

    assert passed >= 16, f"Golden set {passed}/{len(GOLDEN)} < 80%"

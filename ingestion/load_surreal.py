"""Load all ingestion artifacts into SurrealDB.

Applies schema, bulk-inserts codes / duties / chunks in batches of 500.
"""

import asyncio
import json
import logging
from pathlib import Path

from surrealdb import AsyncSurreal

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
SCHEMA_PATH = Path(__file__).parent.parent / "src" / "db" / "schema.surql"

BATCH = 500


async def _apply_schema(db: AsyncSurreal) -> None:
    ddl = SCHEMA_PATH.read_text(encoding="utf-8")
    for stmt in ddl.split(";"):
        stmt = stmt.strip()
        if stmt:
            await db.query(stmt)
    logger.info("Schema applied")


async def _bulk_insert(db: AsyncSurreal, table: str, rows: list[dict]) -> None:
    total = len(rows)
    inserted = 0
    for i in range(0, total, BATCH):
        batch = rows[i : i + BATCH]
        await db.query(f"INSERT IGNORE INTO {table} $rows", {"rows": batch})
        inserted += len(batch)
        logger.info("  %s: %d / %d", table, inserted, total)


async def load(surreal_url: str, surreal_user: str, surreal_pass: str) -> None:
    codes = json.loads((DATA_DIR / "build" / "classifier.json").read_text(encoding="utf-8"))
    duties = json.loads((DATA_DIR / "build" / "duties.json").read_text(encoding="utf-8"))
    chunks = json.loads((DATA_DIR / "build" / "chunks_embedded.json").read_text(encoding="utf-8"))

    async with AsyncSurreal(surreal_url) as db:
        await db.signin({"username": surreal_user, "password": surreal_pass})
        await db.use("tnved", "main")

        await _apply_schema(db)

        logger.info("Inserting %d codes...", len(codes))
        await _bulk_insert(db, "codes", codes)

        logger.info("Inserting %d duties...", len(duties))
        await _bulk_insert(db, "duties", duties)

        logger.info("Inserting %d chunks...", len(chunks))
        await _bulk_insert(db, "chunks", chunks)

        # Verify
        counts = {}
        for tbl in ("codes", "duties", "chunks"):
            res = await db.query(f"SELECT count() FROM {tbl} GROUP ALL")
            counts[tbl] = res[0]["count"] if res else 0

        print("\n=== SurrealDB load summary ===")
        for tbl, cnt in counts.items():
            expected = {"codes": len(codes), "duties": len(duties), "chunks": len(chunks)}[tbl]
            status = "✓" if cnt == expected else "✗"
            print(f"  {status} {tbl}: {cnt} / {expected}")


def main() -> None:
    import os

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    url = os.environ.get("SURREAL_URL", "ws://localhost:8000/rpc")
    user = os.environ.get("SURREAL_USER", "root")
    pw = os.environ.get("SURREAL_PASS", "root")

    asyncio.run(load(url, user, pw))


if __name__ == "__main__":
    main()

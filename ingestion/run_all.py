"""Orchestrate full ingestion pipeline: parse → embed → load.

Idempotent: skips steps whose output JSON already exists unless --force.
"""

import argparse
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "build"

STEPS = [
    ("parse_classifier", DATA_DIR / "classifier.json"),
    ("parse_duties", DATA_DIR / "duties.json"),
    ("load_rules", DATA_DIR / "rules.txt"),
    ("parse_explanations", DATA_DIR / "chunks.json"),
    ("embed", DATA_DIR / "chunks_embedded.json"),
    ("load_surreal", None),  # always run
]


def _run_step(module: str) -> float:
    import importlib

    t0 = time.monotonic()
    mod = importlib.import_module(f"ingestion.{module}")
    mod.main()
    return time.monotonic() - t0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force", action="store_true", help="Re-run all steps even if output exists"
    )
    parser.add_argument("--skip-load", action="store_true", help="Skip SurrealDB load step")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    print("\n=== TN VED ingestion pipeline ===\n")
    results = []

    for module, output in STEPS:
        if module == "load_surreal" and args.skip_load:
            print(f"  SKIP  {module} (--skip-load)")
            continue

        if output and output.exists() and not args.force:
            print(f"  SKIP  {module} (output exists: {output.name})")
            results.append((module, "skipped", 0.0))
            continue

        print(f"  RUN   {module} ...")
        try:
            elapsed = _run_step(module)
            print(f"  DONE  {module} ({elapsed:.1f}s)")
            results.append((module, "ok", elapsed))
        except Exception as exc:
            print(f"  FAIL  {module}: {exc}")
            logger.exception("Step %s failed", module)
            raise SystemExit(1) from exc

    print("\n=== Summary ===")
    for mod, status, t in results:
        print(f"  {status:7s}  {mod}  {f'({t:.1f}s)' if t else ''}")


if __name__ == "__main__":
    main()

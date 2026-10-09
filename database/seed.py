"""Seed MongoDB with the 36 fictional DEMO providers (idempotent).

Source of truth: ``backend/app/data/providers.py`` — this script NEVER
invents additional providers. Each record is upserted by its stable id
(``demo-001`` ... ``demo-036``), so running it any number of times cannot
produce duplicates. All records retain ``is_demo = true``.

Usage (from the repository root):
    docker compose up -d mongodb
    backend\\.venv\\Scripts\\python.exe database\\seed.py

Configuration comes from ``MONGODB_URI`` / ``DATABASE_NAME`` (see
``.env.example``). No credentials or connection strings are ever printed.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from pymongo import AsyncMongoClient  # noqa: E402
from pymongo.errors import PyMongoError  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.data.providers import DEMO_PROVIDERS  # noqa: E402

EXPECTED_COUNT = len(DEMO_PROVIDERS)  # 36


async def seed_providers() -> dict[str, int]:
    """Upsert every demo provider into MongoDB.

    Returns counts: inserted / skipped (already current) / updated /
    total (collection size) / found (demo ids present).
    """
    settings = get_settings()
    client = AsyncMongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    try:
        await client.admin.command("ping")
    except PyMongoError as exc:
        raise SystemExit(
            "ERROR: cannot reach MongoDB "
            f"({exc.__class__.__name__}).\n"
            "Start it with:  docker compose up -d mongodb\n"
            "Connection details come from MONGODB_URI in the environment."
        ) from exc

    try:
        providers = client[settings.database_name]["providers"]
        # Same query-supporting indexes the application creates (idempotent).
        await providers.create_index("id", unique=True)
        await providers.create_index("city")
        await providers.create_index("specialization")
        await providers.create_index("consultation_fee")
        await providers.create_index("rating")

        inserted = skipped = updated = 0
        for provider in DEMO_PROVIDERS:
            doc = provider.model_dump()
            result = await providers.replace_one({"id": doc["id"]}, doc, upsert=True)
            if result.upserted_id is not None:
                inserted += 1
            elif result.modified_count:
                updated += 1
            else:
                skipped += 1

        total = await providers.count_documents({})
        found = await providers.count_documents(
            {"id": {"$in": [p.id for p in DEMO_PROVIDERS]}}
        )
        return {
            "inserted": inserted,
            "skipped": skipped,
            "updated": updated,
            "total": total,
            "found": found,
        }
    finally:
        await client.close()


def main() -> None:
    """Seed, verify the final count, and exit non-zero on any failure."""
    stats = asyncio.run(seed_providers())
    print(f"Seed complete (database: {get_settings().database_name}):")
    print(f"  inserted : {stats['inserted']}")
    print(f"  skipped  : {stats['skipped']} (already up to date)")
    print(f"  updated  : {stats['updated']}")
    print(f"  total    : {stats['total']} providers (expected {EXPECTED_COUNT})")
    if stats["total"] != EXPECTED_COUNT or stats["found"] != EXPECTED_COUNT:
        raise SystemExit(
            f"ERROR: verification failed - expected exactly {EXPECTED_COUNT} demo "
            f"providers, found {stats['found']} (collection total {stats['total']})."
        )
    print(f"  verified : all {EXPECTED_COUNT} demo providers present, is_demo=True")


if __name__ == "__main__":
    main()

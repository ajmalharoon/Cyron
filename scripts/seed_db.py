#!/usr/bin/env python3
"""Inserts a handful of example targets so a fresh database isn't empty
when you first open the UI. Safe to run more than once — targets are
upserted on their unique `value` column.

Usage (from the backend/ directory, with its venv active):
    DATABASE_URL=postgresql+asyncpg://cyron:cyron@localhost:5432/cyron \
        python ../scripts/seed_db.py
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.target import Target  # noqa: E402

EXAMPLE_TARGETS = [
    ("example.com", "domain"),
    ("example.net", "domain"),
]


async def main() -> None:
    async with SessionLocal() as session:
        for value, ttype in EXAMPLE_TARGETS:
            existing = (await session.execute(select(Target).where(Target.value == value))).scalar_one_or_none()
            if existing:
                print(f"skip  {value} (already present)")
                continue
            session.add(Target(id=uuid.uuid4(), value=value, type=ttype))
            print(f"added {value}")
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())

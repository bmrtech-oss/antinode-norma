import os

import pytest

from antinode_norma.database import migrate, upsert_seed_records


DATABASE_URL = os.getenv("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith(("postgresql://", "postgres://")),
    reason="Set DATABASE_URL to a test PostgreSQL instance to run this integration test",
)


def test_postgres_migration_and_seed_upsert():
    migrate(DATABASE_URL)
    records = iter([("test", "postgres-1", {"value": "first"})])
    assert upsert_seed_records(records, DATABASE_URL) == 1
    assert upsert_seed_records(iter([("test", "postgres-1", {"value": "updated"})]), DATABASE_URL) == 1

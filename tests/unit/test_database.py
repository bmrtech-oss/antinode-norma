import sqlite3

from antinode_norma.database import migrate, seed_database
from antinode_norma.local_seed import seed_local


def test_sqlite_migration_and_idempotent_seed(tmp_path):
    seed_root = tmp_path / "seed"
    database_url = f"sqlite:///{tmp_path / 'norma.db'}"
    seed_local(seed_root, reset=True)

    migrate(database_url)
    first = seed_database(seed_root, database_url)
    second = seed_database(seed_root, database_url)

    assert first == 7
    assert second == 7
    connection = sqlite3.connect(tmp_path / "norma.db")
    try:
        count = connection.execute("SELECT COUNT(*) FROM norma_seed_records").fetchone()[0]
    finally:
        connection.close()
    assert count == 7

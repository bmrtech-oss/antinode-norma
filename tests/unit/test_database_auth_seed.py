import sqlite3

from antinode_norma.local_seed import seed_local


def test_database_auth_users_and_roles_are_seeded(tmp_path):
    root = tmp_path / "seed"
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    seed_local(root, reset=True, database_url=database_url)

    connection = sqlite3.connect(tmp_path / "app.db")
    try:
        users = connection.execute("SELECT username FROM users ORDER BY username").fetchall()
        roles = connection.execute("SELECT role FROM user_roles ORDER BY role").fetchall()
        tenants = connection.execute("SELECT id FROM tenants").fetchall()
    finally:
        connection.close()

    assert [row[0] for row in users] == ["admin", "generator", "reviewer", "viewer"]
    assert [row[0] for row in roles] == ["admin", "generator", "reviewer", "viewer"]
    assert tenants == [("seed-tenant",)]

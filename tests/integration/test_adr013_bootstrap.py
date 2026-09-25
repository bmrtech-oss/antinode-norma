import json
from pathlib import Path

import yaml

from antinode_norma.local_seed import seed_local


def test_adr013_seed_and_compose_contract(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seed_root = tmp_path / ".runtime" / "local-seed"

    first = seed_local(seed_root, reset=True)
    second = seed_local(seed_root, reset=False)

    assert first == second
    assert json.loads((seed_root / "users.json").read_text(encoding="utf-8"))[0]["id"] == "seed-admin"
    assert len(list((seed_root / "features").glob("*.feature"))) == 3

    repo_root = Path(__file__).resolve().parents[2]
    compose = yaml.safe_load(
        (repo_root / "docker-compose.yml").read_text(encoding="utf-8")
    )
    services = compose["services"]
    assert {"db", "local-seed", "app-http", "app-mcp"} <= services.keys()
    assert services["db"]["healthcheck"]["test"]
    assert any(item.startswith("DATABASE_URL=") for item in services["app-http"]["environment"])
    assert "NORMA_RUNTIME_MODE=mcp" in services["app-mcp"]["environment"]
    assert ".:/app:Z" in services["app-http"]["volumes"]
    assert ".:/app:Z" in services["app-mcp"]["volumes"]
    assert services["app-http"]["depends_on"]["local-seed"]["condition"] == "service_completed_successfully"

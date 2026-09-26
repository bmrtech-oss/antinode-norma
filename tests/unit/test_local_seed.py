import json
import yaml

from antinode_norma.local_seed import seed_local


def test_local_seed_is_idempotent_and_reset_scoped(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / ".runtime" / "local-seed"

    first = seed_local(root=root, reset=True)
    second = seed_local(root=root, reset=False)

    assert first == second
    assert json.loads((root / "users.json").read_text())
    assert len(json.loads((root / "users.json").read_text())) == 4
    assert len(json.loads((root / "approvals.json").read_text())) == 3
    assert len(list((root / "features").glob("*.feature"))) == 3
    assert (root / "traceability.json").exists()
    assert (root / "audit.json").exists()
    assert (root / "analytics.json").exists()
    assert (root / "execution_history.json").exists()
    assert (root / "plugins.json").exists()
    assert (root / "notifications.json").exists()
    assert json.loads((tmp_path / ".runtime/local-seed-complete.json").read_text()) == first


def test_seed_manifest_and_config_example_are_safe_and_complete():
    manifest = yaml.safe_load(open("examples/seed/manifest.yml", encoding="utf-8"))
    config = open("norma.config.example.yml", encoding="utf-8").read()

    assert manifest["expected_counts"] == {"users": 4, "approvals": 3, "features": 3}
    assert manifest["provider"] == "mock"
    assert "OPENAI_API_KEY" not in config
    assert "llm_provider: mock" in config
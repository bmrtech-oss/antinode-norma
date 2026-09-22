import io

from fastapi.testclient import TestClient

from antinode_norma.server.api import app


def test_generation_workflow_requires_authentication(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    response = client.post(
        "/v1/imports",
        files={"file": ("cases.csv", io.BytesIO(b"ID,Summary,Action\nTC-1,Login,log in\n"), "text/csv")},
    )
    assert response.status_code == 401


def test_generation_resources_are_isolated_by_owner(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    owner = {"X-User-ID": "admin-owner", "X-Tenant-ID": "tenant-a"}
    other = {"X-User-ID": "other", "X-Tenant-ID": "tenant-a"}
    imported = client.post(
        "/v1/imports",
        headers=owner,
        files={"file": ("cases.csv", io.BytesIO(b"ID,Summary,Action\nTC-1,Login,log in\n"), "text/csv")},
    ).json()
    import_id = imported["id"]
    assert client.get(f"/v1/imports/{import_id}", headers=other).status_code == 404
    job = client.post("/v1/generation-jobs", headers=owner, json={"import_id": import_id})
    assert job.status_code == 201
    job_id = job.json()["id"]
    assert client.get(f"/v1/generation-jobs/{job_id}", headers=other).status_code == 404
    assert client.get(f"/v1/generation-jobs/{job_id}/events", headers=other).status_code == 404
    assert client.get(f"/v1/generation-jobs/{job_id}/download", headers=other).status_code == 404

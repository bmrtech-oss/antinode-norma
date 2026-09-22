import io
import time
from openpyxl import Workbook

from fastapi.testclient import TestClient

from antinode_norma.server.api import app


def test_csv_import_preview_validate_and_generation(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    payload = b"ID,Summary,Action,So that\nTC-1,Login,log in,access app\n"

    response = client.post(
        "/v1/api/imports/upload",
        files={"file": ("cases.csv", io.BytesIO(payload), "text/csv")},
    )
    assert response.status_code == 201
    imported = response.json()
    assert imported["row_count"] == 1

    preview = client.get(f"/v1/api/imports/{imported['id']}/preview")
    assert preview.status_code == 200
    assert preview.json()["rows"][0]["id"] == "TC-1"

    validation = client.post(f"/v1/api/imports/{imported['id']}/validate")
    assert validation.status_code == 200
    assert validation.json()["valid"] is True

    job = client.post("/v1/api/generation/jobs", json={"import_id": imported["id"]})
    assert job.status_code == 201
    assert job.json()["status"] == "completed"
    assert client.get(f"/v1/api/generation/jobs/{job.json()['id']}").status_code == 200


def test_public_phase_one_contract_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    response = client.post(
        "/v1/imports",
        files={"file": ("cases.csv", io.BytesIO(b"ID,Summary,Action\nTC-1,Login,log in\n"), "text/csv")},
    )
    assert response.status_code == 201
    import_id = response.json()["id"]
    assert client.get(f"/v1/imports/{import_id}").status_code == 200
    assert client.get(f"/v1/imports/{import_id}/preview").status_code == 200
    job = client.post("/v1/generation-jobs", json={"import_id": import_id})
    assert job.status_code == 201


def test_import_rejects_unsupported_files(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    response = TestClient(app).post(
        "/v1/api/imports/upload",
        files={"file": ("cases.txt", io.BytesIO(b"not supported"), "text/plain")},
    )
    assert response.status_code == 415


def test_xlsx_preview_exposes_worksheets_and_mapping_drives_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Requirements"
    sheet.append(["Case Key", "Summary Text", "User Action"])
    sheet.append(["REQ-1", "Sign in", "authenticate"])
    notes = workbook.create_sheet("Notes")
    notes.append(["Ignore"])
    path = tmp_path / "requirements.xlsx"
    workbook.save(path)

    client = TestClient(app)
    response = client.post(
        "/v1/imports",
        files={"file": ("requirements.xlsx", path.read_bytes(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 201
    imported = response.json()
    assert imported["worksheet_names"] == ["Requirements", "Notes"]
    import_id = imported["id"]

    preview = client.get(f"/v1/imports/{import_id}/preview").json()
    assert preview["columns"] == ["Case Key", "Summary Text", "User Action"]
    assert preview["rows"][0]["values"]["Case Key"] == "REQ-1"

    mapped = client.post(f"/v1/imports/{import_id}/mapping", json={
        "worksheet": "Requirements",
        "columns": {"id": "Case Key", "title": "Summary Text", "action": "User Action"},
    })
    assert mapped.status_code == 200
    assert mapped.json()["mapping"]["id"] == "Case Key"
    validation = client.post(f"/v1/imports/{import_id}/validate").json()
    assert validation["valid"] is True
    job = client.post("/v1/generation-jobs", json={"import_id": import_id})
    assert job.status_code == 201
    for _ in range(100):
        if client.get(f"/v1/generation-jobs/{job.json()['id']}").json()["status"] == "completed":
            break
        time.sleep(0.01)
    results = client.get(f"/v1/generation-jobs/{job.json()['id']}/results").json()["results"]
    assert "Feature: Sign in" in results[0]["content"]


def test_mapping_rejects_unknown_columns(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    imported = client.post(
        "/v1/imports",
        files={"file": ("cases.csv", io.BytesIO(b"Key,Action\nTC-1,run\n"), "text/csv")},
    ).json()
    response = client.post(f"/v1/imports/{imported['id']}/mapping", json={
        "columns": {"id": "Missing"},
    })
    assert response.status_code == 422


def test_generation_sanitizes_artifact_names_and_supports_download(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("NORMA_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    client = TestClient(app)
    imported = client.post(
        "/v1/imports",
        files={"file": ("cases.csv", io.BytesIO(b"ID,Summary,Action\n../escape,Login,log in\n"), "text/csv")},
    ).json()
    job = client.post("/v1/generation-jobs", json={"import_id": imported["id"]}).json()

    for _ in range(100):
        if client.get(f"/v1/generation-jobs/{job['id']}").json()["status"] == "completed":
            break
        time.sleep(0.01)

    result = client.get(f"/v1/generation-jobs/{job['id']}/results").json()["results"][0]
    assert result["artifact_name"] == "escape.feature"
    assert "/" not in result["artifact_name"]
    assert "\\" not in result["artifact_name"]
    assert client.get(f"/v1/generation-jobs/{job['id']}/download").status_code == 200

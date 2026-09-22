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
    artifact = client.get(
        f"/v1/generation-jobs/{job['id']}/results/{result['id']}/download"
    )
    assert artifact.status_code == 200
    assert "Feature: Login" in artifact.text


def test_generation_job_history_supports_status_filter_and_pagination(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    imported = client.post(
        "/v1/imports",
        files={"file": ("history.csv", io.BytesIO(b"ID,Summary,Action\nTC-1,Login,log in\n"), "text/csv")},
    ).json()
    job = client.post("/v1/generation-jobs", json={"import_id": imported["id"]}).json()
    for _ in range(100):
        if client.get(f"/v1/generation-jobs/{job['id']}").json()["status"] == "completed":
            break
        time.sleep(0.01)

    response = client.get("/v1/generation-jobs?status=completed&offset=0&limit=1")
    assert response.status_code == 200
    history = response.json()
    assert history["total"] == 1
    assert len(history["items"]) == 1
    assert history["items"][0]["id"] == job["id"]
    assert history["items"][0]["source_filename"] == "history.csv"


def test_successful_generation_result_can_be_submitted_for_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    imported = client.post(
        "/v1/imports",
        files={"file": ("approval.csv", io.BytesIO(b"ID,Summary,Action\nTC-1,Login,log in\n"), "text/csv")},
    ).json()
    job = client.post("/v1/generation-jobs", json={"import_id": imported["id"]}).json()
    for _ in range(100):
        if client.get(f"/v1/generation-jobs/{job['id']}").json()["status"] == "completed":
            break
        time.sleep(0.01)

    result = client.get(f"/v1/generation-jobs/{job['id']}/results").json()["results"][0]
    response = client.post(
        f"/v1/generation-jobs/{job['id']}/results/{result['id']}/submit-approval"
    )
    assert response.status_code == 200
    assert response.json()["feature_id"] == "TC-1"
    assert response.json()["status"] == "PENDING"
    assert response.json()["source_job_id"] == job["id"]
    assert response.json()["source_result_id"] == result["id"]


def test_failed_generation_result_cannot_be_submitted_for_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    imported = client.post(
        "/v1/imports",
        files={"file": ("approval.csv", io.BytesIO(b"ID,Summary,Action\nTC-1,,\n"), "text/csv")},
    ).json()
    job = client.post("/v1/generation-jobs", json={"import_id": imported["id"]}).json()
    result = client.get(f"/v1/generation-jobs/{job['id']}/results").json()["results"][0]
    response = client.post(
        f"/v1/generation-jobs/{job['id']}/results/{result['id']}/submit-approval"
    )
    assert response.status_code == 409


def test_submitted_generation_result_appears_in_feature_review_with_traceability(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    imported = client.post(
        "/v1/imports",
        files={"file": ("review.csv", io.BytesIO(b"ID,Summary,Action\nTC-9,Review me,review the result\n"), "text/csv")},
    ).json()
    job = client.post("/v1/generation-jobs", json={"import_id": imported["id"]}).json()
    for _ in range(100):
        if client.get(f"/v1/generation-jobs/{job['id']}").json()["status"] == "completed":
            break
        time.sleep(0.01)
    result = client.get(f"/v1/generation-jobs/{job['id']}/results").json()["results"][0]
    client.post(f"/v1/generation-jobs/{job['id']}/results/{result['id']}/submit-approval")

    response = client.get("/api/features", headers={"X-User-ID": "feature-reviewer"})
    assert response.status_code == 200
    generated = next(item for item in response.json() if item["source_result_id"] == result["id"])
    assert generated["id"] == "TC-9"
    assert generated["status"] == "PENDING"
    assert generated["approval_id"]
    assert "Feature: Review me" in generated["gherkin"]

    approved = client.post(
        f"/api/approvals/{generated['approval_id']}/approve",
        json={"reviewer": "qa-reviewer", "reason": "Reviewed"},
        headers={"X-User-ID": "admin_user"},
    )
    assert approved.status_code == 200
    refreshed = client.get("/api/features", headers={"X-User-ID": "feature-reviewer"}).json()
    updated = next(item for item in refreshed if item["source_result_id"] == result["id"])
    assert updated["status"] == "APPROVED"


def test_selected_generation_results_can_be_submitted_in_bulk(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    imported = client.post(
        "/v1/imports",
        files={"file": ("bulk.csv", io.BytesIO(
            b"ID,Summary,Action\nTC-1,Login,log in\nTC-2,Logout,log out\n"
        ), "text/csv")},
    ).json()
    job = client.post("/v1/generation-jobs", json={"import_id": imported["id"]}).json()
    for _ in range(100):
        if client.get(f"/v1/generation-jobs/{job['id']}").json()["status"] == "completed":
            break
        time.sleep(0.01)
    results = client.get(f"/v1/generation-jobs/{job['id']}/results").json()["results"]
    response = client.post(
        f"/v1/generation-jobs/{job['id']}/results/submit-approval",
        json={"result_ids": [item["id"] for item in results]},
    )
    assert response.status_code == 200
    assert len(response.json()["submitted"]) == 2
    refreshed = client.get(f"/v1/generation-jobs/{job['id']}/results").json()["results"]
    assert {item["approval_status"] for item in refreshed} == {"PENDING"}

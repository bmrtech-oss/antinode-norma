from antinode_norma.server.api import app


def test_versioned_api_contract_exposes_canonical_paths_and_methods() -> None:
    paths = app.openapi()["paths"]

    assert "/health" in paths
    assert set(paths["/health"]) == {"get"}
    assert set(paths["/v1/imports"]) == {"post"}
    assert set(paths["/v1/imports/{import_id}/validate"]) == {"post"}
    assert set(paths["/v1/generation-jobs"]) == {"get", "post"}
    assert set(paths["/v1/generation-jobs/{job_id}"]) == {"get"}


def test_versioned_api_contract_references_typed_response_models() -> None:
    paths = app.openapi()["paths"]

    assert paths["/health"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }
    assert paths["/v1/imports"]["post"]["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ImportResponse"
    }
    assert paths["/v1/imports/{import_id}/validate"]["post"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ] == {"$ref": "#/components/schemas/ImportValidationResponse"}
    assert paths["/v1/generation-jobs"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/GenerationJobListResponse"
    }
    assert paths["/v1/generation-jobs"]["post"]["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/GenerationJobResponse"
    }


def test_legacy_api_aliases_remain_compatible_with_canonical_operations() -> None:
    paths = app.openapi()["paths"]

    assert set(paths["/v1/api/imports"]) == set(paths["/v1/imports"])
    assert set(paths["/v1/api/generation-jobs"]) == set(paths["/v1/generation-jobs"])

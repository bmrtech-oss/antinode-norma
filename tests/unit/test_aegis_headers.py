from antinode_aegis.headers import normalize_headers, normalize_row


def test_normalize_headers_maps_common_aliases() -> None:
    assert normalize_headers([" Case_ID ", "Scenario Title", "As_a", "so-that"]) == {
        " Case_ID ": "id",
        "Scenario Title": "scenario_title",
        "As_a": "role",
        "so-that": "benefit",
    }


def test_normalize_row_preserves_values_and_normalizes_unknown_fields() -> None:
    row = normalize_row(
        {
            "Acceptance Criteria": "The report downloads",
            "Release-Version": "1.2",
            "Tags": "smoke|export",
        }
    )

    assert row == {
        "acceptance_criteria": "The report downloads",
        "release_version": "1.2",
        "tags": "smoke|export",
    }

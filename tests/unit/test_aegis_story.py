import pytest

from antinode_aegis.story import ingest_stories


def test_ingest_stories_supports_single_and_list_inputs() -> None:
    story = {
        "story_id": "JIRA-123",
        "role": "admin",
        "action": "manage users",
        "benefit": "control access",
        "acceptance_criteria": ["Can view list", "Can disable user"],
        "tags": ["admin"],
    }

    single = ingest_stories(story, source_reference="jira")
    multiple = ingest_stories([story, {"id": "JIRA-124", "action": "audit users"}], source_reference="jira")

    assert single[0].requirement_id == "JIRA-123"
    assert single[0].acceptance_criteria == ["Can view list", "Can disable user"]
    assert single[0].provenance.source_reference == "jira"
    assert [item.requirement_id for item in multiple] == ["JIRA-123", "JIRA-124"]
    assert multiple[1].provenance.source_reference == "jira#2"


def test_ingest_stories_rejects_invalid_sources() -> None:
    with pytest.raises(ValueError, match="Invalid story source type"):
        ingest_stories("not a story")

    with pytest.raises(ValueError, match="only mapping"):
        ingest_stories([{"id": "valid"}, "invalid"])  # type: ignore[list-item]

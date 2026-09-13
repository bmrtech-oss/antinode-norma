from antinode_norma.core.normalize import normalize_header, split_multi


def test_normalize_header_aliases():
    assert normalize_header("Case ID") == "id"
    assert normalize_header("Summary") == "title"
    assert normalize_header("As a") == "role"
    assert normalize_header("I want to") == "action"
    assert normalize_header("So that") == "benefit"
    assert normalize_header("Acceptance Criteria") == "acceptance_criteria"
    assert normalize_header("Labels") == "tags"


def test_normalize_header_unknown():
    assert normalize_header("Custom Field Name") == "custom_field_name"


def test_split_multi_string_delimiters():
    raw = "First criteria; Second criteria| Third criteria\nFourth criteria"
    res = split_multi(raw)
    assert len(res) == 4
    assert res == [
        "First criteria",
        "Second criteria",
        "Third criteria",
        "Fourth criteria",
    ]


def test_split_multi_bullet_lists():
    raw = "- Link sent to email\n- User sets new password\n* Error shown on invalid token"
    res = split_multi(raw)
    assert res == [
        "Link sent to email",
        "User sets new password",
        "Error shown on invalid token",
    ]


def test_split_multi_list_input():
    raw_list = ["Step 1; Step 2", "- Step 3"]
    res = split_multi(raw_list)
    assert res == ["Step 1", "Step 2", "Step 3"]

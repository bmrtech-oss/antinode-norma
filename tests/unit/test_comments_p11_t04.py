"""Unit tests for Phase 11 Task P11-T04: Comments and Mentions."""

from fastapi.testclient import TestClient

from antinode_norma.collaboration import CommentStore, extract_mentions
from antinode_norma.server.api import app


def test_extract_mentions():
    text = "Great feature! CC @qa_lead and @dev_user for review."
    mentions = extract_mentions(text)
    assert set(mentions) == {"qa_lead", "dev_user"}


def test_comment_store():
    store = CommentStore()
    c1 = store.add_comment(
        feature_id="feat-100",
        author_id="user-1",
        text="Please review @qa_lead",
    )

    assert c1.feature_id == "feat-100"
    assert c1.author_id == "user-1"
    assert c1.mentions == ["qa_lead"]

    comments = store.get_comments("feat-100")
    assert len(comments) == 1
    assert comments[0].id == c1.id


def test_comments_api_endpoints():
    client = TestClient(app, headers={"X-User-ID": "test_user"})

    # Post comment
    res_post = client.post(
        "/api/comments",
        json={
            "feature_id": "feat-200",
            "text": "Looks good! @lead_dev",
        },
    )
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["feature_id"] == "feat-200"
    assert "lead_dev" in data["mentions"]

    # List comments for feature
    res_get = client.get("/api/comments?feature_id=feat-200")
    assert res_get.status_code == 200
    items = res_get.json()
    assert len(items) >= 1
    assert any(i["id"] == data["id"] for i in items)

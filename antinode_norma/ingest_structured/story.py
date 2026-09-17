from typing import Dict, Any
from antinode_norma.core.types import TestCase
from antinode_norma.core.normalize import split_multi


def story_to_case(story: Dict[str, Any]) -> TestCase:
    """Convert raw or parsed story dict into a TestCase instance."""
    case_id = str(story.get("story_id") or story.get("id") or "STORY-001").strip()
    action = str(story.get("action") or "").strip()
    title = str(story.get("title") or (f"Story: {action}" if action else "User Story")).strip()
    role = str(story.get("role") or "user").strip()
    benefit = str(story.get("benefit") or "").strip()

    raw_criteria = story.get("acceptance_criteria") or story.get("criteria")
    acceptance_criteria = split_multi(raw_criteria)

    raw_tags = story.get("tags") or story.get("labels")
    tags = split_multi(raw_tags)

    metadata = {
        k: v
        for k, v in story.items()
        if k not in {"id", "story_id", "title", "role", "action", "benefit", "acceptance_criteria", "criteria", "tags", "labels"}
    }

    return TestCase(
        id=case_id,
        title=title,
        role=role,
        action=action,
        benefit=benefit,
        acceptance_criteria=acceptance_criteria,
        tags=tags,
        metadata=metadata,
    )

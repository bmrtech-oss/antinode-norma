"""Aegis story-dictionary ingestion adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from antinode_aegis.contracts import RequirementIR
from antinode_norma.ingest_structured.story import story_to_case


def ingest_stories(
    source: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    source_reference: str | None = None,
    release_profile: str = "aegis-foundation",
) -> list[RequirementIR]:
    """Convert one or more story dictionaries into versioned Aegis IR."""

    if isinstance(source, Mapping):
        stories = [source]
    elif isinstance(source, Sequence) and not isinstance(source, (str, bytes)):
        if not all(isinstance(story, Mapping) for story in source):
            raise ValueError("Story lists must contain only mapping values")
        stories = list(source)
    else:
        raise ValueError(f"Invalid story source type: {type(source)}")

    requirements: list[RequirementIR] = []
    for index, story in enumerate(stories, 1):
        reference = source_reference
        if reference is not None and len(stories) > 1:
            reference = f"{reference}#{index}"
        requirements.append(
            RequirementIR.from_test_case(
                story_to_case(dict(story)),
                source_kind="story",
                source_reference=reference,
                release_profile=release_profile,
            )
        )
    return requirements

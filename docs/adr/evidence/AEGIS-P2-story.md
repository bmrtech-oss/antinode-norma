# AEGIS-P2 Story Adapter Evidence

- **Requirement:** `AEGIS-P2-STORY`
- **Release profile:** `aegis-foundation`
- **Task:** `P2-T03`
- **Verified:** 2026-09-23
- **Implementation:** `antinode_aegis/story.py`

## Commands

```text
python -m pytest tests/unit/test_aegis_story.py tests/unit/test_ingest.py --no-cov -q
```

## Result

- Single and list story inputs produce versioned Aegis `RequirementIR` values.
- Story IDs, acceptance criteria, tags, and source references are preserved.
- Invalid story source types and mixed non-mapping lists fail explicitly.

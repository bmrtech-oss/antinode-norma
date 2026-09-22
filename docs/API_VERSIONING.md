# API Versioning

This document describes the current API versioning model used by the project and how it aligns with the implementation in `antinode_norma/server/api.py`.

## Current implementation

The server defines a versioned router with a canonical `/v1` prefix and also mounts legacy unversioned aliases for compatibility:

```python
v1_router = APIRouter(prefix="/v1")
...
# Mount /v1/ versioned router and legacy unversioned aliases
app.include_router(v1_router)
app.include_router(features_router)
app.include_router(approvals_router)
...
```

This means the repo currently follows a hybrid approach:

- `/v1` is the canonical versioned surface area.
- Unversioned routes remain available as compatibility shims during transition.
- New functionality should be introduced under `/v1` and existing behavior should not silently change without a clear compatibility policy.

## Versioning policy

1. Canonical route namespace
   - New routes should be added under `/v1`.
   - Route consumers should prefer `/v1/...` when interacting with the API.

2. Backward compatibility
   - Breaking changes must be introduced through a new route version (for example `/v2/...`), not by mutating the semantics of an existing `/v1` route in place.
   - Legacy unversioned aliases should only remain as temporary compatibility layers while migration is underway.

3. Deprecation process
   - When a legacy route is scheduled for removal, document the replacement in release notes and migration guidance.
   - Add a deprecation timeline for clients before the route is removed.
   - Prefer explicit version-by-contract discussions over quietly changing semantics.

4. Documentation and validation
   - API changes should be reflected in the server docs and any client examples.
   - Tests should verify route prefixes and compatibility expectations for versioned endpoints.

## Notes for this repository

The implementation is intentionally conservative: it supports a v1 namespace while retaining compatibility aliases rather than enforcing a strict cut-over policy in code. This is a pragmatic transition model that keeps existing clients working while making the canonical version explicit.

If the project later adopts stricter deprecation headers or a formal sunset policy, the server and client docs should be updated together to reflect the enforcement mechanism.

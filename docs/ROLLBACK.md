# Feature Flags & Rollback Procedures — Antinode Norma

This document outlines the feature flag resolution mechanism, feature flag lifecycle, and zero-downtime rollback procedures.

---

## 1. Feature Flag Resolution Priority

Feature flag settings are resolved in the following priority order (highest to lowest):
1. **CLI Flag Overrides** (e.g. `--enable-unified-agent`)
2. **Environment Variables** (`NORMA_FEATURE_<NAME>=true|false`)
3. **Configuration File** (`norma.config.yml`)
4. **Platform Defaults** (`antinode_norma/core/features.py`)

---

## 2. Feature Flag Lifecycle

All high-risk features follow a 4-stage rollout lifecycle:
1. **Introduce**: Code merged behind feature flag (default: `false`).
2. **Soak**: Enabled in non-production environments for 5 days of validation.
3. **Default-On**: Flag default changed to `true` in config after successful soak.
4. **Retire**: Feature flag removed after 2 stable minor releases.

---

## 3. Rollback Procedures

- **Flag Instant Rollback**: Set `NORMA_FEATURE_<NAME>=false` in environment or `norma.config.yml` to instantly disable problematic capabilities without code redeployment.
- **Git Revert**: High-risk tasks are encapsulated in atomic commits/PRs allowing safe revert via `git revert <commit-sha>`.

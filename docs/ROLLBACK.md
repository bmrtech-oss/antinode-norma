# Rollback Strategy & Feature Flags (ADR-001 §5.4)

This document specifies the feature flag architecture, flag resolution order, flag lifecycle management, soak testing guidelines, and rollback mechanisms for Antinode Norma.

---

## 1. Feature Flags Overview

All high-risk features and architectural changes are gated behind feature flags configured in `norma.config.yml` or runtime environments.

### Core Feature Flags (ADR-001 §5.4)

```yaml
features:
  unified_agent: false
  cache_exact: false
  cache_semantic: false
  governance_audit: false
  governance_approval: false
  auth_saml: false
  execution_cloud: false
  edge_discovery: false
```

---

## 2. Resolution Hierarchy

Feature flag status is resolved dynamically in the following order of precedence (highest to lowest):

1. **CLI / Function Argument Override** (`cli_override=True/False`)
2. **Runtime Overrides** (`FeatureFlagResolver(runtime_overrides={...})`)
3. **Environment Variables** (`NORMA_FEATURE_<FLAG_NAME>=true|false`)
4. **Configuration File** (`norma.config.yml` under `features:`)
5. **System Defaults** (`DEFAULT_FEATURE_FLAGS` in `antinode_norma/core/features.py`)

---

## 3. Feature Flag Lifecycle

Every gated feature follows a strict 4-stage lifecycle before permanent integration:

1. **Introduce**: Feature code lands in `norma-bdd` disabled by default (`default: false`).
2. **Soak**: Feature is enabled in non-production / staging environments for at least **5 business days** without critical defects.
3. **Default-On**: Flag default is switched to `true` in `DEFAULT_FEATURE_FLAGS` after successful soak validation.
4. **Retire**: Flag checks and conditional branches are cleaned up and removed after **2 full releases**.

---

## 4. Rollback & Revert Procedures

### Instant Feature Flag Rollback
If a newly enabled feature introduces regression in production:
- Instantly set the environment variable `NORMA_FEATURE_<NAME>=false` or set `features.<name>: false` in `norma.config.yml`.
- No code rebuild or deployment is required for flag toggles.

### Code Revert Protocol
If a task PR causes an unresolvable issue or security defect:
- Every high-risk task PR is designed to be atomic and cleanly revertible via:
  ```bash
  git revert <commit-sha> -m 1
  ```
- Open escalation issue per `docs/ESCALATION.md` and attach logs.

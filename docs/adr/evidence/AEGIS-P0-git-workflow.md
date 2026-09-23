# AEGIS-P0 Git Workflow Evidence

- **Requirement:** `AEGIS-P0-GIT-WORKFLOW`
- **Release profile:** `aegis-foundation`
- **Phase:** P0
- **Task:** `P0-T03`
- **Verified:** 2026-09-23
- **Implementation:** `docs/GIT_WORKFLOW.md`

## Commands

```text
python -m pytest tests/unit/test_aegis_p0_git_workflow.py --no-cov -q
```

## Result

- Branch naming, integration-branch targeting, squash-merge, and branch
  protection expectations are documented.
- Conventional commit types and ADR task metadata trailers are documented.
- Pull-request review, CI, secret scanning, and cost-gate requirements are
  documented.
- The policy is checked against the repository's current CI triggers and
  Gitleaks step.
- P0-T03 documents policy; repository branch protection remains an environment
  configuration that must be verified before release approval.

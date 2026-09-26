# Git Workflow & Commit Conventions — Antinode Norma

This document describes the branching model, commit conventions, pull request requirements, and release tagging for Antinode Norma.

---

## 1. Branching Strategy

```text
main                    ← Stable, tagged releases (e.g. v2.0.0)
  └── norma-bdd         ← Long-lived integration branch
        ├── task/P0-T01-secrets-strategy
        ├── task/P4-T03-repair-loop
        └── task/P12-T02-docs-consolidation
```

- **Integration Branch**: `norma-bdd` serves as the primary convergence branch for parallel track development.
- **Task Branches**: Created per task using naming convention: `task/<PHASE>-<TASK-ID>-<slug>`.
- **Target & Merge**: Task branches target `norma-bdd` and are squash-merged upon passing required CI checks and reviewer approval.
- **Repository configuration**: Branch protection and required checks must be
  configured on the selected integration branch before this policy is treated
  as enforced. The current CI workflow also validates `main` and `develop`;
  those triggers do not replace branch protection.

---

## 2. Commit Message Convention

Commits follow the Conventional Commits format with ADR task metadata trailers:

```text
<type>(<scope>): <subject>

[optional body]

Task: P12-T02
Phase: P12
Track: Docs
```

### Supported Types
- `feat`: New feature or capability
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or refactoring test cases
- `refactor`: Code changes without functional alteration
- `chore`: Maintenance or build tooling updates

---

## 3. Pull Request & CI Gate Requirements

Every PR to `norma-bdd` must pass all required automated CI checks:
1. `ruff check . --select F401` (Zero lint errors)
2. Unit & Integration test suite (`pytest -m "not integration"`)
3. `gitleaks` secret detection scan
4. Cost Gate check (`cost_per_run <= $0.02`)

The task author must include the phase/task identifier in the PR description and
link the relevant ADR evidence artifact. Reviewers must confirm that the target
branch, required checks, and approval requirements match the repository settings.

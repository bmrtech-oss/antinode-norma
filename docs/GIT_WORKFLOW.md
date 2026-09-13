# Git Workflow & Development Strategy (ADR-001 §5.3)

This document outlines the branching strategy, commit conventions, pull request requirements, release tagging policy, and merge controls for the Antinode Norma platform.

---

## 1. Branch Hierarchy & Naming

```text
main                    ← Stable, tagged releases (vX.Y.Z)
  └── norma-bdd         ← Long-lived integration branch
        ├── task/P0-T01-secrets-strategy
        ├── task/P0-T03-git-workflow
        └── task/P4-T03-repair-loop
```

- **`main`**: Production branch containing stable releases. Direct pushes forbidden. Annotated release tags applied here only.
- **`norma-bdd`**: Long-lived parallel integration branch where feature/task branches target PRs.
- **Task Branches**: Short-lived branches created from `norma-bdd`.
  - Format: `task/<PHASE>-<TASK-ID>-<slug>` (e.g., `task/P0-T03-git-workflow`).

---

## 2. Commit Message Conventions

Commits follow Conventional Commits enriched with mandatory task trailers:

```text
<type>(<scope>): <short summary>

<optional description / context>

Task: P0-T03
Phase: P0
Track: Foundations
```

### Commit Types
- `feat`: New feature or capability
- `fix`: Bug fix
- `docs`: Documentation updates
- `test`: Adding or modifying tests
- `refactor`: Code refactoring without behavioral change
- `chore`: Maintenance tasks or build script updates

---

## 3. Pull Request & Code Review Policy

- Target branch: `norma-bdd` (squash-merge strategy).
- All PRs must use `.github/PULL_REQUEST_TEMPLATE.md`.
- **Required Automated Checks**:
  - Linting & import checks (`ruff`)
  - Unit & contract tests (`pytest -m "not integration"`)
  - Secret scanning (`gitleaks`)
  - Cost Gate check (for Phase P6+)
- **Approval Gate**: Every task requires explicit review and approval before merging into `norma-bdd`.

---

## 4. Freeze Rules & Release Tagging

- **Merge Freeze**: Applied during Phase exit gate validation. No non-essential PRs merged until phase audit passes.
- **Release Tags**:
  - Format: `v<major>.<minor>.<patch>` (e.g., `v2.0.0`).
  - Tags created on `main` branch only.

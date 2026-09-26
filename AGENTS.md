# Repository Guidance

- Treat `pyproject.toml`, the implementation, and `.github/workflows/ci.yml` as the sources of truth for supported versions, commands, and CI behavior.
- Keep changes scoped to the owning package and preserve public CLI, API, MCP, and file-format contracts unless the task asks to change them.
- Add or update focused tests for behavior changes. Avoid live network calls and credentials in unit tests.
- Keep documentation claims and repository maps aligned with files that exist; do not describe generated output as maintained source.
- Do not edit generated files, local environment files, or unrelated user changes unless the task requires it.

Useful checks:

- Python tests: `python -m pytest -m "not integration"`
- Python unused imports: `python -m ruff check . --select F401`
- UI checks: `npm --prefix ui run ci:ui`
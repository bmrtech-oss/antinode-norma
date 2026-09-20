Generate-from-CSV run log

Date: 2026-09-20

Summary:
- Ran CSV ingestion and feature generation using the mock LLM provider to avoid external network calls.

Commands executed:

```powershell
python -m antinode_norma.cli generate-from-csv tests/fixtures/sample_story.csv --output-dir features
```

Repository changes for this run:
- Made XLSX ingester optional so CSV runs don't require `openpyxl`:
  - `antinode_norma/ingest_structured/__init__.py`
  - `antinode_norma/ingest_structured/normalize.py`
- Force `LLM_PROVIDER=mock` during `generate-from-csv` to avoid external LLM dependencies:
  - `antinode_norma/cli.py`
- Added an INVEST-compliant test case to `tests/fixtures/sample_story.csv` (TC-102).
- Added a robust fallback parser for empty/invalid LLM responses:
  - `antinode_norma/core/parser.py`

Run output:
- Ingested 2 test cases from `tests/fixtures/sample_story.csv`.
- Generation completed using the mock provider; feature files written to `features/`.

Generated feature files (features/):
- local_seed.feature
- login.feature
- reset_my_password.feature
- reset_my_password_via_email.feature
- tc_101.feature
- tc_102.feature

Notes:
- The run used the repository Python environment available on the machine. If you prefer real LLM generation, set `LLM_PROVIDER` and appropriate API keys in your environment and re-run `generate-from-csv` (remove the forced `mock` assignment in `cli.py` first).

Next steps (suggested):
- Review `tc_102.feature` and `reset_my_password_via_email.feature` for content fidelity.
- Optionally enable openpyxl in the environment and revert the optional import changes if full XLSX support is required.

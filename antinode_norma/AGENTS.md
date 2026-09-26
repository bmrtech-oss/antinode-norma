# Python Package Guidance

- Keep the package compatible with Python 3.10+, as declared in `pyproject.toml`.
- Prefer existing package boundaries: core logic, gates, code generation, server adapters, and persistence each have distinct responsibilities.
- For LLM changes, preserve provider-specific credentials, model resolution, and fallback behavior in `utils/llm_factory.py`; cover changes with provider tests.
- Add behavior tests under the existing `tests/` layout and run the narrow test before the broader non-integration suite.
- Keep external I/O at the relevant adapter boundary; avoid adding network or credential requirements to unit tests.
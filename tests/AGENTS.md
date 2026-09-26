# Test Guidance

- Keep unit tests deterministic, isolated, and free of external credentials or network access.
- Mark tests that require external services with the repository's pytest markers and keep fixtures local to the test that owns them where practical.
- For subprocess tests, model the real process protocol and lifecycle; avoid relying on scheduling or output ordering that the protocol does not guarantee.
- Run the focused test file first, then `python -m pytest -m "not integration"` for broader validation.
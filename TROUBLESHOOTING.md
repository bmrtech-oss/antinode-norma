# Troubleshooting

This guide covers the most common errors when using Antinode Norma.

## 1. API rate limits

**Symptom:** Requests fail with rate-limit errors or timeouts.

**Fix:**
- Use a lower-temperature LLM model if supported.
- Retry the request after a short delay.
- For OpenRouter, ensure your key is valid and that you are on a free or paid plan that supports the model.
- If using a shared API key, rotate it or use a dedicated account to avoid throttling.

## 2. Invalid LLM JSON responses

**Symptom:** The tool receives malformed JSON from the LLM and cannot parse step mappings.

**Fix:**
- Verify the prompt and model settings in `.env`.
- Lower `LLM_TEMPERATURE` to reduce response variability.
- Use `LLM_PROVIDER=mock` for local testing to confirm the rest of the pipeline works.
- If the error persists, inspect the raw LLM output in the log and add clearer instructions for structured JSON if needed.

## 3. Missing environment variables

**Symptom:** The CLI reports missing keys like `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, or `LLM_PROVIDER`.

**Fix:**
- Copy `.env.example` or `.env.docker.example` to `.env`.
- Set `LLM_PROVIDER` to one of the supported providers: `openrouter`, `openai`, `anthropic`, `local`, or `mock`.
- For OpenRouter, set `OPENROUTER_API_KEY` and optionally `LLM_BASE_URL`.
- Run `python -m antinode_norma.cli --help` if the CLI flags are not recognized.

## 4. Playwright generation failures

**Symptom:** Generated Playwright code fails to execute or validate in CI.

**Fix:**
- Ensure Playwright dependencies are installed in the environment.
- Run `pytest -m "not integration"` locally to confirm unit-level health.
- If using Docker, run `docker compose run --rm app pytest -m "not integration"`.
- Review the generated test file for missing selectors or mismatched step definitions, then adjust the feature input or codegen settings.

## 5. Docker or container environment issues

**Symptom:** Docker build or container runtime fails during image creation or execution.

**Fix:**
- Make sure Docker/Podman is installed and running.
- Use `docker compose build` to rebuild the image after changing dependencies.
- If Playwright browser installation fails, verify available disk space and container privileges.
- For local mock mode, set `LLM_PROVIDER=mock` in `.env` or pass it with `-e LLM_PROVIDER=mock` on `docker run`.

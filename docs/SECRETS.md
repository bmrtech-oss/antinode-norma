# Secrets Strategy & Policy (ADR-001 §5.1)

This document outlines the security, configuration, and secret management policies for Antinode Norma.

---

## 1. Local Environment Configuration

- **`.env` is Git-Ignored**: Secrets and API keys must **never** be committed to version control. The `.env` file is listed in `.gitignore`.
- **`.env.example` is Committed**: `.env.example` serves as the template for required and optional environment variables. When adding new secrets or runtime options, update `.env.example` immediately.
- **Environment Loading**: `python-dotenv` loads environment variables automatically at CLI startup.

---

## 2. Secrets Inventory & Requirements

### LLM Providers (Required depending on provider selection)

- `OPENAI_API_KEY`: Required when `LLM_PROVIDER=openai` or `NORMA_LLM_PROVIDER=openai`.
- `ANTHROPIC_API_KEY`: Required when `LLM_PROVIDER=anthropic` or `NORMA_LLM_PROVIDER=anthropic`.
- `OPENROUTER_API_KEY`: Required when `LLM_PROVIDER=openrouter` or `NORMA_LLM_PROVIDER=openrouter`.

### Delivery Integrations (Optional)

- `TESTRAIL_URL`, `TESTRAIL_USER`, `TESTRAIL_PASSWORD`, `TESTRAIL_PROJECT_ID`
- `XRAY_BASE_URL`, `XRAY_TOKEN`, `XRAY_PROJECT_KEY`

### Notifications (Optional)

- `SLACK_WEBHOOK_URL`
- `TEAMS_WEBHOOK_URL`

### Runtime Overrides

- `NORMA_LLM_PROVIDER` (default: `openai`)
- `NORMA_LLM_MODEL` (default: `gpt-4o-mini`)
- `NORMA_CACHE_PATH` (default: `build/llm_cache.json`)
- `NORMA_LOG_PROMPTS` (default: `false`)

---

## 3. Fail-Fast Secret Check Policy

When a required secret is missing during runtime initialization (e.g., initializing an LLM provider client without its corresponding API key set in `.env` or system environment):

1. The platform must **fail fast** by raising an exception immediately before executing requests.
2. The error message must explicitly name the missing key and point the operator to `.env.example` for guidance on setting up their environment.

Optional integration secrets (e.g., TestRail or Slack webhooks when feature is unused) will log warnings or skip optional execution rather than causing fatal crashes.

---

## 4. CI/CD & Secret Scanning

- **GitHub Actions Secrets**: Production and CI API keys are injected via GitHub Actions Secrets (`secrets.OPENROUTER_API_KEY`, `secrets.OPENAI_API_KEY`, `secrets.ANTHROPIC_API_KEY`).
- **Gitleaks Scanning**: Gitleaks is configured via `.pre-commit-config.yaml` and CI pipelines to prevent accidental secret commits.

---

## 5. Secret Rotation Protocol

1. **Schedule**: All production API keys and tokens undergo quarterly key rotation.
2. **Procedure**:
   - Generate new API key in the provider dashboard (OpenAI, Anthropic, OpenRouter, JIRA, TestRail, Xray).
   - Update repository secrets in GitHub Actions settings.
   - Update local development `.env` files.
   - Revoke old API keys after confirming zero disruption.
3. **Audit Log**: Rotation events are logged and tracked internally by the Security Lead.

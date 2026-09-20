# Secrets Management Strategy — Antinode Norma

This document outlines the secrets management policy, handling rules, environment variable schema, and automated secret scanning.

---

## 1. Secrets Handling Rules

1. **No Committed Secrets**: Never commit private keys, API tokens, passwords, or authentication secrets into git.
2. **Local Environment (`.env`)**: Local secrets must be stored in `.env` (which is excluded via `.gitignore`).
3. **Template (`.env.example`)**: `.env.example` is committed with placeholder values for all supported secrets and runtime overrides.
4. **CI Secrets**: GitHub Actions secrets store credentials for integration tests and deployments.
5. **Fail-Fast Validation**: CLI and server startup checks validate required provider secrets and fail fast with guidance if missing.

---

## 2. Environment Variables Schema (`.env.example`)

```ini
# LLM Provider API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=

# Delivery Integrations
TESTRAIL_URL=
TESTRAIL_USER=
TESTRAIL_PASSWORD=
TESTRAIL_PROJECT_ID=
XRAY_BASE_URL=
XRAY_TOKEN=
XRAY_PROJECT_KEY=

# Notification Webhooks
SLACK_WEBHOOK_URL=
TEAMS_WEBHOOK_URL=

# Runtime Overrides
NORMA_LLM_PROVIDER=openai
NORMA_LLM_MODEL=gpt-4o-mini
NORMA_CACHE_PATH=build/llm_cache.json
NORMA_LOG_PROMPTS=false

# Authentication (OIDC / SAML)
NORMA_OIDC_CLIENT_ID=
NORMA_OIDC_CLIENT_SECRET=
NORMA_OIDC_DISCOVERY_URL=
```

---

## 3. Automated Scanning & Secret Rotation

- **Gitleaks CI Hook**: `gitleaks` scans all commits and PRs for potential credential leaks.
- **Rotation Schedule**: Production API keys and service credentials undergo quarterly rotation, managed by the Security Lead.

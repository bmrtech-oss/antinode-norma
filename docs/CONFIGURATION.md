# Configuration Guide — Antinode Norma

This document covers configuration options, feature flags, configuration file schema (`norma.config.yml`), and environment variables.

---

## 1. Feature Flags (`norma.config.yml`)

High-risk features and platform capabilities are controlled by boolean feature flags. Flags can be specified in `norma.config.yml` or overridden via environment variables (`NORMA_FEATURE_<NAME>`).

```yaml
features:
  unified_agent: true       # Enables NormaAgent unified generation pipeline
  cache_exact: true          # Enables ExactPromptCache
  cache_semantic: true       # Enables SemanticPromptCache
  governance_audit: true     # Enables content-hashed Audit Log
  governance_approval: true  # Enables Approval Gate requirement
  auth_saml: false           # Enables SAML 2.0 authentication support
  execution_cloud: true      # Enables cloud runner grid support (BrowserStack/SauceLabs)
  edge_discovery: false      # Enables edge discovery experimental mode
  database: false            # Enables SQLite/PostgreSQL persistence (false uses file-based)
```

---

## 2. Configuration File Schema (`norma.config.yml`)

An example `norma.config.yml` configuration:

```yaml
version: "2.0"

llm:
  provider: openai           # openai, anthropic, openrouter, gemini, groq, mistral, local, mock
  model: gpt-4o-mini
  temperature: 0.2
  cache: true
  cache_path: build/llm_cache.json

gates:
  soft_threshold: 0.85
  semantic_threshold: 0.85
  declarative_threshold: 0.90
  reuse_threshold: 0.90

governance:
  audit_file: build/audit_events.jsonl
  require_approval: true

execution:
  max_workers: 4
  retries: 2
  retry_delay: 1.0
  provider_timeout_seconds: 30
  provider_retry_max: 2
  provider_retry_base_seconds: 0.5
  provider_retry_max_seconds: 8
  provider_circuit_failure_threshold: 3
  provider_circuit_reset_seconds: 30
  capture_artifacts: true
  reporter: junit
  cloud_provider: null       # browserstack, saucelabs, lambdatest

delivery:
  testrail:
    enabled: false
    url: ""
    user: ""
  xray:
    enabled: false
    base_url: ""

features:
  unified_agent: true
  cache_exact: true
  cache_semantic: true
  governance_audit: true
  governance_approval: true
  auth_saml: false
  execution_cloud: true
  database: false
```

---

## 3. Environment Variables

Environment variables take precedence over configuration file settings.

| Environment Variable | Description | Default |
|---|---|---|
| `NORMA_LLM_PROVIDER` | LLM provider name (`openai`, `anthropic`, `openrouter`, `gemini`, `groq`, `mistral`, `local`, `mock`) | `openai` |
| `NORMA_LLM_MODEL` | Target LLM model name | `gpt-4o-mini` |
| `NORMA_CACHE_PATH` | Path to prompt cache file | `build/llm_cache.json` |
| `NORMA_LOG_PROMPTS` | Whether to log prompts to stdout (`true`/`false`) | `false` |
| `NORMA_FEATURE_<NAME>` | Override feature flag (e.g., `NORMA_FEATURE_UNIFIED_AGENT=true`) | per config |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENROUTER_API_KEY` | OpenRouter API key | - |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Google Gemini API key | - |
| `GROQ_API_KEY` | Groq API key | - |
| `MISTRAL_API_KEY` | Mistral API key | - |
| `NORMA_OIDC_CLIENT_ID` | OIDC Client ID | - |
| `NORMA_OIDC_CLIENT_SECRET` | OIDC Client Secret | - |
| `NORMA_OIDC_DISCOVERY_URL` | OIDC Issuer Discovery URL | - |
| `NORMA_RETENTION_CLEANUP_ENABLED` | Run the safe, idempotent artifact/import cleanup sweep at startup | `false` |
| `NORMA_ARTIFACT_RETENTION_DAYS` | Age threshold for generated artifact files from terminal jobs | `30` |
| `NORMA_IMPORT_RETENTION_DAYS` | Age threshold for unreferenced uploaded import files | `30` |
| `NORMA_GENERATION_PROVIDER` | Optional provider used for generation execution; unset uses local rendering | unset |
| `NORMA_GENERATION_PROVIDER_TIMEOUT_SECONDS` | Per-attempt provider deadline | `30` |
| `NORMA_GENERATION_PROVIDER_MAX_RETRIES` | Maximum retries after the initial provider attempt | `2` |
| `NORMA_GENERATION_PROVIDER_RETRY_BASE_SECONDS` | Initial exponential retry delay | `0.5` |
| `NORMA_GENERATION_PROVIDER_RETRY_MAX_SECONDS` | Maximum retry delay | `8` |
| `NORMA_GENERATION_CIRCUIT_FAILURE_THRESHOLD` | Consecutive provider failures before opening the circuit | `3` |
| `NORMA_GENERATION_CIRCUIT_RESET_SECONDS` | Open-circuit cooldown before a recovery probe | `30` |

### Deterministic deployment validation

For deployments without approved non-production provider credentials, use
`LLM_PROVIDER=mock` and leave `NORMA_GENERATION_PROVIDER` unset. This is the
approved provider-mock equivalence path for validating upload, validation,
queueing, progress, recovery, approval, artifact, audit, and retention
behavior without external network calls or secrets. It does not validate model
quality, provider-specific request compatibility, provider quotas, or live
credential configuration. A production deployment using a real provider must
complete a separate non-production live-provider integration before release.

---

## 4. Migration & Rollback Policy (ADR-002 H3-T03)

1. **Rollback Requirement:** Every database migration script must have a documented and tested rollback path (`downgrade()` routine or restore procedure).
2. **Backup-First Gate:** Destructive migrations (e.g. column drops, table restructures) require an automated pre-migration database backup gate (`VACUUM INTO` or snapshot) prior to execution, as detailed in `docs/DR.md` and `docs/MIGRATION.md`.

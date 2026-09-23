# Component Sourcing Register

This register is the evidence boundary for reuse decisions in ADR-003. A
candidate counts as **verified** only when the current repository manifest or
source usage, license metadata, maintenance/security review, and an adapter or
integration test are all identified. A named future recommendation is not
treated as an installed dependency or as realized effort savings.

## Verified current reuse

| Concern | Component | Evidence | License / review | Status |
|---|---|---|---|---|
| API and contracts | FastAPI, Pydantic v2 | `pyproject.toml`; `antinode_norma/server/` | Package metadata reviewed; permissive open-source licenses; existing API and schema tests | Verified |
| Frontend | React 18, TypeScript, Vite, Tailwind | `ui/package.json`; `ui/src/` | Package metadata reviewed; permissive open-source licenses; `npm --prefix ui run ci:ui` | Verified |
| Browser verification | Playwright | `ui/package.json`; `ui/e2e/` | Package metadata reviewed; Apache-2.0; browser quality suite passes | Verified |
| Structured input | openpyxl, PyYAML | `pyproject.toml`; `antinode_aegis/csv.py`, `xlsx.py`, `config.py` | Package metadata reviewed; permissive open-source licenses; P2 adapter tests pass | Verified |
| BDD parsing | gherkin-official, behave | `pyproject.toml`; `antinode_norma/` | Package metadata reviewed; permissive open-source licenses; existing BDD tests pass | Verified |
| Quality and security tooling | Ruff, gitleaks | `requirements-dev.txt`; `.github/workflows/ci.yml` | Tool license and CI action provenance reviewed; focused lint and secret scans are required | Verified |

The verified list describes reuse already present in the repository. It does
not claim that future Aegis capabilities, such as a durable queue or
knowledge graph, are implemented.

## Future candidates requiring a separate verification record

These candidates remain recommendations from ADR-003 and must not be added to
production dependencies without a new license, maintenance, security, adapter,
and operational review:

| Concern | Candidate | Current status |
|---|---|---|
| Durable relational state | PostgreSQL, SQLAlchemy, Alembic | Not installed or verified |
| Background execution | Redis with Dramatiq or Celery | Not installed or verified |
| Authentication and authorization | Authlib OIDC, Casbin | Not installed or verified |
| UI server state | TanStack Query, Zod | Not installed or verified |
| Evaluation and calibration | Promptfoo, scikit-learn, NumPy, pandas | Not installed or verified |
| Knowledge graph | Kuzu, FalkorDB, Apache Jena | Not installed or verified |
| Audit and telemetry | OpenTelemetry, Prometheus, Grafana | Not installed or verified |
| PII detection | Microsoft Presidio | Not installed or verified |
| Delivery | OCI, nginx, Kubernetes | Deployment options, not repository dependencies |

## Verification rule

Before selecting a future candidate, add its exact version or lockfile entry,
license source, maintenance/security findings, integration boundary, adapter
tests, and rollback path to this register and to the relevant evidence record.
Until then, the candidate remains a hypothesis and contributes no savings to
the ADR's 33% reuse estimate.

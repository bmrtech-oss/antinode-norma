# Antinode Norma — Repository Summary (Revised)

> **Repository:** [https://github.com/bmrtech-oss/antinode-norma](https://github.com/bmrtech-oss/antinode-norma)  
> **License:** MIT  
> **Organization:** Antinode Labs (`bmrtech-oss`)  
> **Current Version:** 0.1.0 (released June 27, 2026)

---

## 📌 Table of Contents

1. [Overview](#overview)
2. [Why Norma?](#why-norma)
3. [What Makes It Stand Out](#what-makes-it-stand-out)
4. [Architecture](#architecture)
5. [Autonomous BDD Agent](#autonomous-bdd-agent)
6. [Current Core Features (Implemented)](#current-core-features-implemented)
7. [Planned Capabilities (Roadmap)](#planned-capabilities-roadmap)
8. [Phased Implementation Plan](#phased-implementation-plan)
9. [code‑intel Integration – The Missing Half](#codeintel-integration--the-missing-half)
10. [Technology Stack](#technology-stack)
11. [Project Structure](#project-structure)
12. [Getting Started](#getting-started)
13. [Competitive Position](#competitive-position)
14. [Engineering Philosophy](#engineering-philosophy)
15. [Licensing & Community](#licensing--community)

---

## Overview

**Antinode Norma** is an open‑source BDD (Behavior‑Driven Development) platform that transforms raw user stories into validated Gherkin `.feature` files and, ultimately, executable tests. It applies an **INVEST quality gate** as a hard checkpoint – stories that fail are rejected with structured, actionable feedback, never silently processed.

- **Current maturity:** 7.5/10 (open‑source) – solid architecture, but gaps in reliability and intelligence.
- **Target:** 9.0/10 – production‑grade, self‑improving, and grounded in real code structure.

---

## Why Norma?

> **It enforces quality before it generates anything.**  
> Most BDD tools will happily produce Gherkin from a vague, untestable story – Norma won't.

- **Saves rework** – INVEST gate catches bad stories at source.
- **Collapses the BDD pipeline** – one command goes from JIRA ticket to a merged PR with validated `.feature` and passing tests.
- **Works with your LLM budget** – switch providers with one env variable; OpenRouter free tier means zero LLM cost to start.

---

## What Makes It Stand Out

- **INVEST‑First, Not Generate‑First** – every `.feature` file is guaranteed to come from a story that is Independent, Negotiable, Valuable, Estimable, Small, and Testable.
- **Autonomous End‑to‑End BDD Pipeline** – the `run_bdd_agent` fetches stories, improves them, generates Gherkin, runs tests, fixes errors, opens PRs, and comments on JIRA – all in one command.
- **Pure Core Architecture** – business logic is side‑effect‑free and provider‑agnostic; unit‑testable without API keys.
- **Native Claude Desktop Integration** – ships as a `.mcpb` plugin; product managers can generate features directly in Claude.
- **LLM Provider Freedom** – Anthropic, OpenAI, OpenRouter, or local models – switch with one env variable.

---

## Architecture

The system follows a **strict layered design** inspired by functional programming. All side effects (LLM calls, file I/O) are isolated at the edges.

```
┌─────────────────────────────────────────────┐
│           External Connectors               │
│        JIRA Cloud  │  GitHub  │  CLI        │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│         MCP Transport (stdio / SSE)         │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│          Norma MCP Server                   │
│  submit_story │ improve_story │             │
│  generate_feature │ run_bdd_agent           │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│     Pure Core (side‑effect‑free)            │
│  Parser → INVEST Gate → Gherkin Generator   │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│           Effects Layer                     │
│      File I/O  │  LLM API Calls             │
└─────────────────────────────────────────────┘
```

| Layer | Role |
|---|---|
| **Connectors** | Ingest stories from JIRA, GitHub, or CLI |
| **MCP Transport** | Routes messages via stdio/SSE |
| **Norma MCP Server** | Exposes BDD tools callable by Claude or any MCP client |
| **Pure Core** | Parser → INVEST → Gherkin generation (no I/O) |
| **Effects Layer** | File writes, LLM calls – all side effects isolated |

---

## Autonomous BDD Agent

The **ReAct‑style agent** (`run_bdd_agent`) orchestrates multi‑step BDD workflows end‑to‑end.

### Agent Workflow

```
User Story (CLI / JIRA)
         │
         ▼
  ┌─────────────┐     fail     ┌──────────────┐
  │ INVEST Gate │ ──────────▶  │ Story Improver│
  └──────┬──────┘              └──────┬───────┘
         │ pass                       │ retry
         ▼                            │
  ┌─────────────┐◀───────────────────┘
  │  Generate   │
  │   Gherkin   │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐     fail     ┌──────────────┐
  │  Run Tests  │ ──────────▶  │  Fix Gherkin │
  │(Behave/Cuke)│              └──────┬───────┘
  └──────┬──────┘                     │ retry
         │ pass                       │
         ▼                            │
  ┌─────────────┐◀───────────────────┘
  │ Create PR + │
  │ JIRA Comment│
  └─────────────┘
```

### Agent Tools

| Tool | Description |
|---|---|
| `fetch_jira_story` | Fetch story by JIRA key |
| `submit_story` | Submit story to INVEST gate |
| `improve_story` | Rewrite story based on feedback |
| `generate_feature` | Generate Gherkin `.feature` |
| `run_tests` | Execute tests via Behave/Cucumber |
| `fix_gherkin` | Repair validation errors |
| `create_pull_request` | Open PR with feature file |
| `comment_jira` | Post comment on JIRA issue |

---

## Current Core Features (✅ Implemented)

| Feature | Status | Notes |
|---|---|---|
| **INVEST Quality Gate** | ✅ Stable | Hard checkpoint; fails stories that don't meet criteria |
| **Gherkin Generation** | ✅ Stable | Produces `.feature` files via LLM (provider‑agnostic) |
| **Playwright Test Codegen** | ✅ Stable | Generates TypeScript Playwright tests + page objects |
| **MCP Integration** | ✅ Stable | Exposes tools via MCP; Claude Desktop plugin available |
| **Multi‑LLM Support** | ✅ Stable | Anthropic, OpenAI, OpenRouter, local models |
| **CLI + Python API** | ✅ Stable | Full command‑line interface and programmatic use |
| **JIRA / GitHub Connectors** | ✅ Stable | Fetch stories, post comments, trigger status transitions |
| **Docker Support** | ✅ Stable | Containerised development and deployment |
| **Failure Storage (SQLite)** | ✅ Passive | Stores test failure data; currently read‑only |
| **Basic Step Mapping** | ⚠️ Regex‑based | Works, but brittle (~80‑85% success rate) – this is the **top priority gap** |

---

## Planned Capabilities (📅 Roadmap)

| Capability | Target Phase | Status |
|---|---|---|
| **LLM‑backed step mapping** | Phase 1 | 📅 Planned – hybrid rule + LLM + similarity fallback |
| **Self‑healing selectors** | Phase 2 | 📅 Planned – automatic repair of broken selectors |
| **Debug observability** (`--show-mapping-decisions`) | Phase 0 | 📅 Planned – quick win |
| **Richer error messages** | Phase 0 | 📅 Planned – actionable feedback |
| **Knowledge Graph + RAG** | Phase 3 | 📅 Planned – domain ontology, graph, grounded generation |
| **Failure‑aware generation** | Phase 2 | 📅 Planned – learn from test failures |
| **Visual Testing** | Phase 5 | 📅 Planned – Playwright snapshots (Percy optional) |
| **Accessibility Testing** | Phase 5 | 📅 Planned – axe‑core integration |
| **Mobile / API / Load Testing Emitters** | Phase 4 | 📅 Planned – Appium, REST/GraphQL, k6/JMeter |
| **code‑intel Integration** | Phase 3+ | 📅 Planned – bridge to code intelligence system |
| **Plugin Registry** | Phase 4 | 📅 Planned – extensible emitter system |

---

## Phased Implementation Plan

The roadmap is structured into **five phases** with clear deliverables, effort estimates, and success metrics. This plan prioritises **reliability** (Phases 0–2) before **breadth** (Phases 3–5).

---

### Phase 0: Foundation & Quick Wins (Month 1) – **7.5 → 8.0**

| Task | Deliverable | Effort |
|------|-------------|--------|
| 0.1 Fix logging anti‑pattern | Replace `basicConfig()` with module‑level loggers | 2 days |
| 0.2 Add `--show-mapping-decisions` debug mode | CLI flag to output step‑by‑step decisions | 3 days |
| 0.3 Normalise LLM cache keys | Cache on canonical template `ACTION<selector>` | 2 days |
| 0.4 Richer error messages | Domain‑specific exceptions with fixes and docs | 3 days |

**Success Criteria:**
- Cache hit rate improves >50%.
- Debug mode produces clear decision logs.
- All error messages are actionable.

---

### Phase 1: Step Mapping Overhaul (Months 2–3) – **8.0 → 8.5**

| Task | Deliverable | Effort |
|------|-------------|--------|
| 1.1 Hybrid step mapper | `LLMStepMapper` with rule → LLM → similarity fallback, confidence scoring | 3 weeks |
| 1.2 Expand selector strategies | Support `data-testid` > `role` > `text` > `CSS` > `XPath` | 1 week |
| 1.3 Prompt engineering library | Domain‑specific templates (ecommerce, saas, fintech) with few‑shot examples | 2 weeks |
| 1.4 Step mapping test harness | Dataset of 500+ steps; dashboard; CI regression checks | 1 week |

**Success Criteria:**
- Mapping success rate ≥95% on test harness.
- Selector priority works as documented.

---

### Phase 2: Self‑Healing & Feedback Loop (Months 4–5) – **8.5 → 9.0**

| Task | Deliverable | Effort |
|------|-------------|--------|
| 2.1 Self‑healing selectors | `SelectorHealer` with alternative selectors, DOM similarity, LLM location, confidence scoring | 4 weeks |
| 2.2 Failure‑driven learning | Enhanced `FailureAnalyzer` → pattern detection, proactive prompt injection | 2 weeks |
| 2.3 Intelligent retry logic | Error classification (transient/recoverable/fatal) with exponential backoff | 1 week |
| 2.4 Feedback loop CLI | `anorm learn --auto-update` to feed failures into graph | 1 week |

**Success Criteria:**
- Self‑healing recovers >90% of broken selectors.
- Failure report highlights top failing tests.
- `anorm learn` updates knowledge store.

---

### Phase 3: Knowledge Foundation & RAG (Months 6–8) – **9.0 → 9.2**

| Task | Deliverable | Effort |
|------|-------------|--------|
| 3.1 Domain ontology schema | YAML ontology; INVEST validates entities/actions | 2 weeks |
| 3.2 Knowledge graph (property graph) | NetworkX (embedded) + optional Neo4j; write hooks in effects layer | 3 weeks |
| 3.3 RAG context builder | Embeddings (ChromaDB) + graph traversal → grounded prompt | 3 weeks |
| 3.4 Determinism scorecard | `anorm metrics` – step reuse, INVEST pass rate, determinism | 1 week |

**Success Criteria:**
- Step reuse rate >80% after 20 stories.
- Same story submitted twice produces identical output ≥95%.

---

### Phase 4: Extensibility & Frameworks (Months 9–11) – **9.2 → 9.4**

| Task | Deliverable | Effort |
|------|-------------|--------|
| 4.1 Plugin registry | `Emitter` interface; plugin discovery via entry_points | 3 weeks |
| 4.2 Mobile testing (Appium) | Emitter with touch gestures, mobile selectors | 3 weeks |
| 4.3 API testing (REST/GraphQL) | Emitter for Supertest/REST Assured; contract testing | 2 weeks |
| 4.4 Performance/load testing (k6/JMeter) | Emitter with load profile configuration | 2 weeks |

**Success Criteria:**
- At least 3 community plugins within 3 months.
- Generated mobile/API/load tests pass 80% on sample projects.

---

### Phase 5: Enterprise Polish & Production Readiness (Months 12–14) – **9.4 → 9.5**

| Task | Deliverable | Effort |
|------|-------------|--------|
| 5.1 Visual testing | Playwright snapshot assertions; Percy optional; baseline management | 3 weeks |
| 5.2 Accessibility testing | axe‑core integration; WCAG 2.1 AA reporting | 2 weeks |
| 5.3 Agent state machine | Formal state machine with checkpoint/resume | 2 weeks |
| 5.4 Config precedence & validation | `--show-config`; schema validation | 1 week |
| 5.5 Performance optimisation | Async I/O, request deduplication, LRU cache, parallel LLM calls | 3 weeks |
| 5.6 Test data management | Fixtures, seeding, isolation, cleanup | 2 weeks |
| 5.7 Secrets detection & security | Lint for hardcoded secrets; env var replacement | 2 weeks |
| 5.8 Flakiness detection | Rerun flaky tests, auto‑quarantine | 2 weeks |

**Success Criteria:**
- Visual testing detects 95% of pixel regressions.
- Batch generation time reduced >50%.
- No secrets committed; flaky tests quarantined correctly.

---

## code‑intel Integration – The Missing Half

> **Repo:** [https://github.com/bmrtech-oss/code-intel](https://github.com/bmrtech-oss/code-intel) – production‑ready code intelligence system (PostgreSQL + pgvector, Redis, Ollama).

**What Norma lacks today:** understanding of the actual codebase. `code‑intel` fills that gap – it knows symbols, call graphs, dead code, and dependencies.

**Together they enable:**

1. **Coverage‑gap story generation** – `anorm coverage-gaps` surfaces untested functions as candidate stories.
2. **Impact‑aware stale feature detection** – on git push, Norma queries code‑intel to flag affected feature files before CI.
3. **Grounded Gherkin generation** – LLM generates steps referencing actual symbols from code‑intel.

**Implementation Steps** (planned for Phase 3+):

| Step | File / Component |
|------|------------------|
| 1. Share database | Point Norma at code‑intel’s PostgreSQL; add `NORMA_DB_URL` |
| 2. Symbol bridge | `connectors/code_intel_bridge.py` – query symbols via REST/SQL |
| 3. Coverage gaps | `cli/coverage.py` – SQL join with `norma_step_definitions` |
| 4. Impact detection | `connectors/git_hook.py` – PR comment on stale features |
| 5. Grounded generation | `knowledge/udf_generator.py` – PostgreSQL UDF for `generate_gherkin` |
| 6. MCP bridge | Expose `get_coverage_gaps` and `get_impact` as MCP tools |

This integration is **planned** and will be delivered as part of Phase 3+.

---

## Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Language** | Python 3.9+ |
| **CLI** | Click (`anorm`) |
| **LLM Providers** | Anthropic, OpenAI, OpenRouter, local |
| **Integration** | MCP (stdio/SSE) |
| **Plugin** | Claude Desktop `.mcpb` (Node.js ≥16) |
| **Connectors** | JIRA Cloud, GitHub |
| **Test Runners** | Behave, Cucumber, Playwright |
| **Testing** | pytest, pytest‑cov, pytest‑asyncio |
| **Container** | Docker |
| **License** | MIT |

---

## Project Structure (Condensed)

```
antinode-norma/
├── antinode_norma/       # Main package
├── claude-plugin/        # Claude Desktop plugin
├── tests/                # Unit / integration / connector tests
├── docs/                 # Comprehensive guides
├── examples/             # Demo scripts
├── Dockerfile, docker-compose.yml
└── codegen.yaml          # Configuration
```

---

## Getting Started

```bash
# Clone & install
git clone https://github.com/bmrtech-oss/antinode-norma
pip install -e .

# Configure
cp .env.example .env   # set LLM_PROVIDER, API keys

# Generate
anorm generate "As a user, I want to reset my password."

# Run agent with JIRA
anorm agent "Generate feature for JIRA-123 and create a PR if tests pass."

# Claude Desktop plugin
npm install -g @anthropic-ai/mcpb
cd claude-plugin && mcpb pack   # drag .mcpb into Claude Desktop
```

---

## Competitive Position

| Tool Category | Their Strength | Norma's Angle |
|---|---|---|
| AI Test Generators (Mabl, Testim) | Speed, self‑healing | Open‑source, no lock‑in, reusable assets |
| BDD Frameworks (Cucumber, Behave) | Strong Gherkin support | Automates step mapping and test generation |
| Recorders (Playwright Codegen) | Quick start | Generates maintainable assets, not one‑off scripts |
| Conversational AI (ChatGPT) | Interactive | Structured, validated, workflow‑integrated |

**Strategic positioning:** *"The open‑source alternative to closed AI test generators – AI‑assisted step mapping, not AI‑generated guesswork."*

---

## Engineering Philosophy

The four‑layer model ensures relevance in the AI era:

1. **Pure Core** – survives LLM provider/model changes.
2. **MCP + CLI** – standard protocol, connects to every AI client.
3. **Agentification** – accepts goals, not just commands; sticky workflows.
4. **Plugin Release** – zero‑friction distribution inside AI assistants.

---

## Licensing & Community

- **License:** MIT
- **Issues:** [https://github.com/bmrtech-oss/antinode-norma/issues](https://github.com/bmrtech-oss/antinode-norma/issues)
- **Contributing:** See `CONTRIBUTING.md`
- **Organisation:** Antinode Labs (`bmrtech-oss`)

---

*This summary is living documentation – please open an issue for clarifications or suggestions.*
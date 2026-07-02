# Antinode Norma — Phased Implementation Plan with Copilot Prompts

This document provides the **top user stories** for each phase of the Antinode Norma roadmap, along with **actionable prompts** you can paste directly into GitHub Copilot (Chat or Inline) to implement each task.

All stories and prompts align with the **AI Development Playbook** constraints:
- **Core Tenets**: Trunk‑Based Development, Evaluate AI Like Unit Tests, Unix Philosophy.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2.
- **Quality**: `pytest`, `promptfoo`, type hints required.
- **Process**: Architecture Decision Records (ADRs) for significant decisions.

---

## Phase 0: Foundation & Quick Wins

**Goal:** Fix fundamental quality-of-life issues – logging, observability, error messages, and cache normalisation.

### User Stories

#### Story 0.1: Standardise Logging & Error Handling
**As a** developer, **I want** consistent structured logs and actionable error messages, **so that** I can debug quickly.

**Acceptance Criteria**:
- Remove all `logging.basicConfig()` calls.
- Use `logger = logging.getLogger(__name__)` in every module.
- Log level configurable via `codegen.yaml`.
- All exceptions are domain‑specific with fixes and doc links.
- Create an ADR.

#### Story 0.2: Implement Debug Mode for Step Mapping
**As a** user, **I want** a `--show-mapping-decisions` flag, **so that** I can see exactly how steps were mapped.

**Acceptance Criteria**:
- CLI flag `-d` / `--show-mapping-decisions`.
- Human‑readable console output + JSON log.
- Shows input, candidates, selected mapping, confidence, and reason.

#### Story 0.3: Normalise LLM Cache Keys
**As a** developer, **I want** the cache to recognise semantically identical steps, **so that** cache hit rate improves.

**Acceptance Criteria**:
- Cache key generated from canonical form: `ACTION<selector_type><selector_value>`.
- Migration script to re‑key existing cache.

---

### Copilot Prompts for Phase 0

#### Prompt for Story 0.1 (Logging & Error Handling)
```
@workspace Find all calls to logging.basicConfig() in agent.py and remove them. Replace with module‑level loggers using logging.getLogger(__name__). Add a configuration option in codegen.yaml to set log level (DEBUG, INFO, etc.) and read it in the agent. Replace generic Exception raises with domain‑specific classes: StepMappingError (includes step text and suggested fixes), LLMTimeoutError (includes retry guidance), SelectorNotFoundError (includes alternative suggestions). Update all error handling to use these new types. Provide a migration guide for users.
```

#### Prompt for Story 0.2 (Debug Mode)
```
Add a CLI flag --show-mapping-decisions (short -d) to the main entry point. When enabled, for each Gherkin step, output: Input text, Candidate mappings from the rule engine, Selected mapping with confidence score, Reason for selection (or failure). Log this as structured JSON to a separate debug log file. Also provide a function to print a human‑readable summary to stdout.
```

#### Prompt for Story 0.3 (Cache Normalisation)
```
Current LLM cache keys are raw step text; two semantically identical steps with different punctuation produce different keys. Implement a normalisation function that: strips extra whitespace and quotes; normalises action words (e.g., "click" → "CLICK"); extracts selector type (css, role, text) and value; returns a canonical key: ACTION<selector_type><selector_value>. Update the cache get/set methods to use this normalised key. Provide a migration script to re‑key existing cache entries.
```

---

## Phase 1: Step Mapping Overhaul

**Goal:** Increase step mapping success from ~80% to ≥95% using a hybrid LLM approach.

### User Stories

#### Story 1.1: Implement a Hybrid Step Mapper
**As a** test engineer, **I want** accurate mapping of Gherkin steps, **so that** I don't have to manually fix 15‑20% of generated code.

**Acceptance Criteria**:
- `LLMStepMapper` with cascading: RuleEngine → LLM → Similarity Search → User Feedback.
- Confidence scoring (0‑1) for each decision.
- Configurable LLM provider (OpenAI, Anthropic, OpenRouter) and timeout.
- ADR documenting new architecture.
- Mapping success ≥95% in test harness.

#### Story 1.2: Expand Selector Strategies
**As a** developer, **I want** the mapper to prioritise stable selectors (`data‑testid` > `role` > `text` > `CSS` > `XPath`), **so that** generated tests are less brittle.

**Acceptance Criteria**:
- `SelectorGenerator` produces multiple candidates, scored by uniqueness and stability.
- Priority order documented.

#### Story 1.3: Build a Prompt Engineering Library
**As a** developer, **I want** domain‑specific prompt templates with few‑shot examples, **so that** LLM output is more accurate.

**Acceptance Criteria**:
- Templates for ecommerce, saas, fintech.
- Chain‑of‑thought instructions.
- Versioning and A/B testing support.

#### Story 1.4: Create a Step Mapping Test Harness
**As a** developer, **I want** a comprehensive test suite of 500+ steps, **so that** I can prevent regressions.

**Acceptance Criteria**:
- Dataset of real‑world Gherkin steps with known mappings.
- CLI command `anorm test-mapping` generates a dashboard.
- Integrated into CI.

---

### Copilot Prompts for Phase 1

#### Prompt for Story 1.1 (Hybrid Mapper)
```
Implement an LLMStepMapper class that extends the existing RuleEngine. The mapping pipeline should be:
1. RuleEngine (fast path) → returns mapping with confidence if regex matches.
2. LLM Mapper (slow path) → uses few‑shot prompting to map the step (provider‑agnostic, configurable timeout).
3. Similarity Search (fallback) → uses embeddings (e.g., sentence‑transformers) to find the closest known mapping.
4. User Feedback (learning) → store manual corrections for retraining.
The class should accept a provider (OpenAI, Anthropic, OpenRouter) via config. Return a MappingResult with confidence score, selector, and action type. Add unit tests that mock LLM responses and verify the fallback chain works correctly.
```

#### Prompt for Story 1.2 (Selector Strategies)
```
Enhance the SelectorGenerator to generate multiple selector candidates with priority order: data‑testid > role > text > CSS > XPath. For a given element, produce a list of selectors and score them by: uniqueness (number of matches in DOM), stability (likelihood of change), readability. Update the step mapping to use the highest scored selector that works. Store the full candidate list in the cache for future fallback.
```

#### Prompt for Story 1.3 (Prompt Library)
```
Create a PromptLibrary class that stores domain‑specific prompt templates:
- ecommerce: for checkout, cart, payment flows.
- saas: for login, dashboard, settings.
- fintech: for forms, validation, security.
Each template includes: system prompt with domain context, few‑shot examples (at least 5 per domain), chain‑of‑thought instructions. The library should allow versioning and A/B testing; the user can specify a template version in codegen.yaml. Add a function to automatically select the domain based on the feature file content.
```

#### Prompt for Story 1.4 (Test Harness)
```
Create a test harness that validates the mapping quality:
- Load a test dataset of 500+ real‑world Gherkin steps with known correct mappings (store in tests/mapping_harness/dataset.json).
- Run the mapping pipeline and measure success rate (exact match, partial match, failure).
- Generate a dashboard (HTML) with detailed results per step.
- Integrate this into CI to prevent regression when updating mapping logic.
- Provide a CLI command: `anorm test-mapping --dataset path/to/steps.json`.
```

---

## Phase 2: Self‑Healing & Feedback Loop

**Goal:** Make Norma resilient to UI changes and capable of learning from test failures.

### User Stories

#### Story 2.1: Implement Self‑Healing Selectors
**As a** test maintainer, **I want** broken selectors to be automatically repaired, **so that** tests don't break on minor UI changes.

**Acceptance Criteria**:
- `SelectorHealer` with strategies: alternative selectors, DOM similarity, LLM‑based location.
- Confidence scoring for healed selectors.
- Audit log of all healing attempts.
- Auto‑update if confidence >0.8; otherwise flag for manual review.
- Recovers >90% of broken selectors in simulation.

#### Story 2.2: Create a Failure‑Aware Generation Loop
**As a** team lead, **I want** Norma to learn from past failures, **so that** maintenance burden decreases.

**Acceptance Criteria**:
- `anorm learn` ingests test reports and stores failure patterns.
- Pattern detection (e.g., selector fails 40%).
- Failure rules injected into prompts to avoid known issues.
- Weekly failure report with trends.

---

### Copilot Prompts for Phase 2

#### Prompt for Story 2.1 (Self‑Healing)
```
Implement a SelectorHealer class with the following strategies:
1. Try alternative selectors from the candidate list (stored in cache).
2. Search DOM for similar elements (using text similarity, attribute proximity).
3. Use LLM to locate the intended element given the step description and current DOM.
The healer should produce a new selector with a confidence score. If confidence > 0.8, automatically update the test step; else, flag for manual review. Log all healing attempts for audit. Write a simulation that mutates a test page (change IDs, move elements) and verifies that the healer can recover the correct selector in >90% of cases.
```

#### Prompt for Story 2.2 (Failure‑Aware Generation)
```
Enhance the existing FailureAnalyzer to:
- Detect patterns: e.g., "selector #auth‑button fails 40% of the time" → automatically trigger healing or alert the team.
- Inject failure examples into the LLM prompt during generation to avoid known pitfalls.
- Generate a weekly report (markdown) with top failing tests, flaky tests, and root cause categories.
- Add a CLI command `anorm learn --report-file playwright-report.json --auto-update-graph` that feeds failures into the knowledge graph and updates step mappings.
```

---

## Phase 3: Knowledge Foundation & RAG

**Goal:** Build a persistent memory to make generation deterministic, reusable, and grounded.

### User Stories

#### Story 3.1: Define a Domain Ontology
**As a** product owner, **I want** to define project‑specific vocabulary, **so that** Norma generates consistent Gherkin.

**Acceptance Criteria**:
- YAML ontology schema (`norma‑ontology.yaml`).
- INVEST gate validates entities/actions against ontology.
- LLM prompt constrained to use ontology terms.
- CLI commands: `anorm ontology validate`, `anorm ontology stats`.

#### Story 3.2: Build a Knowledge Graph & RAG Context Builder
**As a** developer, **I want** Norma to reuse existing step definitions and past stories, **so that** generation is deterministic and consistent.

**Acceptance Criteria**:
- Property graph (NetworkX + optional Neo4j) persisting Stories, FeatureFiles, StepDefinitions, etc.
- RAG pipeline: embed story → vector search → graph lookup → assemble grounded prompt.
- Step reuse rate >80% after 20 stories.
- Same story submitted twice gives identical output ≥95%.

---

### Copilot Prompts for Phase 3

#### Prompt for Story 3.1 (Ontology)
```
Design a domain ontology schema in YAML format. The schema should define entities (with synonyms and actions), outcomes (success/failure), and step verbs (given/when/then). Create a pure function `load_ontology(path) -> Ontology` that returns a typed dataclass. Extend the INVEST gate: if a story references an entity not in the ontology, flag it as "Unknown entity" before any LLM call. Add a CLI command `anorm ontology validate --story "..."` to dry‑run the check. Also add `anorm ontology stats` to show entity coverage across generated feature files.
```

#### Prompt for Story 3.2 (Knowledge Graph & RAG)
```
Build a knowledge graph foundation:
- Define nodes: Story, FeatureFile, StepDefinition, PageObject, Entity, TestRun, INVESTResult.
- Define edges: GENERATES, USES, MAPS_TO, SIMILAR_TO, FAILED_INVEST, BROKE, BELONGS_TO.
- Use NetworkX for embedded zero‑infra graph; allow Neo4j as optional backend via env flag `NORMA_GRAPH_BACKEND`.
- On every submit_story, generate_feature, run_tests, write nodes/edges as a side effect.
- Expose `graph.query(cypher_or_networkx)` for internal use.

Implement a RAG context builder that:
- Embeds the story (using sentence‑transformers) and performs a vector search (ChromaDB) to retrieve top‑K similar FeatureFiles.
- Queries the graph for step definitions used by those similar features.
- Retrieves ontology rules for entities in the story.
- Assembles a grounded prompt: [story] + [examples] + [step definitions] + [rules].
Pass this context into the LLM call. Measure step reuse rate before/after; target >80%.
```

---

## Phase 4: Extensibility & Frameworks

**Goal:** Expand to mobile, API, and load testing via a pluggable architecture.

### User Stories

#### Story 4.1: Create a Plugin Registry for Custom Emitters
**As a** community contributor, **I want** to add a new test framework without modifying core, **so that** I can share it easily.

**Acceptance Criteria**:
- Emitter interface defined (`Emitter` abstract class).
- Plugin discovery via `entry_points` or `plugins/` directory.
- CLI commands: `anorm plugin list`, `anorm plugin install <name>`.
- Sample plugin in `examples/`.

#### Story 4.2: Implement a Mobile Testing Emitter (Appium)
**As a** mobile developer, **I want** Appium tests generated from Gherkin, **so that** I can automate mobile testing.

**Acceptance Criteria**:
- Appium emitter generating Java/JavaScript tests.
- Supports touch gestures (tap, swipe, pinch).
- Supports mobile selectors (accessibility ID, XPath, UIAutomator).

---

### Copilot Prompts for Phase 4

#### Prompt for Story 4.1 (Plugin Registry)
```
Design a plugin system for emitters:
- Define an Emitter interface (abstract class) with methods: generate_test_file, supported_framework, setup_instructions.
- Add a PluginManager that discovers plugins via entry_points (setuptools) or a plugins directory.
- Allow users to install plugins via pip and enable them in codegen.yaml.
- Create a registry that stores metadata about installed plugins.
- Provide CLI commands: `anorm plugin list` and `anorm plugin install <name>`.
- Write a sample custom emitter as a reference and include it in the examples/ directory.
```

#### Prompt for Story 4.2 (Mobile Emitter)
```
Create a new emitter for Appium (mobile testing) that:
- Translates Gherkin steps to Appium commands (Java or JavaScript).
- Supports touch gestures: tap, swipe, pinch, long press.
- Uses mobile‑specific selectors: accessibility ID, XPath, UIAutomator.
- Configures capabilities (platform, device name, app path).
- Integrates with Sauce Labs/BrowserStack for cloud devices.
- Add the emitter to the Orchestrator's framework selection.
```

---

## Phase 5: Enterprise Polish & Production Readiness

**Goal:** Add visual testing, accessibility, performance optimisation, security, and flakiness detection.

### User Stories

#### Story 5.1: Integrate Visual Testing
**As a** QA engineer, **I want** visual snapshot assertions in Playwright tests, **so that** UI regressions are caught.

**Acceptance Criteria**:
- Inject `toHaveScreenshot()` into generated tests.
- CLI command `anorm visual-update` to manage baselines.
- Diff detection with threshold.
- Optional integration with Percy/Chromatic.

#### Story 5.2: Optimize Performance for Scale
**As a** user with a large suite, **I want** fast and cost‑efficient generation, **so that** CI pipelines don't slow down.

**Acceptance Criteria**:
- Async I/O (`asyncio`) for LLM calls and file ops.
- Request deduplication for identical steps.
- Parallel LLM calls using `asyncio.gather`.
- Cache eviction policy (LRU, TTL).
- Batch generation time reduced >50%.

---

### Copilot Prompts for Phase 5

#### Prompt for Story 5.1 (Visual Testing)
```
Implement a visual testing module that:
- Injects Playwright snapshot assertions (`expect(page).toHaveScreenshot(...)`) into generated tests when `--enable-visual-testing` is set.
- Provides a CLI command `anorm visual-update` to update baselines.
- Detects pixel‑level regressions and fails the test if differences exceed a threshold.
- Optionally integrates with Percy or Chromatic via API wrappers (configurable).
- Write tests that simulate UI changes and verify that visual diffs are correctly detected.
```

#### Prompt for Story 5.2 (Performance Optimisation)
```
Optimise the system for performance and cost:
- Convert synchronous I/O to async (aiohttp, async LLM clients).
- Implement request deduplication: if the same step is requested multiple times in a batch, reuse the mapping result.
- Add a cache eviction policy (LRU, TTL) to prevent unbounded growth.
- Enable parallel LLM calls for batch generation using asyncio.gather.
- Add a cost estimator that tracks tokens used per run and provides a summary.
- Benchmark the batch generation speed before and after changes, and measure cache hit rate and cost reduction.
```

---

## How to Use These Prompts

1. **Open your repository** in VS Code with GitHub Copilot enabled.
2. **Use Copilot Chat** or inline completions.
3. **Paste the prompt** verbatim, or adjust the file paths and class names to match your codebase.
4. **Iterate** with follow‑up prompts like: "Now add unit tests", "Add docstrings", "Refactor to use Pydantic models".
5. **Reference the AI Development Playbook** for deeper constraints (e.g., ADR format, testing guidelines).

---

## Summary Table of Prompts

| Phase | Task | Copilot Prompt Summary |
|-------|------|------------------------|
| **0** | Logging & Errors | Replace basicConfig, add domain exceptions |
| **0** | Debug Mode | Add `--show-mapping-decisions` flag |
| **0** | Cache Normalisation | Canonical cache keys with migration |
| **1** | Hybrid Mapper | Rule → LLM → Similarity cascade |
| **1** | Selector Expansion | Priority order and scoring |
| **1** | Prompt Library | Domain templates with few‑shot |
| **1** | Test Harness | Dataset, dashboard, CI integration |
| **2** | Self‑Healing | Alternative selectors, LLM location |
| **2** | Failure Loop | Ingest reports, inject rules into prompts |
| **3** | Ontology | YAML schema, INVEST validation |
| **3** | Knowledge Graph & RAG | Graph nodes/edges, ChromaDB, grounded prompt |
| **4** | Plugin Registry | Emitter interface, discovery, CLI |
| **4** | Mobile Emitter | Appium with gestures and mobile selectors |
| **5** | Visual Testing | Playwright snapshots, baseline management |
| **5** | Performance | Async I/O, deduplication, parallel calls |

---

*This document is a companion to the AI Development Playbook. For complete quality and process guidelines, refer to the playbook directly.*
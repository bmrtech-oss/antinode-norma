# Roadmap to Score 9/10: AI-Enhanced Test Generation

## Current Score: 7.5/10  
## Target Score: 9/10

This roadmap outlines **phased improvements** that will elevate the solution to compete with modern AI‑powered testing tools. Each phase includes **concrete tasks** that can be fed to Copilot for implementation.

---

## Phase 1: AI‑Powered Step Mapping (Score +0.7)

**Goal:** Replace hard‑coded regex rules with dynamic LLM‑based step mapping.

### Why:
- Current rule engine is limited to predefined patterns.
- AI can understand natural language and generate appropriate Playwright actions on the fly.

### Tasks:

1. **Create a new LLM-based step mapper module**
   - File: `antinode_norma/codegen/engine/llm_step_mapper.py`
   - Implement `async def map_step_with_llm(step_text: str) -> Tuple[ActionType, str, str]`
   - Use a prompt template with few‑shot examples of Gherkin → Playwright mapping.
   - Support fallback to rule engine if LLM fails.

2. **Integrate the LLM mapper into the parsing pipeline**
   - Modify `GherkinParser._parse_steps()` to try LLM mapping first, fallback to rule engine.
   - Add caching to avoid repeated LLM calls for identical steps.

3. **Prompt engineering**
   - Create a set of 20–30 example mappings for training.
   - Use chain‑of‑thought prompting for complex steps (e.g., "When the user logs in with the new password" → navigate to dashboard).

4. **Add configuration toggle**
   - Add `use_llm_mapping: bool` to `QualityConfig`.
   - Set default to `true` if LLM provider is configured.

5. **Add tests**
   - Unit tests for `llm_step_mapper.py`.
   - Integration test with mock LLM.

---

## Phase 2: Self‑Healing Selectors (Score +0.5)

**Goal:** Automatically recover from broken selectors using AI.

### Why:
- Tests fail when UI changes; self‑healing reduces maintenance.

### Tasks:

1. **Create a selector healing module**
   - File: `antinode_norma/codegen/post_processors/healer.py`
   - Implement `async def heal_selector(page, old_selector, step_context) -> str`
   - Use AI to suggest alternative selectors (e.g., from text, role, data‑testid, aria‑label).

2. **Integrate healer into test execution**
   - Create a Playwright fixture that intercepts `locator()` calls and attempts healing on failure.
   - Log healing events for later review.

3. **Add configuration**
   - Add `enable_self_healing: bool` to `QualityConfig`.
   - Default to `false` initially; users can enable it.

4. **Store healing history**
   - Save successful healing mappings to a local cache for future runs.

5. **Tests**
   - Mock failing selectors and verify healing logic.

---

## Phase 3: Enhanced Story → Feature Generation (Score +0.4)

**Goal:** Improve Gherkin quality with advanced prompting and few‑shot learning.

### Why:
- Current generation is basic; better AI prompts yield more robust features.

### Tasks:

1. **Create a prompt library**
   - File: `antinode_norma/core/prompts.py`
   - Define templates for:
     - INVEST assessment.
     - Feature generation with examples.
     - Gherkin validation.

2. **Add few‑shot examples**
   - Include 5–10 high‑quality feature files as examples in prompts.
   - Use dynamic injection based on story domain (e.g., "login", "checkout").

3. **Chain‑of‑thought prompting**
   - Ask LLM to reason about acceptance criteria before generating Gherkin.
   - Provide intermediate steps (e.g., "What scenarios are needed?").

4. **Feedback loop**
   - Allow users to manually improve generated features and feed them back as examples.

5. **Tests**
   - Compare output quality with baseline examples using BLEU or semantic similarity.

---

## Phase 4: Visual Testing (Score +0.3)

**Goal:** Add screenshot comparison for UI validation.

### Why:
- Visual regressions are common; snapshot testing catches them early.

### Tasks:

1. **Extend Playwright emitter**
   - Add `--include-visual-tests` flag to generation command.
   - For each scenario, include a visual snapshot assertion after key steps.

2. **Create visual test runner**
   - Use Playwright's `expect(page).toHaveScreenshot()`.
   - Store baseline images in `visual-snapshots/` directory.

3. **Add CI integration**
   - Automatically update snapshots on PRs with a label "visual-update".

4. **Configuration**
   - Add `enable_visual_testing: bool` to `QualityConfig`.

5. **Tests**
   - Verify that snapshot generation and comparison work.

---

## Phase 5: Learning from Test Failures (Score +0.3)

**Goal:** Use failure data to improve future test generation.

### Why:
- Continuous learning reduces flakiness and improves accuracy.

### Tasks:

1. **Create a failure analysis module**
   - File: `antinode_norma/core/failure_analyzer.py`
   - Parse Playwright test results (JSON) to extract failing steps and error messages.

2. **Feed failures back to generation**
   - Store failures in a local database (SQLite).
   - Use them as negative examples in prompts to avoid similar issues.

3. **Auto‑healing suggestions**
   - When a test fails, suggest alternative step mappings or selectors.

4. **Add CLI command**
   - `anorm learn` to analyse past runs and update mappings.

5. **Tests**
   - Mock failures and verify learning updates.

---

## Phase 6: CLI & UX Improvements (Score +0.2)

**Goal:** Make the tool more user‑friendly and polished.

### Why:
- Better UX increases adoption and reduces friction.

### Tasks:

1. **Improve CLI output**
   - Add progress bars (using `tqdm` or rich).
   - Colour‑coded messages (green=success, red=error, yellow=warning).
   - Show step‑by‑step breakdown of generation.

2. **Better error messages**
   - When a step cannot be mapped, suggest possible fixes (e.g., "Did you mean ...?").

3. **Add `--interactive` mode**
   - For unmapped steps, ask the user to provide a mapping on the fly.

4. **Add `--dry-run`**
   - Show what would be generated without writing files.

5. **Update help text**
   - Add examples to `--help` output.

6. **Add shell completion**
   - For bash/zsh/powershell.

---

## Phase 7: Advanced Integrations (Score +0.2)

**Goal:** Connect with external tools for seamless workflows.

### Why:
- Integration with JIRA, TestRail, CI/CD enhances value.

### Tasks:

1. **JIRA integration**
   - Auto‑link generated tests to JIRA issues.
   - Update issue status on test pass/fail.

2. **TestRail integration**
   - Upload test cases to TestRail suites.

3. **CI/CD plugins**
   - Provide GitHub Actions and GitLab CI templates.

4. **Slack/Teams notifications**
   - Send test results to channels.

5. **Configuration**
   - Add environment variables for integrations.

---

## Phase 8: Documentation & Community (Score +0.2)

**Goal:** Make the project easy to adopt and contribute to.

### Why:
- Good docs attract users and contributors.

### Tasks:

1. **Update main README**
   - Include all features, screenshots, and quick start.

2. **Create a markdown tutorial**
   - 5‑minute demo tutorial in written form.

3. **Add more examples**
   - Create `examples/` with sample stories and generated tests.

4. **Write API documentation**
   - For all modules using Sphinx or MkDocs.

5. **Create CONTRIBUTING.md**
   - Clear guidelines for contributors.

6. **Add issue templates**
   - Bug report, feature request, question.

---

## Phase 9: Performance & Scalability (Score +0.1)

**Goal:** Handle large test suites efficiently.

### Why:
- Performance matters for enterprise adoption.

### Tasks:

1. **Parallel generation**
   - Generate tests for multiple feature files in parallel.

2. **Caching**
   - Cache LLM responses for identical steps.

3. **Optimise parsing**
   - Use faster parsers (e.g., `parsimonious`).

4. **Benchmark**
   - Measure generation time for 100+ scenarios.

---

## Scoring Summary

| Phase | Improvement | Score |
| :--- | :--- | :--- |
| **Baseline** | – | 7.5 |
| 1. AI step mapping | +0.7 | 8.2 |
| 2. Self‑healing | +0.5 | 8.7 |
| 3. Enhanced generation | +0.4 | 9.1 |
| 4. Visual testing | +0.3 | 9.4 (already >9) |
| 5. Learning from failures | +0.3 | 9.7 |
| 6. UX | +0.2 | 9.9 |
| 7. Integrations | +0.2 | 10.1 (capped at 9) |

**After Phase 3 (Enhanced generation), the score already reaches 9.1.** The remaining phases are optional but push the tool toward 10.

---

## Implementation Strategy

- **Start with Phase 1 and Phase 3** – these are the highest‑impact improvements.
- Use Copilot to implement each task by providing clear specifications.
- Keep existing code as a fallback (e.g., rule engine remains as fallback).
- Write tests for each new feature.
- Update documentation as you go.

---

## How to Use This with Copilot

For each task, create a new branch and ask Copilot:

> "Implement Phase 1, Task 1: Create `antinode_norma/codegen/engine/llm_step_mapper.py` with an async function `map_step_with_llm(step_text: str) -> Tuple[ActionType, str, str]` using few‑shot examples. Use the OpenAI SDK if available, fallback to rules. Include docstrings and error handling."

Then review the code, add tests, and merge.

---

**Final Result:** A robust, AI‑first BDD test generation tool that can compete with commercial offerings, while remaining open‑source and extensible.
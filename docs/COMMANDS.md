# Command Reference

## AI-powered Step Mapping

A new `QualityConfig` option enables natural language Gherkin step mapping using an LLM before falling back to the existing `RuleEngine`.

### Environment variables

- `CODEGEN_QUALITY_USE_LLM_MAPPING=true`
  - Enable LLM-backed step mapping.
  - Set to `false` to disable the LLM and use the fallback rule engine only.

- `CODEGEN_QUALITY_LLM_MAPPING_CACHE_SIZE=1000`
  - Set the maximum number of cached LLM mappings.
  - Cached mappings are persisted across process runs for faster repeat parsing.

- `CODEGEN_QUALITY_LLM_MAPPING_TIMEOUT=5`
  - Timeout in seconds for the LLM mapping call.

### Example Gherkin steps supported

These example steps can now be interpreted by the AI step mapper:

- `When the user clicks the reset link in the email`
- `And the browser navigates to "https://example.com/reset"`
- `Then the page title should contain "Reset Password"`
- `When I fill "jane@example.com" into "#email"`

### Fallback behavior

If LLM mapping fails or returns invalid output, the parser automatically falls back to the existing `RuleEngine` mapping logic.

### Notes

- LLM mapping is async behind the scenes but exposed through a synchronous wrapper for parser compatibility.
- The cache is persisted in the user home directory as `.antinode_norma_llm_step_cache.json`.

# Code Generation Guidance

- Preserve the current flow from Gherkin parsing and step mapping through the test model, orchestrator, emitters, and post-processors.
- Keep framework-specific output in the matching emitter or template rather than branching across unrelated pipeline stages.
- Treat generated test syntax and output paths as user-facing contracts; add or update focused tests when changing them.
- Use deterministic rule-based behavior when possible, and preserve the configured LLM fallback and cache behavior when changing step mapping.
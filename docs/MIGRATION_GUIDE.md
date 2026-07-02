# Migration Guide

## Logging changes
- The agent no longer calls logging.basicConfig() directly.
- Logging is configured from the top-level log_level value in codegen.yaml.
- Supported values include DEBUG, INFO, WARNING, ERROR, and CRITICAL.

## Error handling changes
- Step mapping failures now raise StepMappingError with the offending step text and remediation suggestions.
- LLM timeout failures now raise LLMTimeoutError with retry guidance.
- Selector resolution failures now raise SelectorNotFoundError with alternatives.

## Upgrade steps
1. Update codegen.yaml to set a log_level value, for example log_level: INFO.
2. If you catch generic exceptions around step mapping or selector healing, update them to handle the new domain-specific error classes.
3. Review any custom handlers that previously expected ValueError or generic Exception from these paths.

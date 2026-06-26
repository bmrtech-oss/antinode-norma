# Antinode Norma – Claude Desktop Plugin

This plugin adds BDD feature generation capabilities to Claude Desktop.

It exposes the autonomous BDD agent plus direct MCP tools for feature validation and executable test generation:
- `submit_story`
- `improve_story`
- `generate_feature`
- `run_bdd_agent`
- `generate_tests`
- `generate_page_objects`
- `generate_step_defs`
- `validate_feature`

## Installation

1. Package this directory as a `.mcpb` file using the MCPB CLI:
   ```bash
   npm install -g @anthropic-ai/mcpb
   mcpb pack
   ```

2. Set required environment variables before launching Claude Desktop.
   Create a `.env` file in `claude-plugin/` or export values in your shell. Example:
   ```bash
   export OPENROUTER_API_KEY=sk-or-...
   export LLM_PROVIDER=openrouter
   export LLM_TEMPERATURE=0.2
   export LLM_MAX_TOKENS=1024
   ```

3. Install the generated `antinode-norma.mcpb` file in Claude Desktop.

4. Open Claude Desktop and verify `antinode-norma` appears in the Extensions panel.

For full plugin configuration and usage examples, see `docs/CLAUDE_PLUGIN.md`.
Here's the **English version** of the Claude Desktop plugin packaging script and explanation.

---

## Packaging Script for Claude Desktop Plugin

The official `mcpb pack` command accepts **positional arguments**: the directory to pack and the output file path. There are **no flags** like `--out` or `-o`.

### Usage

```bash
mcpb pack <directory> [output]
```

- `<directory>` – The directory containing your plugin (`manifest.json`, `index.js`, etc.).
- `[output]` – The output `.mcpb` file path (optional). If omitted, it uses the plugin name from `manifest.json` and writes to the current directory.

**Example:**

```bash
mcpb pack . dist/antinode-norma-0.1.0.mcpb
```

---

## How to Use

### 1. Make the script executable (Linux/macOS)

```bash
chmod +x claude-plugin/pack.sh
```

### 2. Run the script

```bash
cd claude-plugin
./pack.sh          # Linux/macOS
# or
.\pack.ps1         # Windows PowerShell
```

### 3. Output

```
📦 Packing plugin (v0.1.0)...
✅ Packaging complete!
📁 dist/antinode-norma-0.1.0.mcpb
📁 dist/antinode-norma.mcpb (shortcut version)
```

---

## Version Management

The script automatically reads the `version` field from `package.json`. Update your `package.json` when releasing a new version:

```json
{
  "name": "antinode-norma-plugin",
  "version": "0.1.0",
  ...
}
```

Each `mcpb pack` run will generate a versioned `.mcpb` file (e.g., `antinode-norma-0.1.0.mcpb`) and a non-versioned shortcut (`antinode-norma.mcpb`) for easy installation.

---

## About the `@anthropic-ai/mcpb` Package

The `mcpb` CLI tool is installed globally via npm:

```bash
npm install -g @anthropic-ai/mcpb
```

It provides the `mcpb` command with subcommands: `init`, `pack`, `validate`, etc. There is **no JavaScript API** – it is designed to be used as a CLI tool, not a library. Therefore, calling it from a shell script is the recommended approach.

---

## Verifying the Packed File

After packing, you can verify the file:

```bash
# List contents of the .mcpb file (it's a zip archive)
unzip -l dist/antinode-norma.mcpb
```

You should see `manifest.json`, `index.js`, and any other files from your plugin directory.

---

## Installing the Plugin in Claude Desktop

1. Open Claude Desktop.
2. Drag the `.mcpb` file into the Claude window, or use **Developer → Extensions → Install Extension**.
3. The plugin will appear in the Extensions panel.

---

## Environment Variables Reminder

Users must export required environment variables (e.g., `OPENROUTER_API_KEY`) **before launching Claude Desktop**. The plugin reads them via `${VAR}` syntax in `manifest.json`. The `.env` file is **not** included in the bundle for security.

Example:

```bash
export OPENROUTER_API_KEY=sk-or-...
open -a "Claude Desktop"   # macOS
```

---

## Next Steps

- Add the `dist/` folder to your `.gitignore`.
- Commit only the source files (`manifest.json`, `index.js`, `package.json`, etc.).
- When releasing a new version, update `package.json`, run `pack.sh`, and attach the generated `.mcpb` to your GitHub release.

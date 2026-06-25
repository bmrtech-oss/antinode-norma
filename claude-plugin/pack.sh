#!/bin/bash
# Claude Desktop plugin packaging script

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Read version from package.json (fallback to 0.1.0)
VERSION=$(node -p "require('./package.json').version" 2>/dev/null || echo "0.1.0")

# Create dist directory
mkdir -p dist

# Pack the plugin with versioned filename
echo "📦 Packing plugin (v${VERSION})..."
mcpb pack . "dist/antinode-norma-${VERSION}.mcpb"

# Create a copy without version suffix for convenience
cp "dist/antinode-norma-${VERSION}.mcpb" "dist/antinode-norma.mcpb"

echo "✅ Packaging complete!"
echo "📁 dist/antinode-norma-${VERSION}.mcpb"
echo "📁 dist/antinode-norma.mcpb (shortcut version)"
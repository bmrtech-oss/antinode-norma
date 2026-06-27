#!/usr/bin/env node
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Path to the Norma MCP server module (adjust if needed)
// Assumes the plugin is inside the antinode-norma project root.
const serverModule = join(__dirname, '..', 'antinode_norma', 'server', 'mcp_server.py');

const server = spawn('python', ['-m', 'antinode_norma.server.mcp_server'], {
    stdio: ['pipe', 'pipe', 'pipe', 'ipc'],
    env: { ...process.env, PYTHONPATH: join(__dirname, '..') }
});

// Forward stdin/stdout/stderr
process.stdin.pipe(server.stdin);
server.stdout.pipe(process.stdout);
server.stderr.pipe(process.stderr);

// Handle process exit
server.on('close', (code) => {
    process.exit(code);
});

process.on('SIGTERM', () => {
    server.kill('SIGTERM');
    process.exit(0);
});

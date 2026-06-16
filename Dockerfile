# Dockerfile for antinode-norma

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any)
# RUN apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./
COPY requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install the package in editable mode
RUN pip install -e .

# Set environment variables (can be overridden at runtime)
ENV LLM_PROVIDER=openrouter
ENV OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
ENV LLM_MODEL=openai/gpt-oss-120b:free
ENV LLM_BASE_URL=https://openrouter.ai/api/v1
ENV LLM_TEMPERATURE=0.2
ENV LLM_MAX_TOKENS=1024

# Default command: show help
CMD ["anorm", "--help"]

# Alternative: run the MCP server (requires stdio)
# CMD ["python", "-m", "antinode_norma.server.mcp_server"]
# Dockerfile for antinode-norma

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Python, Node, and Playwright browser support
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      gnupg \
      git \
      build-essential \
      libnss3 \
      libxss1 \
      libasound2 \
      libatk-bridge2.0-0 \
      libgtk-3-0 \
      libgbm1 \
      libdrm2 \
      libx11-xcb1 \
      libxcomposite1 \
      libxdamage1 \
      libxrandr2 \
      libatk1.0-0 \
      libcups2 \
      libxkbcommon0 \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js for Playwright and frontend tooling
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependency manifests and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy Node dependency manifests and install JavaScript dependencies
COPY package*.json ./
RUN npm ci

# Copy the application and install it in editable mode
COPY . .

# Install the package in editable mode
RUN pip install -e .

# Install Playwright browsers and required browser dependencies
RUN npx playwright install --with-deps

# Set environment variables (can be overridden at runtime)
ENV LLM_PROVIDER=openrouter
ENV OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
ENV LLM_MODEL=openai/gpt-oss-120b:free
ENV LLM_BASE_URL=https://openrouter.ai/api/v1
ENV LLM_TEMPERATURE=0.2
ENV LLM_MAX_TOKENS=1024
ENV PYTHONUNBUFFERED=1

# Default command: show help
CMD ["anorm", "--help"]

# Alternative: run the MCP server (requires stdio)
# CMD ["python", "-m", "antinode_norma.server.mcp_server"]

FROM python:3.12-slim AS base

# Base stage with common settings
FROM base AS builder

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Enable bytecode compilation and use copy mode for better Docker compatibility
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# Copy only dependency files first for better caching
COPY pyproject.toml /app/

# Create virtual environment and install dependencies
RUN uv venv && \
    uv pip install fastmcp>=0.1.0 python-telegram-bot>=21.0 python-dotenv>=1.0.0 requests>=2.31.0

# Copy application code and environment file
COPY telegram_mcp_server.py .
COPY .env .
COPY utils/ ./utils/
COPY config/ ./config/

# Final stage
FROM base

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire app directory including venv from builder
COPY --from=builder /app /app

# Create necessary directories
RUN mkdir -p data logs

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# The MCP server will communicate via stdio
CMD ["python", "telegram_mcp_server.py"]

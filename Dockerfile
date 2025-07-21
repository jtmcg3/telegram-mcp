FROM python:3.12-slim AS base

# Base stage with common settings
FROM base AS builder

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Enable bytecode compilation and use copy mode for better Docker compatibility
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock README.md LICENSE /app/

# Create virtual environment and install dependencies using uv.lock
RUN uv venv && \
    uv sync --frozen

# Copy application code
COPY src/ /app/src/

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
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Health check - verify Python can import the module
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import telegram_mcp; print('Health check passed')" || exit 1

# The MCP server will communicate via stdio
CMD ["python", "-m", "telegram_mcp.server"]
# Contributing to Telegram MCP Server

Thank you for your interest in contributing to Telegram MCP Server! We welcome contributions from the community.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or fix
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/telegram-mcp.git
cd telegram-mcp

# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install development dependencies
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy
```

## Code Style

- We use `ruff` for code formatting and linting
- Type hints are required for all functions
- Maximum line length is 100 characters

Run checks before submitting:
```bash
uv run ruff check .
uv run mypy .
```

## Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Aim for high test coverage

```bash
uv run pytest
uv run pytest --cov=telegram_mcp
```

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense
- Reference issues when applicable

Example:
```
Add rate limiting to message sending

- Implement token bucket algorithm
- Add configuration for rate limits
- Update documentation

Fixes #123
```

## Pull Request Process

1. Update documentation for any changed functionality
2. Add tests for new features
3. Ensure all checks pass
4. Request review from maintainers
5. Address feedback promptly

## Reporting Issues

- Check existing issues first
- Provide clear reproduction steps
- Include relevant logs (without sensitive data)
- Specify your environment

## Security

- Never commit sensitive data
- Report security issues privately
- Follow security best practices

## Questions?

Feel free to open a discussion or reach out to maintainers.

Thank you for contributing!
# Telegram MCP Server

A Model Context Protocol (MCP) server that enables bidirectional communication between LLMs and humans via Telegram.

## Overview

This MCP server acts as a bridge between your LLM and Telegram, allowing:
- LLMs to send messages to users via Telegram
- LLMs to wait for and receive human responses
- Conversation history management
- Secure, authorized-user-only communication

## Architecture

```
LLM → FastMCP → Telegram Bot → Telegram App (Human)
LLM ← FastMCP ← Telegram Bot ← Telegram App (Human)
```

## Quick Start

### Prerequisites

- Python 3.11+
- UV package manager
- A Telegram account
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd telegram-mcp
```

2. **Install UV package manager**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Install dependencies**
```bash
uv sync
```

### Telegram Bot Setup

1. **Create a Telegram Bot**
   - Open Telegram and search for @BotFather
   - Send `/newbot` and follow the instructions
   - Save your bot token

2. **Get your Chat ID**
   - Copy `.env.example` to `.env`
   - Add your bot token to `.env`
   - Send a message to your bot on Telegram
   - Run: `uv run python utils/get_chat_id.py`
   - Copy your chat ID to `.env`

### Configuration

Create a `.env` file with your credentials:
```bash
cp .env.example .env
# Edit .env with your bot token and chat ID
```

### Running the Server

**Local Development:**
```bash
uv run python telegram_mcp_server.py
```

**Docker Deployment:**
```bash
./docker-run.sh
```

## MCP Tools

The server provides three tools for LLM interaction:

### 1. send_message_to_human
Send a message to the human via Telegram and optionally wait for a response.

```python
{
    "message": "Hello! Can you help me with this task?",
    "wait_for_response": true,
    "timeout_seconds": 300
}
```

### 2. get_conversation_history
Retrieve recent conversation history between LLM and human.

```python
{
    "limit": 10  # Number of recent messages to return
}
```

### 3. clear_conversation_history
Clear the conversation history.

```python
{}  # No parameters required
```

## Integration Example

See `docs/llm_integration_example.py` for a complete example of how to integrate this MCP server with your LLM.

## Security Features

- **Authorization**: Only responds to a specific, pre-configured chat ID
- **Environment Variables**: Sensitive tokens stored in environment variables
- **Docker Isolation**: Run in a containerized environment for additional security
- **Non-root User**: Docker container runs as unprivileged user

## Project Structure

```
telegram-mcp/
├── telegram_mcp_server.py    # Main MCP server
├── utils/
│   └── get_chat_id.py       # Utility to find your chat ID
├── config/                   # Configuration directory
├── data/                     # Conversation data persistence
├── logs/                     # Application logs
├── pyproject.toml           # Project configuration and dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker orchestration
├── docker-run.sh           # Docker run helper script
└── .env.example            # Environment variables template
```

## Development

### Adding Dependencies

All dependencies must be managed with UV:
```bash
uv add <package-name>
```

### Running Tests

```bash
# TODO: Add test command when tests are implemented
```

### Logging

Logs are written to the `logs/` directory. Set `LOG_LEVEL` in your `.env` file to control verbosity.

## Troubleshooting

### Bot not responding
- Verify your bot token is correct
- Ensure you've messaged the bot first
- Check that your chat ID matches

### Connection errors
- Check your internet connection
- Verify Telegram API is accessible
- Review logs in `logs/` directory

### Docker issues
- Ensure Docker is running
- Check `docker-compose logs -f telegram-mcp`
- Verify `.env` file exists and is readable

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues first
- Include relevant logs and configuration (without tokens)
# Telegram MCP Server

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://github.com/modelcontextprotocol)

Enable seamless bidirectional communication between Large Language Models (LLMs) and humans through Telegram using the Model Context Protocol (MCP).

## Overview

Telegram MCP Server bridges the gap between AI assistants and human users by providing a robust, secure communication channel through Telegram. This allows LLMs to:

- Send messages to users and wait for responses
- Maintain conversation history
- Handle asynchronous human interactions
- Integrate seamlessly with any MCP-compatible LLM client

## Features

- **Bidirectional Communication**: Send messages and receive responses
- **Conversation Management**: Track and retrieve conversation history
- **Security**: Whitelist-based authorization for chat IDs
- **Async Architecture**: Non-blocking operations for optimal performance
- **Docker Support**: Easy deployment with Docker Compose
- **Type Safety**: Full type hints throughout the codebase

## Quick Start

### Prerequisites

- Python 3.12 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Your Telegram Chat ID

### Installation (NOTE: currently only installation from source is supported)

```bash
# Using UV (recommended)
uv add telegram-mcp

# Using pip
pip install telegram-mcp
```

### Setup

1. **Create a Telegram Bot**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow the instructions
   - Save the bot token

2. **Get Your Chat ID**:
   ```bash
   # Set your bot token
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   
   # Run the utility
   telegram-mcp get-chat-id
   
   # Send a message to your bot and the chat ID will be displayed
   ```

3. **Configure Environment**:
   ```bash
   # Create .env file
   cat > .env << EOF
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   EOF
   ```

4. **Run the Server**:
   ```bash
   telegram-mcp server
   ```

## Usage with LLM Clients

### Example with Claude Code

```bash
# locally running docker? From the cloned project directory:
docker build -t telegram-mcp-server .
# then for claude code integration:
claude mcp add telegram-mcp -- docker run -i telegram-mcp-server

# locally running the python server itself? 
# TODO
```

### Example Integration

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Connect to the Telegram MCP server
    async with stdio_client(
        StdioServerParameters(
            command="telegram-mcp",
            args=["server"],
            env={"TELEGRAM_BOT_TOKEN": "...", "TELEGRAM_CHAT_ID": "..."}
        )
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # Send a message and wait for response
            result = await session.call_tool(
                "send_message_to_human",
                arguments={
                    "message": "Hello! How can I help you today?",
                    "wait_for_response": True,
                    "timeout_seconds": 300
                }
            )
            
            print(f"Human response: {result.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Available Tools

1. **send_message_to_human**
   - Send a message to the user via Telegram
   - Optionally wait for a response with timeout
   - Returns message status and response (if waiting)

2. **get_conversation_history**
   - Retrieve recent conversation messages
   - Configurable limit on number of messages
   - Returns formatted conversation history

3. **clear_conversation_history**
   - Clear all stored conversation history
   - Returns confirmation of clearing

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f telegram-mcp

# Stop the server
docker-compose down
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/telegram-mcp.git
cd telegram-mcp

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install development dependencies
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy
```

### Running Tests

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=telegram_mcp

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .
```

### Project Structure

```
telegram-mcp/
├── src/
│   └── telegram_mcp/
│       ├── __init__.py      # Package initialization
│       ├── server.py        # Main server implementation
│       ├── config.py        # Configuration management
│       ├── logging.py       # Logging setup
│       └── cli.py          # Command-line interface
├── examples/
│   └── basic_usage.py      # Example integration
├── tests/
│   └── test_server.py      # Test suite
├── docs/                   # Documentation
├── docker-compose.yml      # Docker configuration
├── pyproject.toml         # Project metadata
└── README.md             # This file
```

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN` (required): Your Telegram bot token
- `TELEGRAM_CHAT_ID` (required): Authorized user's chat ID
- `LOG_LEVEL` (optional): Logging level (default: INFO)
- `MCP_SERVER_NAME` (optional): MCP server name (default: telegram-mcp)

### Advanced Configuration

See `src/telegram_mcp/config.py` for all available configuration options.

## Security Considerations

- **Authentication**: Only responds to the configured chat ID
- **Environment Variables**: Never commit `.env` files
- **Token Security**: Rotate bot tokens regularly
- **Rate Limiting**: Implement rate limiting for production use

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) for the MCP specification
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for Telegram integration
- [FastMCP](https://github.com/fastmcp/fastmcp) for MCP server implementation

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/telegram-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/telegram-mcp/discussions)
- **Documentation**: [Full Documentation](https://github.com/yourusername/telegram-mcp/wiki)
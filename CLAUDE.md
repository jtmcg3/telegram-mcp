# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Telegram MCP (Model Context Protocol) server that enables bidirectional communication between LLMs and humans via Telegram. The server acts as a bridge, allowing LLMs to send messages to a user's Telegram chat and wait for responses.

## Architecture

The system follows this communication flow:
```
LLM → FastMCP → Telegram Bot → Telegram App (Human)
LLM ← FastMCP ← Telegram Bot ← Telegram App (Human)
```

### Key Components

1. **TelegramMCPServer** (telegram_mcp_server.py): Main server class that:
   - Integrates FastMCP for LLM communication
   - Manages Telegram bot functionality
   - Handles message routing and conversation history
   - Provides MCP tools for LLM interaction

2. **MCP Tools**:
   - `send_message_to_human`: Send messages to Telegram with optional response waiting
   - `get_conversation_history`: Retrieve past conversation messages
   - `clear_conversation_history`: Reset conversation state

## Development Commands

### Dependency Management
**IMPORTANT**: All dependencies MUST be maintained using UV package manager.

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Add new dependencies
uv add <package-name>
```

### Setup Environment
```bash
# Create .env file with required tokens
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env
echo "TELEGRAM_CHAT_ID=your_chat_id_here" >> .env

# Get your chat ID (run after messaging your bot)
uv run python docs/get_chat_id.py
```

### Running the Server
```bash
# Run locally
uv run python telegram_mcp_server.py

# Run with Docker
chmod +x docker-run.sh
./docker-run.sh

# Check Docker logs
docker-compose logs -f telegram-mcp
```

### Testing Integration
```bash
# Run the example LLM integration
uv run python docs/llm_integration_example.py
```

## Project Structure

- `telegram_mcp_server.py`: Main MCP server implementation
- `main.py`: Basic entry point (currently minimal)
- `docs/`:
  - `Implementation_plan.md`: Detailed architecture and setup guide
  - `telegram_mcp_server.py`: Full server implementation
  - `llm_integration_example.py`: Example LLM client
  - `docker_setup.txt`: Docker configuration files
  - `get_chat_id.py`: Utility to find Telegram chat ID

## Key Implementation Details

1. **Security**: The bot only responds to a specific authorized chat ID
2. **Async Architecture**: Uses asyncio for non-blocking operations
3. **Error Handling**: Robust error management with proper logging
4. **Timeout Handling**: Configurable timeouts for waiting for human responses
5. **State Management**: Tracks pending responses and conversation history

## Dependencies

Currently minimal in pyproject.toml, but the full implementation requires:
- `fastmcp>=0.1.0`
- `python-telegram-bot>=21.0`
- `python-dotenv`
- `asyncio`

## Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- `TELEGRAM_CHAT_ID`: Authorized user's chat ID

Optional:
- `LOG_LEVEL`: Logging level (default: INFO)
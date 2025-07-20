#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Validate required environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN not set"
    echo "Please create a .env file with your bot token"
    exit 1
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "Error: TELEGRAM_CHAT_ID not set"
    echo "Please create a .env file with your chat ID"
    exit 1
fi

# Build and run the container
docker-compose up --build -d

echo "Telegram MCP Server started!"
echo "Check logs with: docker-compose logs -f telegram-mcp"
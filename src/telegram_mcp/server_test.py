#!/usr/bin/env python3
"""Tests for Telegram MCP Server using FastMCP testing patterns."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import os
import json

from fastmcp import Client
from .server import TelegramMCPServer


@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def server(mock_bot):
    """Create a server instance with mocked bot."""
    # Set required environment variables for testing
    os.environ['MCP_SERVER_NAME'] = 'telegram-mcp'
    
    with patch('telegram_mcp.server.Bot', return_value=mock_bot):
        server = TelegramMCPServer("test_token", 12345)
        server.bot = mock_bot
        return server


def parse_tool_result(result):
    """Parse the result from CallToolResult."""
    # The result.content[0].text contains the JSON response
    return json.loads(result.content[0].text)


@pytest.mark.asyncio
async def test_send_message_without_wait(server, mock_bot):
    """Test sending message without waiting for response using FastMCP Client."""
    mock_bot.send_message.return_value = Mock(message_id=1)
    
    # Use FastMCP Client for in-memory testing
    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "send_message_to_human",
            {
                "message": "Test message",
                "wait_for_response": False
            }
        )
        
        # Parse the JSON response
        result_dict = parse_tool_result(result)
        
        assert result_dict['sent'] is True
        assert 'message_id' in result_dict
        assert 'timestamp' in result_dict
        mock_bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="Test message",
            parse_mode='Markdown'
        )
        
        # Check conversation history
        assert len(server.conversation_history) == 1
        assert server.conversation_history[0]['message'] == "Test message"


@pytest.mark.asyncio
async def test_send_message_with_timeout(server, mock_bot):
    """Test sending message with response timeout."""
    mock_bot.send_message.return_value = Mock(message_id=1)
    
    # Use FastMCP Client for in-memory testing
    async with Client(server.mcp) as client:
        # Start task to call tool (will timeout)
        task = asyncio.create_task(
            client.call_tool(
                "send_message_to_human",
                {
                    "message": "Test message",
                    "wait_for_response": True,
                    "timeout_seconds": 2
                }
            )
        )
        
        # Give it time to set up pending response
        await asyncio.sleep(0.1)
        
        # Verify pending response was created
        assert len(server.pending_responses) == 1
        
        # Wait for timeout
        result = await task
        
        # Parse the JSON response
        result_dict = parse_tool_result(result)
        
        assert result_dict['sent'] is True
        assert result_dict['response'] is None
        assert 'error' in result_dict
        assert result_dict['error'] == 'Response timeout'


@pytest.mark.asyncio
async def test_conversation_history(server):
    """Test conversation history management using FastMCP Client."""
    # Add some messages to history
    server.conversation_history = [
        {
            'timestamp': '2024-01-01T00:00:00',
            'type': 'llm_to_human',
            'message': 'Hello',
            'message_id': 1
        },
        {
            'timestamp': '2024-01-01T00:01:00',
            'type': 'human_to_llm',
            'message': 'Hi',
            'in_reply_to': 1
        }
    ]
    
    # Use FastMCP Client for in-memory testing
    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "get_conversation_history",
            {"limit": 10}
        )
        
        # Parse the JSON response
        result_dict = parse_tool_result(result)
        
        assert 'history' in result_dict
        assert len(result_dict['history']) == 2
        assert result_dict['total_messages'] == 2
        assert result_dict['history'][0]['message'] == 'Hello'
        assert result_dict['history'][1]['message'] == 'Hi'


@pytest.mark.asyncio
async def test_conversation_history_with_limit(server):
    """Test conversation history with limit."""
    # Add multiple messages
    for i in range(5):
        server.conversation_history.append({
            'timestamp': f'2024-01-01T00:0{i}:00',
            'type': 'llm_to_human',
            'message': f'Message {i}',
            'message_id': i
        })
    
    # Use FastMCP Client for in-memory testing
    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "get_conversation_history",
            {"limit": 3}
        )
        
        # Parse the JSON response
        result_dict = parse_tool_result(result)
        
        assert len(result_dict['history']) == 3
        assert result_dict['total_messages'] == 5
        # Should return the 3 most recent messages
        assert result_dict['history'][0]['message'] == 'Message 2'
        assert result_dict['history'][2]['message'] == 'Message 4'


@pytest.mark.asyncio
async def test_clear_conversation_history(server):
    """Test clearing conversation history using FastMCP Client."""
    # Add some messages
    server.conversation_history = [
        {
            'timestamp': '2024-01-01T00:00:00',
            'type': 'llm_to_human',
            'message': 'Hello',
            'message_id': 1
        }
    ]
    
    # Use FastMCP Client for in-memory testing
    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "clear_conversation_history",
            {}
        )
        
        # Parse the JSON response
        result_dict = parse_tool_result(result)
        
        assert result_dict['cleared'] is True
        assert len(server.conversation_history) == 0


@pytest.mark.asyncio
async def test_mcp_tools_available(server):
    """Test that all expected MCP tools are available."""
    async with Client(server.mcp) as client:
        tools = await client.list_tools()
        
        # Check all expected tools are available
        tool_names = [tool.name for tool in tools]
        assert 'send_message_to_human' in tool_names
        assert 'get_conversation_history' in tool_names
        assert 'clear_conversation_history' in tool_names
        
        # Verify tool descriptions
        send_tool = next(t for t in tools if t.name == 'send_message_to_human')
        assert 'Send a message to the human via Telegram' in send_tool.description


@pytest.mark.asyncio
async def test_server_ping(server):
    """Test server ping functionality."""
    async with Client(server.mcp) as client:
        # Ping should work
        is_alive = await client.ping()
        assert is_alive is True


def test_server_initialization():
    """Test server initialization."""
    with patch('telegram_mcp.server.Bot'):
        server = TelegramMCPServer("test_token", 12345)
        
        assert server.bot_token == "test_token"
        assert server.authorized_chat_id == 12345
        assert server.pending_responses == {}
        assert server.conversation_history == []
        assert server.mcp is not None
        # Server name comes from settings which defaults to 'Telegram Bridge'
        assert server.mcp.name in ["telegram-mcp", "Telegram Bridge"]


@pytest.mark.asyncio
async def test_handle_telegram_message(server, mock_bot):
    """Test handling incoming Telegram messages."""
    # Create a mock update
    update = Mock()
    update.effective_chat.id = 12345
    update.message.chat_id = 12345
    update.message.text = "Test response"
    update.message.message_id = 456
    update.message.reply_text = AsyncMock()
    
    # Set up pending response
    response_id = "response_123"
    server.pending_responses[response_id] = {
        'waiting': True,
        'response': None,
        'timestamp': '2024-01-01T00:00:00'
    }
    
    # Create mock context
    context = Mock()
    
    # Call handler
    await server.handle_telegram_message(update, context)
    
    # Check response was recorded
    assert server.pending_responses[response_id]['waiting'] is False
    assert server.pending_responses[response_id]['response'] == "Test response"
    
    # Check conversation history
    assert len(server.conversation_history) == 1
    assert server.conversation_history[0]['type'] == 'human_to_llm'
    assert server.conversation_history[0]['message'] == "Test response"
    
    # Check confirmation was sent
    update.message.reply_text.assert_called_once_with("✅ Response received and forwarded to LLM")


@pytest.mark.asyncio
async def test_unauthorized_message(server, mock_bot):
    """Test handling messages from unauthorized users."""
    # Create a mock update from different chat ID
    update = Mock()
    update.effective_chat.id = 99999  # Different from authorized
    update.message.chat_id = 99999
    update.message.text = "Unauthorized message"
    update.message.reply_text = AsyncMock()
    
    # Create mock context
    context = Mock()
    
    # Call handler - should return without processing
    await server.handle_telegram_message(update, context)
    
    # Check no history was added
    assert len(server.conversation_history) == 0
    
    # Check no responses were recorded
    assert len(server.pending_responses) == 0
    
    # Check unauthorized message was sent
    update.message.reply_text.assert_called_once_with("❌ Unauthorized access")


@pytest.mark.asyncio
async def test_send_message_with_response(server, mock_bot):
    """Test sending message and receiving response."""
    mock_bot.send_message.return_value = Mock(message_id=123)
    
    # Start a task to send message and wait for response
    async def send_and_wait():
        async with Client(server.mcp) as client:
            return await client.call_tool(
                "send_message_to_human",
                {
                    "message": "Hello human",
                    "wait_for_response": True,
                    "timeout_seconds": 5
                }
            )
    
    # Start the send task
    send_task = asyncio.create_task(send_and_wait())
    
    # Give it time to set up
    await asyncio.sleep(0.1)
    
    # Simulate human response
    update = Mock()
    update.effective_chat.id = 12345
    update.message.chat_id = 12345
    update.message.text = "Hello LLM"
    update.message.message_id = 456
    update.message.reply_text = AsyncMock()
    
    context = Mock()
    
    # Find the pending response
    response_key = list(server.pending_responses.keys())[0]
    
    # Simulate response handling
    await server.handle_telegram_message(update, context)
    
    # Get the result
    result = await send_task
    
    # Parse the JSON response
    result_dict = parse_tool_result(result)
    
    assert result_dict['sent'] is True
    assert result_dict['response'] == "Hello LLM"
    assert 'message_id' in result_dict
    
    # Check conversation history has both messages
    assert len(server.conversation_history) == 2
    assert server.conversation_history[0]['type'] == 'llm_to_human'
    assert server.conversation_history[0]['message'] == 'Hello human'
    assert server.conversation_history[1]['type'] == 'human_to_llm'
    assert server.conversation_history[1]['message'] == 'Hello LLM'


@pytest.mark.asyncio
async def test_unsolicited_message(server, mock_bot):
    """Test handling unsolicited messages (no pending response)."""
    # Create a mock update
    update = Mock()
    update.effective_chat.id = 12345
    update.message.chat_id = 12345
    update.message.text = "Unsolicited message"
    update.message.message_id = 789
    update.message.reply_text = AsyncMock()
    
    # No pending responses
    assert len(server.pending_responses) == 0
    
    # Create mock context
    context = Mock()
    
    # Call handler
    await server.handle_telegram_message(update, context)
    
    # Check conversation history was updated
    assert len(server.conversation_history) == 1
    assert server.conversation_history[0]['type'] == 'human_to_llm'
    assert server.conversation_history[0]['message'] == "Unsolicited message"
    
    # Check appropriate response was sent
    update.message.reply_text.assert_called_once_with(
        "📝 Message noted. Waiting for LLM to request next interaction."
    )


# Additional integration test for the full server lifecycle
@pytest.mark.asyncio
async def test_server_lifecycle(server):
    """Test starting and stopping the server."""
    # Server should be created successfully
    assert server is not None
    assert server.telegram_app is None  # Not started yet
    
    # We can't test actual startup without real Telegram credentials
    # but we can verify the structure is correct
    assert hasattr(server, 'run_server')
    assert hasattr(server, 'start_telegram_bot')
    assert hasattr(server, 'stop_telegram_bot')
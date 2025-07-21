#!/usr/bin/env python3
"""
Telegram MCP Server - Bidirectional communication between LLM and Telegram
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import sys
from collections import deque
import signal

# Configuration and logging
from .config import settings
from .logging import setup_logging, get_logger

# FastMCP and MCP imports
from fastmcp import FastMCP

# Telegram imports
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Set up logging
setup_logging()
logger = get_logger(__name__)


# Constants
class Constants:
    """Application constants"""
    DEFAULT_TIMEOUT = 300  # Default response timeout in seconds
    MAX_HISTORY_SIZE = 1000  # Maximum conversation history size
    MAX_MESSAGE_PREVIEW = 50  # Characters to show in log previews
    BOT_STARTUP_DELAY = 1  # Seconds to wait for bot initialization


def escape_markdown(text: str) -> str:
    """
    Escape special markdown characters to prevent injection attacks.
    
    Args:
        text: The text to escape
        
    Returns:
        Escaped text safe for Telegram markdown
    """
    # List of special characters in Telegram's MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    # Escape each special character
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

class TelegramMCPServer:
    def __init__(self, bot_token: str, authorized_chat_id: int, max_history_size: int = Constants.MAX_HISTORY_SIZE):
        self.bot_token = bot_token
        self.authorized_chat_id = authorized_chat_id
        self.bot = Bot(token=bot_token)
        self.pending_responses = {}  # Store pending human responses
        self.conversation_history = deque(maxlen=max_history_size)  # Bounded conversation history
        
        # Initialize FastMCP
        self.mcp = FastMCP(settings.MCP_SERVER_NAME or "telegram-mcp")
        self._setup_mcp_tools()
        
        # Initialize Telegram application
        self.telegram_app = None
        
        # Shutdown event for graceful termination
        self._shutdown_event = asyncio.Event()
        
    def _setup_mcp_tools(self):
        """Setup MCP tools for LLM interaction"""
        
        @self.mcp.tool()
        async def send_message_to_human(message: str, wait_for_response: bool = True, timeout_seconds: int = Constants.DEFAULT_TIMEOUT, escape_markdown_chars: bool = True) -> dict:
            """
            Send a message to the human via Telegram and optionally wait for a response.
            
            Args:
                message: The message to send to the human
                wait_for_response: Whether to wait for a human response
                timeout_seconds: How long to wait for a response (default 300 seconds)
                escape_markdown_chars: Whether to escape markdown special characters (default True)
            
            Returns:
                dict: Contains 'sent' status and 'response' if wait_for_response=True
            """
            try:
                # Escape markdown if requested (recommended for user-generated content)
                safe_message = escape_markdown(message) if escape_markdown_chars else message
                
                # Send message to Telegram
                sent_message = await self.bot.send_message(
                    chat_id=self.authorized_chat_id,
                    text=safe_message,
                    parse_mode='Markdown'
                )
                
                # Add to conversation history
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'llm_to_human',
                    'message': message,
                    'message_id': sent_message.message_id
                })
                
                logger.info(f"Sent message to human: {message[:Constants.MAX_MESSAGE_PREVIEW]}...")
                
                if not wait_for_response:
                    return {
                        'sent': True,
                        'message_id': sent_message.message_id,
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Wait for human response using proper async pattern
                response_id = f"response_{sent_message.message_id}"
                try:
                    response = await self._wait_for_response(response_id, timeout_seconds)
                    return {
                        'sent': True,
                        'response': response,
                        'message_id': sent_message.message_id,
                        'timestamp': datetime.now().isoformat()
                    }
                except asyncio.TimeoutError:
                    return {
                        'sent': True,
                        'response': None,
                        'error': 'Response timeout',
                        'message_id': sent_message.message_id,
                        'timestamp': datetime.now().isoformat()
                    }
                
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                return {
                    'sent': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        @self.mcp.tool()
        async def get_conversation_history(limit: int = 10) -> dict:
            """
            Get recent conversation history between LLM and human.
            
            Args:
                limit: Maximum number of recent messages to return
            
            Returns:
                dict: Contains conversation history
            """
            # Convert deque to list for the response
            history_list = list(self.conversation_history)
            recent_history = history_list[-limit:] if limit > 0 else history_list
            return {
                'history': recent_history,
                'total_messages': len(self.conversation_history),
                'timestamp': datetime.now().isoformat()
            }
        
        @self.mcp.tool()
        async def clear_conversation_history() -> dict:
            """
            Clear the conversation history.
            
            Returns:
                dict: Confirmation of history clearing
            """
            self.conversation_history.clear()
            return {
                'cleared': True,
                'timestamp': datetime.now().isoformat()
            }

    async def _wait_for_response(self, response_id: str, timeout_seconds: int) -> str:
        """
        Wait for a response with proper async handling and cleanup.
        
        Args:
            response_id: Unique ID for the response
            timeout_seconds: Maximum time to wait
            
        Returns:
            The response text
            
        Raises:
            asyncio.TimeoutError: If timeout occurs
        """
        event = asyncio.Event()
        self.pending_responses[response_id] = {
            'waiting': True,
            'response': None,
            'timestamp': datetime.now().isoformat(),
            'event': event
        }
        
        try:
            # Wait for the event with timeout
            await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
            return self.pending_responses[response_id]['response']
        finally:
            # Always cleanup the pending response
            self.pending_responses.pop(response_id, None)

    async def handle_telegram_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram messages"""
        
        # Security check - only respond to authorized user
        if update.effective_chat.id != self.authorized_chat_id:
            logger.warning(f"Unauthorized access attempt from chat_id: {update.effective_chat.id}")
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        message_text = update.message.text
        message_id = update.message.message_id
        
        logger.info(f"Received message from human: {message_text[:Constants.MAX_MESSAGE_PREVIEW]}...")
        
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'human_to_llm',
            'message': message_text,
            'message_id': message_id
        })
        
        # Check if this is a response to a pending request
        # Look for any pending responses and fulfill the most recent one
        if self.pending_responses:
            # Get the most recent pending response
            latest_key = max(self.pending_responses.keys(), 
                           key=lambda x: self.pending_responses[x]['timestamp'])
            
            if self.pending_responses[latest_key]['waiting']:
                self.pending_responses[latest_key]['response'] = message_text
                self.pending_responses[latest_key]['waiting'] = False
                
                # Trigger the event to wake up the waiting coroutine
                if 'event' in self.pending_responses[latest_key]:
                    self.pending_responses[latest_key]['event'].set()
                
                # Send confirmation
                await update.message.reply_text("✅ Response received and forwarded to LLM")
                return
        
        # If no pending response, this is an unsolicited message
        # You could implement additional logic here, like storing unsolicited messages
        # or sending them to the LLM proactively
        await update.message.reply_text("📝 Message noted. Waiting for LLM to request next interaction.")

    async def start_telegram_bot(self):
        """Start the Telegram bot"""
        try:
            self.telegram_app = Application.builder().token(self.bot_token).build()
            
            # Add message handler
            self.telegram_app.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_telegram_message)
            )
            
            # Start the bot
            await self.telegram_app.initialize()
            await self.telegram_app.start()
            await self.telegram_app.updater.start_polling()
            
            logger.info("Telegram bot started successfully")
            
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
            raise

    async def stop_telegram_bot(self):
        """Stop the Telegram bot"""
        if self.telegram_app:
            await self.telegram_app.updater.stop()
            await self.telegram_app.stop()
            await self.telegram_app.shutdown()

    async def shutdown_handler(self):
        """Handle graceful shutdown"""
        logger.info("Initiating graceful shutdown...")
        self._shutdown_event.set()
        
        # Cancel all pending responses
        for response_id, response_data in list(self.pending_responses.items()):
            if 'event' in response_data:
                response_data['event'].set()
        
        # Stop the Telegram bot
        await self.stop_telegram_bot()
        
        logger.info("Graceful shutdown complete")

    @asynccontextmanager
    async def run_server(self):
        """Context manager to run both MCP and Telegram services"""
        try:
            # Start Telegram bot
            await self.start_telegram_bot()
            
            # Yield control to the MCP server
            yield self
            
        finally:
            # Cleanup
            await self.stop_telegram_bot()

async def async_main():
    """Async main function to run both Telegram bot and MCP server"""
    
    # Validate configuration
    is_valid, errors = settings.validate()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    # Create directories
    settings.create_directories()
    
    # Log startup info
    logger.info("Starting Telegram MCP Server")
    logger.info(f"Server name: {settings.MCP_SERVER_NAME}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Chat ID: {settings.TELEGRAM_CHAT_ID}")
    
    # Create server instance
    server = TelegramMCPServer(
        settings.TELEGRAM_BOT_TOKEN, 
        int(settings.TELEGRAM_CHAT_ID)
    )
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        asyncio.create_task(server.shutdown_handler())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    # Start Telegram bot in background task
    telegram_task = None
    try:
        # Start the Telegram bot as a background task
        telegram_task = asyncio.create_task(server.start_telegram_bot())
        
        # Give the bot a moment to initialize
        await asyncio.sleep(Constants.BOT_STARTUP_DELAY)
        
        # Check if telegram bot started successfully
        if telegram_task.done() and telegram_task.exception():
            raise telegram_task.exception()
        
        logger.info("Telegram bot started, running MCP server...")
        
        # Run the MCP server (this will handle stdio)
        # Note: FastMCP's run() method needs to be called from sync context
        # So we'll use run_in_executor to bridge the gap
        await loop.run_in_executor(None, server.mcp.run, "stdio")
        
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        # Cleanup
        if telegram_task and not telegram_task.done():
            telegram_task.cancel()
            try:
                await telegram_task
            except asyncio.CancelledError:
                pass
        await server.stop_telegram_bot()


def main():
    """Main entry point - sets up async event loop"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
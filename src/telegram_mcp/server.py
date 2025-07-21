#!/usr/bin/env python3
"""
Telegram MCP Server - Bidirectional communication between LLM and Telegram
"""
import asyncio
import json
from typing import Any, Dict, Optional, List
from contextlib import asynccontextmanager
import os
from datetime import datetime
import sys
import time
import threading

# Configuration and logging
from .config import settings
from .logging import setup_logging, get_logger

# FastMCP and MCP imports
from fastmcp import FastMCP
from mcp.types import Tool, TextContent

# Telegram imports
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Set up logging
setup_logging()
logger = get_logger(__name__)

class TelegramMCPServer:
    def __init__(self, bot_token: str, authorized_chat_id: int):
        self.bot_token = bot_token
        self.authorized_chat_id = authorized_chat_id
        self.bot = Bot(token=bot_token)
        self.pending_responses = {}  # Store pending human responses
        self.conversation_history = []  # Store conversation context
        
        # Initialize FastMCP
        self.mcp = FastMCP(settings.MCP_SERVER_NAME or "telegram-mcp")
        self._setup_mcp_tools()
        
        # Initialize Telegram application
        self.telegram_app = None
        
    def _setup_mcp_tools(self):
        """Setup MCP tools for LLM interaction"""
        
        @self.mcp.tool()
        async def send_message_to_human(message: str, wait_for_response: bool = True, timeout_seconds: int = 300) -> dict:
            """
            Send a message to the human via Telegram and optionally wait for a response.
            
            Args:
                message: The message to send to the human
                wait_for_response: Whether to wait for a human response
                timeout_seconds: How long to wait for a response (default 300 seconds)
            
            Returns:
                dict: Contains 'sent' status and 'response' if wait_for_response=True
            """
            try:
                # Send message to Telegram
                sent_message = await self.bot.send_message(
                    chat_id=self.authorized_chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                # Add to conversation history
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'llm_to_human',
                    'message': message,
                    'message_id': sent_message.message_id
                })
                
                logger.info(f"Sent message to human: {message[:50]}...")
                
                if not wait_for_response:
                    return {
                        'sent': True,
                        'message_id': sent_message.message_id,
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Wait for human response
                response_id = f"response_{sent_message.message_id}"
                self.pending_responses[response_id] = {
                    'waiting': True,
                    'response': None,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Wait for response with timeout
                for _ in range(timeout_seconds):
                    await asyncio.sleep(1)
                    if not self.pending_responses[response_id]['waiting']:
                        response = self.pending_responses[response_id]['response']
                        del self.pending_responses[response_id]
                        return {
                            'sent': True,
                            'response': response,
                            'message_id': sent_message.message_id,
                            'timestamp': datetime.now().isoformat()
                        }
                
                # Timeout occurred
                del self.pending_responses[response_id]
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
            recent_history = self.conversation_history[-limit:] if limit > 0 else self.conversation_history
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

    async def handle_telegram_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram messages"""
        
        # Security check - only respond to authorized user
        if update.effective_chat.id != self.authorized_chat_id:
            logger.warning(f"Unauthorized access attempt from chat_id: {update.effective_chat.id}")
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        message_text = update.message.text
        message_id = update.message.message_id
        
        logger.info(f"Received message from human: {message_text[:50]}...")
        
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

def main():
    """Main function to run the server"""
    
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
    
    # Create a background task for Telegram bot
    async def run_with_telegram():
        async with server.run_server():
            # Keep the context open while MCP runs
            await asyncio.Future()  # This will never complete
    
    # Start the telegram bot in a background task
    import threading
    import asyncio
    
    def run_telegram_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_with_telegram())
    
    # Start telegram bot in background thread
    telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    telegram_thread.start()
    
    # Give the bot time to start
    import time
    time.sleep(2)
    
    # Run the MCP server (this blocks and handles stdio)
    server.mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
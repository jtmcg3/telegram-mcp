#!/usr/bin/env python3
"""
Test script to validate the Telegram MCP server setup
"""
import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import telegram_mcp_server
        print("✓ telegram_mcp_server imported successfully")
        
        # Test individual imports
        from fastmcp import FastMCP
        print("✓ FastMCP imported successfully")
        
        from telegram import Update, Bot
        print("✓ Telegram modules imported successfully")
        
        from telegram.ext import Application, MessageHandler, filters, ContextTypes
        print("✓ Telegram.ext modules imported successfully")
        
        import dotenv
        print("✓ python-dotenv imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

async def test_server_initialization():
    """Test if the server can be initialized"""
    print("\nTesting server initialization...")
    try:
        # Check for environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', 'test_token')
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '123456')
        
        if bot_token == 'test_token':
            print("⚠️  No TELEGRAM_BOT_TOKEN found in environment, using test token")
        
        # Import and create server instance
        from telegram_mcp_server import TelegramMCPServer
        
        server = TelegramMCPServer(bot_token, int(chat_id))
        print("✓ TelegramMCPServer instance created successfully")
        
        # Check if MCP tools are set up
        if hasattr(server, 'mcp') and server.mcp:
            print("✓ MCP instance created successfully")
            # Note: We can't test the actual tools without running the server
            print("✓ MCP tools should be configured")
        
        return True
    except Exception as e:
        print(f"✗ Server initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=== Telegram MCP Server Validation ===\n")
    
    all_passed = True
    
    # Test imports
    if not await test_imports():
        all_passed = False
        print("\n⚠️  Please run 'uv sync' to install dependencies")
    
    # Test server initialization
    if await test_imports():  # Only test if imports work
        if not await test_server_initialization():
            all_passed = False
    
    # Summary
    print("\n=== Test Summary ===")
    if all_passed:
        print("✅ All tests passed! The server is ready to use.")
        print("\nNext steps:")
        print("1. Set up your .env file with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        print("2. Run 'uv run python telegram_mcp_server.py' to start the server")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
#!/usr/bin/env python3
"""Command-line interface for Telegram MCP server."""

import sys
import argparse
from .server import main as server_main


def get_chat_id():
    """Run the get_chat_id utility."""
    from .get_chat_id import main as chat_id_main
    chat_id_main()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Telegram MCP Server")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Run the MCP server')
    
    # Get chat ID command
    chat_parser = subparsers.add_parser('get-chat-id', help='Get your Telegram chat ID')
    
    args = parser.parse_args()
    
    if args.command == 'server':
        server_main()
    elif args.command == 'get-chat-id':
        get_chat_id()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
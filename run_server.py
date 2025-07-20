#!/usr/bin/env python3
"""
Wrapper script to run the MCP server with proper stdio handling
"""
import subprocess
import sys
import os
import time
import signal

def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    sys.exit(0)

def main():
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting Telegram MCP Server...")
    print("The server is now running and ready to accept MCP connections.")
    print("It will respond to messages sent to your Telegram bot.")
    print("\nPress Ctrl+C to stop the server.")
    
    # Run the actual MCP server
    try:
        # Start the server process
        process = subprocess.Popen(
            [sys.executable, "telegram_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Keep the process running
        while True:
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated
                stdout, stderr = process.communicate()
                if stdout:
                    print("Server output:", stdout)
                if stderr:
                    print("Server error:", stderr, file=sys.stderr)
                break
            
            # Sleep briefly to avoid busy waiting
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        process.terminate()
        process.wait()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    main()
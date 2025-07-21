#!/usr/bin/env python3
"""
Example LLM integration with the Telegram MCP Server
This shows how your local LLM would interact with the MCP server
"""
import asyncio
import json
from typing import Dict, Any
import subprocess
import sys

class MCPClient:
    """Simple MCP client to communicate with the Telegram bridge"""
    
    def __init__(self, mcp_server_command: list):
        self.mcp_server_command = mcp_server_command
        self.process = None
        
    async def start(self):
        """Start the MCP server process"""
        self.process = await asyncio.create_subprocess_exec(
            *self.mcp_server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Initialize MCP connection
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "LLM Client",
                    "version": "1.0.0"
                }
            }
        }
        
        await self._send_request(init_request)
        
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server"""
        if not self.process:
            raise RuntimeError("MCP server not started")
            
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        if response_line:
            return json.loads(response_line.decode().strip())
        else:
            raise RuntimeError("No response from MCP server")
    
    async def send_message_to_human(self, message: str, wait_for_response: bool = True, timeout_seconds: int = 300) -> Dict[str, Any]:
        """Send a message to human via Telegram"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "send_message_to_human",
                "arguments": {
                    "message": message,
                    "wait_for_response": wait_for_response,
                    "timeout_seconds": timeout_seconds
                }
            }
        }
        
        return await self._send_request(request)
    
    async def get_conversation_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get conversation history"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_conversation_history",
                "arguments": {
                    "limit": limit
                }
            }
        }
        
        return await self._send_request(request)
    
    async def stop(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

class LLMAssistant:
    """Example LLM assistant that uses Telegram for human interaction"""
    
    def __init__(self):
        self.mcp_client = MCPClient([
            "python", "telegram_mcp_server.py"
        ])
        
    async def start(self):
        """Start the assistant"""
        await self.mcp_client.start()
        print("LLM Assistant started with Telegram integration!")
        
    async def ask_human_question(self, question: str) -> str:
        """Ask the human a question and wait for response"""
        print(f"Asking human: {question}")
        
        response = await self.mcp_client.send_message_to_human(
            message=f"🤖 **LLM Question:**\n\n{question}",
            wait_for_response=True,
            timeout_seconds=300
        )
        
        if response.get('result', {}).get('response'):
            human_response = response['result']['response']
            print(f"Human responded: {human_response}")
            return human_response
        else:
            print("No response received from human")
            return "No response received"
    
    async def notify_human(self, message: str):
        """Send a notification to human without waiting for response"""
        print(f"Notifying human: {message}")
        
        await self.mcp_client.send_message_to_human(
            message=f"📢 **LLM Notification:**\n\n{message}",
            wait_for_response=False
        )
    
    async def interactive_session(self):
        """Run an interactive session with the human"""
        print("Starting interactive session...")
        
        # Greet the human
        await self.notify_human("Hello! I'm your LLM assistant. I can now communicate with you via Telegram!")
        
        # Ask some questions
        name = await self.ask_human_question("What's your name?")
        
        if name and name != "No response received":
            await self.notify_human(f"Nice to meet you, {name}!")
            
            # Ask about a task
            task = await self.ask_human_question(
                "What would you like me to help you with today? Please describe a task or question."
            )
            
            if task and task != "No response received":
                # Simulate thinking/processing
                await self.notify_human("🤔 Let me think about that...")
                await asyncio.sleep(2)  # Simulate processing time
                
                # Provide a response
                await self.notify_human(
                    f"Based on your request: '{task}'\n\n"
                    "I understand you want help with that. While I can't actually perform "
                    "the task right now (this is just a demo), I can communicate with you "
                    "through Telegram to ask clarifying questions, provide updates, and "
                    "get your feedback throughout the process."
                )
                
                # Ask for confirmation
                confirmation = await self.ask_human_question(
                    "Does this communication method work well for you? "
                    "Should I proceed with this type of interaction?"
                )
                
                if confirmation:
                    await self.notify_human("Great! The Telegram integration is working perfectly. 🎉")
    
    async def get_conversation_summary(self):
        """Get and display conversation history"""
        history_response = await self.mcp_client.get_conversation_history(limit=20)
        
        if 'result' in history_response:
            history = history_response['result']['history']
            print(f"\n--- Conversation History ({len(history)} messages) ---")
            
            for msg in history:
                msg_type = "🤖 LLM" if msg['type'] == 'llm_to_human' else "👤 Human"
                timestamp = msg['timestamp']
                message = msg['message'][:100] + "..." if len(msg['message']) > 100 else msg['message']
                print(f"[{timestamp}] {msg_type}: {message}")
    
    async def stop(self):
        """Stop the assistant"""
        await self.mcp_client.stop()
        print("LLM Assistant stopped")

async def main():
    """Main demo function"""
    assistant = LLMAssistant()
    
    try:
        await assistant.start()
        
        # Run interactive session
        await assistant.interactive_session()
        
        # Show conversation history
        await assistant.get_conversation_summary()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await assistant.stop()

if __name__ == "__main__":
    print("LLM Assistant with Telegram Integration Demo")
    print("=" * 50)
    print("Make sure your Telegram MCP server is configured and ready!")
    print("This demo will:")
    print("1. Connect to the Telegram MCP server")
    print("2. Send messages to you via Telegram")
    print("3. Wait for your responses")
    print("4. Show the conversation history")
    print("=" * 50)
    
    asyncio.run(main())
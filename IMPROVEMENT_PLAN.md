# Telegram MCP Server - Improvement Plan

## Executive Summary

This document outlines critical improvements needed for the telegram-mcp server based on a comprehensive code review. The codebase has a solid foundation but requires production-hardening in security, performance, and reliability areas.

## Critical Issues (Priority 1)

### 1. Threading + Asyncio Anti-pattern

**Issue**: The current implementation creates a new event loop in a separate thread, which violates asyncio best practices.

**Current Code** (server.py:274-292):
```python
def run_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_with_telegram())

telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
telegram_thread.start()
```

**Solution**:
```python
async def main():
    server = TelegramMCPServer(settings.TELEGRAM_BOT_TOKEN, int(settings.TELEGRAM_CHAT_ID))
    
    # Create background task for telegram bot
    telegram_task = asyncio.create_task(server.run_server())
    
    # Run MCP server with proper async context
    try:
        await server.mcp.run_async(transport="stdio")
    finally:
        telegram_task.cancel()
        await telegram_task
```

**Reasoning**: Using `asyncio.create_task()` keeps everything in the same event loop, preventing race conditions and simplifying the architecture.

### 2. Security: Environment File in Docker Image

**Issue**: The Dockerfile copies .env files into the image (line 23), embedding secrets in image layers.

**Current Code** (Dockerfile:23):
```dockerfile
COPY .env* /app/
```

**Solution**: Remove this line entirely. Use docker-compose volume mounts or Docker secrets:
```dockerfile
# Remove the COPY .env line
# Use volume mounts in docker-compose.yml instead
```

**Reasoning**: Docker images are often pushed to registries. Embedded secrets can be extracted from image layers even if deleted in later layers.

### 3. Memory Leak in Pending Responses

**Issue**: If an exception occurs between adding and removing from `pending_responses`, entries remain forever.

**Current Code** (server.py:89-110):
```python
self.pending_responses[response_id] = {...}
# If exception here, entry never removed
for _ in range(timeout_seconds):
    await asyncio.sleep(1)
    # ...
del self.pending_responses[response_id]
```

**Solution**:
```python
async def wait_for_response(self, response_id: str, timeout: int):
    try:
        self.pending_responses[response_id] = {
            'waiting': True,
            'response': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Use asyncio.wait_for with proper timeout
        return await asyncio.wait_for(
            self._wait_for_response_impl(response_id),
            timeout=timeout
        )
    finally:
        # Always cleanup
        self.pending_responses.pop(response_id, None)
```

## Security Improvements (Priority 2)

### 4. Markdown Injection Prevention

**Issue**: User input sent via Telegram with `parse_mode='Markdown'` without sanitization.

**Solution**:
```python
def escape_markdown(text: str) -> str:
    """Escape special markdown characters"""
    special_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Usage in send_message_to_human:
safe_message = escape_markdown(message) if contains_user_input else message
sent_message = await self.bot.send_message(
    chat_id=self.authorized_chat_id,
    text=safe_message,
    parse_mode='Markdown'
)
```

### 5. Input Validation Enhancement

**Issue**: Chat ID validation happens after settings are loaded.

**Solution** (config.py):
```python
@classmethod
def validate(cls) -> tuple[bool, list[str]]:
    errors = []
    
    # Validate and convert chat_id early
    if not cls.TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID is required")
    else:
        try:
            cls._validated_chat_id = int(cls.TELEGRAM_CHAT_ID)
        except ValueError:
            errors.append("TELEGRAM_CHAT_ID must be a valid integer")
    
    # ... rest of validation
```

## Performance Optimizations (Priority 3)

### 6. Efficient Timeout Handling

**Issue**: Using a loop with `asyncio.sleep(1)` is inefficient.

**Solution**:
```python
async def _wait_for_response_impl(self, response_id: str):
    """Wait for response using asyncio primitives"""
    event = asyncio.Event()
    self.pending_responses[response_id]['event'] = event
    
    await event.wait()
    return self.pending_responses[response_id]['response']

# In handle_telegram_message:
if self.pending_responses[latest_key]['waiting']:
    self.pending_responses[latest_key]['response'] = message_text
    self.pending_responses[latest_key]['event'].set()  # Wake up waiter
```

### 7. Bounded Conversation History

**Issue**: `conversation_history` list grows unbounded.

**Solution**:
```python
from collections import deque

class TelegramMCPServer:
    def __init__(self, bot_token: str, authorized_chat_id: int, max_history: int = 1000):
        # ...
        self.conversation_history = deque(maxlen=max_history)
```

## Reliability Improvements (Priority 4)

### 8. Connection Retry Logic

**Solution**:
```python
async def start_telegram_bot_with_retry(self, max_retries: int = 5):
    """Start Telegram bot with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            await self.start_telegram_bot()
            return
        except Exception as e:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.error(f"Failed to start bot (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                raise
```

### 9. Graceful Shutdown

**Solution**:
```python
import signal

class TelegramMCPServer:
    def __init__(self, ...):
        # ...
        self._shutdown_event = asyncio.Event()
        
    async def shutdown_handler(self):
        """Handle graceful shutdown"""
        logger.info("Shutting down gracefully...")
        self._shutdown_event.set()
        
        # Close pending responses
        for response_id in list(self.pending_responses.keys()):
            if 'event' in self.pending_responses[response_id]:
                self.pending_responses[response_id]['event'].set()
        
        await self.stop_telegram_bot()

# In main():
loop = asyncio.get_event_loop()
for sig in (signal.SIGTERM, signal.SIGINT):
    loop.add_signal_handler(sig, lambda: asyncio.create_task(server.shutdown_handler()))
```

### 10. Health Check Endpoint

**Solution**:
```python
from aiohttp import web

async def health_check(request):
    """Health check endpoint for monitoring"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_connected': server.telegram_app is not None and server.telegram_app.running,
        'pending_responses': len(server.pending_responses),
        'history_size': len(server.conversation_history)
    }
    return web.json_response(status)

# Add to server startup if ENABLE_HEALTH_CHECK is True
```

## Quick Wins

1. **Add Version Info**:
```python
# In __init__.py
__version__ = "0.1.0"
```

2. **Remove Duplicate Imports**:
- Remove duplicate asyncio import on line 276

3. **Add Type Hints**:
```python
from typing import Dict, Optional, List, Any

async def send_message_to_human(
    self, 
    message: str, 
    wait_for_response: bool = True, 
    timeout_seconds: int = 300
) -> Dict[str, Any]:
```

4. **Extract Magic Numbers**:
```python
class Constants:
    DEFAULT_TIMEOUT = 300
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    MAX_MESSAGE_PREVIEW = 50
```

5. **Add Integration Tests**:
```python
# tests/test_integration.py
import pytest
from telegram_mcp.server import TelegramMCPServer

@pytest.mark.asyncio
async def test_message_roundtrip():
    # Test sending and receiving messages
    pass
```

## Implementation Priority

1. **Week 1**: Fix threading issue and remove .env from Docker
2. **Week 2**: Implement security fixes (markdown escaping, validation)
3. **Week 3**: Add memory leak fixes and performance improvements
4. **Week 4**: Implement reliability features (retry, graceful shutdown)
5. **Week 5**: Add monitoring and quick wins

## Testing Strategy

1. Unit tests for all new utility functions
2. Integration tests for message flow
3. Load testing for memory leak verification
4. Security testing for injection vulnerabilities
5. Docker health check validation

## Monitoring Recommendations

1. Log aggregation with structured JSON logs
2. Metrics for message latency and volume
3. Alerts for connection failures
4. Dashboard for pending responses and history size

## Conclusion

The telegram-mcp server has a solid foundation but needs production hardening. Focus on the critical threading and security issues first, then systematically work through performance and reliability improvements. The suggested changes will make the service more robust, secure, and maintainable.
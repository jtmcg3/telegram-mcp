"""
Configuration settings for Telegram MCP Server
"""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Central configuration for the Telegram MCP Server"""
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Server Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Timeout Configuration
    DEFAULT_RESPONSE_TIMEOUT: int = int(os.getenv('DEFAULT_RESPONSE_TIMEOUT', '300'))
    
    # Directory Configuration
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / 'data'
    LOGS_DIR: Path = BASE_DIR / 'logs'
    CONFIG_DIR: Path = BASE_DIR / 'config'
    
    # MCP Configuration
    MCP_SERVER_NAME: str = os.getenv('MCP_SERVER_NAME', 'Telegram Bridge')
    
    # Optional Features
    ENABLE_HEALTH_CHECK: bool = os.getenv('ENABLE_HEALTH_CHECK', 'true').lower() == 'true'
    HEALTH_CHECK_PORT: int = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate required settings
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID is required")
        
        try:
            int(cls.TELEGRAM_CHAT_ID)
        except ValueError:
            errors.append("TELEGRAM_CHAT_ID must be a valid integer")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if cls.LOG_LEVEL.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.CONFIG_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_log_file_path(cls) -> Path:
        """Get the path for the log file"""
        return cls.LOGS_DIR / 'telegram_mcp.log'
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert settings to dictionary (hiding sensitive values)"""
        return {
            'TELEGRAM_BOT_TOKEN': '***' if cls.TELEGRAM_BOT_TOKEN else 'NOT SET',
            'TELEGRAM_CHAT_ID': cls.TELEGRAM_CHAT_ID if cls.TELEGRAM_CHAT_ID else 'NOT SET',
            'LOG_LEVEL': cls.LOG_LEVEL,
            'DEFAULT_RESPONSE_TIMEOUT': cls.DEFAULT_RESPONSE_TIMEOUT,
            'MCP_SERVER_NAME': cls.MCP_SERVER_NAME,
            'ENABLE_HEALTH_CHECK': cls.ENABLE_HEALTH_CHECK,
            'HEALTH_CHECK_PORT': cls.HEALTH_CHECK_PORT,
            'BASE_DIR': str(cls.BASE_DIR),
            'DATA_DIR': str(cls.DATA_DIR),
            'LOGS_DIR': str(cls.LOGS_DIR),
            'CONFIG_DIR': str(cls.CONFIG_DIR),
        }

# Create a singleton instance
settings = Settings()
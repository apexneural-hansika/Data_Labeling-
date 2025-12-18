"""
Enhanced configuration management with environment support
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class EnhancedConfig:
    """Enhanced application configuration with environment support."""
    
    # Environment
    ENV = os.getenv('ENV', 'development')  # development, staging, production
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    OPENAI_DIRECT_API_KEY: Optional[str] = os.getenv('OPENAI_DIRECT_API_KEY', os.getenv('OPENAI_API_KEY'))
    DEEPSEEK_API_KEY: Optional[str] = os.getenv('DEEPSEEK_API_KEY')
    
    # OpenRouter Configuration
    USE_OPENROUTER: bool = os.getenv('USE_OPENROUTER', 'false').lower() == 'true'
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB default
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/system.log')
    ENABLE_CONSOLE_LOGGING = os.getenv('ENABLE_CONSOLE_LOGGING', 'true').lower() == 'true'
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 10))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))  # seconds
    
    # Background Tasks
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 3))
    TASK_TIMEOUT = float(os.getenv('TASK_TIMEOUT', 600.0))  # 10 minutes
    
    # Resource Management
    CLEANUP_INTERVAL_MINUTES = int(os.getenv('CLEANUP_INTERVAL_MINUTES', 60))
    FILE_MAX_AGE_HOURS = int(os.getenv('FILE_MAX_AGE_HOURS', 24))
    
    # Timeout Settings
    DEFAULT_TIMEOUT = float(os.getenv('DEFAULT_TIMEOUT', 300.0))  # 5 minutes
    API_TIMEOUT = float(os.getenv('API_TIMEOUT', 60.0))  # 1 minute
    
    @classmethod
    def get_model_name(cls, base_model: str) -> str:
        """Get the correct model name based on provider."""
        if cls.USE_OPENROUTER:
            model_map = {
                'gpt-4o-mini': 'openai/gpt-4o-mini',
                'gpt-4o': 'openai/gpt-4o',
                'whisper-1': 'openai/whisper-1'
            }
            return model_map.get(base_model, base_model)
        return base_model
    
    @classmethod
    def get_base_url(cls) -> Optional[str]:
        """Get the base URL for API client."""
        return cls.OPENROUTER_BASE_URL if cls.USE_OPENROUTER else None
    
    @classmethod
    def get_openai_key_for_whisper(cls) -> Optional[str]:
        """Get the appropriate OpenAI API key for Whisper."""
        if cls.OPENAI_DIRECT_API_KEY and cls.OPENAI_DIRECT_API_KEY != cls.OPENAI_API_KEY:
            return cls.OPENAI_DIRECT_API_KEY
        
        if cls.OPENAI_API_KEY:
            if not cls.OPENAI_API_KEY.startswith('sk-or-'):
                return cls.OPENAI_API_KEY
        
        return cls.OPENAI_DIRECT_API_KEY
    
    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            return False, "OPENAI_API_KEY is not set. Please set it as an environment variable or in config.py"
        return True, None
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production."""
        return cls.ENV == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development."""
        return cls.ENV == 'development'


# Import Config from original file for backward compatibility
try:
    from config import Config
except ImportError:
    # Fallback to EnhancedConfig
    Config = EnhancedConfig





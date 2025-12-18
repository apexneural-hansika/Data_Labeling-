"""
Configuration file for API keys and settings
"""
import os
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Application configuration."""
    
    # API Keys - Loaded from .env file, environment variables, or can be set directly
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    # Separate OpenAI key for Whisper (if using OpenRouter for other models)
    # Falls back to OPENAI_API_KEY if not set
    OPENAI_DIRECT_API_KEY: Optional[str] = os.getenv('OPENAI_DIRECT_API_KEY', os.getenv('OPENAI_API_KEY'))
    DEEPSEEK_API_KEY: Optional[str] = os.getenv('DEEPSEEK_API_KEY')
    
    # OpenRouter Configuration
    USE_OPENROUTER: bool = os.getenv('USE_OPENROUTER', 'false').lower() == 'true'
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Model names - Use OpenRouter format if enabled, otherwise OpenAI format
    @classmethod
    def get_model_name(cls, base_model: str) -> str:
        """Get the correct model name based on provider."""
        if cls.USE_OPENROUTER:
            # OpenRouter model names
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
    
    # Alternative: Set API keys directly here (not recommended for production)
    # OPENAI_API_KEY = "your-openai-api-key-here"
    # DEEPSEEK_API_KEY = "your-deepseek-api-key-here"
    
    # Database Configuration (Supabase PostgreSQL with pgvector)
    SUPABASE_DB_URL: Optional[str] = os.getenv(
        'SUPABASE_DB_URL',
        'postgresql://postgres.saynendmovtnshkdtyei:hansika123@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres'
    )
    ENABLE_EMBEDDING_STORAGE: bool = os.getenv('ENABLE_EMBEDDING_STORAGE', 'true').lower() == 'true'
    
    # Embedding Provider Configuration
    EMBEDDING_PROVIDER: str = os.getenv('EMBEDDING_PROVIDER', 'auto').lower()
    # Options: 'auto' (try HuggingFace first, fallback to OpenAI), 'huggingface', 'openai'
    HUGGINGFACE_MODEL: str = os.getenv('HUGGINGFACE_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    # Popular models:
    # - sentence-transformers/all-MiniLM-L6-v2 (384 dim, fast, good quality) [DEFAULT]
    # - sentence-transformers/all-MiniLM-L12-v2 (384 dim, better quality)
    # - sentence-transformers/all-mpnet-base-v2 (768 dim, best quality, slower)
    
    # Guardrails Configuration
    ENABLE_GUARDRAILS: bool = os.getenv('ENABLE_GUARDRAILS', 'true').lower() == 'true'
    ENABLE_CONTENT_FILTER: bool = os.getenv('ENABLE_CONTENT_FILTER', 'true').lower() == 'true'
    ENABLE_PII_DETECTION: bool = os.getenv('ENABLE_PII_DETECTION', 'true').lower() == 'true'
    ENABLE_CATEGORY_RESTRICTIONS: bool = os.getenv('ENABLE_CATEGORY_RESTRICTIONS', 'false').lower() == 'true'
    MIN_QUALITY_THRESHOLD: float = float(os.getenv('MIN_QUALITY_THRESHOLD', '0.6'))
    BLOCKED_CATEGORIES: List[str] = [
        cat.strip() for cat in os.getenv('BLOCKED_CATEGORIES', '').split(',')
        if cat.strip()
    ] if os.getenv('BLOCKED_CATEGORIES') else []
    ALLOWED_CATEGORIES: List[str] = [
        cat.strip() for cat in os.getenv('ALLOWED_CATEGORIES', '').split(',')
        if cat.strip()
    ] if os.getenv('ALLOWED_CATEGORIES') else []
    
    # Caching Configuration
    ENABLE_CACHING: bool = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    ENABLE_MEMORY_CACHE: bool = os.getenv('ENABLE_MEMORY_CACHE', 'true').lower() == 'true'
    ENABLE_DB_CACHE: bool = os.getenv('ENABLE_DB_CACHE', 'true').lower() == 'true'
    MEMORY_CACHE_SIZE: int = int(os.getenv('MEMORY_CACHE_SIZE', '100'))
    MEMORY_CACHE_TTL: int = int(os.getenv('MEMORY_CACHE_TTL', '3600'))  # 1 hour default
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    @classmethod
    def get_openai_key_for_whisper(cls) -> Optional[str]:
        """
        Get the appropriate OpenAI API key for Whisper.
        Uses OPENAI_DIRECT_API_KEY if set, otherwise checks if OPENAI_API_KEY is a valid OpenAI key.
        
        Returns:
            OpenAI API key for Whisper, or None if not available
        """
        # If OPENAI_DIRECT_API_KEY is explicitly set and different from OPENAI_API_KEY, use it
        if cls.OPENAI_DIRECT_API_KEY and cls.OPENAI_DIRECT_API_KEY != cls.OPENAI_API_KEY:
            return cls.OPENAI_DIRECT_API_KEY
        
        # Check if OPENAI_API_KEY is a valid OpenAI key (not OpenRouter)
        if cls.OPENAI_API_KEY:
            # OpenRouter keys start with 'sk-or-', OpenAI keys start with 'sk-'
            if not cls.OPENAI_API_KEY.startswith('sk-or-'):
                return cls.OPENAI_API_KEY
        
        # Return OPENAI_DIRECT_API_KEY as fallback (which defaults to OPENAI_API_KEY)
        return cls.OPENAI_DIRECT_API_KEY
    
    @classmethod
    def get_openai_key_for_embeddings(cls) -> Optional[str]:
        """
        Get the appropriate OpenAI API key for embeddings.
        Embeddings require a direct OpenAI API key (not OpenRouter).
        Uses OPENAI_DIRECT_API_KEY if set, otherwise checks if OPENAI_API_KEY is a valid OpenAI key.
        
        Returns:
            OpenAI API key for embeddings, or None if not available
        """
        # Use the same logic as Whisper - embeddings also need direct OpenAI API
        return cls.get_openai_key_for_whisper()
    
    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validate that required configuration is present.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cls.OPENAI_API_KEY:
            return False, "OPENAI_API_KEY is not set. Please set it as an environment variable or in config.py"
        return True, None


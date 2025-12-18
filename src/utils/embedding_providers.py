"""
Embedding providers - Support for multiple embedding generation methods
"""
import os
from typing import Optional, List
from utils.logger import get_system_logger

logger = get_system_logger()


class EmbeddingProvider:
    """Base class for embedding providers."""
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector or None if generation fails
        """
        raise NotImplementedError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
        """
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key) if api_key else None
        except ImportError:
            self.client = None
            logger.warning("OpenAI package not installed")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI."""
        if not self.client:
            logger.warning("OpenAI client not available")
            return None
        
        try:
            # Truncate text if too long
            max_length = 8000
            if len(text) > max_length:
                text = text[:max_length]
                logger.debug("Text truncated for embedding", original_length=len(text))
            
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug("OpenAI embedding generated", dim=len(embedding))
            return embedding
            
        except Exception as e:
            logger.error("OpenAI embedding generation failed", error=str(e))
            return None


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Hugging Face Sentence Transformers provider (free, local)."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize Hugging Face embedding provider.
        
        Args:
            model_name: Name of the Sentence Transformer model to use
                       Default: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
                       Alternatives:
                       - all-mpnet-base-v2 (768 dim, better quality, slower)
                       - all-MiniLM-L12-v2 (384 dim, better than L6)
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Sentence Transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading Sentence Transformer model", model=self.model_name)
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully", 
                       model=self.model_name,
                       max_seq_length=self.model.max_seq_length)
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.model = None
        except Exception as e:
            logger.error("Failed to load Sentence Transformer model", error=str(e))
            self.model = None
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Sentence Transformers."""
        if not self.model:
            logger.warning("Sentence Transformer model not loaded")
            return None
        
        try:
            # Sentence Transformers handle text length automatically
            # But we can truncate very long texts for efficiency
            max_length = 512  # Typical max for these models
            if len(text) > max_length * 4:  # Rough character estimate
                text = text[:max_length * 4]
                logger.debug("Text truncated for embedding", original_length=len(text))
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            
            # Convert numpy array to list
            embedding_list = embedding.tolist()
            
            logger.debug("HuggingFace embedding generated", 
                        dim=len(embedding_list),
                        model=self.model_name)
            return embedding_list
            
        except Exception as e:
            logger.error("HuggingFace embedding generation failed", error=str(e))
            return None


def create_embedding_provider(provider_type: str = "auto", **kwargs) -> Optional[EmbeddingProvider]:
    """
    Create an embedding provider based on configuration.
    
    Args:
        provider_type: Type of provider to use
                      - "openai": Use OpenAI API
                      - "huggingface": Use Hugging Face Sentence Transformers
                      - "auto": Try HuggingFace first, fallback to OpenAI
        **kwargs: Additional arguments for the provider
                 - api_key: For OpenAI provider
                 - model_name: For HuggingFace provider
    
    Returns:
        EmbeddingProvider instance or None if none available
    """
    if provider_type == "auto":
        # Try HuggingFace first (free, no API key needed)
        try:
            provider = HuggingFaceEmbeddingProvider(
                model_name=kwargs.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2')
            )
            if provider.model:
                logger.info("Using HuggingFace embedding provider (auto-selected)")
                return provider
        except Exception as e:
            logger.debug("HuggingFace provider not available", error=str(e))
        
        # Fallback to OpenAI if available
        api_key = kwargs.get('api_key')
        if api_key and not api_key.startswith('sk-or-'):
            try:
                provider = OpenAIEmbeddingProvider(api_key=api_key)
                if provider.client:
                    logger.info("Using OpenAI embedding provider (auto-selected)")
                    return provider
            except Exception as e:
                logger.debug("OpenAI provider not available", error=str(e))
        
        logger.warning("No embedding provider available in auto mode")
        return None
    
    elif provider_type == "huggingface":
        provider = HuggingFaceEmbeddingProvider(
            model_name=kwargs.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2')
        )
        if provider.model:
            logger.info("Using HuggingFace embedding provider")
            return provider
        return None
    
    elif provider_type == "openai":
        api_key = kwargs.get('api_key')
        provider = OpenAIEmbeddingProvider(api_key=api_key)
        if provider.client:
            logger.info("Using OpenAI embedding provider")
            return provider
        return None
    
    else:
        logger.error("Unknown embedding provider type", provider_type=provider_type)
        return None


def get_embedding_dimension(provider_type: str, model_name: Optional[str] = None) -> int:
    """
    Get the embedding dimension for a provider.
    
    Args:
        provider_type: Type of provider
        model_name: Model name (for HuggingFace)
    
    Returns:
        Embedding dimension
    """
    if provider_type == "openai":
        return 1536  # OpenAI text-embedding-ada-002
    elif provider_type == "huggingface":
        # Common Sentence Transformer dimensions
        if model_name and "mpnet" in model_name.lower():
            return 768
        elif model_name and "L12" in model_name:
            return 384
        else:
            return 384  # Default for all-MiniLM-L6-v2
    else:
        return 384  # Default


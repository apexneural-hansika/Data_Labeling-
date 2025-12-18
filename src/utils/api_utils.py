"""
API utility functions for retry logic and error handling
"""
import time
import random
from typing import Callable, Any, Optional, Dict
from functools import wraps


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    Decorator for retrying API calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on certain errors
                    error_str = str(e).lower()
                    if any(term in error_str for term in ['invalid', 'authentication', 'permission', 'forbidden']):
                        raise e
                    
                    # If this was the last attempt, raise the exception
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    time.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def handle_api_error(error: Exception) -> Dict[str, Any]:
    """
    Handle API errors and return a structured error response.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Dictionary with error information
    """
    error_str = str(error).lower()
    error_msg = str(error)
    
    error_type = 'unknown'
    retryable = True
    
    if 'quota' in error_str or 'insufficient' in error_str or 'rate limit' in error_str:
        error_type = 'quota_exceeded'
        retryable = False
    elif 'timeout' in error_str or 'timed out' in error_str:
        error_type = 'timeout'
        retryable = True
    elif 'invalid' in error_str or 'authentication' in error_str:
        error_type = 'authentication'
        retryable = False
    elif 'network' in error_str or 'connection' in error_str:
        error_type = 'network'
        retryable = True
    elif 'json' in error_str or 'parse' in error_str:
        error_type = 'parsing'
        retryable = True
    
    return {
        'error_type': error_type,
        'error_message': error_msg,
        'retryable': retryable
    }


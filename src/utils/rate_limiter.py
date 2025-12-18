"""
Rate limiting utilities for API endpoints
"""
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
from typing import Dict, Tuple
import time


class RateLimiter:
    """Simple in-memory rate limiter (can be replaced with Redis in production)."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        with self.lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Clean old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
            
            # Check limit
            if len(self.requests[identifier]) >= max_requests:
                reset_time = self.requests[identifier][0] + timedelta(seconds=window_seconds)
                return False, {
                    'allowed': False,
                    'limit': max_requests,
                    'remaining': 0,
                    'reset_at': reset_time.isoformat(),
                    'retry_after': int((reset_time - now).total_seconds())
                }
            
            # Add current request
            self.requests[identifier].append(now)
            
            return True, {
                'allowed': True,
                'limit': max_requests,
                'remaining': max_requests - len(self.requests[identifier]),
                'reset_at': (now + timedelta(seconds=window_seconds)).isoformat()
            }
    
    def get_client_identifier(self) -> str:
        """Get client identifier from request."""
        # Use IP address as identifier
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return request.remote_addr or 'unknown'


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Decorator for rate limiting Flask endpoints.
    
    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = _rate_limiter.get_client_identifier()
            allowed, info = _rate_limiter.is_allowed(
                identifier,
                max_requests=max_requests,
                window_seconds=window_seconds
            )
            
            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {max_requests} per {window_seconds}s',
                    'retry_after': info['retry_after']
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(int(time.time()) + window_seconds)
            
            return response
        
        return decorated_function
    return decorator





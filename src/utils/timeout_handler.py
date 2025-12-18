"""
Timeout handling utilities for API calls and long-running operations
"""
import signal
import threading
from typing import Callable, Any, Optional
from contextlib import contextmanager
from functools import wraps
import time


class TimeoutError(Exception):
    """Custom timeout exception."""
    pass


@contextmanager
def timeout_context(seconds: float):
    """
    Context manager for timeout handling.
    
    Args:
        seconds: Timeout in seconds
        
    Usage:
        with timeout_context(5.0):
            # code that might timeout
            pass
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set up signal handler (Unix only)
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(seconds))
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows fallback: use threading
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = True
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=seconds)
        
        if thread.is_alive():
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
        if exception[0]:
            raise exception[0]
        yield


def with_timeout(seconds: float, default_return: Any = None):
    """
    Decorator for adding timeout to functions.
    
    Args:
        seconds: Timeout in seconds
        default_return: Value to return on timeout
        
    Usage:
        @with_timeout(5.0, default_return=None)
        def my_function():
            # long running operation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            if hasattr(signal, 'SIGALRM'):
                # Unix: use signal
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"{func.__name__} timed out after {seconds} seconds")
                
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(seconds))
                try:
                    result = func(*args, **kwargs)
                    return result
                except TimeoutError:
                    if default_return is not None:
                        return default_return
                    raise
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Windows: use threading with result queue
                from queue import Queue
                result_queue = Queue()
                exception_queue = Queue()
                
                def target():
                    try:
                        result = func(*args, **kwargs)
                        result_queue.put(result)
                    except Exception as e:
                        exception_queue.put(e)
                
                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout=seconds)
                
                if thread.is_alive():
                    if default_return is not None:
                        return default_return
                    raise TimeoutError(f"{func.__name__} timed out after {seconds} seconds")
                
                if not exception_queue.empty():
                    raise exception_queue.get()
                
                if not result_queue.empty():
                    return result_queue.get()
                
                if default_return is not None:
                    return default_return
                raise TimeoutError(f"{func.__name__} completed but returned no result")
        
        return wrapper
    return decorator


class TimeoutManager:
    """Manager for handling timeouts in agentic operations."""
    
    def __init__(self, default_timeout: float = 300.0):
        """
        Initialize timeout manager.
        
        Args:
            default_timeout: Default timeout in seconds (5 minutes)
        """
        self.default_timeout = default_timeout
        self.timeouts: dict = {}
    
    def set_timeout(self, operation_id: str, timeout: float):
        """Set timeout for a specific operation."""
        self.timeouts[operation_id] = timeout
    
    def get_timeout(self, operation_id: str) -> float:
        """Get timeout for a specific operation."""
        return self.timeouts.get(operation_id, self.default_timeout)
    
    def execute_with_timeout(
        self,
        operation_id: str,
        func: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with timeout.
        
        Args:
            operation_id: Unique operation identifier
            func: Function to execute
            *args: Function arguments
            timeout: Optional timeout override
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        timeout = timeout or self.get_timeout(operation_id)
        return with_timeout(timeout)(func)(*args, **kwargs)


# Global timeout manager
_timeout_manager = TimeoutManager()


def get_timeout_manager() -> TimeoutManager:
    """Get global timeout manager instance."""
    return _timeout_manager





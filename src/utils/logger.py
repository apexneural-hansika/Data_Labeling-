"""
Structured logging system for the agentic AI platform
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path
import json


class StructuredLogger:
    """Structured logger with context support."""
    
    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        enable_console: bool = True
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            enable_console: Whether to log to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _log_with_context(self, level: str, message: str, **context):
        """Log with additional context."""
        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            full_message = f"{message} | {context_str}"
        else:
            full_message = message
        
        getattr(self.logger, level.lower())(full_message)
    
    def debug(self, message: str, **context):
        """Log debug message."""
        self._log_with_context("DEBUG", message, **context)
    
    def info(self, message: str, **context):
        """Log info message."""
        self._log_with_context("INFO", message, **context)
    
    def warning(self, message: str, **context):
        """Log warning message."""
        self._log_with_context("WARNING", message, **context)
    
    def error(self, message: str, **context):
        """Log error message."""
        self._log_with_context("ERROR", message, **context)
    
    def critical(self, message: str, **context):
        """Log critical message."""
        self._log_with_context("CRITICAL", message, **context)
    
    def exception(self, message: str, **context):
        """Log exception with traceback."""
        self._log_with_context("ERROR", message, exc_info=True, **context)


# Global logger instances
_system_logger: Optional[StructuredLogger] = None
_agent_logger: Optional[StructuredLogger] = None


def get_system_logger() -> StructuredLogger:
    """Get system logger instance."""
    global _system_logger
    if _system_logger is None:
        _system_logger = StructuredLogger(
            "system",
            log_level="INFO",
            log_file="logs/system.log",
            enable_console=True
        )
    return _system_logger


def get_agent_logger(agent_id: str) -> StructuredLogger:
    """Get agent-specific logger instance."""
    return StructuredLogger(
        f"agent.{agent_id}",
        log_level="INFO",
        log_file=f"logs/agents/{agent_id}.log",
        enable_console=True
    )


# Backward compatibility: print wrapper
def log_print(message: str, agent_id: Optional[str] = None, level: str = "INFO"):
    """
    Print wrapper for backward compatibility.
    Replaces print statements with structured logging.
    """
    if agent_id:
        logger = get_agent_logger(agent_id)
    else:
        logger = get_system_logger()
    
    getattr(logger, level.lower())(message)





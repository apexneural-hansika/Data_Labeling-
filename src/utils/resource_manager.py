"""
Resource management for file cleanup and resource tracking
"""
import os
import atexit
import weakref
from pathlib import Path
from typing import Set, Optional
from datetime import datetime, timedelta
from threading import Lock
from utils.logger import get_system_logger

logger = get_system_logger()


class ResourceManager:
    """Manages file resources and ensures cleanup."""
    
    def __init__(self, cleanup_interval_minutes: int = 60):
        """
        Initialize resource manager.
        
        Args:
            cleanup_interval_minutes: Interval for automatic cleanup
        """
        self.tracked_files: Set[str] = set()
        self.tracked_dirs: Set[str] = set()
        self.lock = Lock()
        self.cleanup_interval = cleanup_interval_minutes
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
    
    def track_file(self, file_path: str, auto_cleanup: bool = True):
        """
        Track a file for cleanup.
        
        Args:
            file_path: Path to file
            auto_cleanup: Whether to auto-cleanup on exit
        """
        with self.lock:
            self.tracked_files.add(file_path)
            logger.debug("Tracking file", file_path=file_path, auto_cleanup=auto_cleanup)
    
    def track_directory(self, dir_path: str, auto_cleanup: bool = False):
        """
        Track a directory (usually for monitoring, not cleanup).
        
        Args:
            dir_path: Path to directory
            auto_cleanup: Whether to auto-cleanup on exit
        """
        with self.lock:
            self.tracked_dirs.add(dir_path)
            logger.debug("Tracking directory", dir_path=dir_path)
    
    def cleanup_file(self, file_path: str, ignore_errors: bool = True) -> bool:
        """
        Clean up a specific file.
        
        Args:
            file_path: Path to file
            ignore_errors: Whether to ignore errors
            
        Returns:
            True if successful
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("Cleaned up file", file_path=file_path)
                return True
            return False
        except Exception as e:
            if not ignore_errors:
                logger.error("Failed to cleanup file", file_path=file_path, error=str(e))
                raise
            logger.warning("Failed to cleanup file (ignored)", file_path=file_path, error=str(e))
            return False
    
    def cleanup_directory(self, dir_path: str, recursive: bool = False, ignore_errors: bool = True) -> bool:
        """
        Clean up a directory.
        
        Args:
            dir_path: Path to directory
            recursive: Whether to clean recursively
            ignore_errors: Whether to ignore errors
            
        Returns:
            True if successful
        """
        try:
            if os.path.exists(dir_path):
                if recursive:
                    import shutil
                    shutil.rmtree(dir_path)
                else:
                    os.rmdir(dir_path)
                logger.debug("Cleaned up directory", dir_path=dir_path, recursive=recursive)
                return True
            return False
        except Exception as e:
            if not ignore_errors:
                logger.error("Failed to cleanup directory", dir_path=dir_path, error=str(e))
                raise
            logger.warning("Failed to cleanup directory (ignored)", dir_path=dir_path, error=str(e))
            return False
    
    def untrack_file(self, file_path: str):
        """Stop tracking a file."""
        with self.lock:
            self.tracked_files.discard(file_path)
    
    def cleanup_old_files(self, directory: str, max_age_hours: int = 24, pattern: Optional[str] = None):
        """
        Clean up old files in a directory.
        
        Args:
            directory: Directory to clean
            max_age_hours: Maximum age in hours
            pattern: Optional filename pattern to match
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return
            
            cleaned = 0
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    # Check pattern
                    if pattern and pattern not in file_path.name:
                        continue
                    
                    # Check age
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned += 1
                            logger.debug("Cleaned up old file", file_path=str(file_path))
                        except Exception as e:
                            logger.warning("Failed to cleanup old file", file_path=str(file_path), error=str(e))
            
            if cleaned > 0:
                logger.info("Cleaned up old files", directory=directory, count=cleaned)
        
        except Exception as e:
            logger.error("Error cleaning up old files", directory=directory, error=str(e))
    
    def cleanup_all(self):
        """Clean up all tracked resources."""
        logger.info("Cleaning up all tracked resources")
        
        with self.lock:
            files_to_clean = list(self.tracked_files)
            self.tracked_files.clear()
        
        for file_path in files_to_clean:
            self.cleanup_file(file_path, ignore_errors=True)
    
    def get_tracked_count(self) -> int:
        """Get count of tracked files."""
        with self.lock:
            return len(self.tracked_files)


# Global resource manager
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get global resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager





"""
Background task processing for async file processing
"""
import threading
import queue
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import uuid
from utils.logger import get_system_logger

logger = get_system_logger()


class TaskStatus:
    """Task status constants."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTaskManager:
    """Manages background tasks for async processing."""
    
    def __init__(self, max_workers: int = 3):
        """
        Initialize background task manager.
        
        Args:
            max_workers: Maximum concurrent workers
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_queue = queue.Queue()
        self.workers: list = []
        self.running = False
        self.lock = threading.Lock()
    
    def start(self):
        """Start background workers."""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting background task workers", workers=self.max_workers)
        
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True, name=f"Worker-{i}")
            worker.start()
            self.workers.append(worker)
    
    def stop(self):
        """Stop background workers."""
        self.running = False
        logger.info("Stopping background task workers")
        
        # Add poison pills to stop workers
        for _ in self.workers:
            self.task_queue.put(None)
        
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        self.workers.clear()
    
    def submit_task(
        self,
        task_func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for background processing.
        
        Args:
            task_func: Function to execute
            *args: Function arguments
            task_id: Optional task ID (generated if not provided)
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        if not task_id:
            task_id = str(uuid.uuid4())
        
        task = {
            'id': task_id,
            'func': task_func,
            'args': args,
            'kwargs': kwargs,
            'status': TaskStatus.PENDING,
            'created_at': datetime.now().isoformat(),
            'result': None,
            'error': None,
            'progress': 0.0
        }
        
        with self.lock:
            self.tasks[task_id] = task
        
        self.task_queue.put(task)
        logger.info("Task submitted", task_id=task_id)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        with self.lock:
            return self.tasks.get(task_id)
    
    def _worker(self):
        """Worker thread that processes tasks."""
        logger.info("Worker thread started", thread=threading.current_thread().name)
        
        while self.running:
            try:
                task = self.task_queue.get(timeout=1.0)
                
                if task is None:  # Poison pill
                    break
                
                task_id = task['id']
                logger.info("Processing task", task_id=task_id)
                
                # Update status
                with self.lock:
                    self.tasks[task_id]['status'] = TaskStatus.PROCESSING
                    self.tasks[task_id]['started_at'] = datetime.now().isoformat()
                
                try:
                    # Execute task
                    result = task['func'](*task['args'], **task['kwargs'])
                    
                    # Update status
                    with self.lock:
                        self.tasks[task_id]['status'] = TaskStatus.COMPLETED
                        self.tasks[task_id]['result'] = result
                        self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
                        self.tasks[task_id]['progress'] = 100.0
                    
                    logger.info("Task completed", task_id=task_id)
                    
                except Exception as e:
                    # Update status
                    with self.lock:
                        self.tasks[task_id]['status'] = TaskStatus.FAILED
                        self.tasks[task_id]['error'] = str(e)
                        self.tasks[task_id]['failed_at'] = datetime.now().isoformat()
                    
                    logger.error("Task failed", task_id=task_id, error=str(e))
                
                finally:
                    self.task_queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Worker error", error=str(e))
        
        logger.info("Worker thread stopped", thread=threading.current_thread().name)
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if task['status'] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    created = datetime.fromisoformat(task['created_at']).timestamp()
                    if created < cutoff:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
                logger.debug("Cleaned up old task", task_id=task_id)


# Global task manager
_task_manager: Optional[BackgroundTaskManager] = None


def get_task_manager() -> BackgroundTaskManager:
    """Get global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
        _task_manager.start()
    return _task_manager





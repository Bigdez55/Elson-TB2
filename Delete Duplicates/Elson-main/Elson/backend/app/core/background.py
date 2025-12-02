"""Background task processing module.

This module provides functionality for processing time-consuming tasks
in the background to improve API response times. It uses a ThreadPoolExecutor
for concurrent task execution.
"""

import logging
import asyncio
import functools
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional
import threading
from datetime import datetime

from app.core.config import settings
from app.core.metrics import record_metric

logger = logging.getLogger(__name__)

# Configure the thread pool size based on settings
thread_pool = ThreadPoolExecutor(
    max_workers=getattr(settings, 'BACKGROUND_WORKERS', 10),
    thread_name_prefix="background_worker"
)

# Queue for tasks
task_queue: List[Dict[str, Any]] = []
# Lock for thread-safe operations on the queue
queue_lock = threading.Lock()
# Flag to control the worker thread
keep_running = True
# Worker thread
worker_thread = None

def start_worker_thread():
    """Start the background worker thread."""
    global worker_thread
    if worker_thread is None or not worker_thread.is_alive():
        worker_thread = threading.Thread(target=process_task_queue, daemon=True)
        worker_thread.start()
        logger.info("Background worker thread started")

def stop_worker_thread():
    """Stop the background worker thread."""
    global keep_running
    keep_running = False
    logger.info("Background worker thread stopping...")

def process_task_queue():
    """Process tasks from the queue continuously."""
    global keep_running
    
    while keep_running:
        task = None
        with queue_lock:
            if task_queue:
                task = task_queue.pop(0)
        
        if task:
            func = task.get("func")
            args = task.get("args", [])
            kwargs = task.get("kwargs", {})
            task_id = task.get("id", "unknown")
            task_name = task.get("name", func.__name__ if func else "unknown")
            
            start_time = time.time()
            try:
                logger.debug(f"Processing background task {task_id}: {task_name}")
                func(*args, **kwargs)
                
                # Record successful completion
                elapsed_ms = (time.time() - start_time) * 1000
                record_metric("background_task_time", elapsed_ms, {
                    "task_name": task_name,
                    "status": "success"
                })
                logger.debug(f"Completed background task {task_id}: {task_name} in {elapsed_ms:.2f}ms")
                
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"Error in background task {task_id}: {task_name} - {str(e)}")
                logger.debug(traceback.format_exc())
                
                # Record failure
                record_metric("background_task_time", elapsed_ms, {
                    "task_name": task_name,
                    "status": "error"
                })
                record_metric("background_task_error", 1, {
                    "task_name": task_name,
                    "error": str(e)[:100]
                })
        else:
            # No tasks, sleep briefly to avoid CPU spinning
            time.sleep(0.1)

def submit_background_task(func: Callable, *args, **kwargs) -> str:
    """Submit a task to be executed in the background.
    
    Args:
        func: The function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Task ID that can be used to query status
    """
    task_id = f"task_{int(time.time() * 1000)}_{len(task_queue)}"
    task_name = kwargs.pop("task_name", func.__name__)
    
    task = {
        "id": task_id,
        "name": task_name,
        "func": func,
        "args": args,
        "kwargs": kwargs,
        "submit_time": datetime.now()
    }
    
    with queue_lock:
        task_queue.append(task)
        queue_length = len(task_queue)
    
    # Track queue metrics
    record_metric("background_task_queue_length", queue_length)
    logger.debug(f"Submitted background task {task_id}: {task_name} (queue length: {queue_length})")
    
    # Ensure worker thread is running
    start_worker_thread()
    
    return task_id

def run_in_background(task_name: Optional[str] = None):
    """Decorator to run a function in the background.
    
    Args:
        task_name: Optional name for the task (defaults to function name)
        
    Returns:
        Decorated function that submits original function to background
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal task_name
            name = task_name or func.__name__
            kwargs["task_name"] = name
            return submit_background_task(func, *args, **kwargs)
        return wrapper
    return decorator

def execute_in_thread(func: Callable, *args, **kwargs) -> Any:
    """Execute a function in a separate thread from the thread pool.
    
    Unlike submit_background_task, this method waits for the result.
    
    Args:
        func: The function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function
    """
    start_time = time.time()
    task_name = kwargs.pop("task_name", func.__name__)
    
    try:
        future = thread_pool.submit(func, *args, **kwargs)
        result = future.result()
        
        # Record metrics
        elapsed_ms = (time.time() - start_time) * 1000
        record_metric("thread_execution_time", elapsed_ms, {
            "task_name": task_name,
            "status": "success"
        })
        
        return result
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"Error executing {task_name} in thread: {str(e)}")
        
        # Record failure
        record_metric("thread_execution_time", elapsed_ms, {
            "task_name": task_name,
            "status": "error"
        })
        record_metric("thread_execution_error", 1, {
            "task_name": task_name,
            "error": str(e)[:100]
        })
        
        # Re-raise the exception
        raise

async def async_to_sync(func: Callable, *args, **kwargs) -> Any:
    """Run a synchronous function in a separate thread for async compatibility.
    
    Args:
        func: The synchronous function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool, 
        functools.partial(func, *args, **kwargs)
    )

def get_queue_status() -> Dict[str, Any]:
    """Get the current status of the task queue.
    
    Returns:
        Dictionary with queue statistics
    """
    with queue_lock:
        queue_size = len(task_queue)
        oldest_task = task_queue[0]["submit_time"] if task_queue else None
    
    return {
        "queue_size": queue_size,
        "oldest_task": oldest_task.isoformat() if oldest_task else None,
        "worker_running": worker_thread is not None and worker_thread.is_alive(),
        "thread_pool_size": thread_pool._max_workers,
        "active_threads": len([t for t in threading.enumerate() 
                              if t.name.startswith("background_worker")])
    }

# Initialize the worker thread on module import
start_worker_thread()
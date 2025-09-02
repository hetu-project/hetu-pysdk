import threading
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue
from typing import Any, Callable, Optional, Tuple

class PriorityThreadPoolExecutor(ThreadPoolExecutor):
    """
    A ThreadPoolExecutor that executes tasks based on their priority.
    Lower priority values are executed first.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize the executor.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        super().__init__(max_workers)
        self._work_queue = PriorityQueue()
        self._counter = 0
        self._counter_lock = threading.Lock()

    def submit(self, fn: Callable, *args: Any, priority: float = 0, **kwargs: Any) -> 'PriorityFuture':
        """Submit a task with priority.
        
        Args:
            fn: Function to execute
            *args: Function arguments
            priority: Task priority (lower values = higher priority)
            **kwargs: Function keyword arguments
            
        Returns:
            Future object representing the execution
        """
        with self._counter_lock:
            self._counter += 1
            # Use counter as tiebreaker for tasks with same priority
            count = self._counter
            
        future = PriorityFuture(priority, count)
        
        def _worker():
            try:
                result = fn(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
                
        # Add to priority queue
        self._work_queue.put((priority, count, _worker))
        
        # Start worker thread if needed
        self._adjust_thread_count()
        
        return future

class PriorityFuture:
    """Future object for priority-based task execution."""
    
    def __init__(self, priority: float, count: int):
        self.priority = priority
        self.count = count
        self._result = None
        self._exception = None
        self._done = threading.Event()
        
    def set_result(self, result: Any):
        """Set the result and mark as done."""
        self._result = result
        self._done.set()
        
    def set_exception(self, exception: Exception):
        """Set an exception and mark as done."""
        self._exception = exception
        self._done.set()
        
    def result(self, timeout: Optional[float] = None) -> Any:
        """Get the result, waiting if necessary.
        
        Args:
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            Task result
            
        Raises:
            TimeoutError: If timeout occurs
            Exception: If task raised an exception
        """
        if not self._done.wait(timeout):
            raise TimeoutError()
        if self._exception:
            raise self._exception
        return self._result
        
    def done(self) -> bool:
        """Check if the task is complete."""
        return self._done.is_set()
        
    def __lt__(self, other: 'PriorityFuture') -> bool:
        """Compare futures based on priority."""
        if not isinstance(other, PriorityFuture):
            return NotImplemented
        return (self.priority, self.count) < (other.priority, other.count) 
"""
Task Monitor for periodic task scheduling

This module provides a thread-based task scheduler for executing
periodic tasks at specified intervals.
"""

import threading
import time
from typing import Callable, Dict, Optional
from dataclasses import dataclass
from ..utils.logger import get_logger

logger = get_logger('task_monitor')


@dataclass
class Task:
    """Represents a periodic task"""
    name: str
    callback: Callable[[], None]
    period_us: int  # Period in microseconds
    last_run: float = 0.0
    enabled: bool = True
    error_count: int = 0


class TaskMonitor:
    """
    Monitor for managing periodic tasks

    Tasks are executed in a dedicated thread with microsecond precision.
    """

    def __init__(self):
        """Initialize task monitor"""
        self.tasks: Dict[str, Task] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def add_task(self, name: str, callback: Callable[[], None], period_us: int):
        """
        Add a periodic task

        Args:
            name: Task name (unique identifier)
            callback: Function to call periodically
            period_us: Period in microseconds
        """
        with self._lock:
            if name in self.tasks:
                logger.warning(f"Task '{name}' already exists, replacing")

            task = Task(
                name=name,
                callback=callback,
                period_us=period_us,
                last_run=time.time()
            )
            self.tasks[name] = task
            logger.debug(f"Added task '{name}' with period {period_us}us ({period_us/1e6:.3f}s)")

    def add_task_ms(self, name: str, callback: Callable[[], None], period_ms: int):
        """
        Add a periodic task with period in milliseconds

        Args:
            name: Task name (unique identifier)
            callback: Function to call periodically
            period_ms: Period in milliseconds
        """
        self.add_task(name, callback, period_ms * 1000)

    def add_task_sec(self, name: str, callback: Callable[[], None], period_sec: float):
        """
        Add a periodic task with period in seconds

        Args:
            name: Task name (unique identifier)
            callback: Function to call periodically
            period_sec: Period in seconds
        """
        self.add_task(name, callback, int(period_sec * 1e6))

    def remove_task(self, name: str):
        """
        Remove a task

        Args:
            name: Task name
        """
        with self._lock:
            if name in self.tasks:
                del self.tasks[name]
                logger.debug(f"Removed task '{name}'")
            else:
                logger.warning(f"Task '{name}' not found")

    def enable_task(self, name: str):
        """
        Enable a task

        Args:
            name: Task name
        """
        with self._lock:
            if name in self.tasks:
                self.tasks[name].enabled = True
                logger.debug(f"Enabled task '{name}'")

    def disable_task(self, name: str):
        """
        Disable a task

        Args:
            name: Task name
        """
        with self._lock:
            if name in self.tasks:
                self.tasks[name].enabled = False
                logger.debug(f"Disabled task '{name}'")

    def start(self):
        """Start task monitor thread"""
        if self.running:
            logger.warning("Task monitor already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Task monitor started")

    def stop(self):
        """Stop task monitor thread"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning("Task monitor thread did not stop gracefully")
            else:
                logger.info("Task monitor stopped")
        self.thread = None

    def _run(self):
        """Main task execution loop"""
        logger.debug("Task monitor thread started")

        while self.running:
            current_time = time.time()

            # Find tasks that are due (within lock)
            tasks_to_execute = []
            with self._lock:
                for task in self.tasks.values():
                    if not task.enabled:
                        continue

                    # Check if task is due
                    period_sec = task.period_us / 1e6
                    if (current_time - task.last_run) >= period_sec:
                        tasks_to_execute.append(task)
                        task.last_run = current_time
                        logger.debug(f"Task '{task.name}' is due, scheduling execution")

            # Execute callbacks OUTSIDE of lock to prevent deadlock
            for task in tasks_to_execute:
                try:
                    logger.debug(f"Executing task '{task.name}'")
                    task.callback()
                    with self._lock:
                        task.error_count = 0
                except Exception as e:
                    with self._lock:
                        task.error_count += 1
                        logger.error(
                            f"Error executing task '{task.name}': {e} "
                            f"(error count: {task.error_count})"
                        )

                        # Disable task after too many errors
                        if task.error_count >= 10:
                            task.enabled = False
                            logger.error(
                                    f"Task '{task.name}' disabled after {task.error_count} errors"
                                )

            # Sleep for a short time to avoid busy-waiting
            # Use minimum task period or 1ms, whichever is smaller
            min_period = 0.001  # 1ms default
            if self.tasks:
                min_period = min(
                    task.period_us / 1e6 for task in self.tasks.values()
                ) / 10  # Sleep 1/10 of minimum period

            time.sleep(min(min_period, 0.001))

        logger.debug("Task monitor thread stopped")

    def get_task_info(self) -> Dict[str, Dict]:
        """
        Get information about all tasks

        Returns:
            Dictionary of task information
        """
        with self._lock:
            return {
                name: {
                    'period_us': task.period_us,
                    'period_ms': task.period_us / 1000,
                    'period_sec': task.period_us / 1e6,
                    'enabled': task.enabled,
                    'error_count': task.error_count,
                    'last_run': task.last_run
                }
                for name, task in self.tasks.items()
            }

    def clear_all_tasks(self):
        """Remove all tasks"""
        with self._lock:
            self.tasks.clear()
            logger.debug("Cleared all tasks")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False

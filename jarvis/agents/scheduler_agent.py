"""
Scheduler Agent — APScheduler-based task scheduling
"""

from datetime import datetime
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from PySide6.QtCore import QObject, Signal
from jarvis.utils.logger import logger


class SchedulerAgent(QObject):
    """APScheduler-based task and reminder scheduler."""

    task_fired = Signal(str, str)   # task_id, task_name
    task_added = Signal(dict)
    task_removed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scheduler = BackgroundScheduler(timezone="local")
        self._jobs: dict[str, dict] = {}

    def start(self):
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def add_one_shot(
        self, name: str, run_at: datetime,
        callback: Callable, args: list = None
    ) -> str:
        """Schedule a one-time task."""
        job = self._scheduler.add_job(
            callback,
            trigger=DateTrigger(run_date=run_at),
            args=args or [],
            id=None,
            name=name,
            misfire_grace_time=300,
        )
        task = {
            "id": job.id,
            "name": name,
            "type": "one-shot",
            "trigger": str(run_at),
            "status": "pending",
        }
        self._jobs[job.id] = task
        self.task_added.emit(task)
        logger.info(f"Scheduled one-shot: '{name}' at {run_at}")
        return job.id

    def add_interval(
        self, name: str, seconds: int = 0, minutes: int = 0,
        hours: int = 0, callback: Callable = None, args: list = None
    ) -> str:
        """Schedule a recurring interval task."""
        job = self._scheduler.add_job(
            callback or (lambda: None),
            trigger=IntervalTrigger(
                seconds=seconds, minutes=minutes, hours=hours
            ),
            args=args or [],
            name=name,
            misfire_grace_time=60,
        )
        task = {
            "id": job.id,
            "name": name,
            "type": "interval",
            "trigger": f"every {hours}h {minutes}m {seconds}s",
            "status": "running",
        }
        self._jobs[job.id] = task
        self.task_added.emit(task)
        return job.id

    def add_cron(
        self, name: str, cron_expression: str,
        callback: Callable, args: list = None
    ) -> str:
        """Schedule a cron-based task (e.g., '0 9 * * *' = 9am daily)."""
        parts = cron_expression.split()
        trigger = CronTrigger(
            minute=parts[0] if len(parts) > 0 else "*",
            hour=parts[1] if len(parts) > 1 else "*",
            day=parts[2] if len(parts) > 2 else "*",
            month=parts[3] if len(parts) > 3 else "*",
            day_of_week=parts[4] if len(parts) > 4 else "*",
        )
        job = self._scheduler.add_job(
            callback, trigger=trigger,
            args=args or [], name=name
        )
        task = {
            "id": job.id,
            "name": name,
            "type": "cron",
            "trigger": cron_expression,
            "status": "running",
        }
        self._jobs[job.id] = task
        self.task_added.emit(task)
        logger.info(f"Scheduled cron: '{name}' ({cron_expression})")
        return job.id

    def remove_task(self, job_id: str):
        """Remove a scheduled task."""
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass
        self._jobs.pop(job_id, None)
        self.task_removed.emit(job_id)

    def get_all_tasks(self) -> list[dict]:
        return list(self._jobs.values())

    def add_reminder(
        self, title: str, message: str, remind_at: datetime,
        notification_callback: Callable = None
    ) -> str:
        """Convenience: add a reminder that fires a notification."""
        def _fire():
            logger.info(f"Reminder fired: {title}")
            self.task_fired.emit("reminder", title)
            if notification_callback:
                notification_callback(title, message)

        return self.add_one_shot(f"Reminder: {title}", remind_at, _fire)


# Singleton
scheduler_agent = SchedulerAgent()

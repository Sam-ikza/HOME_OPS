from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from database.models import Reminder

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def process_due_reminders(db: Session) -> int:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    due = (
        db.query(Reminder)
        .filter(Reminder.due_at <= now)
        .filter(Reminder.status == "scheduled")
        .all()
    )

    for reminder in due:
        reminder.status = "sent"

    if due:
        db.commit()
    return len(due)


def start_scheduler(db_factory) -> BackgroundScheduler:
    global _scheduler

    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")

    def _job():
        db = db_factory()
        try:
            sent = process_due_reminders(db)
            if sent:
                logger.info("processed_reminders=%s", sent)
        finally:
            db.close()

    _scheduler.add_job(_job, "interval", minutes=5, id="reminder_dispatch", replace_existing=True)
    _scheduler.start()
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)

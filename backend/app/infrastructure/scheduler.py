"""Job programado de recordatorios con APScheduler.

En producción con varias réplicas conviene que solo una ejecute el job (o
moverlo a un worker dedicado); la restricción única de reminder_logs evita
duplicados incluso si dos réplicas coinciden.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session, sessionmaker

from app.application.reminders import ReminderService
from app.core.clock import Clock
from app.infrastructure.notifier import Notifier

logger = logging.getLogger("scheduler")


def build_scheduler(
    session_factory: sessionmaker[Session], clock: Clock, notifier: Notifier,
    hours_before: int, interval_minutes: int,
) -> BackgroundScheduler:
    def job() -> None:
        with session_factory() as session:
            try:
                ReminderService(session, clock, notifier, hours_before).run_due()
            except Exception:  # el job nunca debe tumbar el scheduler
                logger.exception("Fallo en el job de recordatorios")

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(job, "interval", minutes=interval_minutes, id="recordatorios",
                      max_instances=1, coalesce=True)
    return scheduler

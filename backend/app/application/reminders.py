"""Recordatorios: busca citas próximas sin aviso y "envía" uno (simulado).

Idempotencia: la restricción única (appointment_id, kind) en reminder_logs
garantiza que una cita reciba como máximo un recordatorio de cada tipo,
aunque el job se ejecute varias veces o en varias réplicas.
"""

import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.application.pagination import PageParams, paginate
from app.core.clock import Clock
from app.core.logging import log_event
from app.domain.enums import AppointmentStatus, ReminderStatus
from app.domain.models import Appointment, ReminderLog
from app.infrastructure.notifier import Notifier

logger = logging.getLogger("reminders")
KIND = "previo_24h"


class ReminderService:
    def __init__(self, session: Session, clock: Clock, notifier: Notifier, hours_before: int) -> None:
        self.session = session
        self.clock = clock
        self.notifier = notifier
        self.hours_before = hours_before

    def run_due(self) -> int:
        now = self.clock.now()
        already = select(ReminderLog.appointment_id).where(ReminderLog.kind == KIND)
        due = self.session.scalars(
            select(Appointment)
            .options(joinedload(Appointment.client), joinedload(Appointment.service),
                     joinedload(Appointment.professional))
            .where(
                Appointment.status == AppointmentStatus.CONFIRMADA,
                Appointment.start_at > now,
                Appointment.start_at <= now + timedelta(hours=self.hours_before),
                Appointment.id.not_in(already),
            )
        ).all()

        sent = 0
        for appt in due:
            message = (
                f"Hola {appt.client.full_name}, te recordamos tu cita de {appt.service.name} "
                f"con {appt.professional.full_name} el {appt.start_at:%d/%m/%Y a las %H:%M}."
            )
            ok = self.notifier.send(appt.client.email, message)
            self.session.add(ReminderLog(
                appointment_id=appt.id, kind=KIND, channel=self.notifier.channel,
                recipient=appt.client.email, message=message,
                status=ReminderStatus.ENVIADO if ok else ReminderStatus.FALLIDO, sent_at=now,
            ))
            sent += 1 if ok else 0
        self.session.commit()
        log_event(logger, "job_recordatorios", evaluadas=len(due), enviados=sent)
        return sent

    def list(self, params: PageParams) -> dict:
        stmt = select(ReminderLog).order_by(ReminderLog.sent_at.desc(), ReminderLog.id.desc())
        return paginate(self.session, stmt, params)

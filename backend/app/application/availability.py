"""Caso de uso: consultar disponibilidad.

Traduce datos persistidos (horarios, excepciones, citas) a los tipos puros de
`app.domain.availability` y delega el cálculo allí.
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.domain.availability import Block, DayException, Interval, compute_slots
from app.domain.enums import BLOCKING_STATUSES
from app.domain.errors import BusinessRuleError, NotFoundError
from app.domain.models import Appointment, Professional, ScheduleException, Service


class AvailabilityService:
    def __init__(self, session: Session, clock: Clock, step_minutes: int) -> None:
        self.session = session
        self.clock = clock
        self.step_minutes = step_minutes

    def load(self, professional_id: int, service_id: int) -> tuple[Professional, Service]:
        prof = self.session.get(Professional, professional_id)
        if not prof or not prof.is_active:
            raise NotFoundError("Profesional no encontrado.")
        service = self.session.get(Service, service_id)
        if not service or not service.is_active:
            raise NotFoundError("Servicio no encontrado.")
        if service not in prof.services:
            raise BusinessRuleError("El profesional no ofrece este servicio.")
        return prof, service

    def busy_intervals(
        self, professional_id: int, day: date, exclude_appointment_id: int | None = None
    ) -> list[Interval]:
        start = datetime.combine(day, time.min)
        stmt = select(Appointment).where(
            Appointment.professional_id == professional_id,
            Appointment.status.in_([s.value for s in BLOCKING_STATUSES]),
            Appointment.start_at < start + timedelta(days=1),
            Appointment.end_at > start,
        )
        if exclude_appointment_id is not None:
            # Al reprogramar, la propia cita no debe bloquear su nuevo horario.
            stmt = stmt.where(Appointment.id != exclude_appointment_id)
        return [Interval(a.start_at, a.end_at) for a in self.session.scalars(stmt)]

    def slots_for_day(
        self,
        professional_id: int,
        service_id: int,
        day: date,
        earliest_start: datetime | None = None,
        exclude_appointment_id: int | None = None,
    ) -> list[datetime]:
        prof, service = self.load(professional_id, service_id)
        blocks = [Block(w.start_time, w.end_time) for w in prof.working_hours if w.weekday == day.weekday()]
        exceptions = [
            DayException(e.start_time, e.end_time)
            for e in self.session.scalars(
                select(ScheduleException).where(
                    ScheduleException.date == day,
                    or_(ScheduleException.professional_id.is_(None),
                        ScheduleException.professional_id == professional_id),
                )
            )
        ]
        if earliest_start is None:
            earliest_start = self.clock.now()
        return compute_slots(
            day=day,
            blocks=blocks,
            exceptions=exceptions,
            busy=self.busy_intervals(professional_id, day, exclude_appointment_id),
            duration_minutes=service.duration_minutes,
            step_minutes=self.step_minutes,
            earliest_start=earliest_start,
        )

"""Casos de uso de citas: reservar, reprogramar, cancelar y cerrar."""

import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.application.availability import AvailabilityService
from app.application.dtos import (
    AppointmentCreateIn,
    AppointmentOut,
    CancelIn,
    RescheduleIn,
    StatusIn,
)
from app.application.pagination import PageParams, apply_sort, paginate
from app.core.clock import Clock
from app.core.logging import log_event
from app.domain.enums import AppointmentStatus, Role
from app.domain.errors import BusinessRuleError, ConflictError, NotFoundError, PermissionDeniedError
from app.domain.models import Appointment, Professional, Service, User
from app.domain.policies import (
    BookingPolicy,
    ensure_bookable_window,
    ensure_can_cancel,
    ensure_can_close,
    ensure_can_reschedule,
)

logger = logging.getLogger("appointments")


def appointment_to_out(a: Appointment) -> AppointmentOut:
    return AppointmentOut(
        id=a.id,
        professional_id=a.professional_id,
        professional_name=a.professional.full_name,
        service_id=a.service_id,
        service_name=a.service.name,
        client_id=a.client_id,
        client_name=a.client.full_name,
        client_email=a.client.email,
        start_at=a.start_at,
        end_at=a.end_at,
        status=AppointmentStatus(a.status),
        price=a.price,
        notes=a.notes,
        cancellation_reason=a.cancellation_reason,
        reschedule_count=a.reschedule_count,
    )


class AppointmentService:
    def __init__(
        self, session: Session, clock: Clock, availability: AvailabilityService, policy: BookingPolicy
    ) -> None:
        self.session = session
        self.clock = clock
        self.availability = availability
        self.policy = policy

    # ----- Consultas -----
    def _base_query(self):
        return select(Appointment).options(
            joinedload(Appointment.professional), joinedload(Appointment.service), joinedload(Appointment.client)
        )

    def _scope(self, stmt, actor: User):
        """Cada rol ve solo lo que le corresponde."""
        if actor.role == Role.CLIENTE:
            return stmt.where(Appointment.client_id == actor.id)
        if actor.role == Role.PROFESIONAL:
            own = actor.professional.id if actor.professional else -1
            return stmt.where(Appointment.professional_id == own)
        return stmt

    def list(
        self,
        actor: User,
        params: PageParams,
        q: str | None = None,
        status: str | None = None,
        professional_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        stmt = self._scope(self._base_query(), actor)
        if q:
            like = f"%{q}%"
            stmt = stmt.join(Appointment.client).join(Appointment.service).where(
                or_(User.full_name.ilike(like), User.email.ilike(like), Service.name.ilike(like))
            )
        if status:
            stmt = stmt.where(Appointment.status == status)
        if professional_id:
            stmt = stmt.where(Appointment.professional_id == professional_id)
        if date_from:
            stmt = stmt.where(Appointment.start_at >= datetime.combine(date_from, time.min))
        if date_to:
            stmt = stmt.where(Appointment.start_at < datetime.combine(date_to + timedelta(days=1), time.min))
        stmt = apply_sort(
            stmt, params.sort,
            {"start_at": Appointment.start_at, "status": Appointment.status, "price": Appointment.price,
             "created_at": Appointment.created_at},
            Appointment.start_at.asc(),
        )
        return paginate(self.session, stmt, params)

    def get(self, actor: User, appointment_id: int) -> Appointment:
        appt = self.session.scalar(self._scope(self._base_query(), actor).where(Appointment.id == appointment_id))
        if not appt:
            # 404 (y no 403) para no revelar la existencia de citas ajenas.
            raise NotFoundError("Cita no encontrada.")
        return appt

    # ----- Comandos -----
    def _earliest_for(self, actor: User) -> datetime:
        now = self.clock.now()
        # El personal puede agendar "para ya" (p. ej. un paciente en recepción);
        # el cliente debe respetar la anticipación mínima.
        if actor.role == Role.CLIENTE:
            return now + timedelta(minutes=self.policy.min_advance_minutes)
        return now

    def _ensure_slot(
        self, actor: User, professional_id: int, service_id: int, start_at: datetime,
        exclude_appointment_id: int | None = None,
    ) -> None:
        now = self.clock.now()
        if actor.role == Role.CLIENTE:
            ensure_bookable_window(start_at, now, self.policy)
        elif start_at <= now:
            raise BusinessRuleError("No se puede reservar en una fecha u hora pasada.")

        # Bloqueo pesimista de la fila del profesional: serializa reservas
        # concurrentes para el mismo profesional en PostgreSQL (en SQLite es no-op).
        self.session.execute(
            select(Professional.id).where(Professional.id == professional_id).with_for_update()
        )
        slots = self.availability.slots_for_day(
            professional_id, service_id, start_at.date(),
            earliest_start=self._earliest_for(actor),
            exclude_appointment_id=exclude_appointment_id,
        )
        if start_at not in slots:
            raise ConflictError(
                "El horario seleccionado no está disponible (fuera de horario, feriado o ya ocupado)."
            )

    def _ensure_client_free(self, client_id: int, start: datetime, end: datetime, exclude_id: int | None) -> None:
        stmt = select(Appointment.id).where(
            Appointment.client_id == client_id,
            Appointment.status == AppointmentStatus.CONFIRMADA,
            Appointment.start_at < end,
            Appointment.end_at > start,
        )
        if exclude_id:
            stmt = stmt.where(Appointment.id != exclude_id)
        if self.session.scalar(stmt):
            raise ConflictError("Ya tienes otra cita que se cruza con ese horario.")

    def create(self, actor: User, data: AppointmentCreateIn) -> Appointment:
        start_at = data.start_at.replace(tzinfo=None, second=0, microsecond=0)
        prof, service = self.availability.load(data.professional_id, data.service_id)

        if actor.role == Role.CLIENTE:
            client_id = actor.id  # un cliente nunca reserva a nombre de otro
        else:
            if data.client_id is None:
                raise BusinessRuleError("Indica el cliente para quien se reserva la cita.")
            if actor.role == Role.PROFESIONAL and (not actor.professional or actor.professional.id != prof.id):
                raise PermissionDeniedError("Solo puedes agendar citas en tu propia agenda.")
            client = self.session.get(User, data.client_id)
            if not client or client.role != Role.CLIENTE:
                raise NotFoundError("Cliente no encontrado.")
            client_id = client.id

        self._ensure_slot(actor, prof.id, service.id, start_at)
        end_at = start_at + timedelta(minutes=service.duration_minutes)
        self._ensure_client_free(client_id, start_at, end_at, None)

        appt = Appointment(
            professional_id=prof.id, service_id=service.id, client_id=client_id,
            start_at=start_at, end_at=end_at, status=AppointmentStatus.CONFIRMADA,
            price=service.price, notes=data.notes, reschedule_count=0,
        )
        self.session.add(appt)
        self.session.commit()
        log_event(logger, "cita_creada", appointment_id=appt.id, professional_id=prof.id, actor_id=actor.id)
        return self.get(actor, appt.id)

    def reschedule(self, actor: User, appointment_id: int, data: RescheduleIn) -> Appointment:
        appt = self.get(actor, appointment_id)
        ensure_can_reschedule(appt.status, appt.start_at, appt.reschedule_count, self.clock.now(),
                              actor.role, self.policy)
        new_start = data.start_at.replace(tzinfo=None, second=0, microsecond=0)
        if new_start == appt.start_at:
            raise BusinessRuleError("El nuevo horario es igual al actual.")
        self._ensure_slot(actor, appt.professional_id, appt.service_id, new_start, exclude_appointment_id=appt.id)
        new_end = new_start + timedelta(minutes=appt.service.duration_minutes)
        self._ensure_client_free(appt.client_id, new_start, new_end, appt.id)

        appt.start_at, appt.end_at = new_start, new_end
        appt.reschedule_count += 1
        # Se borran recordatorios previos para que el job envíe uno nuevo con la hora correcta.
        for r in list(appt.reminders):
            self.session.delete(r)
        self.session.commit()
        log_event(logger, "cita_reprogramada", appointment_id=appt.id, actor_id=actor.id)
        return self.get(actor, appt.id)

    def cancel(self, actor: User, appointment_id: int, data: CancelIn) -> Appointment:
        appt = self.get(actor, appointment_id)
        ensure_can_cancel(appt.status, appt.start_at, self.clock.now(), actor.role, self.policy)
        appt.status = AppointmentStatus.CANCELADA
        appt.cancellation_reason = data.reason
        self.session.commit()
        log_event(logger, "cita_cancelada", appointment_id=appt.id, actor_id=actor.id)
        return appt

    def set_status(self, actor: User, appointment_id: int, data: StatusIn) -> Appointment:
        if actor.role == Role.CLIENTE:
            raise PermissionDeniedError("Solo el personal puede cerrar citas.")
        appt = self.get(actor, appointment_id)
        ensure_can_close(appt.status, appt.start_at, self.clock.now())
        appt.status = AppointmentStatus(data.status)
        self.session.commit()
        return appt

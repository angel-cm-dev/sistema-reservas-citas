"""Políticas de reserva, reprogramación y cancelación (lógica pura).

Se expresan como funciones que lanzan BusinessRuleError con un mensaje claro
para el usuario final. Mantenerlas aisladas facilita probarlas y explicarlas.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.enums import AppointmentStatus, Role
from app.domain.errors import BusinessRuleError


@dataclass(frozen=True)
class BookingPolicy:
    min_advance_minutes: int = 120
    max_advance_days: int = 60
    cancellation_min_hours: int = 24
    max_reschedules: int = 2


def ensure_bookable_window(start_at: datetime, now: datetime, policy: BookingPolicy) -> None:
    """Valida que el inicio no esté en el pasado ni demasiado cerca/lejos.

    - Anticipación mínima: da tiempo al profesional para prepararse.
    - Horizonte máximo: evita agendas "fantasma" a muy largo plazo.
    """
    if start_at <= now:
        raise BusinessRuleError("No se puede reservar en una fecha u hora pasada.")
    if start_at < now + timedelta(minutes=policy.min_advance_minutes):
        raise BusinessRuleError(
            f"Las reservas requieren al menos {policy.min_advance_minutes} minutos de anticipación."
        )
    if start_at > now + timedelta(days=policy.max_advance_days):
        raise BusinessRuleError(
            f"Solo se puede reservar con hasta {policy.max_advance_days} días de anticipación."
        )


def ensure_can_cancel(
    status: str, start_at: datetime, now: datetime, actor_role: str, policy: BookingPolicy
) -> None:
    """El cliente solo cancela con N horas de anticipación; el personal, siempre.

    La restricción protege la agenda del profesional de cancelaciones de último
    minuto que no se pueden volver a ocupar.
    """
    if status != AppointmentStatus.CONFIRMADA:
        raise BusinessRuleError("Solo se pueden cancelar citas confirmadas.")
    if actor_role == Role.CLIENTE and start_at - now < timedelta(hours=policy.cancellation_min_hours):
        raise BusinessRuleError(
            f"Las cancelaciones deben hacerse con al menos {policy.cancellation_min_hours} horas "
            "de anticipación. Comunícate con el centro."
        )


def ensure_can_reschedule(
    status: str, start_at: datetime, reschedule_count: int, now: datetime, actor_role: str,
    policy: BookingPolicy,
) -> None:
    if status != AppointmentStatus.CONFIRMADA:
        raise BusinessRuleError("Solo se pueden reprogramar citas confirmadas.")
    if actor_role == Role.CLIENTE:
        if start_at - now < timedelta(hours=policy.cancellation_min_hours):
            raise BusinessRuleError(
                f"La reprogramación debe hacerse con al menos {policy.cancellation_min_hours} horas "
                "de anticipación."
            )
        # Límite para evitar que un cliente "retenga" horarios moviendo la cita sin fin.
        if reschedule_count >= policy.max_reschedules:
            raise BusinessRuleError(
                f"La cita ya fue reprogramada {policy.max_reschedules} veces (máximo permitido)."
            )


def ensure_can_close(status: str, start_at: datetime, now: datetime) -> None:
    """Marcar completada / no asistió solo tiene sentido después del inicio."""
    if status != AppointmentStatus.CONFIRMADA:
        raise BusinessRuleError("Solo se pueden cerrar citas confirmadas.")
    if start_at > now:
        raise BusinessRuleError("No se puede cerrar una cita que aún no ha comenzado.")

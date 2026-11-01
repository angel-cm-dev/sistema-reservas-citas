"""Datos de ejemplo FICTICIOS para demo.

Uso: `python -m app.infrastructure.seed` (idempotente: no hace nada si ya hay usuarios).
Todas las cuentas demo usan la contraseña `Demo123!`.
"""

import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import Clock, SystemClock
from app.core.config import get_settings
from app.core.security import hash_password
from app.domain.enums import AppointmentStatus, Role
from app.domain.models import (
    Appointment,
    Professional,
    ScheduleException,
    Service,
    User,
    WorkingHour,
)

logger = logging.getLogger("seed")
DEMO_PASSWORD = "Demo123!"


def seed(session: Session, clock: Clock) -> bool:
    if session.scalar(select(User.id).limit(1)):
        return False

    pwd = hash_password(DEMO_PASSWORD)  # un solo hash: bcrypt es lento a propósito

    def user(email: str, name: str, role: Role, phone: str | None = None) -> User:
        u = User(email=email, full_name=name, role=role, phone=phone, password_hash=pwd, is_active=True)
        session.add(u)
        return u

    user("admin@demo.pe", "Administradora Demo", Role.ADMIN)
    u_lopez = user("lucia.lopez@demo.pe", "Lucía López Ramos", Role.PROFESIONAL, "900000001")
    u_quispe = user("marco.quispe@demo.pe", "Marco Quispe Huamán", Role.PROFESIONAL, "900000002")
    clientes = [
        user("cliente@demo.pe", "Carla Cliente Demo", Role.CLIENTE, "900000010"),
        user("jorge.diaz@demo.pe", "Jorge Díaz Torres", Role.CLIENTE, "900000011"),
        user("ana.rojas@demo.pe", "Ana Rojas Paredes", Role.CLIENTE, "900000012"),
    ]

    s_nutri = Service(name="Consulta nutricional", description="Evaluación y plan de alimentación.",
                      duration_minutes=45, price=Decimal("90.00"))
    s_control = Service(name="Control nutricional", description="Seguimiento de plan existente.",
                        duration_minutes=30, price=Decimal("60.00"))
    s_fisio = Service(name="Sesión de fisioterapia", description="Terapia física y rehabilitación.",
                      duration_minutes=60, price=Decimal("120.00"))
    s_eval = Service(name="Evaluación postural", description="Diagnóstico postural inicial.",
                     duration_minutes=30, price=Decimal("70.00"))
    session.add_all([s_nutri, s_control, s_fisio, s_eval])

    p_lopez = Professional(user=u_lopez, full_name=u_lopez.full_name, specialty="Nutrición",
                           bio="Nutricionista con enfoque en hábitos saludables.", services=[s_nutri, s_control])
    p_quispe = Professional(user=u_quispe, full_name=u_quispe.full_name, specialty="Fisioterapia",
                            bio="Fisioterapeuta deportivo.", services=[s_fisio, s_eval])
    session.add_all([p_lopez, p_quispe])

    # Lunes a viernes en dos turnos y sábado por la mañana.
    for prof in (p_lopez, p_quispe):
        for wd in range(5):
            prof.working_hours.append(WorkingHour(weekday=wd, start_time=time(9), end_time=time(13)))
            prof.working_hours.append(WorkingHour(weekday=wd, start_time=time(14), end_time=time(18)))
        prof.working_hours.append(WorkingHour(weekday=5, start_time=time(9), end_time=time(13)))

    today = clock.now().date()
    session.add_all([
        ScheduleException(date=date(today.year, 12, 8), reason="Feriado: Inmaculada Concepción"),
        ScheduleException(date=date(today.year, 12, 25), reason="Feriado: Navidad"),
        ScheduleException(professional=p_quispe, date=today + timedelta(days=10),
                          start_time=time(9), end_time=time(11), reason="Capacitación interna"),
    ])
    session.flush()

    # Citas de ejemplo en la semana actual y la siguiente (en días hábiles).
    def next_weekday(d: date) -> date:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        return d

    plan = [
        (-3, p_lopez, s_nutri, time(9), AppointmentStatus.COMPLETADA, 0),
        (-2, p_quispe, s_fisio, time(10), AppointmentStatus.COMPLETADA, 1),
        (-2, p_lopez, s_control, time(15), AppointmentStatus.NO_ASISTIO, 2),
        (-1, p_quispe, s_eval, time(11), AppointmentStatus.CANCELADA, 0),
        (1, p_lopez, s_nutri, time(10), AppointmentStatus.CONFIRMADA, 0),
        (1, p_quispe, s_fisio, time(15), AppointmentStatus.CONFIRMADA, 1),
        (2, p_lopez, s_control, time(9), AppointmentStatus.CONFIRMADA, 2),
        (3, p_quispe, s_eval, time(16), AppointmentStatus.CONFIRMADA, 0),
        (5, p_lopez, s_nutri, time(14), AppointmentStatus.CONFIRMADA, 1),
    ]
    for offset, prof, svc, t, status, ci in plan:
        d = today + timedelta(days=offset)
        d = next_weekday(d) if offset > 0 else d
        if d.weekday() >= 5:
            d -= timedelta(days=d.weekday() - 4)  # mueve al viernes anterior
        start = datetime.combine(d, t)
        session.add(Appointment(
            professional_id=prof.id, service_id=svc.id, client_id=clientes[ci].id,
            start_at=start, end_at=start + timedelta(minutes=svc.duration_minutes),
            status=status, price=svc.price, reschedule_count=0,
            cancellation_reason="Viaje imprevisto" if status == AppointmentStatus.CANCELADA else None,
        ))
    session.commit()
    return True


def main() -> None:
    from app.infrastructure.db import build_engine, build_session_factory

    settings = get_settings()
    factory = build_session_factory(build_engine(settings.database_url))
    with factory() as session:
        created = seed(session, SystemClock(settings.timezone))
    print("Seed aplicado." if created else "La base ya tenía datos; seed omitido.")


if __name__ == "__main__":
    main()

"""KPIs del panel. Respeta el alcance del rol (el profesional ve solo lo suyo)."""

from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.dtos import KpiOut
from app.core.clock import Clock
from app.domain.enums import AppointmentStatus, Role
from app.domain.models import Appointment, ReminderLog, Service, User


class DashboardService:
    def __init__(self, session: Session, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    def kpis(self, actor: User) -> KpiOut:
        now = self.clock.now()
        today = datetime.combine(now.date(), time.min)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        def scoped(stmt):
            if actor.role == Role.PROFESIONAL:
                own = actor.professional.id if actor.professional else -1
                return stmt.where(Appointment.professional_id == own)
            return stmt

        def count(*conds) -> int:
            return self.session.scalar(scoped(select(func.count(Appointment.id)).where(*conds))) or 0

        active = Appointment.status != AppointmentStatus.CANCELADA
        today_n = count(Appointment.start_at >= today, Appointment.start_at < today + timedelta(days=1), active)
        week_end = week_start + timedelta(days=7)
        week_n = count(Appointment.start_at >= week_start, Appointment.start_at < week_end, active)
        upcoming = count(Appointment.start_at >= now, Appointment.status == AppointmentStatus.CONFIRMADA)

        by_status = {s.value: 0 for s in AppointmentStatus}
        rows = self.session.execute(
            scoped(select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status))
        ).all()
        for status, n in rows:
            by_status[status] = n
        total = sum(by_status.values())
        closed = by_status["completada"] + by_status["no_asistio"]

        revenue = self.session.scalar(scoped(
            select(func.coalesce(func.sum(Appointment.price), 0)).where(
                Appointment.status == AppointmentStatus.COMPLETADA, Appointment.start_at >= month_start
            )
        )) or Decimal("0")

        reminders = self.session.scalar(
            select(func.count(ReminderLog.id)).where(ReminderLog.sent_at >= week_start)
        ) or 0

        top = self.session.execute(scoped(
            select(Service.name, func.count(Appointment.id).label("n"))
            .join(Appointment, Appointment.service_id == Service.id)
            .where(active)
            .group_by(Service.name)
            .order_by(func.count(Appointment.id).desc())
            .limit(5)
        )).all()

        return KpiOut(
            appointments_today=today_n,
            appointments_week=week_n,
            upcoming_confirmed=upcoming,
            # Tasas sobre el total de citas registradas, en porcentaje con 1 decimal.
            cancellation_rate=round(100 * by_status["cancelada"] / total, 1) if total else 0.0,
            no_show_rate=round(100 * by_status["no_asistio"] / closed, 1) if closed else 0.0,
            revenue_month=Decimal(revenue).quantize(Decimal("0.01")),
            reminders_sent_week=reminders,
            by_status=by_status,
            top_services=[{"name": name, "count": n} for name, n in top],
        )

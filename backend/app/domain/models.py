"""Entidades del dominio mapeadas con SQLAlchemy 2 (estilo declarativo tipado).

Decisión pragmática: usamos las entidades ORM como modelo de dominio para
evitar una doble capa de mapeo en un sistema de este tamaño. Las reglas de
negocio puras (disponibilidad, políticas) viven en módulos sin dependencia de
la base de datos: `availability.py` y `policies.py`.
"""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


professional_services = Table(
    "professional_services",
    Base.metadata,
    Column("professional_id", ForeignKey("professionals.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    professional: Mapped["Professional | None"] = relationship(back_populates="user")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    professionals: Mapped[list["Professional"]] = relationship(
        secondary=professional_services, back_populates="services"
    )


class Professional(Base):
    __tablename__ = "professionals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User | None] = relationship(back_populates="professional")
    services: Mapped[list[Service]] = relationship(
        secondary=professional_services, back_populates="professionals"
    )
    working_hours: Mapped[list["WorkingHour"]] = relationship(
        back_populates="professional", cascade="all, delete-orphan", order_by="WorkingHour.weekday"
    )


class WorkingHour(Base):
    """Bloque de atención semanal. Un día puede tener varios bloques (mañana/tarde)."""

    __tablename__ = "working_hours"

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(Integer)  # 0=lunes ... 6=domingo (convención de Python)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    professional: Mapped[Professional] = relationship(back_populates="working_hours")


class ScheduleException(Base):
    """Excepción al horario: feriado global (professional_id nulo) o ausencia puntual.

    Si start_time/end_time son nulos se bloquea el día completo; si no, solo
    ese rango (p. ej. una capacitación de 10:00 a 12:00).
    """

    __tablename__ = "schedule_exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int | None] = mapped_column(
        ForeignKey("professionals.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    reason: Mapped[str] = mapped_column(String(200))

    professional: Mapped[Professional | None] = relationship()


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (Index("ix_appointments_prof_start", "professional_id", "start_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), index=True)
    # Precio "congelado" al reservar: si luego cambia la tarifa del servicio,
    # la cita conserva el precio acordado con el cliente.
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(String(300))
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    professional: Mapped[Professional] = relationship()
    service: Mapped[Service] = relationship()
    client: Mapped[User] = relationship()
    reminders: Mapped[list["ReminderLog"]] = relationship(back_populates="appointment")


class ReminderLog(Base):
    """Registro de recordatorios "enviados" (el envío es simulado)."""

    __tablename__ = "reminder_logs"
    __table_args__ = (UniqueConstraint("appointment_id", "kind", name="uq_reminder_once"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(30), default="previo_24h")
    channel: Mapped[str] = mapped_column(String(20), default="email")
    recipient: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    sent_at: Mapped[datetime] = mapped_column(DateTime)

    appointment: Mapped[Appointment] = relationship(back_populates="reminders")

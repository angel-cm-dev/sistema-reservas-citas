"""DTOs (Pydantic v2): contratos de entrada/salida de la aplicación.

Validan la forma de los datos en el borde; las reglas que dependen del estado
(solapamientos, políticas) se validan en los servicios.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.domain.enums import AppointmentStatus, Role

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


# ---------- Auth / usuarios ----------

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=3, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("La contraseña debe contener letras y números")
        return v


class UserCreateIn(RegisterIn):
    role: Role = Role.CLIENTE


class UserUpdateIn(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    role: Role | None = None
    is_active: bool | None = None


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    phone: str | None
    role: Role
    is_active: bool
    professional_id: int | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Catálogo ----------

class ServiceIn(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int = Field(ge=10, le=480)
    price: Decimal = Field(ge=0, le=100000, decimal_places=2)
    is_active: bool = True


class ServiceOut(ORMModel):
    id: int
    name: str
    description: str | None
    duration_minutes: int
    price: Decimal
    is_active: bool


class ProfessionalIn(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    specialty: str = Field(min_length=3, max_length=120)
    bio: str | None = Field(default=None, max_length=1000)
    user_id: int | None = None
    service_ids: list[int] = Field(default_factory=list)
    is_active: bool = True


class ProfessionalOut(ORMModel):
    id: int
    full_name: str
    specialty: str
    bio: str | None
    user_id: int | None
    is_active: bool
    services: list[ServiceOut] = []


class WorkingHourIn(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0=lunes ... 6=domingo")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_range(self) -> "WorkingHourIn":
        if self.end_time <= self.start_time:
            raise ValueError("La hora de fin debe ser posterior a la de inicio")
        return self


class WorkingHourOut(ORMModel):
    id: int
    weekday: int
    start_time: time
    end_time: time


class WeeklyScheduleIn(BaseModel):
    blocks: list[WorkingHourIn]

    @model_validator(mode="after")
    def no_overlaps(self) -> "WeeklyScheduleIn":
        by_day: dict[int, list[WorkingHourIn]] = {}
        for b in self.blocks:
            by_day.setdefault(b.weekday, []).append(b)
        for blocks in by_day.values():
            blocks.sort(key=lambda b: b.start_time)
            for prev, cur in zip(blocks, blocks[1:], strict=False):
                if cur.start_time < prev.end_time:
                    raise ValueError("Los bloques de un mismo día no pueden solaparse")
        return self


class ExceptionIn(BaseModel):
    professional_id: int | None = Field(default=None, description="Nulo = feriado para todos")
    date: date
    start_time: time | None = None
    end_time: time | None = None
    reason: str = Field(min_length=3, max_length=200)

    @model_validator(mode="after")
    def check_range(self) -> "ExceptionIn":
        if (self.start_time is None) != (self.end_time is None):
            raise ValueError("Indica hora de inicio y fin, o ninguna para bloquear el día completo")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("La hora de fin debe ser posterior a la de inicio")
        return self


class ExceptionOut(ORMModel):
    id: int
    professional_id: int | None
    date: date
    start_time: time | None
    end_time: time | None
    reason: str


# ---------- Disponibilidad ----------

class SlotOut(BaseModel):
    start_at: datetime
    end_at: datetime


class DayAvailabilityOut(BaseModel):
    date: date
    professional_id: int
    service_id: int
    slots: list[SlotOut]


# ---------- Citas ----------

class AppointmentCreateIn(BaseModel):
    professional_id: int
    service_id: int
    start_at: datetime
    notes: str | None = Field(default=None, max_length=500)
    client_id: int | None = Field(default=None, description="Solo admin/profesional: reservar a nombre de un cliente")


class RescheduleIn(BaseModel):
    start_at: datetime


class CancelIn(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


class StatusIn(BaseModel):
    status: Literal["completada", "no_asistio"]


class AppointmentOut(ORMModel):
    id: int
    professional_id: int
    professional_name: str
    service_id: int
    service_name: str
    client_id: int
    client_name: str
    client_email: str
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    price: Decimal
    notes: str | None
    cancellation_reason: str | None
    reschedule_count: int


# ---------- Dashboard / recordatorios ----------

class KpiOut(BaseModel):
    appointments_today: int
    appointments_week: int
    upcoming_confirmed: int
    cancellation_rate: float
    no_show_rate: float
    revenue_month: Decimal
    reminders_sent_week: int
    by_status: dict[str, int]
    top_services: list[dict]


class ReminderOut(ORMModel):
    id: int
    appointment_id: int
    kind: str
    channel: str
    recipient: str
    message: str
    status: str
    sent_at: datetime


class ReminderRunOut(BaseModel):
    sent: int

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AppointmentSvc, AvailabilitySvc, ClockDep, CurrentUser, PageDep, SettingsDep
from app.application.appointments import appointment_to_out
from app.application.dtos import (
    AppointmentCreateIn,
    AppointmentOut,
    CancelIn,
    DayAvailabilityOut,
    Page,
    RescheduleIn,
    SlotOut,
    StatusIn,
)
from app.domain.enums import AppointmentStatus
from app.domain.errors import BusinessRuleError

router = APIRouter(tags=["Citas y disponibilidad"])


@router.get("/availability", response_model=list[DayAvailabilityOut],
            summary="Horarios libres (público). Devuelve `days` días desde `date`.")
def availability(
    svc: AvailabilitySvc, clock: ClockDep, settings: SettingsDep,
    professional_id: int, service_id: int, date: date,
    days: Annotated[int, Query(ge=1, le=14)] = 1,
) -> list[DayAvailabilityOut]:
    # La vista pública aplica la anticipación mínima de clientes.
    earliest = clock.now() + timedelta(minutes=settings.min_advance_minutes)
    duration = svc.load(professional_id, service_id)[1].duration_minutes
    out = []
    for i in range(days):
        day = date + timedelta(days=i)
        slots = svc.slots_for_day(professional_id, service_id, day, earliest_start=earliest)
        out.append(DayAvailabilityOut(
            date=day, professional_id=professional_id, service_id=service_id,
            slots=[SlotOut(start_at=s, end_at=s + timedelta(minutes=duration)) for s in slots],
        ))
    return out


@router.get("/appointments", response_model=Page[AppointmentOut],
            summary="Listar citas (cada rol ve solo las suyas)")
def list_appointments(
    actor: CurrentUser, svc: AppointmentSvc, params: PageDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    status_: Annotated[AppointmentStatus | None, Query(alias="status")] = None,
    professional_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Page[AppointmentOut]:
    if date_from and date_to and date_to < date_from:
        raise BusinessRuleError("date_to no puede ser anterior a date_from.")
    result = svc.list(actor, params, q, status_, professional_id, date_from, date_to)
    return Page[AppointmentOut](**{**result, "items": [appointment_to_out(a) for a in result["items"]]})


@router.post("/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED,
             summary="Reservar cita")
def create_appointment(data: AppointmentCreateIn, actor: CurrentUser, svc: AppointmentSvc):
    return appointment_to_out(svc.create(actor, data))


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, actor: CurrentUser, svc: AppointmentSvc):
    return appointment_to_out(svc.get(actor, appointment_id))


@router.post("/appointments/{appointment_id}/reschedule", response_model=AppointmentOut,
             summary="Reprogramar cita")
def reschedule(appointment_id: int, data: RescheduleIn, actor: CurrentUser, svc: AppointmentSvc):
    return appointment_to_out(svc.reschedule(actor, appointment_id, data))


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentOut, summary="Cancelar cita")
def cancel(appointment_id: int, data: CancelIn, actor: CurrentUser, svc: AppointmentSvc):
    return appointment_to_out(svc.cancel(actor, appointment_id, data))


@router.post("/appointments/{appointment_id}/status", response_model=AppointmentOut,
             summary="Cerrar cita: completada o no asistió (personal)")
def set_status(appointment_id: int, data: StatusIn, actor: CurrentUser, svc: AppointmentSvc):
    return appointment_to_out(svc.set_status(actor, appointment_id, data))

"""Servicios, profesionales, horarios y excepciones.

Las lecturas del catálogo son públicas (las usa la página de reserva); las
escrituras requieren rol admin (o profesional sobre su propia agenda).
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import AdminUser, CatalogSvc, PageDep, StaffUser
from app.application.dtos import (
    ExceptionIn,
    ExceptionOut,
    Page,
    ProfessionalIn,
    ProfessionalOut,
    ServiceIn,
    ServiceOut,
    WeeklyScheduleIn,
    WorkingHourOut,
)

router = APIRouter(tags=["Catálogo"])
Q = Annotated[str | None, Query(max_length=100, description="Búsqueda por texto")]


# ----- Servicios -----
@router.get("/services", response_model=Page[ServiceOut], summary="Listar servicios (público)")
def list_services(svc: CatalogSvc, params: PageDep, q: Q = None, active: bool | None = None):
    result = svc.list_services(params, q, active)
    return Page[ServiceOut](**{**result, "items": [ServiceOut.model_validate(s) for s in result["items"]]})


@router.get("/services/{service_id}", response_model=ServiceOut, summary="Detalle de servicio")
def get_service(service_id: int, svc: CatalogSvc):
    return svc.get_service(service_id)


@router.post("/services", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(data: ServiceIn, _: AdminUser, svc: CatalogSvc):
    return svc.create_service(data)


@router.put("/services/{service_id}", response_model=ServiceOut)
def update_service(service_id: int, data: ServiceIn, _: AdminUser, svc: CatalogSvc):
    return svc.update_service(service_id, data)


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Desactivar servicio (baja lógica)")
def delete_service(service_id: int, _: AdminUser, svc: CatalogSvc):
    svc.deactivate_service(service_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----- Profesionales -----
@router.get("/professionals", response_model=Page[ProfessionalOut], summary="Listar profesionales (público)")
def list_professionals(svc: CatalogSvc, params: PageDep, q: Q = None, service_id: int | None = None,
                       active: bool | None = None):
    result = svc.list_professionals(params, q, service_id, active)
    return Page[ProfessionalOut](
        **{**result, "items": [ProfessionalOut.model_validate(p) for p in result["items"]]}
    )


@router.get("/professionals/{professional_id}", response_model=ProfessionalOut)
def get_professional(professional_id: int, svc: CatalogSvc):
    return svc.get_professional(professional_id)


@router.post("/professionals", response_model=ProfessionalOut, status_code=status.HTTP_201_CREATED)
def create_professional(data: ProfessionalIn, _: AdminUser, svc: CatalogSvc):
    return svc.create_professional(data)


@router.put("/professionals/{professional_id}", response_model=ProfessionalOut)
def update_professional(professional_id: int, data: ProfessionalIn, _: AdminUser, svc: CatalogSvc):
    return svc.update_professional(professional_id, data)


@router.get("/professionals/{professional_id}/working-hours", response_model=list[WorkingHourOut],
            summary="Horario semanal (público)")
def get_schedule(professional_id: int, svc: CatalogSvc):
    return svc.get_schedule(professional_id)


@router.put("/professionals/{professional_id}/working-hours", response_model=list[WorkingHourOut],
            summary="Reemplazar horario semanal")
def put_schedule(professional_id: int, data: WeeklyScheduleIn, actor: StaffUser, svc: CatalogSvc):
    return svc.replace_schedule(actor, professional_id, data)


# ----- Excepciones -----
@router.get("/exceptions", response_model=list[ExceptionOut], summary="Feriados y ausencias")
def list_exceptions(actor: StaffUser, svc: CatalogSvc, professional_id: int | None = None,
                    date_from: date | None = None, date_to: date | None = None):
    return svc.list_exceptions(actor, professional_id, date_from, date_to)


@router.post("/exceptions", response_model=ExceptionOut, status_code=status.HTTP_201_CREATED)
def create_exception(data: ExceptionIn, actor: StaffUser, svc: CatalogSvc):
    return svc.create_exception(actor, data)


@router.delete("/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exception(exception_id: int, actor: StaffUser, svc: CatalogSvc):
    svc.delete_exception(actor, exception_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""Casos de uso del catálogo: servicios, profesionales, horarios y excepciones."""

from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.application.dtos import ExceptionIn, ProfessionalIn, ServiceIn, WeeklyScheduleIn
from app.application.pagination import PageParams, apply_sort, paginate
from app.domain.enums import Role
from app.domain.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.domain.models import Professional, ScheduleException, Service, User, WorkingHour


def ensure_manages_professional(actor: User, professional_id: int | None) -> None:
    """Admin gestiona a todos; un profesional solo su propia agenda."""
    if actor.role == Role.ADMIN:
        return
    own = actor.professional.id if actor.professional else None
    if actor.role == Role.PROFESIONAL and professional_id is not None and own == professional_id:
        return
    raise PermissionDeniedError("Solo puedes gestionar tu propia agenda.")


class CatalogService:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ----- Servicios -----
    def list_services(self, params: PageParams, q: str | None, active: bool | None) -> dict:
        stmt = select(Service)
        if q:
            stmt = stmt.where(Service.name.ilike(f"%{q}%"))
        if active is not None:
            stmt = stmt.where(Service.is_active == active)
        stmt = apply_sort(
            stmt, params.sort,
            {"name": Service.name, "price": Service.price, "duration": Service.duration_minutes},
            Service.name.asc(),
        )
        return paginate(self.session, stmt, params)

    def get_service(self, service_id: int) -> Service:
        service = self.session.get(Service, service_id)
        if not service:
            raise NotFoundError("Servicio no encontrado.")
        return service

    def create_service(self, data: ServiceIn) -> Service:
        self._ensure_unique_service_name(data.name)
        service = Service(**data.model_dump())
        self.session.add(service)
        self.session.commit()
        return service

    def update_service(self, service_id: int, data: ServiceIn) -> Service:
        service = self.get_service(service_id)
        if data.name != service.name:
            self._ensure_unique_service_name(data.name)
        for k, v in data.model_dump().items():
            setattr(service, k, v)
        self.session.commit()
        return service

    def deactivate_service(self, service_id: int) -> None:
        # Baja lógica: borrar físicamente rompería el historial de citas.
        service = self.get_service(service_id)
        service.is_active = False
        self.session.commit()

    def _ensure_unique_service_name(self, name: str) -> None:
        if self.session.scalar(select(Service.id).where(Service.name == name)):
            raise ConflictError("Ya existe un servicio con ese nombre.")

    # ----- Profesionales -----
    def list_professionals(
        self, params: PageParams, q: str | None, service_id: int | None, active: bool | None
    ) -> dict:
        stmt = select(Professional).options(selectinload(Professional.services))
        if q:
            stmt = stmt.where(or_(Professional.full_name.ilike(f"%{q}%"), Professional.specialty.ilike(f"%{q}%")))
        if service_id:
            stmt = stmt.where(Professional.services.any(Service.id == service_id))
        if active is not None:
            stmt = stmt.where(Professional.is_active == active)
        stmt = apply_sort(
            stmt, params.sort,
            {"name": Professional.full_name, "specialty": Professional.specialty},
            Professional.full_name.asc(),
        )
        return paginate(self.session, stmt, params)

    def get_professional(self, professional_id: int) -> Professional:
        prof = self.session.get(Professional, professional_id)
        if not prof:
            raise NotFoundError("Profesional no encontrado.")
        return prof

    def create_professional(self, data: ProfessionalIn) -> Professional:
        prof = Professional(full_name=data.full_name, specialty=data.specialty, bio=data.bio,
                            is_active=data.is_active)
        self._apply_links(prof, data)
        self.session.add(prof)
        self.session.commit()
        return prof

    def update_professional(self, professional_id: int, data: ProfessionalIn) -> Professional:
        prof = self.get_professional(professional_id)
        prof.full_name, prof.specialty, prof.bio, prof.is_active = (
            data.full_name, data.specialty, data.bio, data.is_active
        )
        self._apply_links(prof, data)
        self.session.commit()
        return prof

    def _apply_links(self, prof: Professional, data: ProfessionalIn) -> None:
        if data.user_id is not None:
            user = self.session.get(User, data.user_id)
            if not user or user.role != Role.PROFESIONAL:
                raise ConflictError("El usuario vinculado debe existir y tener rol profesional.")
            taken = self.session.scalar(
                select(Professional.id).where(Professional.user_id == data.user_id)
            )
            if taken and taken != prof.id:
                raise ConflictError("Ese usuario ya está vinculado a otro profesional.")
        prof.user_id = data.user_id
        services = list(self.session.scalars(select(Service).where(Service.id.in_(data.service_ids))))
        if len(services) != len(set(data.service_ids)):
            raise NotFoundError("Alguno de los servicios indicados no existe.")
        prof.services = services

    # ----- Horario semanal -----
    def get_schedule(self, professional_id: int) -> list[WorkingHour]:
        return list(self.get_professional(professional_id).working_hours)

    def replace_schedule(self, actor: User, professional_id: int, data: WeeklyScheduleIn) -> list[WorkingHour]:
        ensure_manages_professional(actor, professional_id)
        prof = self.get_professional(professional_id)
        # Reemplazo completo: más simple y predecible que editar bloque por bloque.
        prof.working_hours.clear()
        self.session.flush()
        for b in data.blocks:
            prof.working_hours.append(WorkingHour(weekday=b.weekday, start_time=b.start_time, end_time=b.end_time))
        self.session.commit()
        return list(prof.working_hours)

    # ----- Excepciones (feriados / ausencias) -----
    def list_exceptions(
        self, actor: User, professional_id: int | None, date_from: date | None, date_to: date | None
    ) -> list[ScheduleException]:
        stmt = select(ScheduleException).order_by(ScheduleException.date)
        if actor.role == Role.PROFESIONAL:
            own = actor.professional.id if actor.professional else -1
            stmt = stmt.where(or_(ScheduleException.professional_id.is_(None),
                                  ScheduleException.professional_id == own))
        elif professional_id is not None:
            stmt = stmt.where(or_(ScheduleException.professional_id.is_(None),
                                  ScheduleException.professional_id == professional_id))
        if date_from:
            stmt = stmt.where(ScheduleException.date >= date_from)
        if date_to:
            stmt = stmt.where(ScheduleException.date <= date_to)
        return list(self.session.scalars(stmt))

    def create_exception(self, actor: User, data: ExceptionIn) -> ScheduleException:
        if data.professional_id is None and actor.role != Role.ADMIN:
            raise PermissionDeniedError("Solo un administrador puede registrar feriados generales.")
        if data.professional_id is not None:
            ensure_manages_professional(actor, data.professional_id)
            self.get_professional(data.professional_id)
        exc = ScheduleException(**data.model_dump())
        self.session.add(exc)
        self.session.commit()
        return exc

    def delete_exception(self, actor: User, exception_id: int) -> None:
        exc = self.session.get(ScheduleException, exception_id)
        if not exc:
            raise NotFoundError("Excepción no encontrada.")
        if exc.professional_id is None and actor.role != Role.ADMIN:
            raise PermissionDeniedError("Solo un administrador puede eliminar feriados generales.")
        if exc.professional_id is not None:
            ensure_manages_professional(actor, exc.professional_id)
        self.session.delete(exc)
        self.session.commit()

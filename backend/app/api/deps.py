"""Inyección de dependencias de FastAPI.

Los recursos compartidos (fábrica de sesiones, reloj, notificador) viven en
`app.state` y se crean en `create_app`, de modo que las pruebas pueden
construir la app con una BD SQLite en memoria y un reloj fijo.
"""

from collections.abc import Callable, Iterator
from typing import Annotated

import jwt
from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.appointments import AppointmentService
from app.application.availability import AvailabilityService
from app.application.catalog import CatalogService
from app.application.dashboard import DashboardService
from app.application.pagination import PageParams
from app.application.reminders import ReminderService
from app.application.users import UserService
from app.core.clock import Clock
from app.core.config import Settings
from app.core.security import decode_access_token
from app.domain.enums import Role
from app.domain.errors import AuthenticationError, PermissionDeniedError
from app.domain.models import User
from app.domain.policies import BookingPolicy

bearer = HTTPBearer(auto_error=False)


def get_session(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_clock(request: Request) -> Clock:
    return request.app.state.clock


SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
ClockDep = Annotated[Clock, Depends(get_clock)]


def get_current_user(
    session: SessionDep, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> User:
    if creds is None:
        raise AuthenticationError("Falta el token de acceso.")
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("El token expiró. Inicia sesión nuevamente.") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Token inválido.") from exc
    user = session.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise AuthenticationError("Usuario no válido o desactivado.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[User], User]:
    """Autorización declarativa por endpoint: `Depends(require_roles(Role.ADMIN))`."""

    def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise PermissionDeniedError("No tienes permisos para esta operación.")
        return user

    return checker


AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
StaffUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.PROFESIONAL))]


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 10,
    sort: Annotated[str | None, Query(description="Campo de orden; prefijo '-' para descendente")] = None,
) -> PageParams:
    return PageParams(page=page, page_size=page_size, sort=sort)


PageDep = Annotated[PageParams, Depends(page_params)]


def policy_from(settings: Settings) -> BookingPolicy:
    return BookingPolicy(
        min_advance_minutes=settings.min_advance_minutes,
        max_advance_days=settings.max_advance_days,
        cancellation_min_hours=settings.cancellation_min_hours,
        max_reschedules=settings.max_reschedules,
    )


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


def get_catalog_service(session: SessionDep) -> CatalogService:
    return CatalogService(session)


def get_availability_service(session: SessionDep, clock: ClockDep, settings: SettingsDep) -> AvailabilityService:
    return AvailabilityService(session, clock, settings.slot_step_minutes)


def get_appointment_service(
    session: SessionDep, clock: ClockDep, settings: SettingsDep,
    availability: Annotated[AvailabilityService, Depends(get_availability_service)],
) -> AppointmentService:
    return AppointmentService(session, clock, availability, policy_from(settings))


def get_reminder_service(request: Request, session: SessionDep, clock: ClockDep,
                         settings: SettingsDep) -> ReminderService:
    return ReminderService(session, clock, request.app.state.notifier, settings.reminder_hours_before)


def get_dashboard_service(session: SessionDep, clock: ClockDep) -> DashboardService:
    return DashboardService(session, clock)


UserSvc = Annotated[UserService, Depends(get_user_service)]
CatalogSvc = Annotated[CatalogService, Depends(get_catalog_service)]
AvailabilitySvc = Annotated[AvailabilityService, Depends(get_availability_service)]
AppointmentSvc = Annotated[AppointmentService, Depends(get_appointment_service)]
ReminderSvc = Annotated[ReminderService, Depends(get_reminder_service)]
DashboardSvc = Annotated[DashboardService, Depends(get_dashboard_service)]

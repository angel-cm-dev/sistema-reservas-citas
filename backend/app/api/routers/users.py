from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, PageDep, StaffUser, UserSvc
from app.application.dtos import Page, UserCreateIn, UserOut, UserUpdateIn
from app.application.users import user_to_out
from app.domain.enums import Role

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("", response_model=Page[UserOut], summary="Listar usuarios (admin; profesional solo clientes)")
def list_users(
    actor: StaffUser, svc: UserSvc, params: PageDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    role: Role | None = None,
) -> Page[UserOut]:
    # El profesional necesita buscar clientes para agendarles citas, nada más.
    if actor.role == Role.PROFESIONAL:
        role = Role.CLIENTE
    result = svc.list(params, q, role)
    return Page[UserOut](**{**result, "items": [user_to_out(u) for u in result["items"]]})


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Crear usuario")
def create_user(data: UserCreateIn, _: AdminUser, svc: UserSvc) -> UserOut:
    return user_to_out(svc.create(data))


@router.patch("/{user_id}", response_model=UserOut, summary="Actualizar usuario")
def update_user(user_id: int, data: UserUpdateIn, _: AdminUser, svc: UserSvc) -> UserOut:
    return user_to_out(svc.update(user_id, data))

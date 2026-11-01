from fastapi import APIRouter, status

from app.api.deps import CurrentUser, UserSvc
from app.application.dtos import LoginIn, RegisterIn, TokenOut, UserOut
from app.application.users import user_to_out
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenOut, summary="Iniciar sesión y obtener JWT")
def login(data: LoginIn, svc: UserSvc) -> TokenOut:
    token, user = svc.login(data)
    return TokenOut(access_token=token, user=user_to_out(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED,
             summary="Registro público de clientes")
def register(data: RegisterIn, svc: UserSvc) -> TokenOut:
    user = svc.register_client(data)
    return TokenOut(access_token=create_access_token(str(user.id), user.role), user=user_to_out(user))


@router.get("/me", response_model=UserOut, summary="Usuario autenticado")
def me(user: CurrentUser) -> UserOut:
    return user_to_out(user)

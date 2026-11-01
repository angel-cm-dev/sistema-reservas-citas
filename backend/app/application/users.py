"""Casos de uso de autenticación y gestión de usuarios."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.application.dtos import LoginIn, RegisterIn, UserCreateIn, UserOut, UserUpdateIn
from app.application.pagination import PageParams, apply_sort, paginate
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.enums import Role
from app.domain.errors import AuthenticationError, ConflictError, NotFoundError
from app.domain.models import User


def user_to_out(user: User) -> UserOut:
    out = UserOut.model_validate(user)
    out.professional_id = user.professional.id if user.professional else None
    return out


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def login(self, data: LoginIn) -> tuple[str, User]:
        user = self.session.scalar(select(User).where(User.email == data.email.lower()))
        # Mismo mensaje para "no existe" y "clave incorrecta": no revelamos
        # qué correos están registrados (enumeración de usuarios).
        if not user or not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Correo o contraseña incorrectos.")
        if not user.is_active:
            raise AuthenticationError("La cuenta está desactivada.")
        return create_access_token(str(user.id), user.role), user

    def register_client(self, data: RegisterIn) -> User:
        # El registro público SIEMPRE crea clientes: un visitante no puede
        # auto-asignarse el rol admin o profesional.
        return self._create(data.email, data.full_name, data.phone, data.password, Role.CLIENTE)

    def create(self, data: UserCreateIn) -> User:
        return self._create(data.email, data.full_name, data.phone, data.password, data.role)

    def _create(self, email: str, full_name: str, phone: str | None, password: str, role: Role) -> User:
        email = email.lower()
        if self.session.scalar(select(User.id).where(User.email == email)):
            raise ConflictError("Ya existe un usuario con ese correo.")
        user = User(
            email=email, full_name=full_name, phone=phone,
            password_hash=hash_password(password), role=role, is_active=True,
        )
        self.session.add(user)
        self.session.commit()
        return user

    def get(self, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if not user:
            raise NotFoundError("Usuario no encontrado.")
        return user

    def update(self, user_id: int, data: UserUpdateIn) -> User:
        user = self.get(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        self.session.commit()
        return user

    def list(self, params: PageParams, q: str | None, role: str | None) -> dict:
        stmt = select(User)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
        if role:
            stmt = stmt.where(User.role == role)
        stmt = apply_sort(
            stmt, params.sort,
            {"name": User.full_name, "email": User.email, "created_at": User.created_at},
            User.full_name.asc(),
        )
        return paginate(self.session, stmt, params)

"""Fixtures de prueba: SQLite en memoria + reloj fijo, sin Docker.

"Ahora" es el lunes 2026-11-02 08:00 (hora local del negocio), así las
reglas de anticipación y ventanas de cancelación son deterministas.
"""

from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.clock import FixedClock
from app.core.config import Settings
from app.core.security import create_access_token
from app.domain.models import Base, User
from app.infrastructure.seed import seed
from app.main import create_app

NOW = datetime(2026, 11, 2, 8, 0)


class FakeNotifier:
    channel = "email"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> bool:
        self.sent.append((recipient, message))
        return True


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()


@pytest.fixture
def app(clock, notifier):
    settings = Settings(database_url="sqlite://", reminders_enabled=False, log_level="WARNING",
                        _env_file=None)
    application = create_app(settings=settings, clock=clock, notifier=notifier)
    Base.metadata.create_all(application.state.engine)
    with application.state.session_factory() as session:
        seed(session, clock)
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db(app):
    with app.state.session_factory() as session:
        yield session


def _token_for(app, email: str) -> dict[str, str]:
    with app.state.session_factory() as s:
        user = s.scalar(select(User).where(User.email == email))
        assert user is not None
        return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}


@pytest.fixture
def admin_h(app):
    return _token_for(app, "admin@demo.pe")


@pytest.fixture
def cliente_h(app):
    return _token_for(app, "cliente@demo.pe")


@pytest.fixture
def otro_cliente_h(app):
    return _token_for(app, "jorge.diaz@demo.pe")


@pytest.fixture
def lopez_h(app):
    return _token_for(app, "lucia.lopez@demo.pe")


@pytest.fixture
def quispe_h(app):
    return _token_for(app, "marco.quispe@demo.pe")

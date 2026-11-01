"""Punto de entrada: composición de la aplicación (composition root).

`create_app` arma todas las dependencias. Recibir `settings` y `clock` como
parámetros permite que las pruebas inyecten SQLite en memoria y un reloj fijo.
"""

import logging
import time as _time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.errors import register_error_handlers
from app.api.routers import admin, appointments, auth, catalog, users
from app.core.clock import Clock, SystemClock
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, log_event, request_id_var
from app.infrastructure.db import build_engine, build_session_factory
from app.infrastructure.notifier import LogNotifier, Notifier
from app.infrastructure.scheduler import build_scheduler

logger = logging.getLogger("http")


def create_app(
    settings: Settings | None = None, clock: Clock | None = None, notifier: Notifier | None = None
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    clock = clock or SystemClock(settings.timezone)
    notifier = notifier or LogNotifier()
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.seed_on_startup:
            from app.infrastructure.seed import seed
            with session_factory() as s:
                seed(s, clock)
        scheduler = None
        if settings.reminders_enabled:
            scheduler = build_scheduler(session_factory, clock, notifier,
                                        settings.reminder_hours_before, settings.reminder_interval_minutes)
            scheduler.start()
        yield
        if scheduler:
            scheduler.shutdown(wait=False)
        engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "API de reservas de citas: profesionales, servicios, horarios, disponibilidad sin "
            "solapamientos, reservas con políticas y recordatorios. Autentícate con "
            "`POST /api/v1/auth/login` y usa el botón **Authorize** con el token."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.clock = clock
    app.state.notifier = notifier
    app.state.engine = engine
    app.state.session_factory = session_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        # Correlación: cada petición lleva un X-Request-ID que aparece en logs y errores.
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        token = request_id_var.set(rid)
        start = _time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        log_event(logger, "request", method=request.method, path=request.url.path,
                  status=response.status_code, ms=round((_time.perf_counter() - start) * 1000, 1),
                  request_id=rid)
        return response

    register_error_handlers(app)

    for router in (auth.router, users.router, catalog.router, appointments.router, admin.router):
        app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["Salud"], summary="Estado del servicio y la base de datos")
    def health():
        db_ok = True
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_ok = False
        return {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "error",
                "version": app.version}

    return app


app = create_app()

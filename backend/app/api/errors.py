"""Manejo global de errores en formato ProblemDetails (RFC 9457).

Toda respuesta de error tiene la misma forma, lo que simplifica el manejo en
el frontend: `{type, title, status, detail, instance, errors?}`.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_var
from app.domain.errors import DomainError

logger = logging.getLogger("errors")
MEDIA = "application/problem+json"


def problem(request: Request, status: int, title: str, detail: str, code: str,
            errors: list | None = None) -> JSONResponse:
    body = {
        "type": f"https://httpstatuses.io/{status}#{code}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "request_id": request_id_var.get(),
    }
    if errors:
        body["errors"] = errors
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(body, status_code=status, media_type=MEDIA, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_handler(request: Request, exc: DomainError):
        return problem(request, exc.status_code, exc.title, exc.detail, exc.code)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        return problem(request, 422, "Datos inválidos", "Revisa los campos indicados.", "validation", errors)

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        return problem(request, exc.status_code, "Error HTTP", str(exc.detail), "http")

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        logger.warning("integrity_error: %s", exc.orig)
        return problem(request, 409, "Conflicto", "La operación viola una restricción de datos.", "integrity")

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        # Nunca filtramos el stacktrace al cliente; queda en el log con su request_id.
        logger.exception("unhandled_error")
        return problem(request, 500, "Error interno", "Ocurrió un error inesperado.", "internal")

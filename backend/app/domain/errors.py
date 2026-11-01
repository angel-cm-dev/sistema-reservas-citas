"""Excepciones de dominio.

La capa de dominio/aplicación lanza estas excepciones sin saber nada de HTTP;
la capa API las traduce a respuestas ProblemDetails (RFC 9457).
"""


class DomainError(Exception):
    status_code = 400
    title = "Solicitud inválida"
    code = "bad_request"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    status_code = 404
    title = "Recurso no encontrado"
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    title = "Conflicto"
    code = "conflict"


class BusinessRuleError(DomainError):
    status_code = 422
    title = "Regla de negocio incumplida"
    code = "business_rule"


class AuthenticationError(DomainError):
    status_code = 401
    title = "No autenticado"
    code = "unauthenticated"


class PermissionDeniedError(DomainError):
    status_code = 403
    title = "Acceso denegado"
    code = "forbidden"

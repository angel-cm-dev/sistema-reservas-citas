"""Paginación y ordenamiento reutilizables para cualquier consulta SELECT."""

import math
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.domain.errors import DomainError


@dataclass(frozen=True)
class PageParams:
    page: int = 1
    page_size: int = 10
    sort: str | None = None  # "campo" asc o "-campo" desc


def apply_sort(stmt: Select, sort: str | None, allowed: dict[str, Any], default: Any) -> Select:
    """Aplica el orden pedido solo si el campo está en la lista blanca.

    La lista blanca evita que el cliente ordene por columnas arbitrarias
    (riesgo de inyección o de exponer datos internos).
    """
    if not sort:
        return stmt.order_by(default)
    desc = sort.startswith("-")
    key = sort.lstrip("-")
    column = allowed.get(key)
    if column is None:
        raise DomainError(f"No se puede ordenar por '{key}'. Opciones: {', '.join(allowed)}")
    return stmt.order_by(column.desc() if desc else column.asc())


def paginate(session: Session, stmt: Select, params: PageParams) -> dict:
    total = session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = session.scalars(
        stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)
    ).unique().all()
    return {
        "items": list(items),
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": max(1, math.ceil(total / params.page_size)) if total else 0,
    }

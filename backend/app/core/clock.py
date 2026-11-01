"""Reloj inyectable.

Las reglas de negocio dependen de "ahora" (anticipación mínima, ventana de
cancelación, recordatorios). Abstraer el reloj permite que las pruebas fijen
una fecha determinista en lugar de depender de la hora real.
"""

from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def __init__(self, tz: str) -> None:
        self._tz = ZoneInfo(tz)

    def now(self) -> datetime:
        # Hora local del negocio sin tzinfo (ver ADR 0002).
        return datetime.now(self._tz).replace(tzinfo=None, microsecond=0)


class FixedClock:
    def __init__(self, fixed: datetime) -> None:
        self.fixed = fixed

    def now(self) -> datetime:
        return self.fixed

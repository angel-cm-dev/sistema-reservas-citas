"""Cálculo de disponibilidad: lógica pura, sin base de datos.

Algoritmo (para un profesional, un servicio y un día):

1. Tomar los bloques de atención del día de la semana (p. ej. 09:00-13:00 y 14:00-18:00).
2. Restar las excepciones del día (feriado completo o ausencia parcial).
3. Recorrer cada bloque libre en pasos de `step` minutos y proponer un inicio
   si [inicio, inicio + duración) cabe COMPLETO en el bloque.
4. Descartar inicios que se solapen con citas existentes o que no respeten la
   anticipación mínima respecto de "ahora".

Dos intervalos semiabiertos [a1, a2) y [b1, b2) se solapan si a1 < b2 y b1 < a2.
Usar intervalos semiabiertos permite citas consecutivas (10:00-10:30 y 10:30-11:00)
sin considerarlas en conflicto.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


@dataclass(frozen=True)
class Interval:
    start: datetime
    end: datetime

    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class Block:
    """Rango horario dentro de un día (sin fecha)."""

    start: time
    end: time


@dataclass(frozen=True)
class DayException:
    """Excepción de un día. start/end nulos = día completo bloqueado."""

    start: time | None = None
    end: time | None = None

    @property
    def full_day(self) -> bool:
        return self.start is None or self.end is None


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def subtract_exceptions(
    day: date, blocks: Iterable[Block], exceptions: Iterable[DayException]
) -> list[Interval]:
    """Convierte los bloques del día en intervalos y les resta las excepciones."""
    free = [Interval(datetime.combine(day, b.start), datetime.combine(day, b.end)) for b in blocks]
    free.sort(key=lambda i: i.start)
    for exc in exceptions:
        if exc.full_day:
            return []
        assert exc.start is not None and exc.end is not None
        cut = Interval(datetime.combine(day, exc.start), datetime.combine(day, exc.end))
        result: list[Interval] = []
        for iv in free:
            if not iv.overlaps(cut):
                result.append(iv)
                continue
            # El corte puede dejar un trozo antes, uno después, o ambos.
            if iv.start < cut.start:
                result.append(Interval(iv.start, cut.start))
            if cut.end < iv.end:
                result.append(Interval(cut.end, iv.end))
        free = result
    return free


def compute_slots(
    day: date,
    blocks: Iterable[Block],
    exceptions: Iterable[DayException],
    busy: Iterable[Interval],
    duration_minutes: int,
    step_minutes: int,
    earliest_start: datetime | None = None,
) -> list[datetime]:
    """Devuelve los inicios disponibles del día, ordenados."""
    if duration_minutes <= 0 or step_minutes <= 0:
        raise ValueError("La duración y el paso deben ser positivos")

    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)
    busy_list = list(busy)
    slots: list[datetime] = []

    for free in subtract_exceptions(day, blocks, exceptions):
        cursor = free.start
        while cursor + duration <= free.end:
            candidate = Interval(cursor, cursor + duration)
            too_early = earliest_start is not None and cursor < earliest_start
            if not too_early and not any(candidate.overlaps(b) for b in busy_list):
                slots.append(cursor)
            cursor += step
    return slots

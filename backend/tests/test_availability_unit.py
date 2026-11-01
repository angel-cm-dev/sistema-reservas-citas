"""Pruebas unitarias del cálculo de disponibilidad (lógica pura)."""

from datetime import date, datetime, time

import pytest

from app.domain.availability import Block, DayException, Interval, compute_slots, subtract_exceptions

DAY = date(2026, 11, 3)


def at(h: int, m: int = 0) -> datetime:
    return datetime.combine(DAY, time(h, m))


def test_slots_fit_completely_inside_block():
    slots = compute_slots(DAY, [Block(time(9), time(12))], [], [], duration_minutes=60, step_minutes=30)
    assert slots == [at(9), at(9, 30), at(10), at(10, 30), at(11)]


def test_busy_interval_removes_overlaps_but_allows_adjacent():
    busy = [Interval(at(10), at(11))]
    slots = compute_slots(DAY, [Block(time(9), time(12))], [], busy, duration_minutes=60, step_minutes=30)
    # 9:00-10:00 termina justo cuando empieza la cita: no hay solapamiento.
    assert slots == [at(9), at(11)]


def test_partial_exception_splits_block():
    free = subtract_exceptions(DAY, [Block(time(9), time(13))], [DayException(time(10), time(11))])
    assert free == [Interval(at(9), at(10)), Interval(at(11), at(13))]


def test_full_day_exception_returns_no_slots():
    slots = compute_slots(DAY, [Block(time(9), time(18))], [DayException()], [], 30, 15)
    assert slots == []


def test_multiple_blocks_morning_and_afternoon():
    blocks = [Block(time(14), time(15)), Block(time(9), time(10))]
    slots = compute_slots(DAY, blocks, [], [], duration_minutes=30, step_minutes=30)
    assert slots == [at(9), at(9, 30), at(14), at(14, 30)]


def test_earliest_start_filters_past_or_too_soon():
    slots = compute_slots(DAY, [Block(time(9), time(11))], [], [], 30, 30, earliest_start=at(10))
    assert slots == [at(10), at(10, 30)]


def test_service_longer_than_block_has_no_slots():
    assert compute_slots(DAY, [Block(time(9), time(9, 30))], [], [], 45, 15) == []


@pytest.mark.parametrize("duration,step", [(0, 15), (30, 0), (-5, 15)])
def test_invalid_parameters_raise(duration, step):
    with pytest.raises(ValueError):
        compute_slots(DAY, [Block(time(9), time(10))], [], [], duration, step)

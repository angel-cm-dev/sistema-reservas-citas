"""Pruebas unitarias de las políticas de reserva/cancelación/reprogramación."""

from datetime import datetime, timedelta

import pytest

from app.domain.enums import AppointmentStatus, Role
from app.domain.errors import BusinessRuleError
from app.domain.policies import (
    BookingPolicy,
    ensure_bookable_window,
    ensure_can_cancel,
    ensure_can_close,
    ensure_can_reschedule,
)

NOW = datetime(2026, 11, 2, 8, 0)
POLICY = BookingPolicy(min_advance_minutes=120, max_advance_days=60, cancellation_min_hours=24, max_reschedules=2)
CONF = AppointmentStatus.CONFIRMADA


def test_cannot_book_in_the_past():
    with pytest.raises(BusinessRuleError, match="pasada"):
        ensure_bookable_window(NOW - timedelta(minutes=1), NOW, POLICY)


def test_min_advance_is_enforced():
    with pytest.raises(BusinessRuleError, match="anticipación"):
        ensure_bookable_window(NOW + timedelta(minutes=60), NOW, POLICY)
    ensure_bookable_window(NOW + timedelta(minutes=120), NOW, POLICY)


def test_max_advance_is_enforced():
    with pytest.raises(BusinessRuleError, match="60 días"):
        ensure_bookable_window(NOW + timedelta(days=61), NOW, POLICY)


def test_client_cannot_cancel_inside_window_but_staff_can():
    start = NOW + timedelta(hours=5)
    with pytest.raises(BusinessRuleError, match="24 horas"):
        ensure_can_cancel(CONF, start, NOW, Role.CLIENTE, POLICY)
    ensure_can_cancel(CONF, start, NOW, Role.PROFESIONAL, POLICY)
    ensure_can_cancel(CONF, start, NOW, Role.ADMIN, POLICY)


def test_cannot_cancel_twice():
    with pytest.raises(BusinessRuleError):
        ensure_can_cancel(AppointmentStatus.CANCELADA, NOW + timedelta(days=3), NOW, Role.ADMIN, POLICY)


def test_client_reschedule_limit():
    start = NOW + timedelta(days=3)
    ensure_can_reschedule(CONF, start, 1, NOW, Role.CLIENTE, POLICY)
    with pytest.raises(BusinessRuleError, match="máximo"):
        ensure_can_reschedule(CONF, start, 2, NOW, Role.CLIENTE, POLICY)
    # El personal no tiene límite (p. ej. si el profesional enferma).
    ensure_can_reschedule(CONF, start, 5, NOW, Role.ADMIN, POLICY)


def test_cannot_close_future_appointment():
    with pytest.raises(BusinessRuleError, match="no ha comenzado"):
        ensure_can_close(CONF, NOW + timedelta(hours=1), NOW)
    ensure_can_close(CONF, NOW - timedelta(hours=1), NOW)

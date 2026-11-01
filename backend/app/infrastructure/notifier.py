"""Canal de notificaciones.

`Notifier` es un puerto: hoy solo existe una implementación simulada que
escribe en el log, pero se podría agregar una de correo (SMTP/SES) o WhatsApp
sin tocar el servicio de recordatorios.
"""

import logging
from typing import Protocol

from app.core.logging import log_event

logger = logging.getLogger("notifier")


class Notifier(Protocol):
    channel: str

    def send(self, recipient: str, message: str) -> bool: ...


class LogNotifier:
    channel = "email"

    def send(self, recipient: str, message: str) -> bool:
        log_event(logger, "recordatorio_simulado", recipient=recipient, message=message)
        return True

"""Configuración centralizada leída de variables de entorno (12-factor).

Todas las reglas de negocio parametrizables (anticipación mínima, ventana de
cancelación, etc.) viven aquí para poder ajustarlas sin tocar código.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Sistema de Reservas de Citas"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./reservas.db"

    jwt_secret: str = "cambia-este-secreto-en-produccion-minimo-32-caracteres"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 120

    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # Zona horaria del negocio: todas las fechas se guardan como hora local
    # "naive" de esta zona (ver docs/decisiones/0002-zona-horaria.md).
    timezone: str = "America/Lima"

    # Políticas de reserva
    slot_step_minutes: int = 15
    min_advance_minutes: int = 120
    max_advance_days: int = 60
    cancellation_min_hours: int = 24
    max_reschedules: int = 2

    # Recordatorios
    reminders_enabled: bool = True
    reminder_hours_before: int = 24
    reminder_interval_minutes: int = 5

    seed_on_startup: bool = False
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

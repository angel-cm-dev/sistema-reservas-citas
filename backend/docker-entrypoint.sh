#!/bin/sh
# Aplica migraciones, carga datos demo (idempotente) y arranca la API.
set -e
alembic upgrade head
if [ "${SEED_ON_START:-true}" = "true" ]; then
  python -m app.infrastructure.seed
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers

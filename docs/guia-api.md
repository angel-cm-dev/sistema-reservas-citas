# Guía de la API (ejemplos curl)

Base: `http://localhost:8000/api/v1` · Swagger UI: `http://localhost:8000/docs` · ReDoc: `http://localhost:8000/redoc`

> Los IDs de los ejemplos corresponden a los datos semilla (1 = Lucía López / Consulta nutricional). Ajusta fechas a días hábiles futuros.

## 1. Autenticación

```bash
# Login: devuelve access_token y el usuario
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.pe","password":"Demo123!"}'

# Guarda el token en una variable (requiere jq)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"cliente@demo.pe","password":"Demo123!"}' | jq -r .access_token)

# Registro público (siempre crea rol cliente)
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"nuevo@demo.pe","full_name":"Nuevo Cliente","password":"Clave1234"}'

curl -s http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $TOKEN"
```

## 2. Catálogo (público)

```bash
# Servicios: búsqueda, filtro, orden (- = descendente) y paginación
curl -s "http://localhost:8000/api/v1/services?q=nutri&active=true&sort=-price&page=1&page_size=10"

# Profesionales que ofrecen un servicio
curl -s "http://localhost:8000/api/v1/professionals?service_id=1"

# Horario semanal de un profesional
curl -s http://localhost:8000/api/v1/professionals/1/working-hours
```

## 3. Disponibilidad

```bash
# Horarios libres de 7 días desde una fecha
curl -s "http://localhost:8000/api/v1/availability?professional_id=1&service_id=1&date=2026-11-03&days=7"
```

Respuesta (resumida):

```json
[
  {
    "date": "2026-11-03",
    "professional_id": 1,
    "service_id": 1,
    "slots": [
      {"start_at": "2026-11-03T09:00:00", "end_at": "2026-11-03T09:45:00"},
      {"start_at": "2026-11-03T09:15:00", "end_at": "2026-11-03T10:00:00"}
    ]
  }
]
```

## 4. Citas

```bash
# Reservar (como cliente)
curl -s -X POST http://localhost:8000/api/v1/appointments \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"professional_id":1,"service_id":1,"start_at":"2026-11-03T11:00:00","notes":"Primera consulta"}'

# Listar mis citas con filtros
curl -s "http://localhost:8000/api/v1/appointments?status=confirmada&date_from=2026-11-01&sort=start_at" \
  -H "Authorization: Bearer $TOKEN"

# Reprogramar
curl -s -X POST http://localhost:8000/api/v1/appointments/10/reschedule \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"start_at":"2026-11-04T09:00:00"}'

# Cancelar
curl -s -X POST http://localhost:8000/api/v1/appointments/10/cancel \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reason":"No podré asistir"}'

# Cerrar como completada (personal; solo después del inicio)
curl -s -X POST http://localhost:8000/api/v1/appointments/10/status \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"completada"}'
```

## 5. Horarios y excepciones (personal)

```bash
# Reemplazar el horario semanal (admin o el propio profesional)
curl -s -X PUT http://localhost:8000/api/v1/professionals/1/working-hours \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"blocks":[{"weekday":0,"start_time":"09:00","end_time":"13:00"},{"weekday":0,"start_time":"14:00","end_time":"18:00"}]}'

# Feriado general (solo admin)
curl -s -X POST http://localhost:8000/api/v1/exceptions \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"date":"2026-12-25","reason":"Navidad"}'

# Ausencia parcial de un profesional
curl -s -X POST http://localhost:8000/api/v1/exceptions \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"professional_id":1,"date":"2026-11-20","start_time":"09:00","end_time":"11:00","reason":"Congreso"}'
```

## 6. Panel y recordatorios

```bash
curl -s http://localhost:8000/api/v1/dashboard/kpis -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X POST http://localhost:8000/api/v1/reminders/run -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s "http://localhost:8000/api/v1/reminders?page=1" -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Formato de errores (ProblemDetails)

Todas las respuestas de error usan `Content-Type: application/problem+json`:

```json
{
  "type": "https://httpstatuses.io/409#conflict",
  "title": "Conflicto",
  "status": 409,
  "detail": "El horario seleccionado no está disponible (fuera de horario, feriado o ya ocupado).",
  "instance": "/api/v1/appointments",
  "request_id": "a1b2c3d4e5f6"
}
```

Errores de validación (422) incluyen `errors: [{"field": "price", "message": "..."}]`.

| Código | Cuándo |
|---|---|
| 400 | Parámetro inválido (p. ej. orden por un campo no permitido) |
| 401 | Falta token, token inválido o expirado, credenciales incorrectas |
| 403 | El rol no permite la operación |
| 404 | Recurso inexistente o ajeno |
| 409 | Horario ocupado, solape del cliente, duplicados |
| 422 | Validación de datos o regla de negocio (anticipación, ventana de cancelación, límite de reprogramaciones) |

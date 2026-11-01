# Modelo de datos

```mermaid
erDiagram
  USERS ||--o| PROFESSIONALS : "vinculado a"
  USERS ||--o{ APPOINTMENTS : "reserva (cliente)"
  PROFESSIONALS ||--o{ WORKING_HOURS : tiene
  PROFESSIONALS ||--o{ SCHEDULE_EXCEPTIONS : "ausencias"
  PROFESSIONALS }o--o{ SERVICES : "ofrece (professional_services)"
  PROFESSIONALS ||--o{ APPOINTMENTS : atiende
  SERVICES ||--o{ APPOINTMENTS : "se agenda"
  APPOINTMENTS ||--o{ REMINDER_LOGS : genera

  USERS {
    int id PK
    string email UK
    string full_name
    string phone
    string password_hash
    string role "admin | profesional | cliente"
    bool is_active
    datetime created_at
  }
  SERVICES {
    int id PK
    string name UK
    text description
    int duration_minutes
    numeric price
    bool is_active
  }
  PROFESSIONALS {
    int id PK
    int user_id FK,UK "nullable"
    string full_name
    string specialty
    text bio
    bool is_active
  }
  WORKING_HOURS {
    int id PK
    int professional_id FK
    int weekday "0=lunes..6=domingo"
    time start_time
    time end_time
  }
  SCHEDULE_EXCEPTIONS {
    int id PK
    int professional_id FK "NULL = feriado general"
    date date
    time start_time "NULL = día completo"
    time end_time
    string reason
  }
  APPOINTMENTS {
    int id PK
    int professional_id FK
    int service_id FK
    int client_id FK
    datetime start_at
    datetime end_at
    string status "confirmada | cancelada | completada | no_asistio"
    numeric price "congelado al reservar"
    text notes
    string cancellation_reason
    int reschedule_count
    datetime created_at
    datetime updated_at
  }
  REMINDER_LOGS {
    int id PK
    int appointment_id FK
    string kind "UK con appointment_id"
    string channel
    string recipient
    text message
    string status
    datetime sent_at
  }
```

## Tablas

| Tabla | Propósito | Reglas relevantes |
|---|---|---|
| `users` | Cuentas de acceso de los tres roles. | Email único (índice). Contraseña solo como hash bcrypt. |
| `services` | Catálogo con duración y precio. | Nombre único. Baja lógica con `is_active`. |
| `professionals` | Personas que atienden. | `user_id` opcional y único: permite que el profesional inicie sesión y gestione su agenda. |
| `professional_services` | Relación N:M profesional–servicio. | La disponibilidad exige que el profesional ofrezca el servicio. |
| `working_hours` | Bloques semanales de atención. | `CHECK weekday BETWEEN 0 AND 6`, `CHECK end_time > start_time`; la API rechaza bloques que se cruzan en el mismo día. |
| `schedule_exceptions` | Feriados y ausencias. | `professional_id` nulo = afecta a todos. `start/end` nulos = día completo. |
| `appointments` | Citas. | `CHECK end_at > start_at`. Índice compuesto `(professional_id, start_at)` para consultar la agenda de un día. El precio se copia del servicio al reservar. |
| `reminder_logs` | Bitácora de recordatorios enviados. | `UNIQUE (appointment_id, kind)`: como máximo un recordatorio de cada tipo por cita (idempotencia). |

## Estados de una cita

```mermaid
stateDiagram-v2
  [*] --> confirmada: reservar
  confirmada --> confirmada: reprogramar
  confirmada --> cancelada: cancelar
  confirmada --> completada: cerrar (después del inicio)
  confirmada --> no_asistio: cerrar (después del inicio)
  cancelada --> [*]
  completada --> [*]
  no_asistio --> [*]
```

Las citas `cancelada` liberan el horario; `completada` y `no_asistio` siguen ocupándolo para no reabrir huecos en el historial.

## Migraciones

- `backend/alembic/versions/0001_esquema_inicial.py` crea el esquema completo.
- Una prueba (`tests/test_migrations.py`) aplica la migración sobre SQLite y verifica que las tablas y columnas coincidan con los modelos, y que el `downgrade` funcione.

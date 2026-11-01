# Sistema de Reservas de Citas

Plataforma full-stack para gestionar la agenda de un centro de servicios (nutrición, fisioterapia, consultorios, salones, etc.): **profesionales y servicios con duración y precio, horarios de atención con feriados y ausencias, cálculo de disponibilidad sin solapamientos, reservas con políticas de cancelación/reprogramación, calendario semanal, recordatorios automáticos y una página pública de reserva** para clientes.

> Proyecto de portafolio. Todos los datos de ejemplo son **ficticios**.

![Stack](https://img.shields.io/badge/FastAPI-0.162-009688) ![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB) ![React](https://img.shields.io/badge/React-18-61DAFB) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1) ![Licencia](https://img.shields.io/badge/licencia-MIT-green)

---

## Características

| Área | Qué incluye |
|---|---|
| **Catálogo** | Servicios (duración, precio, baja lógica) y profesionales con los servicios que ofrecen. |
| **Horarios** | Bloques semanales por profesional (p. ej. 09-13 y 14-18), validación de cruces. |
| **Excepciones** | Feriados generales (afectan a todos) y ausencias por profesional, de día completo o por rango de horas. |
| **Disponibilidad** | Algoritmo puro que resta excepciones y citas existentes; pasos de 15 min configurables; intervalos semiabiertos (citas consecutivas permitidas). |
| **Reservas** | Validación de anticipación mínima/máxima, sin solapes para el profesional **ni para el cliente**, bloqueo pesimista en PostgreSQL, precio congelado al reservar. |
| **Políticas** | Cliente cancela/reprograma hasta 24 h antes, máximo 2 reprogramaciones; el personal puede hacerlo siempre. Cierre como *completada* o *no asistió*. |
| **Recordatorios** | Job programado (APScheduler) que "envía" (simulado) un aviso 24 h antes y lo registra; idempotente por restricción única. |
| **Calendario** | Vista semanal tipo agenda, filtro por profesional y detalle con acciones. |
| **Página pública** | `/reservar`: servicio → profesional → horario libre → registro/login rápido → confirmación. |
| **Panel** | KPIs: citas hoy/semana, próximas, ingresos del mes, tasa de cancelación e inasistencia, servicios top. |
| **Seguridad** | JWT, roles `admin` / `profesional` / `cliente`, autorización por endpoint, bcrypt, errores ProblemDetails. |
| **Calidad** | 50 pruebas backend (unitarias + integración + migraciones), 28 pruebas frontend, CI en GitHub Actions. |

## Arquitectura

```mermaid
flowchart LR
  subgraph Cliente
    B[Navegador<br/>React + Vite + Tailwind]
  end
  subgraph Docker
    N[nginx<br/>SPA + proxy /api]
    subgraph API[FastAPI]
      R[Routers / API<br/>DTOs · JWT · ProblemDetails]
      S[Aplicación<br/>casos de uso]
      D[Dominio<br/>disponibilidad · políticas]
      I[Infraestructura<br/>SQLAlchemy · scheduler · notifier]
    end
    P[(PostgreSQL)]
  end
  B -->|HTTPS| N -->|/api/v1| R --> S --> D
  S --> I --> P
  I -.->|cada 5 min| J[[Job de recordatorios]]
```

Detalle de capas, flujo de una petición y decisiones en [`docs/arquitectura.md`](docs/arquitectura.md).

## Stack y justificación

| Tecnología | Por qué |
|---|---|
| **FastAPI** | Validación automática con Pydantic, OpenAPI/Swagger gratis y excelente rendimiento. |
| **SQLAlchemy 2 + Alembic** | ORM tipado (`Mapped[...]`) y migraciones versionadas reproducibles. |
| **Pydantic v2** | DTOs con validación declarativa y mensajes claros. |
| **PostgreSQL 16** | Transacciones robustas y `SELECT ... FOR UPDATE` para evitar reservas dobles concurrentes. |
| **SQLite (pruebas)** | Las pruebas corren en memoria, sin Docker, en segundos. |
| **APScheduler** | Job periódico en el mismo proceso, suficiente para el volumen de un centro. |
| **bcrypt + PyJWT** | Hash de contraseñas lento por diseño y tokens sin estado. |
| **React 18 + TypeScript + Vite** | Tipado de extremo a extremo y builds rápidos. |
| **Tailwind CSS** | Diseño consistente, responsive y modo oscuro con `dark:`. |
| **Vitest + Testing Library** | Pruebas rápidas con la misma configuración de Vite. |

## Inicio rápido con Docker (un comando)

```bash
cp .env.example .env        # opcional: ajusta secretos
docker compose up --build
```

- Frontend: <http://localhost:8080> (página pública: <http://localhost:8080/reservar>)
- API + Swagger: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

El contenedor del backend aplica las migraciones (`alembic upgrade head`) y carga los datos demo automáticamente.

## Inicio sin Docker

### Backend (Python 3.12+)

Probado con Python 3.14 en local y 3.13 en CI/Docker; las versiones de dependencias están fijadas en `requirements.txt`.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                 # usa SQLite local por defecto
alembic upgrade head                 # crea el esquema
python -m app.infrastructure.seed    # datos demo ficticios
uvicorn app.main:app --reload        # http://localhost:8000/docs
```

Para usar PostgreSQL local cambia `DATABASE_URL` a `postgresql+psycopg://usuario:clave@localhost:5432/reservas`.

### Frontend (Node 20+)

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173 (proxy /api → :8000)
```

## Credenciales demo

Todas usan la contraseña **`Demo123!`**:

| Rol | Correo | Qué puede hacer |
|---|---|---|
| Administrador | `admin@demo.pe` | Todo: catálogo, horarios, feriados, citas, recordatorios, panel. |
| Profesional | `lucia.lopez@demo.pe` / `marco.quispe@demo.pe` | Su agenda, su horario, sus ausencias, cerrar sus citas. |
| Cliente | `cliente@demo.pe` | Reservar, ver, reprogramar y cancelar sus citas. |

## Endpoints principales

Prefijo: `/api/v1`. Documentación interactiva en `/docs`. Ejemplos `curl` en [`docs/guia-api.md`](docs/guia-api.md).

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| POST | `/auth/login` | Público | Obtiene JWT |
| POST | `/auth/register` | Público | Registro de clientes |
| GET | `/auth/me` | Autenticado | Usuario actual |
| GET | `/services` | Público | Servicios (búsqueda, filtro, orden, paginación) |
| POST/PUT/DELETE | `/services[/{id}]` | Admin | Gestión de servicios |
| GET | `/professionals` | Público | Profesionales (filtro por servicio) |
| POST/PUT | `/professionals[/{id}]` | Admin | Gestión de profesionales |
| GET/PUT | `/professionals/{id}/working-hours` | Público / Admin o el propio profesional | Horario semanal |
| GET/POST/DELETE | `/exceptions` | Admin / Profesional | Feriados y ausencias |
| GET | `/availability` | Público | Horarios libres por día (`days` hasta 14) |
| GET | `/appointments` | Autenticado (filtrado por rol) | Listado con filtros y paginación |
| POST | `/appointments` | Autenticado | Reservar |
| POST | `/appointments/{id}/reschedule` | Dueño / Personal | Reprogramar |
| POST | `/appointments/{id}/cancel` | Dueño / Personal | Cancelar |
| POST | `/appointments/{id}/status` | Personal | Completada / No asistió |
| GET | `/dashboard/kpis` | Admin / Profesional | KPIs |
| GET | `/reminders` · POST `/reminders/run` | Admin | Historial / ejecutar job |
| GET | `/users` · POST · PATCH | Admin (profesional: solo lista clientes) | Usuarios |
| GET | `/health` | Público | Estado de API y BD |

## Pruebas

```bash
# Backend: unitarias + integración + migración, con SQLite en memoria (sin Docker)
cd backend && pytest                 # 50 pruebas
ruff check .                         # lint

# Frontend
cd frontend && npm test              # 28 pruebas (Vitest)
npm run lint && npm run build
```

Las pruebas del backend fijan "ahora" en el lunes 2026-11-02 08:00 con un **reloj inyectable**, así las reglas de anticipación y cancelación son deterministas.

## Estructura de carpetas

```
sistema-reservas-citas/
├── backend/
│   ├── app/
│   │   ├── core/            # Configuración, seguridad (JWT/bcrypt), logging JSON, reloj
│   │   ├── domain/          # Entidades, enums, errores, disponibilidad y políticas (lógica pura)
│   │   ├── application/     # Casos de uso (servicios), DTOs, paginación
│   │   ├── infrastructure/  # BD, notificador simulado, scheduler, seed
│   │   ├── api/             # Routers, dependencias (DI + roles), manejo de errores
│   │   └── main.py          # Composition root: create_app()
│   ├── alembic/             # Migraciones versionadas
│   ├── tests/               # pytest (unitarias + integración + migraciones)
│   └── Dockerfile           # Multi-stage, usuario no root
├── frontend/
│   ├── src/
│   │   ├── api/             # Cliente HTTP (token, ProblemDetails) y endpoints tipados
│   │   ├── auth/            # Contexto de sesión y rutas protegidas por rol
│   │   ├── components/      # Layout, SlotPicker, ScheduleEditor, UI reutilizable
│   │   ├── pages/           # Panel, Calendario, Citas, Reserva pública, Catálogo...
│   │   ├── lib/             # Fechas, formato, validación, cálculo del calendario
│   │   └── hooks/           # useAsync, useDebounced
│   ├── nginx.conf           # SPA + proxy /api
│   └── Dockerfile           # Build + nginx sin privilegios
├── docs/                    # Arquitectura, modelo de datos, ADRs, guía de API
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Variables de entorno

| Variable | Por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./reservas.db` | Cadena SQLAlchemy (PostgreSQL en Docker) |
| `JWT_SECRET` | valor de ejemplo | **Cámbialo** en producción (≥ 32 caracteres) |
| `JWT_EXPIRES_MINUTES` | `120` | Vigencia del token |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080` | Orígenes permitidos |
| `TIMEZONE` | `America/Lima` | Zona horaria del negocio |
| `SLOT_STEP_MINUTES` | `15` | Granularidad de los horarios ofrecidos |
| `MIN_ADVANCE_MINUTES` | `120` | Anticipación mínima para clientes |
| `MAX_ADVANCE_DAYS` | `60` | Horizonte máximo de reserva |
| `CANCELLATION_MIN_HOURS` | `24` | Ventana mínima para que el cliente cancele/reprograme |
| `MAX_RESCHEDULES` | `2` | Reprogramaciones máximas por cita (cliente) |
| `REMINDERS_ENABLED` | `true` | Activa el job de recordatorios |
| `REMINDER_HOURS_BEFORE` | `24` | Con cuánta anticipación se avisa |
| `REMINDER_INTERVAL_MINUTES` | `5` | Frecuencia del job |
| `SEED_ON_START` | `true` | (Docker) carga datos demo al arrancar |
| `VITE_API_URL` | `/api/v1` | URL base de la API para el frontend |

## Qué aprenderás con este proyecto

- Diseñar un **algoritmo de disponibilidad** como función pura y probarlo de forma aislada.
- Aplicar **Clean Architecture** pragmática en FastAPI: dominio sin dependencias, casos de uso, infraestructura intercambiable y composition root.
- Modelar **políticas de negocio** (anticipación, ventanas de cancelación, límites) con mensajes claros.
- Evitar **reservas dobles** con validación + bloqueo pesimista (`FOR UPDATE`).
- Hacer el tiempo **testeable** con un reloj inyectable.
- Construir **jobs idempotentes** apoyándote en restricciones de base de datos.
- Estandarizar errores con **ProblemDetails (RFC 9457)** y consumirlos en el frontend.
- Implementar **JWT con roles** y autorización por endpoint y por alcance de datos.
- Construir un **calendario semanal** y un **flujo de reserva por pasos** en React + Tailwind con modo oscuro.
- Contenerizar con **Docker multi-stage** y usuarios no root, y automatizar la calidad con **GitHub Actions**.

## Roadmap

- [ ] Envío real de recordatorios (correo SMTP/SES, WhatsApp) implementando el puerto `Notifier`.
- [ ] Restricción de exclusión `EXCLUDE USING gist` en PostgreSQL como segunda barrera contra solapes.
- [ ] Lista de espera cuando no hay horarios.
- [ ] Pagos/adelantos en línea.
- [ ] Exportación iCal y sincronización con Google Calendar.
- [ ] Multi-sede y multi-zona horaria.

## Licencia

[MIT](LICENSE) © 2026 Angel Castañeda Meza

## Autor

**Angel Castañeda Meza** — Ingeniero de Sistemas · Lima, Perú
GitHub: [@angel-cm-dev](https://github.com/angel-cm-dev)

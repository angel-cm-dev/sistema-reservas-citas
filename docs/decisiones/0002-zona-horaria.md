# ADR 0002 · Fechas en hora local "naive" del negocio

- **Estado:** aceptada
- **Fecha:** 2026-11-01

## Contexto

Las citas son eventos de "reloj de pared": una cita a las 10:00 en Lima debe seguir siendo a las 10:00 aunque cambien reglas de horario de verano o el servidor esté en UTC. Además, SQLite (usado en pruebas) no conserva zonas horarias.

## Decisión

- Todas las fechas de agenda (`start_at`, `end_at`, horarios, excepciones) se guardan **sin zona**, interpretadas en la zona del negocio configurada en `TIMEZONE` (por defecto `America/Lima`).
- "Ahora" se obtiene con `SystemClock`, que convierte la hora actual a esa zona y le quita el `tzinfo`.
- El frontend trata los strings ISO como hora local y **evita `toISOString()`**, que convertiría a UTC (ver `frontend/src/lib/dates.ts`).

## Consecuencias

- (+) Comparaciones simples y consistentes entre BD, backend y frontend.
- (+) Pruebas deterministas con `FixedClock`.
- (−) Un despliegue multi-sede en distintas zonas requeriría guardar la zona por sede (anotado en el roadmap).

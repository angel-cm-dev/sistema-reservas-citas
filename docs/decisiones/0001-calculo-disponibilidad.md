# ADR 0001 · Cálculo de disponibilidad como función pura y única fuente de verdad

- **Estado:** aceptada
- **Fecha:** 2026-11-01

## Contexto

La página pública muestra horarios libres y la API debe rechazar reservas inválidas. Si ambas cosas usan reglas distintas (p. ej. la UI calcula huecos y la API solo revisa solapes), tarde o temprano divergen: se ofrecen horarios que luego fallan, o se aceptan reservas en feriados o a las 10:07.

## Decisión

- `domain/availability.py::compute_slots` es una **función pura**: recibe bloques de atención, excepciones, intervalos ocupados, duración, paso y "hora mínima", y devuelve los inicios válidos.
- Al reservar o reprogramar, el servicio recalcula `slots_for_day` y **solo acepta `start_at` si está en esa lista**. Esto cubre de una vez: horario de atención, feriados, ausencias, solapes, alineación al paso de 15 min y anticipación mínima.
- Se usan **intervalos semiabiertos** `[inicio, fin)`: dos citas consecutivas (10:00–10:30 y 10:30–11:00) no se consideran en conflicto.
- En PostgreSQL se toma un `SELECT ... FOR UPDATE` sobre la fila del profesional antes de validar, para serializar reservas concurrentes del mismo profesional.

## Consecuencias

- (+) Una sola regla, probada con pruebas unitarias sin base de datos.
- (+) La UI y la API nunca discrepan.
- (−) Cada reserva recalcula el día (costo bajo: decenas de filas).
- (−) El bloqueo por profesional serializa reservas simultáneas para esa persona (aceptable para el volumen esperado). Como mejora futura se puede añadir una restricción `EXCLUDE USING gist` en PostgreSQL.

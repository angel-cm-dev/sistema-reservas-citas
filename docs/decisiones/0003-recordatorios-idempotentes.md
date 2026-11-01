# ADR 0003 · Recordatorios con job en proceso e idempotencia por restricción única

- **Estado:** aceptada
- **Fecha:** 2026-11-01

## Contexto

Se necesita avisar a los clientes 24 horas antes de su cita. Montar una cola (Celery + Redis) es excesivo para un centro con decenas de citas diarias, pero el envío no debe duplicarse si el job corre varias veces o hay varias réplicas.

## Decisión

- Un **job de APScheduler** dentro del proceso de la API se ejecuta cada `REMINDER_INTERVAL_MINUTES` y busca citas `confirmada` que empiezan en las próximas `REMINDER_HOURS_BEFORE` horas sin recordatorio.
- El envío pasa por el puerto `Notifier`; hoy la implementación `LogNotifier` **simula** el envío escribiendo en el log, y el resultado se guarda en `reminder_logs`.
- `reminder_logs` tiene `UNIQUE (appointment_id, kind)`: aunque dos ejecuciones coincidan, solo una puede registrar el recordatorio.
- Al **reprogramar** una cita se borran sus recordatorios para que se envíe uno nuevo con la hora correcta.
- El administrador puede forzar la ejecución con `POST /api/v1/reminders/run` (útil para demos y pruebas).

## Consecuencias

- (+) Sin infraestructura adicional; fácil de probar (se inyecta un notificador falso).
- (+) Cambiar a correo o WhatsApp solo requiere otra implementación de `Notifier`.
- (−) Con muchas réplicas, todas ejecutan el job (la restricción evita duplicados, pero se desperdicia trabajo). Alternativa futura: un worker dedicado o un lock con `pg_try_advisory_lock`.

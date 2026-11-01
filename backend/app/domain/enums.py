from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    PROFESIONAL = "profesional"
    CLIENTE = "cliente"


class AppointmentStatus(StrEnum):
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"
    NO_ASISTIO = "no_asistio"


class ReminderStatus(StrEnum):
    ENVIADO = "enviado"
    FALLIDO = "fallido"


# Estados que "ocupan" la agenda del profesional. Una cita cancelada libera el
# horario; una completada o con inasistencia ya pasó, pero se mantiene para
# no reabrir huecos en el historial.
BLOCKING_STATUSES = (
    AppointmentStatus.CONFIRMADA,
    AppointmentStatus.COMPLETADA,
    AppointmentStatus.NO_ASISTIO,
)

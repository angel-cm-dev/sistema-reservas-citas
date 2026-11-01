import { minutesOfDay, parseLocal } from "./dates";

export interface CalendarRange {
  startHour: number;
  endHour: number;
}

export interface PositionedEvent {
  top: number; // porcentaje
  height: number; // porcentaje
}

/**
 * Calcula la posición vertical (en %) de un evento dentro de la columna del día.
 * Se recorta al rango visible para que eventos fuera de horario no desborden.
 */
export function positionEvent(startIso: string, endIso: string, range: CalendarRange): PositionedEvent | null {
  const total = (range.endHour - range.startHour) * 60;
  const from = Math.max(minutesOfDay(parseLocal(startIso)) - range.startHour * 60, 0);
  const to = Math.min(minutesOfDay(parseLocal(endIso)) - range.startHour * 60, total);
  if (to <= 0 || from >= total || to <= from) return null;
  return { top: (from / total) * 100, height: ((to - from) / total) * 100 };
}

/** Agrupa elementos por fecha "YYYY-MM-DD" usando el campo de inicio. */
export function groupByDay<T extends { start_at: string }>(items: T[]): Record<string, T[]> {
  return items.reduce<Record<string, T[]>>((acc, item) => {
    const key = item.start_at.slice(0, 10);
    (acc[key] ||= []).push(item);
    return acc;
  }, {});
}

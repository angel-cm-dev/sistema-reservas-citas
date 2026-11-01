/**
 * Utilidades de fechas sin dependencias externas.
 *
 * El backend trabaja con hora local del negocio "naive" (sin zona): por eso
 * aquí manipulamos strings ISO locales ("2026-11-03T10:00:00") y evitamos
 * `toISOString()`, que convertiría a UTC y desplazaría las horas.
 */

export const WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
export const WEEKDAYS_SHORT = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

const pad = (n: number) => String(n).padStart(2, "0");

/** Date -> "YYYY-MM-DD" usando la fecha local. */
export function toISODate(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** Date -> "YYYY-MM-DDTHH:mm:00" local. */
export function toLocalISO(d: Date): string {
  return `${toISODate(d)}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`;
}

/** "YYYY-MM-DD" o "YYYY-MM-DDTHH:mm[:ss]" -> Date local (sin desfase UTC). */
export function parseLocal(value: string): Date {
  const [datePart, timePart = "00:00:00"] = value.split("T");
  const [y, m, d] = datePart.split("-").map(Number);
  const [hh, mm, ss = 0] = timePart.split(":").map((x) => Number(x.slice(0, 2)));
  return new Date(y, m - 1, d, hh, mm, ss);
}

export function addDays(d: Date, days: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + days);
  return r;
}

/** Lunes de la semana de `d` (semana ISO, como en Perú). */
export function startOfWeek(d: Date): Date {
  const r = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const day = (r.getDay() + 6) % 7; // 0 = lunes
  return addDays(r, -day);
}

export function weekDays(anyDay: Date): Date[] {
  const start = startOfWeek(anyDay);
  return Array.from({ length: 7 }, (_, i) => addDays(start, i));
}

export function isSameDay(a: Date, b: Date): boolean {
  return toISODate(a) === toISODate(b);
}

/** Minutos desde medianoche, útil para posicionar eventos en la grilla del calendario. */
export function minutesOfDay(d: Date): number {
  return d.getHours() * 60 + d.getMinutes();
}

/** Diferencia en horas (b - a). */
export function hoursBetween(a: Date, b: Date): number {
  return (b.getTime() - a.getTime()) / 3_600_000;
}

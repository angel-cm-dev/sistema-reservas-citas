import { parseLocal } from "./dates";

const currency = new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN" });

export function formatMoney(value: string | number): string {
  return currency.format(typeof value === "string" ? Number(value) : value);
}

export function formatTime(iso: string): string {
  return iso.slice(11, 16);
}

export function formatDate(iso: string): string {
  const d = parseLocal(iso);
  return d.toLocaleDateString("es-PE", { weekday: "short", day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(iso: string): string {
  return `${formatDate(iso)} · ${formatTime(iso)}`;
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h} h ${m} min` : `${h} h`;
}

export const STATUS_LABELS: Record<string, string> = {
  confirmada: "Confirmada",
  cancelada: "Cancelada",
  completada: "Completada",
  no_asistio: "No asistió",
};

export const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  profesional: "Profesional",
  cliente: "Cliente",
};

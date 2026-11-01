import type { AppointmentStatus } from "../../api/types";
import { STATUS_LABELS } from "../../lib/format";

const COLORS: Record<AppointmentStatus, string> = {
  confirmada: "bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300",
  completada: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300",
  cancelada: "bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  no_asistio: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300",
};

export function StatusBadge({ status }: { status: AppointmentStatus }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${COLORS[status]}`}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

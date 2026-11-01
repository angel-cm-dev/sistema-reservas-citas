import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import { appointmentsApi, professionalsApi } from "../api/endpoints";
import type { Appointment } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { AppointmentActions } from "../components/AppointmentActions";
import { PageHeader } from "../components/ui/Field";
import { Modal } from "../components/ui/Modal";
import { ErrorState, Loading } from "../components/ui/States";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { groupByDay, positionEvent } from "../lib/calendar";
import { addDays, isSameDay, toISODate, weekDays, WEEKDAYS_SHORT } from "../lib/dates";
import { formatDateTime, formatMoney, formatTime } from "../lib/format";

const RANGE = { startHour: 8, endHour: 19 };
const HOURS = Array.from({ length: RANGE.endHour - RANGE.startHour }, (_, i) => RANGE.startHour + i);
const HOUR_PX = 56;

const EVENT_COLORS: Record<string, string> = {
  confirmada: "border-sky-500 bg-sky-50 text-sky-800 dark:bg-sky-950/70 dark:text-sky-200",
  completada: "border-emerald-500 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-200",
  no_asistio: "border-amber-500 bg-amber-50 text-amber-800 dark:bg-amber-950/70 dark:text-amber-200",
  cancelada: "border-slate-400 bg-slate-100 text-slate-500 line-through dark:bg-slate-800",
};

export default function CalendarPage() {
  const { hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  const [anchor, setAnchor] = useState(new Date());
  const [professionalId, setProfessionalId] = useState("");
  const [showCancelled, setShowCancelled] = useState(false);
  const [selected, setSelected] = useState<Appointment | null>(null);
  const days = useMemo(() => weekDays(anchor), [anchor]);
  const from = toISODate(days[0]);
  const to = toISODate(days[6]);

  const pros = useAsync(() => (isAdmin ? professionalsApi.list({ page_size: 100 }) : Promise.resolve(null)), [isAdmin]);
  const appts = useAsync(
    () => appointmentsApi.list({ date_from: from, date_to: to, page_size: 200, sort: "start_at", professional_id: professionalId || undefined }),
    [from, to, professionalId],
  );

  const byDay = useMemo(() => {
    const items = (appts.data?.items ?? []).filter((a) => showCancelled || a.status !== "cancelada");
    return groupByDay(items);
  }, [appts.data, showCancelled]);

  const today = new Date();
  const label = `${days[0].toLocaleDateString("es-PE", { day: "numeric", month: "short" })} – ${days[6].toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" })}`;

  return (
    <>
      <PageHeader
        title="Calendario semanal"
        subtitle={label}
        actions={
          <>
            <button className="btn-secondary px-2" onClick={() => setAnchor(addDays(anchor, -7))} aria-label="Semana anterior"><ChevronLeft className="h-4 w-4" /></button>
            <button className="btn-secondary" onClick={() => setAnchor(new Date())}>Hoy</button>
            <button className="btn-secondary px-2" onClick={() => setAnchor(addDays(anchor, 7))} aria-label="Semana siguiente"><ChevronRight className="h-4 w-4" /></button>
          </>
        }
      />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        {isAdmin && (
          <select className="input max-w-xs" value={professionalId} onChange={(e) => setProfessionalId(e.target.value)} aria-label="Profesional">
            <option value="">Todos los profesionales</option>
            {pros.data?.items.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
          </select>
        )}
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={showCancelled} onChange={(e) => setShowCancelled(e.target.checked)} />
          Mostrar canceladas
        </label>
      </div>

      {appts.error && <ErrorState message={appts.error} onRetry={appts.reload} />}
      {appts.loading && !appts.data && <Loading />}
      {appts.data && (
        <div className="card overflow-x-auto">
          <div className="grid min-w-[760px]" style={{ gridTemplateColumns: "56px repeat(7, minmax(0, 1fr))" }}>
            <div />
            {days.map((d, i) => (
              <div key={i} className={`border-b border-l border-slate-200 px-2 py-2 text-center text-xs dark:border-slate-800 ${isSameDay(d, today) ? "bg-brand-50 font-semibold text-brand-700 dark:bg-brand-900/30 dark:text-brand-200" : ""}`}>
                {WEEKDAYS_SHORT[i]} <span className="text-base">{d.getDate()}</span>
              </div>
            ))}
            <div className="relative" style={{ height: HOURS.length * HOUR_PX }}>
              {HOURS.map((h, i) => (
                <div key={h} className="absolute right-2 text-[11px] text-slate-400" style={{ top: i * HOUR_PX - 6 }}>{`${h}:00`}</div>
              ))}
            </div>
            {days.map((d) => (
              <div key={toISODate(d)} className="relative border-l border-slate-200 dark:border-slate-800" style={{ height: HOURS.length * HOUR_PX }}>
                {HOURS.map((h, i) => (
                  <div key={h} className="absolute inset-x-0 border-t border-slate-100 dark:border-slate-800/60" style={{ top: i * HOUR_PX }} />
                ))}
                {(byDay[toISODate(d)] ?? []).map((a) => {
                  const pos = positionEvent(a.start_at, a.end_at, RANGE);
                  if (!pos) return null;
                  return (
                    <button
                      key={a.id}
                      onClick={() => setSelected(a)}
                      className={`absolute inset-x-1 overflow-hidden rounded-md border-l-4 px-1.5 py-1 text-left text-[11px] leading-tight shadow-sm ${EVENT_COLORS[a.status]}`}
                      style={{ top: `${pos.top}%`, height: `${pos.height}%` }}
                      title={`${a.service_name} – ${a.client_name}`}
                    >
                      <span className="font-semibold tabular-nums">{formatTime(a.start_at)}</span> {a.client_name}
                      <span className="block truncate opacity-80">{a.service_name}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}

      <Modal open={!!selected} title="Detalle de la cita" onClose={() => setSelected(null)}>
        {selected && (
          <div className="space-y-2 text-sm">
            <p><span className="text-slate-500">Cliente:</span> {selected.client_name} ({selected.client_email})</p>
            <p><span className="text-slate-500">Servicio:</span> {selected.service_name}</p>
            <p><span className="text-slate-500">Profesional:</span> {selected.professional_name}</p>
            <p><span className="text-slate-500">Inicio:</span> {formatDateTime(selected.start_at)} – {formatTime(selected.end_at)}</p>
            <p><span className="text-slate-500">Precio:</span> {formatMoney(selected.price)}</p>
            <p><StatusBadge status={selected.status} /></p>
            {selected.notes && <p className="text-slate-500">Notas: {selected.notes}</p>}
            <div className="border-t border-slate-200 pt-3 dark:border-slate-800">
              <AppointmentActions appt={selected} onDone={() => { setSelected(null); appts.reload(); }} />
            </div>
          </div>
        )}
      </Modal>
    </>
  );
}

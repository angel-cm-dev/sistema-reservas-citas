import { BellRing, CalendarCheck, CalendarClock, CalendarDays, Percent, UserX, Wallet } from "lucide-react";
import type { ComponentType } from "react";
import { Link } from "react-router-dom";
import { appointmentsApi, dashboardApi } from "../api/endpoints";
import { PageHeader } from "../components/ui/Field";
import { ErrorState, Loading } from "../components/ui/States";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { toISODate } from "../lib/dates";
import { formatDateTime, formatMoney, STATUS_LABELS } from "../lib/format";

function Kpi({ label, value, icon: Icon, hint }: { label: string; value: string | number; icon: ComponentType<{ className?: string }>; hint?: string }) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
        <Icon className="h-5 w-5 text-brand-500" />
      </div>
      <p className="mt-2 text-2xl font-bold tabular-nums">{value}</p>
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const kpis = useAsync(() => dashboardApi.kpis(), []);
  const upcoming = useAsync(
    () => appointmentsApi.list({ status: "confirmada", date_from: toISODate(new Date()), page_size: 5, sort: "start_at" }),
    [],
  );

  if (kpis.loading) return <Loading />;
  if (kpis.error || !kpis.data) return <ErrorState message={kpis.error ?? "Sin datos"} onRetry={kpis.reload} />;
  const k = kpis.data;
  const total = Object.values(k.by_status).reduce((a, b) => a + b, 0) || 1;

  return (
    <>
      <PageHeader title="Panel" subtitle="Resumen de la actividad de la agenda" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label="Citas hoy" value={k.appointments_today} icon={CalendarDays} />
        <Kpi label="Citas esta semana" value={k.appointments_week} icon={CalendarCheck} />
        <Kpi label="Próximas confirmadas" value={k.upcoming_confirmed} icon={CalendarClock} />
        <Kpi label="Ingresos del mes" value={formatMoney(k.revenue_month)} icon={Wallet} hint="Citas completadas" />
        <Kpi label="Tasa de cancelación" value={`${k.cancellation_rate}%`} icon={Percent} />
        <Kpi label="Inasistencias" value={`${k.no_show_rate}%`} icon={UserX} hint="Sobre citas cerradas" />
        <Kpi label="Recordatorios (semana)" value={k.reminders_sent_week} icon={BellRing} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="card p-5">
          <h2 className="mb-4 font-semibold">Citas por estado</h2>
          <ul className="space-y-3">
            {Object.entries(k.by_status).map(([status, n]) => (
              <li key={status}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{STATUS_LABELS[status]}</span>
                  <span className="tabular-nums text-slate-500">{n}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800">
                  <div className="h-2 rounded-full bg-brand-500" style={{ width: `${(n / total) * 100}%` }} />
                </div>
              </li>
            ))}
          </ul>
          <h3 className="mb-2 mt-6 text-sm font-semibold">Servicios más reservados</h3>
          <ol className="space-y-1 text-sm">
            {k.top_services.map((s) => (
              <li key={s.name} className="flex justify-between">
                <span>{s.name}</span>
                <span className="tabular-nums text-slate-500">{s.count}</span>
              </li>
            ))}
          </ol>
        </section>

        <section className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold">Próximas citas</h2>
            <Link to="/calendario" className="text-sm text-brand-600 hover:underline">Ver calendario</Link>
          </div>
          {upcoming.loading && <Loading />}
          {upcoming.error && <ErrorState message={upcoming.error} onRetry={upcoming.reload} />}
          {upcoming.data && upcoming.data.items.length === 0 && <p className="text-sm text-slate-500">No hay citas próximas.</p>}
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {upcoming.data?.items.map((a) => (
              <li key={a.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{a.client_name}</p>
                  <p className="truncate text-xs text-slate-500">{a.service_name} · {a.professional_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs tabular-nums">{formatDateTime(a.start_at)}</p>
                  <StatusBadge status={a.status} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}

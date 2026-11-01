import { ArrowDownUp, CalendarPlus, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { appointmentsApi, professionalsApi } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import { AppointmentActions } from "../components/AppointmentActions";
import { PageHeader } from "../components/ui/Field";
import { Pagination } from "../components/ui/Pagination";
import { EmptyState, ErrorState, Loading } from "../components/ui/States";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useAsync, useDebounced } from "../hooks/useAsync";
import { formatDateTime, formatMoney, STATUS_LABELS } from "../lib/format";

export default function AppointmentsPage() {
  const { user, hasRole } = useAuth();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [professionalId, setProfessionalId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sort, setSort] = useState("-start_at");
  const [page, setPage] = useState(1);
  const debouncedQ = useDebounced(q);
  const isAdmin = hasRole("admin");
  const isClient = hasRole("cliente");

  const list = useAsync(
    () =>
      appointmentsApi.list({
        page, page_size: 10, sort, q: debouncedQ, status,
        professional_id: professionalId || undefined, date_from: dateFrom, date_to: dateTo,
      }),
    [page, sort, debouncedQ, status, professionalId, dateFrom, dateTo],
  );
  const pros = useAsync(() => (isAdmin ? professionalsApi.list({ page_size: 100 }) : Promise.resolve(null)), [isAdmin]);

  // Cualquier cambio de filtro vuelve a la página 1.
  const withReset = <T,>(setter: (v: T) => void) => (v: T) => {
    setter(v);
    setPage(1);
  };

  return (
    <>
      <PageHeader
        title={isClient ? "Mis citas" : "Citas"}
        subtitle={isClient ? "Revisa, reprograma o cancela tus reservas" : `Agenda ${user?.role === "profesional" ? "personal" : "general"}`}
        actions={
          (isClient || isAdmin) && (
            <Link to="/reservar" className="btn-primary">
              <CalendarPlus className="h-4 w-4" /> Nueva reserva
            </Link>
          )
        }
      />

      <div className="card mb-4 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="relative lg:col-span-2">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input className="input pl-9" placeholder="Buscar por cliente, correo o servicio" value={q}
            onChange={(e) => withReset(setQ)(e.target.value)} aria-label="Buscar" />
        </div>
        <select className="input" value={status} onChange={(e) => withReset(setStatus)(e.target.value)} aria-label="Estado">
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <input type="date" className="input" value={dateFrom} onChange={(e) => withReset(setDateFrom)(e.target.value)} aria-label="Desde" />
        <input type="date" className="input" value={dateTo} onChange={(e) => withReset(setDateTo)(e.target.value)} aria-label="Hasta" />
        {isAdmin && (
          <select className="input" value={professionalId} onChange={(e) => withReset(setProfessionalId)(e.target.value)} aria-label="Profesional">
            <option value="">Todos los profesionales</option>
            {pros.data?.items.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
          </select>
        )}
      </div>

      <div className="card overflow-hidden">
        {list.loading && <Loading />}
        {list.error && <ErrorState message={list.error} onRetry={list.reload} />}
        {list.data && list.data.items.length === 0 && (
          <EmptyState title="No hay citas" description="Ajusta los filtros o crea una nueva reserva." />
        )}
        {list.data && list.data.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
              <thead className="bg-slate-50 dark:bg-slate-900/60">
                <tr>
                  <th className="th">
                    <button className="inline-flex items-center gap-1 uppercase" onClick={() => setSort(sort === "start_at" ? "-start_at" : "start_at")}>
                      Fecha y hora <ArrowDownUp className="h-3 w-3" />
                    </button>
                  </th>
                  {!isClient && <th className="th">Cliente</th>}
                  <th className="th">Servicio</th>
                  <th className="th">Profesional</th>
                  <th className="th">Precio</th>
                  <th className="th">Estado</th>
                  <th className="th text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {list.data.items.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="td whitespace-nowrap tabular-nums">{formatDateTime(a.start_at)}</td>
                    {!isClient && (
                      <td className="td">
                        <p className="font-medium">{a.client_name}</p>
                        <p className="text-xs text-slate-500">{a.client_email}</p>
                      </td>
                    )}
                    <td className="td">{a.service_name}</td>
                    <td className="td">{a.professional_name}</td>
                    <td className="td tabular-nums">{formatMoney(a.price)}</td>
                    <td className="td">
                      <StatusBadge status={a.status} />
                      {a.cancellation_reason && <p className="mt-1 text-xs text-slate-500">{a.cancellation_reason}</p>}
                    </td>
                    <td className="td text-right">
                      <AppointmentActions appt={a} onDone={list.reload} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {list.data && (
          <Pagination page={list.data.page} pages={list.data.pages} total={list.data.total} onChange={setPage} />
        )}
      </div>
    </>
  );
}

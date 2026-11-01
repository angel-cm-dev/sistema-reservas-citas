import { Play } from "lucide-react";
import { useState } from "react";
import { remindersApi } from "../api/endpoints";
import { PageHeader } from "../components/ui/Field";
import { Pagination } from "../components/ui/Pagination";
import { Alert, EmptyState, ErrorState, Loading } from "../components/ui/States";
import { useAsync } from "../hooks/useAsync";
import { formatDateTime } from "../lib/format";

export default function RemindersPage() {
  const [page, setPage] = useState(1);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const list = useAsync(() => remindersApi.list({ page, page_size: 10 }), [page]);

  const run = async () => {
    setBusy(true);
    try {
      const r = await remindersApi.run();
      setMsg(`Job ejecutado: ${r.sent} recordatorio(s) enviado(s).`);
      list.reload();
    } catch (e) {
      setMsg((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Recordatorios"
        subtitle="El job programado avisa 24 h antes de cada cita (envío simulado y registrado)"
        actions={<button className="btn-primary" onClick={run} disabled={busy}><Play className="h-4 w-4" /> Ejecutar ahora</button>}
      />
      {msg && <div className="mb-4"><Alert kind="info">{msg}</Alert></div>}
      <div className="card overflow-hidden">
        {list.loading && <Loading />}
        {list.error && <ErrorState message={list.error} onRetry={list.reload} />}
        {list.data?.items.length === 0 && <EmptyState title="Aún no se enviaron recordatorios" description="Se envían automáticamente para citas en las próximas 24 horas." />}
        {list.data && list.data.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
              <thead className="bg-slate-50 dark:bg-slate-900/60">
                <tr><th className="th">Enviado</th><th className="th">Cita</th><th className="th">Destinatario</th><th className="th">Mensaje</th><th className="th">Estado</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {list.data.items.map((r) => (
                  <tr key={r.id}>
                    <td className="td whitespace-nowrap">{formatDateTime(r.sent_at)}</td>
                    <td className="td">#{r.appointment_id}</td>
                    <td className="td">{r.recipient}<p className="text-xs text-slate-500">{r.channel}</p></td>
                    <td className="td max-w-md text-xs text-slate-600 dark:text-slate-300">{r.message}</td>
                    <td className="td"><span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">{r.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {list.data && <Pagination page={list.data.page} pages={list.data.pages} total={list.data.total} onChange={setPage} />}
      </div>
    </>
  );
}

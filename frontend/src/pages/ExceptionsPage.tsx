import { Trash2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { exceptionsApi, professionalsApi } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import { Field, PageHeader } from "../components/ui/Field";
import { Alert, EmptyState, ErrorState, Loading } from "../components/ui/States";
import { useAsync } from "../hooks/useAsync";
import { toISODate } from "../lib/dates";
import { formatDate } from "../lib/format";
import { hasErrors, minLength, required, validate, type Errors } from "../lib/validation";

interface Form {
  date: string;
  fullDay: boolean;
  start_time: string;
  end_time: string;
  reason: string;
  professional_id: string;
}

export default function ExceptionsPage() {
  const { user, hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  const [from, setFrom] = useState(toISODate(new Date()));
  const list = useAsync(() => exceptionsApi.list({ date_from: from }), [from]);
  const pros = useAsync(() => (isAdmin ? professionalsApi.list({ page_size: 100 }) : Promise.resolve(null)), [isAdmin]);
  const [form, setForm] = useState<Form>({
    date: "", fullDay: true, start_time: "09:00", end_time: "11:00", reason: "",
    professional_id: isAdmin ? "" : String(user?.professional_id ?? ""),
  });
  const [errors, setErrors] = useState<Errors<Form>>({});
  const [msg, setMsg] = useState<{ kind: "error" | "success"; text: string } | null>(null);

  const proName = (id: number | null) => (id === null ? "Todos (feriado)" : pros.data?.items.find((p) => p.id === id)?.full_name ?? "Mi agenda");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate(form, {
      date: [required()],
      reason: [required(), minLength(3)],
      end_time: [(v, all) => (!all.fullDay && String(v) <= all.start_time ? "Debe ser posterior al inicio" : null)],
    });
    setErrors(errs);
    if (hasErrors(errs)) return;
    try {
      await exceptionsApi.create({
        date: form.date,
        reason: form.reason,
        professional_id: form.professional_id ? Number(form.professional_id) : null,
        start_time: form.fullDay ? null : form.start_time,
        end_time: form.fullDay ? null : form.end_time,
      });
      setMsg({ kind: "success", text: "Excepción registrada. La disponibilidad se actualizó." });
      setForm({ ...form, date: "", reason: "" });
      list.reload();
    } catch (err) {
      setMsg({ kind: "error", text: (err as Error).message });
    }
  };

  const remove = async (id: number) => {
    try {
      await exceptionsApi.remove(id);
      list.reload();
    } catch (err) {
      setMsg({ kind: "error", text: (err as Error).message });
    }
  };

  return (
    <>
      <PageHeader title="Feriados y ausencias" subtitle="Días u horas en que no se aceptan reservas" />
      <div className="grid gap-6 lg:grid-cols-3">
        <form onSubmit={submit} noValidate className="card space-y-3 p-5">
          <h2 className="font-semibold">Nueva excepción</h2>
          {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
          {isAdmin && (
            <Field label="Aplica a" htmlFor="ex-pro">
              <select id="ex-pro" className="input" value={form.professional_id} onChange={(e) => setForm({ ...form, professional_id: e.target.value })}>
                <option value="">Todos los profesionales (feriado)</option>
                {pros.data?.items.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
              </select>
            </Field>
          )}
          <Field label="Fecha" htmlFor="ex-date" error={errors.date}>
            <input id="ex-date" type="date" className="input" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
          </Field>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.fullDay} onChange={(e) => setForm({ ...form, fullDay: e.target.checked })} /> Día completo
          </label>
          {!form.fullDay && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="Desde" htmlFor="ex-start"><input id="ex-start" type="time" className="input" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} /></Field>
              <Field label="Hasta" htmlFor="ex-end" error={errors.end_time}><input id="ex-end" type="time" className="input" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} /></Field>
            </div>
          )}
          <Field label="Motivo" htmlFor="ex-reason" error={errors.reason}>
            <input id="ex-reason" className="input" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
          </Field>
          <button className="btn-primary w-full">Registrar</button>
        </form>

        <section className="card overflow-hidden lg:col-span-2">
          <div className="flex items-center justify-between gap-3 border-b border-slate-200 p-4 dark:border-slate-800">
            <h2 className="font-semibold">Próximas excepciones</h2>
            <input type="date" className="input w-44" value={from} onChange={(e) => setFrom(e.target.value)} aria-label="Desde" />
          </div>
          {list.loading && <Loading />}
          {list.error && <ErrorState message={list.error} onRetry={list.reload} />}
          {list.data?.length === 0 && <EmptyState title="Sin excepciones registradas" />}
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {list.data?.map((x) => {
              const canDelete = isAdmin || x.professional_id !== null;
              return (
                <li key={x.id} className="flex items-center justify-between gap-3 px-4 py-3">
                  <div>
                    <p className="text-sm font-medium">{formatDate(x.date)} · {x.start_time ? `${x.start_time.slice(0, 5)}–${x.end_time?.slice(0, 5)}` : "Día completo"}</p>
                    <p className="text-xs text-slate-500">{x.reason} · {proName(x.professional_id)}</p>
                  </div>
                  {canDelete && (
                    <button className="rounded p-2 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950" onClick={() => remove(x.id)} aria-label="Eliminar">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      </div>
    </>
  );
}

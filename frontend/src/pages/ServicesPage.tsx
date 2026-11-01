import { Pencil, Plus, Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { servicesApi } from "../api/endpoints";
import type { Service } from "../api/types";
import { Field, PageHeader } from "../components/ui/Field";
import { Modal } from "../components/ui/Modal";
import { Pagination } from "../components/ui/Pagination";
import { Alert, EmptyState, ErrorState, Loading } from "../components/ui/States";
import { useAsync, useDebounced } from "../hooks/useAsync";
import { formatDuration, formatMoney } from "../lib/format";
import { hasErrors, minLength, numberBetween, required, validate, type Errors } from "../lib/validation";

interface Form {
  name: string;
  description: string;
  duration_minutes: string;
  price: string;
  is_active: boolean;
}

const EMPTY: Form = { name: "", description: "", duration_minutes: "30", price: "", is_active: true };

const serviceSchema = {
  name: [required<Form>(), minLength<Form>(3)],
  duration_minutes: [required<Form>(), numberBetween<Form>(10, 480)],
  price: [required<Form>(), numberBetween<Form>(0, 100000)],
};

function ServiceForm({ initial, onSaved, onCancel }: { initial: Service | null; onSaved: () => void; onCancel: () => void }) {
  const [form, setForm] = useState<Form>(
    initial
      ? { name: initial.name, description: initial.description ?? "", duration_minutes: String(initial.duration_minutes), price: initial.price, is_active: initial.is_active }
      : EMPTY,
  );
  const [errors, setErrors] = useState<Errors<Form>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate(form, serviceSchema);
    setErrors(errs);
    if (hasErrors(errs)) return;
    setBusy(true);
    setError(null);
    const payload = { ...form, description: form.description || null, duration_minutes: Number(form.duration_minutes), price: Number(form.price).toFixed(2) };
    try {
      if (initial) await servicesApi.update(initial.id, payload);
      else await servicesApi.create(payload);
      onSaved();
    } catch (err) {
      setError((err as Error).message);
      if (err instanceof ApiError) setErrors(err.fieldErrors as Errors<Form>);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} noValidate className="space-y-3">
      {error && <Alert>{error}</Alert>}
      <Field label="Nombre" htmlFor="name" error={errors.name}>
        <input id="name" className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      </Field>
      <Field label="Descripción" htmlFor="description">
        <textarea id="description" className="input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Duración (min)" htmlFor="duration" error={errors.duration_minutes}>
          <input id="duration" type="number" min={10} step={5} className="input" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} />
        </Field>
        <Field label="Precio (S/)" htmlFor="price" error={errors.price}>
          <input id="price" type="number" min={0} step="0.01" className="input" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
        </Field>
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Activo (visible para reservas)
      </label>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" className="btn-secondary" onClick={onCancel}>Cancelar</button>
        <button className="btn-primary" disabled={busy}>{busy ? "Guardando..." : "Guardar"}</button>
      </div>
    </form>
  );
}

export default function ServicesPage() {
  const [q, setQ] = useState("");
  const [active, setActive] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Service | null | "new">(null);
  const dq = useDebounced(q);
  const list = useAsync(() => servicesApi.list({ q: dq, active: active || undefined, page, page_size: 10, sort: "name" }), [dq, active, page]);

  return (
    <>
      <PageHeader title="Servicios" subtitle="Catálogo con duración y precio" actions={
        <button className="btn-primary" onClick={() => setEditing("new")}><Plus className="h-4 w-4" /> Nuevo servicio</button>
      } />
      <div className="card mb-4 flex flex-col gap-3 p-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input className="input pl-9" placeholder="Buscar servicio" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Buscar" />
        </div>
        <select className="input sm:w-48" value={active} onChange={(e) => { setActive(e.target.value); setPage(1); }} aria-label="Estado">
          <option value="">Todos</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
      </div>
      <div className="card overflow-hidden">
        {list.loading && <Loading />}
        {list.error && <ErrorState message={list.error} onRetry={list.reload} />}
        {list.data?.items.length === 0 && <EmptyState title="Sin servicios" description="Crea el primer servicio del catálogo." />}
        {list.data && list.data.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
              <thead className="bg-slate-50 dark:bg-slate-900/60">
                <tr><th className="th">Servicio</th><th className="th">Duración</th><th className="th">Precio</th><th className="th">Estado</th><th className="th text-right">Acciones</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {list.data.items.map((s) => (
                  <tr key={s.id}>
                    <td className="td"><p className="font-medium">{s.name}</p><p className="text-xs text-slate-500">{s.description}</p></td>
                    <td className="td">{formatDuration(s.duration_minutes)}</td>
                    <td className="td tabular-nums">{formatMoney(s.price)}</td>
                    <td className="td">{s.is_active ? <span className="text-emerald-600">Activo</span> : <span className="text-slate-400">Inactivo</span>}</td>
                    <td className="td text-right">
                      <button className="btn-secondary px-2 py-1 text-xs" onClick={() => setEditing(s)}><Pencil className="h-3 w-3" /> Editar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {list.data && <Pagination page={list.data.page} pages={list.data.pages} total={list.data.total} onChange={setPage} />}
      </div>
      <Modal open={editing !== null} title={editing === "new" ? "Nuevo servicio" : "Editar servicio"} onClose={() => setEditing(null)}>
        {editing !== null && (
          <ServiceForm initial={editing === "new" ? null : editing} onCancel={() => setEditing(null)} onSaved={() => { setEditing(null); list.reload(); }} />
        )}
      </Modal>
    </>
  );
}

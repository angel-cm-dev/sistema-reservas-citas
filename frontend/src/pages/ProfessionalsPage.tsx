import { Clock, Pencil, Plus, Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import { professionalsApi, servicesApi, usersApi } from "../api/endpoints";
import type { Professional } from "../api/types";
import { ScheduleEditor } from "../components/ScheduleEditor";
import { Field, PageHeader } from "../components/ui/Field";
import { Modal } from "../components/ui/Modal";
import { Pagination } from "../components/ui/Pagination";
import { Alert, EmptyState, ErrorState, Loading } from "../components/ui/States";
import { useAsync, useDebounced } from "../hooks/useAsync";
import { hasErrors, minLength, required, validate, type Errors } from "../lib/validation";

interface Form {
  full_name: string;
  specialty: string;
  bio: string;
  user_id: string;
  service_ids: number[];
  is_active: boolean;
}

function ProfessionalForm({ initial, onSaved, onCancel }: { initial: Professional | null; onSaved: () => void; onCancel: () => void }) {
  const services = useAsync(() => servicesApi.list({ page_size: 100, active: true }), []);
  const users = useAsync(() => usersApi.list({ role: "profesional", page_size: 100 }), []);
  const [form, setForm] = useState<Form>({
    full_name: initial?.full_name ?? "",
    specialty: initial?.specialty ?? "",
    bio: initial?.bio ?? "",
    user_id: initial?.user_id ? String(initial.user_id) : "",
    service_ids: initial?.services.map((s) => s.id) ?? [],
    is_active: initial?.is_active ?? true,
  });
  const [errors, setErrors] = useState<Errors<Form>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const toggleService = (id: number) =>
    setForm({ ...form, service_ids: form.service_ids.includes(id) ? form.service_ids.filter((x) => x !== id) : [...form.service_ids, id] });

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate(form, {
      full_name: [required(), minLength(3)],
      specialty: [required(), minLength(3)],
      service_ids: [(v) => ((v as number[]).length ? null : "Selecciona al menos un servicio")],
    });
    setErrors(errs);
    if (hasErrors(errs)) return;
    setBusy(true);
    setError(null);
    const payload = { ...form, bio: form.bio || null, user_id: form.user_id ? Number(form.user_id) : null };
    try {
      if (initial) await professionalsApi.update(initial.id, payload);
      else await professionalsApi.create(payload);
      onSaved();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} noValidate className="space-y-3">
      {error && <Alert>{error}</Alert>}
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Nombre completo" htmlFor="pname" error={errors.full_name}>
          <input id="pname" className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        </Field>
        <Field label="Especialidad" htmlFor="specialty" error={errors.specialty}>
          <input id="specialty" className="input" value={form.specialty} onChange={(e) => setForm({ ...form, specialty: e.target.value })} />
        </Field>
      </div>
      <Field label="Biografía" htmlFor="bio">
        <textarea id="bio" className="input" rows={2} value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} />
      </Field>
      <Field label="Usuario vinculado (para que gestione su agenda)" htmlFor="user">
        <select id="user" className="input" value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })}>
          <option value="">Sin usuario</option>
          {users.data?.items.map((u) => <option key={u.id} value={u.id}>{u.full_name} · {u.email}</option>)}
        </select>
      </Field>
      <fieldset>
        <legend className="label">Servicios que ofrece</legend>
        <div className="grid gap-1 sm:grid-cols-2">
          {services.data?.items.map((s) => (
            <label key={s.id} className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.service_ids.includes(s.id)} onChange={() => toggleService(s.id)} /> {s.name}
            </label>
          ))}
        </div>
        {errors.service_ids && <p className="mt-1 text-xs text-rose-600">{errors.service_ids}</p>}
      </fieldset>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Activo
      </label>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" className="btn-secondary" onClick={onCancel}>Cancelar</button>
        <button className="btn-primary" disabled={busy}>{busy ? "Guardando..." : "Guardar"}</button>
      </div>
    </form>
  );
}

export default function ProfessionalsPage() {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Professional | null | "new">(null);
  const [scheduleFor, setScheduleFor] = useState<Professional | null>(null);
  const dq = useDebounced(q);
  const list = useAsync(() => professionalsApi.list({ q: dq, page, page_size: 10 }), [dq, page]);

  return (
    <>
      <PageHeader title="Profesionales" subtitle="Equipo, servicios y horarios de atención" actions={
        <button className="btn-primary" onClick={() => setEditing("new")}><Plus className="h-4 w-4" /> Nuevo profesional</button>
      } />
      <div className="card mb-4 p-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input className="input pl-9" placeholder="Buscar por nombre o especialidad" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Buscar" />
        </div>
      </div>
      {list.loading && <Loading />}
      {list.error && <ErrorState message={list.error} onRetry={list.reload} />}
      {list.data?.items.length === 0 && <div className="card"><EmptyState title="Sin profesionales" /></div>}
      <div className="grid gap-4 md:grid-cols-2">
        {list.data?.items.map((p) => (
          <article key={p.id} className="card p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold">{p.full_name}</h3>
                <p className="text-sm text-brand-600">{p.specialty}</p>
              </div>
              {!p.is_active && <span className="rounded-full bg-slate-200 px-2 text-xs dark:bg-slate-800">Inactivo</span>}
            </div>
            {p.bio && <p className="mt-2 text-sm text-slate-500">{p.bio}</p>}
            <div className="mt-3 flex flex-wrap gap-1">
              {p.services.map((s) => <span key={s.id} className="rounded-full bg-brand-50 px-2 py-0.5 text-xs text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">{s.name}</span>)}
            </div>
            <div className="mt-4 flex gap-2">
              <button className="btn-secondary px-3 py-1 text-xs" onClick={() => setEditing(p)}><Pencil className="h-3 w-3" /> Editar</button>
              <button className="btn-secondary px-3 py-1 text-xs" onClick={() => setScheduleFor(p)}><Clock className="h-3 w-3" /> Horario</button>
            </div>
          </article>
        ))}
      </div>
      {list.data && <div className="card mt-4"><Pagination page={list.data.page} pages={list.data.pages} total={list.data.total} onChange={setPage} /></div>}

      <Modal open={editing !== null} title={editing === "new" ? "Nuevo profesional" : "Editar profesional"} onClose={() => setEditing(null)} wide>
        {editing !== null && (
          <ProfessionalForm initial={editing === "new" ? null : editing} onCancel={() => setEditing(null)} onSaved={() => { setEditing(null); list.reload(); }} />
        )}
      </Modal>
      <Modal open={!!scheduleFor} title={`Horario semanal · ${scheduleFor?.full_name ?? ""}`} onClose={() => setScheduleFor(null)} wide>
        {scheduleFor && <ScheduleEditor professionalId={scheduleFor.id} />}
      </Modal>
    </>
  );
}

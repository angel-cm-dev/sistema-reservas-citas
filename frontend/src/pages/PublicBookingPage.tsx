import { CheckCircle2, Clock, Moon, Sun } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { appointmentsApi, professionalsApi, servicesApi, usersApi } from "../api/endpoints";
import type { Appointment, Professional, Service } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { SlotPicker } from "../components/SlotPicker";
import { Field } from "../components/ui/Field";
import { Alert, EmptyState, ErrorState, Loading } from "../components/ui/States";
import { useAsync } from "../hooks/useAsync";
import { formatDateTime, formatDuration, formatMoney, formatTime } from "../lib/format";
import { email, hasErrors, minLength, required, strongPassword, validate, type Errors } from "../lib/validation";
import { useTheme } from "../theme/ThemeContext";

function Step({ n, title, done, children }: { n: number; title: string; done?: boolean; children: React.ReactNode }) {
  return (
    <section className="card p-5">
      <h2 className="mb-4 flex items-center gap-3 font-semibold">
        <span className={`grid h-7 w-7 place-items-center rounded-full text-sm ${done ? "bg-brand-600 text-white" : "bg-slate-100 dark:bg-slate-800"}`}>{n}</span>
        {title}
      </h2>
      {children}
    </section>
  );
}

interface AccountForm {
  full_name: string;
  email: string;
  phone: string;
  password: string;
}

/** Bloque de identificación: login o registro rápido de cliente sin salir del flujo. */
function AccountBox() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"register" | "login">("register");
  const [form, setForm] = useState<AccountForm>({ full_name: "", email: "", phone: "", password: "" });
  const [errors, setErrors] = useState<Errors<AccountForm>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const schema =
      mode === "register"
        ? { full_name: [required<AccountForm>(), minLength<AccountForm>(3)], email: [required<AccountForm>(), email<AccountForm>()], password: [strongPassword<AccountForm>()] }
        : { email: [required<AccountForm>(), email<AccountForm>()], password: [required<AccountForm>()] };
    const errs = validate(form, schema);
    setErrors(errs);
    if (hasErrors(errs)) return;
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") await register({ ...form, phone: form.phone || undefined });
      else await login(form.email, form.password);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const set = (k: keyof AccountForm) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  return (
    <form onSubmit={submit} noValidate className="space-y-3">
      <div className="flex gap-2 text-sm">
        <button type="button" className={mode === "register" ? "btn-primary" : "btn-secondary"} onClick={() => setMode("register")}>Soy nuevo</button>
        <button type="button" className={mode === "login" ? "btn-primary" : "btn-secondary"} onClick={() => setMode("login")}>Ya tengo cuenta</button>
      </div>
      {error && <Alert>{error}</Alert>}
      {mode === "register" && (
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Nombre completo" htmlFor="full_name" error={errors.full_name}>
            <input id="full_name" className="input" value={form.full_name} onChange={set("full_name")} />
          </Field>
          <Field label="Teléfono (opcional)" htmlFor="phone">
            <input id="phone" className="input" value={form.phone} onChange={set("phone")} />
          </Field>
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Correo" htmlFor="acc-email" error={errors.email}>
          <input id="acc-email" type="email" className="input" value={form.email} onChange={set("email")} />
        </Field>
        <Field label="Contraseña" htmlFor="acc-password" error={errors.password}>
          <input id="acc-password" type="password" className="input" value={form.password} onChange={set("password")} />
        </Field>
      </div>
      <button className="btn-primary" disabled={busy}>{busy ? "Procesando..." : mode === "register" ? "Crear cuenta y continuar" : "Ingresar y continuar"}</button>
    </form>
  );
}

export default function PublicBookingPage() {
  const { user, hasRole } = useAuth();
  const { theme, toggle } = useTheme();
  const [service, setService] = useState<Service | null>(null);
  const [pro, setPro] = useState<Professional | null>(null);
  const [slot, setSlot] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [clientId, setClientId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<Appointment | null>(null);
  const staff = hasRole("admin", "profesional");

  const services = useAsync(() => servicesApi.list({ active: true, page_size: 50 }), []);
  const pros = useAsync(
    () => (service ? professionalsApi.list({ service_id: service.id, active: true, page_size: 50 }) : Promise.resolve(null)),
    [service?.id],
  );
  const clients = useAsync(() => (staff ? usersApi.list({ role: "cliente", page_size: 200 }) : Promise.resolve(null)), [staff]);

  const confirm = async () => {
    if (!service || !pro || !slot) return;
    setBusy(true);
    setError(null);
    try {
      const appt = await appointmentsApi.create({
        professional_id: pro.id, service_id: service.id, start_at: slot, notes: notes || undefined,
        client_id: staff ? Number(clientId) : undefined,
      });
      setDone(appt);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setDone(null);
    setSlot(null);
    setPro(null);
    setService(null);
    setNotes("");
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">R</span> Centro de Bienestar
          </Link>
          <div className="flex items-center gap-2">
            <button onClick={toggle} className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Cambiar tema">
              {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            <Link to={user ? "/citas" : "/login"} className="btn-secondary">{user ? "Mis citas" : "Ingresar"}</Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-4 p-4 sm:p-6">
        <div>
          <h1 className="text-2xl font-bold">Reserva tu cita</h1>
          <p className="text-sm text-slate-500">Elige el servicio, el profesional y un horario libre. Solo mostramos horarios realmente disponibles.</p>
        </div>

        {done ? (
          <section className="card flex flex-col items-center gap-3 p-8 text-center">
            <CheckCircle2 className="h-12 w-12 text-emerald-500" />
            <h2 className="text-xl font-semibold">¡Cita confirmada!</h2>
            <p className="text-sm text-slate-500">
              {done.service_name} con {done.professional_name}<br />
              {formatDateTime(done.start_at)} – {formatTime(done.end_at)} · {formatMoney(done.price)}
            </p>
            <p className="text-xs text-slate-400">Recibirás un recordatorio 24 horas antes.</p>
            <div className="flex gap-2">
              <button className="btn-secondary" onClick={reset}>Reservar otra</button>
              <Link to="/citas" className="btn-primary">Ver mis citas</Link>
            </div>
          </section>
        ) : (
          <>
            <Step n={1} title="Elige un servicio" done={!!service}>
              {services.loading && <Loading />}
              {services.error && <ErrorState message={services.error} onRetry={services.reload} />}
              {services.data?.items.length === 0 && <EmptyState title="No hay servicios disponibles" />}
              <div className="grid gap-3 sm:grid-cols-2">
                {services.data?.items.map((s) => (
                  <button key={s.id} onClick={() => { setService(s); setPro(null); setSlot(null); }}
                    className={`rounded-xl border p-4 text-left transition ${service?.id === s.id ? "border-brand-600 ring-2 ring-brand-500/30" : "border-slate-200 hover:border-brand-400 dark:border-slate-700"}`}>
                    <p className="font-medium">{s.name}</p>
                    <p className="text-xs text-slate-500">{s.description}</p>
                    <p className="mt-2 flex items-center gap-3 text-sm">
                      <span className="flex items-center gap-1 text-slate-500"><Clock className="h-3.5 w-3.5" />{formatDuration(s.duration_minutes)}</span>
                      <span className="font-semibold">{formatMoney(s.price)}</span>
                    </p>
                  </button>
                ))}
              </div>
            </Step>

            {service && (
              <Step n={2} title="Elige un profesional" done={!!pro}>
                {pros.loading && <Loading />}
                {pros.data?.items.length === 0 && <EmptyState title="Ningún profesional ofrece este servicio" />}
                <div className="grid gap-3 sm:grid-cols-2">
                  {pros.data?.items.map((p) => (
                    <button key={p.id} onClick={() => { setPro(p); setSlot(null); }}
                      className={`rounded-xl border p-4 text-left transition ${pro?.id === p.id ? "border-brand-600 ring-2 ring-brand-500/30" : "border-slate-200 hover:border-brand-400 dark:border-slate-700"}`}>
                      <p className="font-medium">{p.full_name}</p>
                      <p className="text-xs text-slate-500">{p.specialty}</p>
                      {p.bio && <p className="mt-1 text-xs text-slate-400">{p.bio}</p>}
                    </button>
                  ))}
                </div>
              </Step>
            )}

            {service && pro && (
              <Step n={3} title="Elige fecha y hora" done={!!slot}>
                <SlotPicker professionalId={pro.id} serviceId={service.id} value={slot} onChange={setSlot} />
              </Step>
            )}

            {service && pro && slot && (
              <Step n={4} title="Confirma tu reserva">
                <div className="mb-4 rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-800/60">
                  <p><strong>{service.name}</strong> con {pro.full_name}</p>
                  <p>{formatDateTime(slot)} · {formatDuration(service.duration_minutes)} · {formatMoney(service.price)}</p>
                </div>
                {!user ? (
                  <AccountBox />
                ) : (
                  <div className="space-y-3">
                    {error && <Alert>{error}</Alert>}
                    {staff && (
                      <Field label="Cliente" htmlFor="client">
                        <select id="client" className="input" value={clientId} onChange={(e) => setClientId(e.target.value)}>
                          <option value="">Selecciona un cliente</option>
                          {clients.data?.items.map((c) => <option key={c.id} value={c.id}>{c.full_name} · {c.email}</option>)}
                        </select>
                      </Field>
                    )}
                    <Field label="Notas para el profesional (opcional)" htmlFor="notes">
                      <textarea id="notes" className="input" rows={2} maxLength={500} value={notes} onChange={(e) => setNotes(e.target.value)} />
                    </Field>
                    <button className="btn-primary" disabled={busy || (staff && !clientId)} onClick={confirm}>
                      {busy ? "Reservando..." : "Confirmar reserva"}
                    </button>
                    <p className="text-xs text-slate-500">Puedes cancelar o reprogramar hasta 24 horas antes de tu cita.</p>
                  </div>
                )}
              </Step>
            )}
          </>
        )}
      </main>
    </div>
  );
}

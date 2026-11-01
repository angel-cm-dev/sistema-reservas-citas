import { CalendarPlus } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Field } from "../components/ui/Field";
import { Alert } from "../components/ui/States";
import { email, hasErrors, required, validate, type Errors } from "../lib/validation";

interface Form {
  email: string;
  password: string;
}

const DEMO = [
  { label: "Admin", email: "admin@demo.pe" },
  { label: "Profesional", email: "lucia.lopez@demo.pe" },
  { label: "Cliente", email: "cliente@demo.pe" },
];

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState<Form>({ email: "", password: "" });
  const [errors, setErrors] = useState<Errors<Form>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate(form, { email: [required(), email()], password: [required()] });
    setErrors(errs);
    if (hasErrors(errs)) return;
    setBusy(true);
    setError(null);
    try {
      await login(form.email, form.password);
      const from = (location.state as { from?: string } | null)?.from ?? "/";
      navigate(from, { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-gradient-to-br from-brand-600 to-brand-900 p-12 text-white lg:flex">
        <div className="text-xl font-bold">Reservas · Centro de Bienestar</div>
        <div>
          <h2 className="text-4xl font-bold leading-tight">Agenda sin cruces, recordatorios automáticos.</h2>
          <p className="mt-4 max-w-md text-brand-100">
            Gestiona profesionales, servicios, horarios y feriados. Tus clientes reservan en línea solo en horarios realmente libres.
          </p>
        </div>
        <p className="text-sm text-brand-200">Proyecto de portafolio · datos ficticios</p>
      </div>
      <div className="flex items-center justify-center p-6">
        <form onSubmit={submit} noValidate className="w-full max-w-sm space-y-4">
          <div>
            <h1 className="text-2xl font-bold">Iniciar sesión</h1>
            <p className="text-sm text-slate-500">Ingresa con tu cuenta o usa una cuenta demo.</p>
          </div>
          {error && <Alert>{error}</Alert>}
          <Field label="Correo" htmlFor="email" error={errors.email}>
            <input id="email" type="email" className="input" autoComplete="username" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} aria-invalid={!!errors.email} />
          </Field>
          <Field label="Contraseña" htmlFor="password" error={errors.password}>
            <input id="password" type="password" className="input" autoComplete="current-password" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} aria-invalid={!!errors.password} />
          </Field>
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? "Ingresando..." : "Ingresar"}
          </button>
          <div className="rounded-lg border border-dashed border-slate-300 p-3 text-xs dark:border-slate-700">
            <p className="mb-2 font-medium">Cuentas demo (contraseña Demo123!)</p>
            <div className="flex flex-wrap gap-2">
              {DEMO.map((d) => (
                <button type="button" key={d.email} className="btn-secondary px-2 py-1 text-xs"
                  onClick={() => setForm({ email: d.email, password: "Demo123!" })}>
                  {d.label}
                </button>
              ))}
            </div>
          </div>
          <Link to="/reservar" className="flex items-center justify-center gap-2 text-sm text-brand-600 hover:underline">
            <CalendarPlus className="h-4 w-4" /> Reservar una cita sin iniciar sesión
          </Link>
        </form>
      </div>
    </div>
  );
}

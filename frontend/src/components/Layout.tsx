import {
  BellRing,
  CalendarDays,
  CalendarOff,
  CalendarPlus,
  Clock,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Menu,
  Moon,
  Stethoscope,
  Sun,
  Users,
} from "lucide-react";
import { useState, type ComponentType } from "react";
import { NavLink, Outlet } from "react-router-dom";
import type { Role } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS } from "../lib/format";
import { useTheme } from "../theme/ThemeContext";

interface NavItem {
  to: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  roles: Role[];
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Panel", icon: LayoutDashboard, roles: ["admin", "profesional"] },
  { to: "/calendario", label: "Calendario", icon: CalendarDays, roles: ["admin", "profesional"] },
  { to: "/citas", label: "Citas", icon: ListChecks, roles: ["admin", "profesional", "cliente"] },
  { to: "/reservar", label: "Reservar cita", icon: CalendarPlus, roles: ["cliente", "admin"] },
  { to: "/servicios", label: "Servicios", icon: Stethoscope, roles: ["admin"] },
  { to: "/profesionales", label: "Profesionales", icon: Users, roles: ["admin"] },
  { to: "/mi-horario", label: "Mi horario", icon: Clock, roles: ["profesional"] },
  { to: "/excepciones", label: "Feriados y ausencias", icon: CalendarOff, roles: ["admin", "profesional"] },
  { to: "/recordatorios", label: "Recordatorios", icon: BellRing, roles: ["admin"] },
];

export function navFor(role: Role): NavItem[] {
  return NAV_ITEMS.filter((i) => i.roles.includes(role));
}

export function Layout() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const [open, setOpen] = useState(false);
  if (!user) return null;

  const sidebar = (
    <nav className="flex h-full flex-col gap-1 p-4" aria-label="Navegación principal">
      <div className="mb-6 flex items-center gap-2 px-2">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-brand-600 font-bold text-white">R</div>
        <div>
          <p className="font-semibold leading-tight">Reservas</p>
          <p className="text-xs text-slate-500">Centro de Bienestar</p>
        </div>
      </div>
      {navFor(user.role).map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/"}
          onClick={() => setOpen(false)}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
              isActive
                ? "bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-200"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            }`
          }
        >
          <Icon className="h-4 w-4" />
          {label}
        </NavLink>
      ))}
      <div className="mt-auto border-t border-slate-200 pt-4 dark:border-slate-800">
        <p className="truncate px-3 text-sm font-medium">{user.full_name}</p>
        <p className="truncate px-3 text-xs text-slate-500">
          {ROLE_LABELS[user.role]} · {user.email}
        </p>
        <button onClick={logout} className="mt-3 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
          <LogOut className="h-4 w-4" /> Cerrar sesión
        </button>
      </div>
    </nav>
  );

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 lg:block">
        <div className="sticky top-0 h-screen">{sidebar}</div>
      </aside>
      {open && (
        <div className="fixed inset-0 z-40 bg-slate-900/50 lg:hidden" onClick={() => setOpen(false)}>
          <aside className="h-full w-64 bg-white dark:bg-slate-900" onClick={(e) => e.stopPropagation()}>
            {sidebar}
          </aside>
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/80 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
          <button className="rounded p-2 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden" onClick={() => setOpen(true)} aria-label="Abrir menú">
            <Menu className="h-5 w-5" />
          </button>
          <span className="text-sm text-slate-500 max-lg:hidden">Hola, {user.full_name.split(" ")[0]}</span>
          <button onClick={toggle} className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Cambiar tema">
            {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
        </header>
        <main className="mx-auto w-full max-w-7xl flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

import { lazy, Suspense } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { RequireAuth } from "./auth/RequireAuth";
import { Layout } from "./components/Layout";
import { Loading } from "./components/ui/States";
import LoginPage from "./pages/LoginPage";

// Carga diferida por página: el bundle inicial solo trae login y layout.
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const CalendarPage = lazy(() => import("./pages/CalendarPage"));
const AppointmentsPage = lazy(() => import("./pages/AppointmentsPage"));
const PublicBookingPage = lazy(() => import("./pages/PublicBookingPage"));
const ServicesPage = lazy(() => import("./pages/ServicesPage"));
const ProfessionalsPage = lazy(() => import("./pages/ProfessionalsPage"));
const MySchedulePage = lazy(() => import("./pages/MySchedulePage"));
const ExceptionsPage = lazy(() => import("./pages/ExceptionsPage"));
const RemindersPage = lazy(() => import("./pages/RemindersPage"));

/** El cliente no tiene panel de KPIs: su inicio es "Mis citas". */
function Home() {
  const { user } = useAuth();
  if (user?.role === "cliente") return <Navigate to="/citas" replace />;
  return <DashboardPage />;
}

function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
      <p className="text-5xl font-bold text-brand-600">404</p>
      <p className="text-slate-500">La página que buscas no existe.</p>
      <Link to="/" className="btn-primary">Volver al inicio</Link>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/reservar" element={<PublicBookingPage />} />
        <Route element={<RequireAuth />}>
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="citas" element={<AppointmentsPage />} />
            <Route element={<RequireAuth roles={["admin", "profesional"]} />}>
              <Route path="calendario" element={<CalendarPage />} />
              <Route path="excepciones" element={<ExceptionsPage />} />
            </Route>
            <Route element={<RequireAuth roles={["admin"]} />}>
              <Route path="servicios" element={<ServicesPage />} />
              <Route path="profesionales" element={<ProfessionalsPage />} />
              <Route path="recordatorios" element={<RemindersPage />} />
            </Route>
            <Route element={<RequireAuth roles={["profesional"]} />}>
              <Route path="mi-horario" element={<MySchedulePage />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Route>
        </Route>
      </Routes>
    </Suspense>
  );
}

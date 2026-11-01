import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { Role } from "../api/types";
import { Loading } from "../components/ui/States";
import { useAuth } from "./AuthContext";

/** Protege rutas: exige sesión y, opcionalmente, uno de los roles indicados. */
export function RequireAuth({ roles }: { roles?: Role[] }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <Loading label="Verificando sesión..." />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <Outlet />;
}

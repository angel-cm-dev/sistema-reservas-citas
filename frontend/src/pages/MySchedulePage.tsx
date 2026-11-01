import { useAuth } from "../auth/AuthContext";
import { ScheduleEditor } from "../components/ScheduleEditor";
import { PageHeader } from "../components/ui/Field";
import { EmptyState } from "../components/ui/States";

export default function MySchedulePage() {
  const { user } = useAuth();
  return (
    <>
      <PageHeader title="Mi horario" subtitle="Bloques semanales en los que recibes reservas" />
      <div className="card p-5">
        {user?.professional_id ? <ScheduleEditor professionalId={user.professional_id} /> : <EmptyState title="Tu usuario no está vinculado a un profesional" description="Pide a un administrador que lo vincule." />}
      </div>
    </>
  );
}

import { useState } from "react";
import { appointmentsApi } from "../api/endpoints";
import type { Appointment } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { parseLocal } from "../lib/dates";
import { formatDateTime } from "../lib/format";
import { SlotPicker } from "./SlotPicker";
import { Modal } from "./ui/Modal";
import { Alert } from "./ui/States";

type Mode = "cancel" | "reschedule" | null;

/** Acciones sobre una cita, respetando rol y estado (el backend valida igual). */
export function AppointmentActions({ appt, onDone }: { appt: Appointment; onDone: () => void }) {
  const { hasRole } = useAuth();
  const [mode, setMode] = useState<Mode>(null);
  const [reason, setReason] = useState("");
  const [slot, setSlot] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (appt.status !== "confirmada") return <span className="text-xs text-slate-400">—</span>;
  const started = parseLocal(appt.start_at) <= new Date();
  const staff = hasRole("admin", "profesional");

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      setMode(null);
      onDone();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const close = () => {
    setMode(null);
    setError(null);
    setReason("");
    setSlot(null);
  };

  return (
    <div className="flex flex-wrap justify-end gap-1">
      {!started && (
        <>
          <button className="btn-secondary px-2 py-1 text-xs" onClick={() => setMode("reschedule")}>Reprogramar</button>
          <button className="btn-secondary px-2 py-1 text-xs text-rose-600" onClick={() => setMode("cancel")}>Cancelar</button>
        </>
      )}
      {started && staff && (
        <>
          <button className="btn-secondary px-2 py-1 text-xs" disabled={busy}
            onClick={() => run(() => appointmentsApi.setStatus(appt.id, "completada"))}>Completada</button>
          <button className="btn-secondary px-2 py-1 text-xs" disabled={busy}
            onClick={() => run(() => appointmentsApi.setStatus(appt.id, "no_asistio"))}>No asistió</button>
        </>
      )}

      <Modal open={mode === "cancel"} title="Cancelar cita" onClose={close}>
        <p className="mb-3 text-sm text-slate-500">
          {appt.service_name} · {formatDateTime(appt.start_at)}
        </p>
        {error && <div className="mb-3"><Alert>{error}</Alert></div>}
        <label className="label" htmlFor="reason">Motivo</label>
        <textarea id="reason" className="input" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
        {!staff && <p className="mt-2 text-xs text-slate-500">Las cancelaciones requieren al menos 24 horas de anticipación.</p>}
        <div className="mt-4 flex justify-end gap-2">
          <button className="btn-secondary" onClick={close}>Volver</button>
          <button className="btn-danger" disabled={busy || reason.trim().length < 3}
            onClick={() => run(() => appointmentsApi.cancel(appt.id, reason.trim()))}>
            Confirmar cancelación
          </button>
        </div>
      </Modal>

      <Modal open={mode === "reschedule"} title="Reprogramar cita" onClose={close} wide>
        <p className="mb-3 text-sm text-slate-500">
          Actual: {formatDateTime(appt.start_at)} · {appt.professional_name}
        </p>
        {error && <div className="mb-3"><Alert>{error}</Alert></div>}
        {mode === "reschedule" && (
          <SlotPicker professionalId={appt.professional_id} serviceId={appt.service_id} value={slot} onChange={setSlot} />
        )}
        <div className="mt-4 flex justify-end gap-2">
          <button className="btn-secondary" onClick={close}>Volver</button>
          <button className="btn-primary" disabled={busy || !slot} onClick={() => slot && run(() => appointmentsApi.reschedule(appt.id, slot))}>
            Confirmar nuevo horario
          </button>
        </div>
      </Modal>
    </div>
  );
}

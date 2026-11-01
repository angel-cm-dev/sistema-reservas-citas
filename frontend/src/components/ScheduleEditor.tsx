import { Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { professionalsApi } from "../api/endpoints";
import type { WorkingHour } from "../api/types";
import { useAsync } from "../hooks/useAsync";
import { WEEKDAYS } from "../lib/dates";
import { Alert, ErrorState, Loading } from "./ui/States";

/** Valida que en un mismo día los bloques no se crucen y que fin > inicio. */
export function scheduleErrors(blocks: WorkingHour[]): string | null {
  for (const b of blocks) {
    if (b.end_time <= b.start_time) return `${WEEKDAYS[b.weekday]}: la hora de fin debe ser posterior a la de inicio.`;
  }
  const sorted = [...blocks].sort((a, b) => a.weekday - b.weekday || a.start_time.localeCompare(b.start_time));
  for (let i = 1; i < sorted.length; i++) {
    const prev = sorted[i - 1];
    const cur = sorted[i];
    if (prev.weekday === cur.weekday && cur.start_time < prev.end_time) {
      return `${WEEKDAYS[cur.weekday]}: hay bloques que se cruzan.`;
    }
  }
  return null;
}

export function ScheduleEditor({ professionalId }: { professionalId: number }) {
  const { data, loading, error, reload } = useAsync(() => professionalsApi.schedule(professionalId), [professionalId]);
  const [blocks, setBlocks] = useState<WorkingHour[]>([]);
  const [message, setMessage] = useState<{ kind: "error" | "success"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (data) setBlocks(data.map((b) => ({ ...b, start_time: b.start_time.slice(0, 5), end_time: b.end_time.slice(0, 5) })));
  }, [data]);

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  const update = (i: number, patch: Partial<WorkingHour>) => setBlocks(blocks.map((b, j) => (j === i ? { ...b, ...patch } : b)));

  const save = async () => {
    const err = scheduleErrors(blocks);
    if (err) return setMessage({ kind: "error", text: err });
    setBusy(true);
    try {
      await professionalsApi.saveSchedule(professionalId, blocks.map(({ weekday, start_time, end_time }) => ({ weekday, start_time, end_time })));
      setMessage({ kind: "success", text: "Horario guardado." });
      reload();
    } catch (e) {
      setMessage({ kind: "error", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      {message && <Alert kind={message.kind}>{message.text}</Alert>}
      {blocks.length === 0 && <p className="text-sm text-slate-500">Sin bloques: el profesional no recibe reservas.</p>}
      {blocks.map((b, i) => (
        <div key={i} className="flex flex-wrap items-center gap-2">
          <select className="input w-36" value={b.weekday} onChange={(e) => update(i, { weekday: Number(e.target.value) })} aria-label="Día">
            {WEEKDAYS.map((d, idx) => <option key={d} value={idx}>{d}</option>)}
          </select>
          <input type="time" className="input w-28" value={b.start_time} onChange={(e) => update(i, { start_time: e.target.value })} aria-label="Inicio" />
          <span className="text-slate-400">a</span>
          <input type="time" className="input w-28" value={b.end_time} onChange={(e) => update(i, { end_time: e.target.value })} aria-label="Fin" />
          <button className="rounded p-2 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950" onClick={() => setBlocks(blocks.filter((_, j) => j !== i))} aria-label="Quitar bloque">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
      <div className="flex flex-wrap gap-2 pt-2">
        <button className="btn-secondary" onClick={() => setBlocks([...blocks, { weekday: 0, start_time: "09:00", end_time: "13:00" }])}>
          <Plus className="h-4 w-4" /> Agregar bloque
        </button>
        <button className="btn-primary" onClick={save} disabled={busy}>{busy ? "Guardando..." : "Guardar horario"}</button>
      </div>
    </div>
  );
}

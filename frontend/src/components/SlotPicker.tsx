import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import { availabilityApi } from "../api/endpoints";
import { useAsync } from "../hooks/useAsync";
import { addDays, parseLocal, toISODate, WEEKDAYS_SHORT } from "../lib/dates";
import { formatTime } from "../lib/format";
import { ErrorState, Loading } from "./ui/States";

interface Props {
  professionalId: number;
  serviceId: number;
  value: string | null;
  onChange: (startAt: string) => void;
}

const DAYS = 7;

/** Selector de horarios libres: tira de 7 días + botones de hora. */
export function SlotPicker({ professionalId, serviceId, value, onChange }: Props) {
  const today = toISODate(new Date());
  const [from, setFrom] = useState(today);
  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const { data, loading, error, reload } = useAsync(
    () => availabilityApi.get(professionalId, serviceId, from, DAYS),
    [professionalId, serviceId, from],
  );

  const shift = (days: number) => {
    setFrom(toISODate(addDays(parseLocal(from), days)));
    setSelectedDay(null);
  };

  const firstWithSlots = data?.find((d) => d.slots.length > 0)?.date ?? null;
  const activeDay = selectedDay ?? firstWithSlots;
  const day = data?.find((d) => d.date === activeDay);

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <button type="button" className="btn-secondary px-2" onClick={() => shift(-DAYS)} disabled={from <= today} aria-label="Semana anterior">
          <ChevronLeft className="h-4 w-4" />
        </button>
        <div className="grid flex-1 grid-cols-7 gap-1">
          {(data ?? []).map((d) => {
            const date = parseLocal(d.date);
            const active = d.date === activeDay;
            const empty = d.slots.length === 0;
            return (
              <button
                type="button"
                key={d.date}
                disabled={empty}
                onClick={() => setSelectedDay(d.date)}
                className={`rounded-lg border px-1 py-2 text-center text-xs transition ${
                  active
                    ? "border-brand-600 bg-brand-600 text-white"
                    : empty
                      ? "cursor-not-allowed border-transparent text-slate-300 dark:text-slate-600"
                      : "border-slate-200 hover:border-brand-400 dark:border-slate-700"
                }`}
              >
                <span className="block">{WEEKDAYS_SHORT[(date.getDay() + 6) % 7]}</span>
                <span className="block text-base font-semibold">{date.getDate()}</span>
              </button>
            );
          })}
        </div>
        <button type="button" className="btn-secondary px-2" onClick={() => shift(DAYS)} aria-label="Semana siguiente">
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {loading && <Loading label="Buscando horarios libres..." />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && !day && (
        <p className="py-6 text-center text-sm text-slate-500">No hay horarios disponibles esta semana. Prueba la siguiente.</p>
      )}
      {!loading && day && (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-5" role="listbox" aria-label="Horarios disponibles">
          {day.slots.map((s) => (
            <button
              type="button"
              role="option"
              aria-selected={value === s.start_at}
              key={s.start_at}
              onClick={() => onChange(s.start_at)}
              className={`rounded-lg border px-2 py-2 text-sm tabular-nums transition ${
                value === s.start_at
                  ? "border-brand-600 bg-brand-600 text-white"
                  : "border-slate-200 hover:border-brand-400 dark:border-slate-700"
              }`}
            >
              {formatTime(s.start_at)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

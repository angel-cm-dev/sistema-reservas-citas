import { useCallback, useEffect, useRef, useState } from "react";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * Ejecuta una función asíncrona cuando cambian sus dependencias y expone
 * los estados de carga / error / datos. Ignora respuestas obsoletas para
 * evitar condiciones de carrera al cambiar filtros rápidamente.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const callId = useRef(0);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fn, deps);

  useEffect(() => {
    const id = ++callId.current;
    setLoading(true);
    setError(null);
    run()
      .then((d) => id === callId.current && setData(d))
      .catch((e: Error) => id === callId.current && setError(e.message))
      .finally(() => id === callId.current && setLoading(false));
  }, [run, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, loading, error, reload };
}

/** Retrasa un valor (útil para búsquedas mientras el usuario escribe). */
export function useDebounced<T>(value: T, ms = 350): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

/**
 * Validación de formularios mínima y declarativa.
 * Las mismas reglas existen en el backend (Pydantic): aquí solo mejoran la
 * experiencia mostrando errores antes de enviar.
 */

export type Rule<T> = (value: unknown, all: T) => string | null;
export type Schema<T> = { [K in keyof T]?: Rule<T>[] };
export type Errors<T> = Partial<Record<keyof T, string>>;

export const required = <T,>(msg = "Campo obligatorio"): Rule<T> => (v) =>
  v === undefined || v === null || String(v).trim() === "" ? msg : null;

export const minLength = <T,>(n: number): Rule<T> => (v) =>
  String(v ?? "").trim().length < n ? `Mínimo ${n} caracteres` : null;

export const email = <T,>(): Rule<T> => (v) =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v ?? "")) ? null : "Correo inválido";

export const numberBetween = <T,>(min: number, max: number): Rule<T> => (v) => {
  const n = Number(v);
  return Number.isFinite(n) && n >= min && n <= max ? null : `Debe estar entre ${min} y ${max}`;
};

export const strongPassword = <T,>(): Rule<T> => (v) => {
  const s = String(v ?? "");
  if (s.length < 8) return "Mínimo 8 caracteres";
  if (!/\d/.test(s) || !/[a-zA-Z]/.test(s)) return "Debe contener letras y números";
  return null;
};

export function validate<T extends object>(values: T, schema: Schema<T>): Errors<T> {
  const errors: Errors<T> = {};
  for (const key of Object.keys(schema) as (keyof T)[]) {
    for (const rule of schema[key] ?? []) {
      const msg = rule(values[key], values);
      if (msg) {
        errors[key] = msg;
        break;
      }
    }
  }
  return errors;
}

export const hasErrors = (e: object) => Object.keys(e).length > 0;

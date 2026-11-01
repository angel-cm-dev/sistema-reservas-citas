export type Role = "admin" | "profesional" | "cliente";
export type AppointmentStatus = "confirmada" | "cancelada" | "completada" | "no_asistio";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone: string | null;
  role: Role;
  is_active: boolean;
  professional_id: number | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Service {
  id: number;
  name: string;
  description: string | null;
  duration_minutes: number;
  price: string;
  is_active: boolean;
}

export interface Professional {
  id: number;
  full_name: string;
  specialty: string;
  bio: string | null;
  user_id: number | null;
  is_active: boolean;
  services: Service[];
}

export interface WorkingHour {
  id?: number;
  weekday: number;
  start_time: string;
  end_time: string;
}

export interface ScheduleException {
  id: number;
  professional_id: number | null;
  date: string;
  start_time: string | null;
  end_time: string | null;
  reason: string;
}

export interface Slot {
  start_at: string;
  end_at: string;
}

export interface DayAvailability {
  date: string;
  professional_id: number;
  service_id: number;
  slots: Slot[];
}

export interface Appointment {
  id: number;
  professional_id: number;
  professional_name: string;
  service_id: number;
  service_name: string;
  client_id: number;
  client_name: string;
  client_email: string;
  start_at: string;
  end_at: string;
  status: AppointmentStatus;
  price: string;
  notes: string | null;
  cancellation_reason: string | null;
  reschedule_count: number;
}

export interface Kpis {
  appointments_today: number;
  appointments_week: number;
  upcoming_confirmed: number;
  cancellation_rate: number;
  no_show_rate: number;
  revenue_month: string;
  reminders_sent_week: number;
  by_status: Record<AppointmentStatus, number>;
  top_services: { name: string; count: number }[];
}

export interface ReminderLog {
  id: number;
  appointment_id: number;
  kind: string;
  channel: string;
  recipient: string;
  message: string;
  status: string;
  sent_at: string;
}

/** Forma de error ProblemDetails (RFC 9457) que devuelve el backend. */
export interface ProblemDetails {
  type?: string;
  title: string;
  status: number;
  detail?: string;
  errors?: { field: string; message: string }[];
}

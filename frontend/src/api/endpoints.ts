import { api } from "./client";
import type {
  Appointment,
  DayAvailability,
  Kpis,
  Page,
  Professional,
  ReminderLog,
  ScheduleException,
  Service,
  TokenResponse,
  User,
  WorkingHour,
} from "./types";

export interface ListParams {
  page?: number;
  page_size?: number;
  sort?: string;
  q?: string;
  [key: string]: string | number | boolean | undefined;
}

export const authApi = {
  login: (email: string, password: string) => api.post<TokenResponse>("/auth/login", { email, password }),
  register: (data: { email: string; full_name: string; phone?: string; password: string }) =>
    api.post<TokenResponse>("/auth/register", data),
  me: () => api.get<User>("/auth/me"),
};

export const servicesApi = {
  list: (p: ListParams = {}) => api.get<Page<Service>>("/services", p),
  create: (data: Omit<Service, "id">) => api.post<Service>("/services", data),
  update: (id: number, data: Omit<Service, "id">) => api.put<Service>(`/services/${id}`, data),
  deactivate: (id: number) => api.del<void>(`/services/${id}`),
};

export const professionalsApi = {
  list: (p: ListParams = {}) => api.get<Page<Professional>>("/professionals", p),
  create: (data: unknown) => api.post<Professional>("/professionals", data),
  update: (id: number, data: unknown) => api.put<Professional>(`/professionals/${id}`, data),
  schedule: (id: number) => api.get<WorkingHour[]>(`/professionals/${id}/working-hours`),
  saveSchedule: (id: number, blocks: WorkingHour[]) =>
    api.put<WorkingHour[]>(`/professionals/${id}/working-hours`, { blocks }),
};

export const exceptionsApi = {
  list: (p: ListParams = {}) => api.get<ScheduleException[]>("/exceptions", p),
  create: (data: Omit<ScheduleException, "id">) => api.post<ScheduleException>("/exceptions", data),
  remove: (id: number) => api.del<void>(`/exceptions/${id}`),
};

export const availabilityApi = {
  get: (professional_id: number, service_id: number, date: string, days = 1) =>
    api.get<DayAvailability[]>("/availability", { professional_id, service_id, date, days }),
};

export const appointmentsApi = {
  list: (p: ListParams = {}) => api.get<Page<Appointment>>("/appointments", p),
  create: (data: { professional_id: number; service_id: number; start_at: string; notes?: string; client_id?: number }) =>
    api.post<Appointment>("/appointments", data),
  reschedule: (id: number, start_at: string) => api.post<Appointment>(`/appointments/${id}/reschedule`, { start_at }),
  cancel: (id: number, reason: string) => api.post<Appointment>(`/appointments/${id}/cancel`, { reason }),
  setStatus: (id: number, status: "completada" | "no_asistio") =>
    api.post<Appointment>(`/appointments/${id}/status`, { status }),
};

export const usersApi = {
  list: (p: ListParams = {}) => api.get<Page<User>>("/users", p),
};

export const dashboardApi = {
  kpis: () => api.get<Kpis>("/dashboard/kpis"),
};

export const remindersApi = {
  list: (p: ListParams = {}) => api.get<Page<ReminderLog>>("/reminders", p),
  run: () => api.post<{ sent: number }>("/reminders/run"),
};

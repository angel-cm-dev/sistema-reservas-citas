from fastapi import APIRouter

from app.api.deps import AdminUser, DashboardSvc, PageDep, ReminderSvc, StaffUser
from app.application.dtos import KpiOut, Page, ReminderOut, ReminderRunOut

router = APIRouter(tags=["Panel y recordatorios"])


@router.get("/dashboard/kpis", response_model=KpiOut, summary="KPIs del panel")
def kpis(actor: StaffUser, svc: DashboardSvc) -> KpiOut:
    return svc.kpis(actor)


@router.get("/reminders", response_model=Page[ReminderOut], summary="Historial de recordatorios")
def list_reminders(_: AdminUser, svc: ReminderSvc, params: PageDep):
    result = svc.list(params)
    return Page[ReminderOut](**{**result, "items": [ReminderOut.model_validate(r) for r in result["items"]]})


@router.post("/reminders/run", response_model=ReminderRunOut, summary="Ejecutar el job de recordatorios ahora")
def run_reminders(_: AdminUser, svc: ReminderSvc) -> ReminderRunOut:
    return ReminderRunOut(sent=svc.run_due())

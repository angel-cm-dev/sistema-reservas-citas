"""Pruebas de integración de la API (FastAPI TestClient + SQLite en memoria).

Datos semilla relevantes (ver app/infrastructure/seed.py), con "ahora" = lun 2026-11-02 08:00:
- Lucía López (prof 1): Consulta nutricional (45 min) y Control nutricional (30 min).
- Cita confirmada de cliente@demo.pe el mar 2026-11-03 10:00-10:45 con Lucía.
- Horario: lun-vie 09-13 y 14-18; sáb 09-13. Feriado general 2026-12-08.
"""

from sqlalchemy import select

from app.domain.models import Professional, Service

BASE = "/api/v1"


def ids(db) -> dict[str, int]:
    return {
        "lopez": db.scalar(select(Professional.id).where(Professional.full_name.like("Lucía%"))),
        "quispe": db.scalar(select(Professional.id).where(Professional.full_name.like("Marco%"))),
        "nutri": db.scalar(select(Service.id).where(Service.name == "Consulta nutricional")),
        "control": db.scalar(select(Service.id).where(Service.name == "Control nutricional")),
        "fisio": db.scalar(select(Service.id).where(Service.name == "Sesión de fisioterapia")),
    }


def book(client, headers, prof, svc, start, **extra):
    return client.post(f"{BASE}/appointments", headers=headers,
                       json={"professional_id": prof, "service_id": svc, "start_at": start, **extra})


# ---------- Salud y autenticación ----------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"
    assert "X-Request-ID" in r.headers


def test_login_success_and_me(client):
    r = client.post(f"{BASE}/auth/login", json={"email": "admin@demo.pe", "password": "Demo123!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["role"] == "admin"


def test_login_failure_returns_problem_details(client):
    r = client.post(f"{BASE}/auth/login", json={"email": "admin@demo.pe", "password": "incorrecta"})
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["status"] == 401 and body["title"] and body["detail"]


def test_register_always_creates_client(client):
    r = client.post(f"{BASE}/auth/register", json={
        "email": "nuevo@demo.pe", "full_name": "Nuevo Cliente", "password": "Clave1234", "role": "admin"})
    assert r.status_code == 201
    assert r.json()["user"]["role"] == "cliente"


def test_register_weak_password_validation(client):
    r = client.post(f"{BASE}/auth/register", json={
        "email": "x@demo.pe", "full_name": "Xx Yy", "password": "solotexto"})
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "password"


def test_protected_endpoint_requires_token(client):
    assert client.get(f"{BASE}/appointments").status_code == 401


# ---------- Catálogo ----------

def test_services_public_list_with_search_and_pagination(client):
    r = client.get(f"{BASE}/services", params={"q": "nutri", "page_size": 1, "sort": "-price"})
    body = r.json()
    assert r.status_code == 200
    assert body["total"] == 2 and body["pages"] == 2
    assert body["items"][0]["name"] == "Consulta nutricional"


def test_invalid_sort_field_is_rejected(client):
    r = client.get(f"{BASE}/services", params={"sort": "password_hash"})
    assert r.status_code == 400


def test_only_admin_creates_services(client, admin_h, cliente_h):
    payload = {"name": "Masaje relajante", "duration_minutes": 50, "price": "100.00"}
    assert client.post(f"{BASE}/services", json=payload, headers=cliente_h).status_code == 403
    r = client.post(f"{BASE}/services", json=payload, headers=admin_h)
    assert r.status_code == 201
    dup = client.post(f"{BASE}/services", json=payload, headers=admin_h)
    assert dup.status_code == 409


def test_service_validation_errors(client, admin_h):
    r = client.post(f"{BASE}/services", json={"name": "X", "duration_minutes": 5, "price": -1}, headers=admin_h)
    assert r.status_code == 422
    fields = {e["field"] for e in r.json()["errors"]}
    assert {"name", "duration_minutes", "price"} <= fields


def test_professional_can_edit_only_own_schedule(client, db, lopez_h):
    i = ids(db)
    blocks = {"blocks": [{"weekday": 0, "start_time": "10:00", "end_time": "12:00"}]}
    own = client.put(f"{BASE}/professionals/{i['lopez']}/working-hours", json=blocks, headers=lopez_h)
    other = client.put(f"{BASE}/professionals/{i['quispe']}/working-hours", json=blocks, headers=lopez_h)
    assert own.status_code == 200
    assert other.status_code == 403


def test_overlapping_schedule_blocks_rejected(client, db, admin_h):
    i = ids(db)
    blocks = {"blocks": [{"weekday": 0, "start_time": "09:00", "end_time": "12:00"},
                         {"weekday": 0, "start_time": "11:00", "end_time": "13:00"}]}
    r = client.put(f"{BASE}/professionals/{i['lopez']}/working-hours", json=blocks, headers=admin_h)
    assert r.status_code == 422


# ---------- Disponibilidad ----------

def test_availability_excludes_existing_appointment(client, db):
    i = ids(db)
    r = client.get(f"{BASE}/availability", params={
        "professional_id": i["lopez"], "service_id": i["nutri"], "date": "2026-11-03"})
    starts = [s["start_at"][11:16] for s in r.json()[0]["slots"]]
    assert "09:00" in starts and "09:15" in starts  # 09:15-10:00 es adyacente a la cita de 10:00
    assert "09:30" not in starts and "10:00" not in starts and "10:30" not in starts
    assert "10:45" in starts
    assert "12:30" not in starts  # 12:30 + 45 min se sale del bloque de la mañana
    assert "17:15" in starts and "17:30" not in starts


def test_availability_respects_holiday_and_min_advance(client, db):
    i = ids(db)
    holiday = client.get(f"{BASE}/availability", params={
        "professional_id": i["lopez"], "service_id": i["nutri"], "date": "2026-12-08"}).json()
    assert holiday[0]["slots"] == []
    today = client.get(f"{BASE}/availability", params={
        "professional_id": i["lopez"], "service_id": i["nutri"], "date": "2026-11-02"}).json()
    first = today[0]["slots"][0]["start_at"]
    assert first.endswith("10:00:00")  # ahora 08:00 + 120 min de anticipación


def test_availability_multiple_days_and_sunday_closed(client, db):
    i = ids(db)
    r = client.get(f"{BASE}/availability", params={
        "professional_id": i["lopez"], "service_id": i["control"], "date": "2026-11-07", "days": 2}).json()
    assert len(r) == 2
    assert r[0]["slots"] and r[1]["slots"] == []  # sábado mañana sí, domingo no


def test_availability_service_not_offered(client, db):
    i = ids(db)
    r = client.get(f"{BASE}/availability", params={
        "professional_id": i["lopez"], "service_id": i["fisio"], "date": "2026-11-03"})
    assert r.status_code == 422


# ---------- Reservas ----------

def test_client_books_and_double_booking_is_rejected(client, db, cliente_h, otro_cliente_h):
    i = ids(db)
    r = book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-03T11:00:00")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "confirmada" and body["end_at"].endswith("11:45:00")
    assert body["price"] == "90.00"
    clash = book(client, otro_cliente_h, i["lopez"], i["control"], "2026-11-03T11:30:00")
    assert clash.status_code == 409


def test_booking_misaligned_or_outside_hours_rejected(client, db, cliente_h):
    i = ids(db)
    assert book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-03T11:05:00").status_code == 409
    assert book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-03T13:00:00").status_code == 409
    assert book(client, cliente_h, i["lopez"], i["nutri"], "2026-12-08T10:00:00").status_code == 409


def test_booking_too_soon_violates_policy(client, db, cliente_h):
    i = ids(db)
    r = book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-02T09:00:00")
    assert r.status_code == 422
    assert "anticipación" in r.json()["detail"]


def test_client_cannot_overlap_own_appointments(client, db, cliente_h):
    i = ids(db)
    # cliente@demo.pe ya tiene cita mar 10:00-10:45 con Lucía; intenta fisio con Marco a las 10:00.
    r = book(client, cliente_h, i["quispe"], i["fisio"], "2026-11-03T10:00:00")
    assert r.status_code == 409
    assert "otra cita" in r.json()["detail"]


def test_staff_books_for_client(client, db, lopez_h, quispe_h):
    i = ids(db)
    users = client.get(f"{BASE}/users", headers=lopez_h, params={"q": "jorge"}).json()["items"]
    assert all(u["role"] == "cliente" for u in users)
    jorge = users[0]["id"]
    ok = book(client, lopez_h, i["lopez"], i["control"], "2026-11-02T09:00:00", client_id=jorge)
    assert ok.status_code == 201  # el personal no está sujeto a la anticipación mínima
    other = book(client, quispe_h, i["lopez"], i["control"], "2026-11-04T15:00:00", client_id=jorge)
    assert other.status_code == 403


def test_roles_see_only_their_appointments(client, cliente_h, lopez_h, admin_h):
    mine = client.get(f"{BASE}/appointments", headers=cliente_h).json()
    assert mine["total"] >= 1
    assert all(a["client_email"] == "cliente@demo.pe" for a in mine["items"])
    lopez = client.get(f"{BASE}/appointments", headers=lopez_h, params={"page_size": 50}).json()
    assert all(a["professional_name"].startswith("Lucía") for a in lopez["items"])
    every = client.get(f"{BASE}/appointments", headers=admin_h, params={"page_size": 50}).json()
    assert every["total"] == 9


def test_appointment_filters(client, admin_h):
    r = client.get(f"{BASE}/appointments", headers=admin_h, params={
        "status": "confirmada", "date_from": "2026-11-03", "date_to": "2026-11-03", "sort": "-start_at"}).json()
    assert r["total"] == 2
    assert r["items"][0]["start_at"] > r["items"][1]["start_at"]
    q = client.get(f"{BASE}/appointments", headers=admin_h, params={"q": "fisioterapia"}).json()
    assert all(a["service_name"] == "Sesión de fisioterapia" for a in q["items"])


def test_other_client_gets_404_on_foreign_appointment(client, cliente_h, otro_cliente_h):
    appt = client.get(f"{BASE}/appointments", headers=cliente_h, params={"status": "confirmada"}).json()["items"][0]
    assert client.get(f"{BASE}/appointments/{appt['id']}", headers=otro_cliente_h).status_code == 404


# ---------- Cancelación y reprogramación ----------

def test_cancel_frees_slot(client, db, cliente_h, otro_cliente_h):
    i = ids(db)
    appt = book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-04T15:00:00").json()
    r = client.post(f"{BASE}/appointments/{appt['id']}/cancel", headers=cliente_h, json={"reason": "No podré asistir"})
    assert r.status_code == 200 and r.json()["status"] == "cancelada"
    again = book(client, otro_cliente_h, i["lopez"], i["nutri"], "2026-11-04T15:00:00")
    assert again.status_code == 201


def test_client_cannot_cancel_late_but_staff_can(client, db, cliente_h, lopez_h):
    i = ids(db)
    appt = book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-02T14:00:00").json()
    late = client.post(f"{BASE}/appointments/{appt['id']}/cancel", headers=cliente_h, json={"reason": "Imprevisto"})
    assert late.status_code == 422
    staff = client.post(f"{BASE}/appointments/{appt['id']}/cancel", headers=lopez_h,
                        json={"reason": "Reprograma por teléfono"})
    assert staff.status_code == 200


def test_reschedule_and_limit(client, db, cliente_h):
    i = ids(db)
    appt = book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-05T09:00:00").json()
    url = f"{BASE}/appointments/{appt['id']}/reschedule"
    r1 = client.post(url, headers=cliente_h, json={"start_at": "2026-11-05T09:30:00"})
    assert r1.status_code == 200 and r1.json()["reschedule_count"] == 1
    # Puede moverse a un horario que se solapa con su propio horario anterior.
    r2 = client.post(url, headers=cliente_h, json={"start_at": "2026-11-05T09:45:00"})
    assert r2.status_code == 200
    r3 = client.post(url, headers=cliente_h, json={"start_at": "2026-11-05T11:00:00"})
    assert r3.status_code == 422 and "máximo" in r3.json()["detail"]


def test_close_appointment_rules(client, db, cliente_h, lopez_h):
    i = ids(db)
    appt = book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-06T09:00:00").json()
    url = f"{BASE}/appointments/{appt['id']}/status"
    assert client.post(url, headers=cliente_h, json={"status": "completada"}).status_code == 403
    assert client.post(url, headers=lopez_h, json={"status": "completada"}).status_code == 422


# ---------- Recordatorios y panel ----------

def test_reminder_job_is_idempotent(client, db, cliente_h, admin_h, notifier):
    i = ids(db)
    book(client, cliente_h, i["lopez"], i["nutri"], "2026-11-02T15:00:00")
    first = client.post(f"{BASE}/reminders/run", headers=admin_h).json()
    assert first["sent"] == 1
    assert notifier.sent[0][0] == "cliente@demo.pe"
    assert client.post(f"{BASE}/reminders/run", headers=admin_h).json()["sent"] == 0
    logs = client.get(f"{BASE}/reminders", headers=admin_h).json()
    assert logs["total"] == 1 and logs["items"][0]["status"] == "enviado"


def test_reminders_admin_only(client, cliente_h):
    assert client.post(f"{BASE}/reminders/run", headers=cliente_h).status_code == 403


def test_dashboard_kpis(client, admin_h, lopez_h, cliente_h):
    k = client.get(f"{BASE}/dashboard/kpis", headers=admin_h).json()
    assert k["by_status"]["cancelada"] == 1
    assert k["by_status"]["completada"] == 2
    assert k["cancellation_rate"] == round(100 / 9, 1)
    assert k["upcoming_confirmed"] == 5
    lopez = client.get(f"{BASE}/dashboard/kpis", headers=lopez_h).json()
    assert lopez["upcoming_confirmed"] == 3
    assert client.get(f"{BASE}/dashboard/kpis", headers=cliente_h).status_code == 403


def test_holiday_exception_only_admin(client, db, lopez_h, admin_h):
    i = ids(db)
    general = {"date": "2026-11-20", "reason": "Aniversario del centro"}
    assert client.post(f"{BASE}/exceptions", json=general, headers=lopez_h).status_code == 403
    own = {"professional_id": i["lopez"], "date": "2026-11-20", "start_time": "09:00",
           "end_time": "11:00", "reason": "Congreso"}
    assert client.post(f"{BASE}/exceptions", json=own, headers=lopez_h).status_code == 201
    assert client.post(f"{BASE}/exceptions", json=general, headers=admin_h).status_code == 201
    slots = client.get(f"{BASE}/availability", params={
        "professional_id": i["lopez"], "service_id": i["nutri"], "date": "2026-11-20"}).json()[0]["slots"]
    assert slots == []

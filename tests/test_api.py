"""Сквозной тест REST API на in-memory адаптерах."""
from datetime import timedelta

import pytest
from fakes import FakeEngine, PlainHasher, make_uow_factory
from fastapi.testclient import TestClient

from salary.adapters.inbound.http.app import create_app
from salary.adapters.outbound.security.jwt_tokens import JwtTokenService
from salary.application.services.auth import AuthService
from salary.application.services.employees import EmployeeService
from salary.application.services.payroll import PayrollService
from salary.application.services.sick_leaves import SickLeaveService
from salary.config import Settings
from salary.container import Container
from salary.domain.payroll import PayrollCalculator


@pytest.fixture
def client():
    uow = make_uow_factory()
    container = Container(
        engine=FakeEngine(),
        auth=AuthService(uow, PlainHasher(), JwtTokenService("test-secret-" + "x" * 32, timedelta(minutes=5))),
        employees=EmployeeService(uow),
        sick_leaves=SickLeaveService(uow),
        payroll=PayrollService(uow, PayrollCalculator()),
    )
    settings = Settings(_env_file=None, admin_login="admin", admin_password="admin123")
    with TestClient(create_app(settings, container)) as c:
        yield c


def login(client, login, password):
    r = client.post("/api/auth/login", json={"login": login, "password": password})
    return r


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_full_flow(client):
    r = client.post("/api/auth/register", json={"login": "ivan", "password": "secret1", "full_name": "Иван"})
    assert r.status_code == 201
    uid = r.json()["id"]
    assert login(client, "ivan", "secret1").status_code == 403

    admin = auth(login(client, "admin", "admin123").json()["access_token"])
    assert client.post(f"/api/admin/employees/{uid}/verify", headers=admin).json()["status"] == "active"
    r = client.put(f"/api/admin/employees/{uid}/salary", json={"base_salary": "22000"}, headers=admin)
    assert r.json()["base_salary"] == "22000.00"
    r = client.post(
        f"/api/admin/employees/{uid}/bonuses",
        json={"amount": "1000", "kind": "allowance", "year": 2026, "month": 10, "comment": "стаж"},
        headers=admin,
    )
    assert r.status_code == 201

    user = auth(login(client, "ivan", "secret1").json()["access_token"])
    assert client.get("/api/admin/employees", headers=user).status_code == 403
    assert len(client.get("/api/me/bonuses", headers=user).json()) == 1
    r = client.post("/api/me/sick-leaves", json={"date_from": "2026-10-05", "date_to": "2026-10-09"}, headers=user)
    assert r.status_code == 201
    leave_id = r.json()["id"]

    leaves = client.get("/api/admin/sick-leaves?status=pending", headers=admin).json()
    assert leaves[0]["employee_name"] == "Иван"
    client.post(f"/api/admin/sick-leaves/{leave_id}/approve", headers=admin)

    slip = client.get("/api/me/payslip?year=2026&month=10", headers=user).json()
    assert slip["sick_days"] == 5
    assert slip["sick_pay"] == "2500.00"
    assert slip["total"] == "20500.00"


def test_unauthorized(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=auth("garbage")).status_code == 401


def test_static_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "<html" in r.text.lower()

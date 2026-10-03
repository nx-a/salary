"""Функции администратора."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from salary.adapters.inbound.http.dependencies import AdminUser, ContainerDep
from salary.adapters.inbound.http.schemas import (
    BonusIn,
    BonusOut,
    PayslipOut,
    SalaryIn,
    SickLeaveAdminOut,
    SickLeaveOut,
    UserOut,
)
from salary.domain.models import SickLeaveStatus, UserStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/employees", response_model=list[UserOut])
def list_employees(_: AdminUser, container: ContainerDep, status_: UserStatus | None = Query(None, alias="status")):
    return container.employees.list(status_)


@router.get("/employees/{user_id}", response_model=UserOut)
def get_employee(user_id: int, _: AdminUser, container: ContainerDep):
    return container.employees.get(user_id)


@router.post("/employees/{user_id}/verify", response_model=UserOut)
def verify_employee(user_id: int, _: AdminUser, container: ContainerDep):
    return container.employees.verify(user_id)


@router.post("/employees/{user_id}/reject", response_model=UserOut)
def reject_employee(user_id: int, _: AdminUser, container: ContainerDep):
    return container.employees.reject(user_id)


@router.put("/employees/{user_id}/salary", response_model=UserOut)
def set_salary(user_id: int, body: SalaryIn, _: AdminUser, container: ContainerDep):
    return container.employees.set_salary(user_id, body.base_salary)


@router.get("/employees/{user_id}/bonuses", response_model=list[BonusOut])
def employee_bonuses(user_id: int, _: AdminUser, container: ContainerDep):
    return container.employees.bonuses(user_id)


@router.post("/employees/{user_id}/bonuses", response_model=BonusOut, status_code=status.HTTP_201_CREATED)
def add_bonus(user_id: int, body: BonusIn, _: AdminUser, container: ContainerDep):
    return container.employees.add_bonus(user_id, body.amount, body.kind, body.year, body.month, body.comment)


@router.delete("/bonuses/{bonus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bonus(bonus_id: int, _: AdminUser, container: ContainerDep):
    container.employees.delete_bonus(bonus_id)


@router.get("/employees/{user_id}/payslip", response_model=PayslipOut)
def employee_payslip(
    user_id: int,
    _: AdminUser,
    container: ContainerDep,
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
):
    return container.payroll.payslip(user_id, year, month)


@router.get("/sick-leaves", response_model=list[SickLeaveAdminOut])
def list_sick_leaves(
    _: AdminUser, container: ContainerDep, status_: SickLeaveStatus | None = Query(None, alias="status")
):
    names = {u.id: u.full_name for u in container.employees.list()}
    return [
        SickLeaveAdminOut.model_validate(leave).model_copy(update={"employee_name": names.get(leave.user_id, "")})
        for leave in container.sick_leaves.list(status_)
    ]


@router.post("/sick-leaves/{leave_id}/approve", response_model=SickLeaveOut)
def approve_sick_leave(leave_id: int, _: AdminUser, container: ContainerDep):
    return container.sick_leaves.approve(leave_id)


@router.post("/sick-leaves/{leave_id}/reject", response_model=SickLeaveOut)
def reject_sick_leave(leave_id: int, _: AdminUser, container: ContainerDep):
    return container.sick_leaves.reject(leave_id)

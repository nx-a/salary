"""Личный кабинет сотрудника."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from salary.adapters.inbound.http.dependencies import ContainerDep, CurrentUser
from salary.adapters.inbound.http.schemas import BonusOut, PayslipOut, SickLeaveIn, SickLeaveOut

router = APIRouter(prefix="/me", tags=["employee"])


@router.get("/bonuses", response_model=list[BonusOut])
def my_bonuses(
    user: CurrentUser,
    container: ContainerDep,
    year: int | None = Query(default=None),
    month: int | None = Query(default=None, ge=1, le=12),
):
    return container.employees.bonuses(user.id, year, month)


@router.get("/sick-leaves", response_model=list[SickLeaveOut])
def my_sick_leaves(user: CurrentUser, container: ContainerDep):
    return container.sick_leaves.list_for_user(user.id)


@router.post("/sick-leaves", response_model=SickLeaveOut, status_code=status.HTTP_201_CREATED)
def create_sick_leave(body: SickLeaveIn, user: CurrentUser, container: ContainerDep):
    return container.sick_leaves.create(user.id, body.date_from, body.date_to, body.comment)


@router.get("/payslip", response_model=PayslipOut)
def my_payslip(
    user: CurrentUser,
    container: ContainerDep,
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
):
    return container.payroll.payslip(user.id, year, month)

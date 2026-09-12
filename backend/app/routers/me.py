from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import CurrentUser, get_current_user
from backend.app.models.employee import Employee
from backend.app.schemas.employee import EmployeeSummary, LeaveBalanceResponse
from backend.app.services.balance_service import BalanceService

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/profile", response_model=EmployeeSummary)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    employee = await db.scalar(select(Employee).where(Employee.employee_id == current_user.employee_id))
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found.")
    return employee


@router.get("/leave-balance", response_model=list[LeaveBalanceResponse])
async def get_leave_balance(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await BalanceService.get_employee_balance(db, current_user.employee_id)

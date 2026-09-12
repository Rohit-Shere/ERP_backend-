from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import CurrentUser, get_current_user
from backend.app.schemas.leave_application import LeaveApplicationCreate, LeaveApplicationResponse
from backend.app.services.leave_service import LeaveService

router = APIRouter(prefix="/leave-applications", tags=["leave-applications"])


@router.post("/", response_model=LeaveApplicationResponse)
async def create_leave_application(
    payload: LeaveApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await LeaveService.create_application(db, current_user.employee_id, payload)


@router.get("/my", response_model=list[LeaveApplicationResponse])
async def get_my_applications(
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    applications = await LeaveService.list_employee_applications(db, current_user.employee_id)
    if status is not None:
        applications = [application for application in applications if application.status == status]
    return applications

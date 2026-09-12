from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import CurrentUser, require_role
from backend.app.services.leave_service import LeaveService
from backend.app.schemas.approval import ApprovalDecision
from backend.app.schemas.leave_application import LeaveApplicationResponse

router = APIRouter(prefix="/hod", tags=["hod"])


@router.get("/leave-applications", response_model=list[LeaveApplicationResponse])
async def list_hod_applications(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("DEPARTMENT_HEAD")),
):
    from sqlalchemy import select
    from backend.app.models.employee import Employee

    employee = await db.scalar(select(Employee).where(Employee.employee_id == current_user.employee_id))
    if employee is None:
        return []
    return await LeaveService.list_department_applications(db, employee.department_id)


@router.post("/leave-applications/{application_id}/approve")
async def approve_application(
    application_id: int,
    payload: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("DEPARTMENT_HEAD")),
):
    return await LeaveService.record_decision(
        db, application_id, current_user.employee_id, "DEPARTMENT_HEAD", "APPROVED", payload.comments
    )


@router.post("/leave-applications/{application_id}/reject")
async def reject_application(
    application_id: int,
    payload: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("DEPARTMENT_HEAD")),
):
    return await LeaveService.record_decision(
        db, application_id, current_user.employee_id, "DEPARTMENT_HEAD", "REJECTED", payload.comments
    )

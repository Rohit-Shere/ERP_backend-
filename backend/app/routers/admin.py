from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import CurrentUser, require_role
from backend.app.schemas.approval import ApprovalDecision
from backend.app.schemas.leave_application import LeaveApplicationResponse
from backend.app.services.leave_service import LeaveService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/leave-applications", response_model=list[LeaveApplicationResponse])
async def list_pending_admin_applications(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return await LeaveService.list_pending_admin_applications(db)


@router.post("/leave-applications/{application_id}/approve")
async def approve_application(
    application_id: int,
    payload: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return await LeaveService.record_decision(
        db, application_id, current_user.employee_id, "ADMIN", "APPROVED", payload.comments
    )


@router.post("/leave-applications/{application_id}/reject")
async def reject_application(
    application_id: int,
    payload: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return await LeaveService.record_decision(
        db, application_id, current_user.employee_id, "ADMIN", "REJECTED", payload.comments
    )

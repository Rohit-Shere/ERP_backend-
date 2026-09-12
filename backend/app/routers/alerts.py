from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import CurrentUser, get_current_user
from backend.app.schemas.alert import AlertReadResponse, AlertResponse
from backend.app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_my_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await AlertService.list_employee_alerts(db, current_user.employee_id)


@router.patch("/{alert_id}/read", response_model=AlertReadResponse)
async def mark_alert_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await AlertService.mark_read(db, current_user.employee_id, alert_id)
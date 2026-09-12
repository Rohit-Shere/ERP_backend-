from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.leave_alert import LeaveAlert


def alert_title(alert_type: str) -> str:
    titles = {
        "APPROACHING_LIMIT": "Leave balance approaching threshold",
        "LIMIT_REACHED": "Leave limit reached",
        "LIMIT_EXCEEDED": "Leave entitlement exceeded",
    }
    return titles.get(alert_type, alert_type.replace("_", " ").title())


def serialize_alert(alert: LeaveAlert) -> dict:
    return {
        "id": alert.alert_id,
        "type": alert.alert_type,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert_title(alert.alert_type),
        "message": alert.message,
        "read": alert.is_read,
        "created_at": alert.created_at,
        "leave_type_id": alert.leave_type_id,
        "leave_id": alert.leave_id,
        "academic_year": alert.academic_year,
        "threshold_value": alert.threshold_value,
        "actual_value": alert.actual_value,
    }


class AlertService:
    @staticmethod
    async def list_employee_alerts(db: AsyncSession, employee_id: int) -> list[dict]:
        result = await db.scalars(
            select(LeaveAlert)
            .where(LeaveAlert.employee_id == employee_id)
            .order_by(LeaveAlert.created_at.desc())
        )
        return [serialize_alert(alert) for alert in result.all()]

    @staticmethod
    async def mark_read(db: AsyncSession, employee_id: int, alert_id: int) -> dict:
        if db.in_transaction():
            await db.commit()

        async with db.begin():
            alert = await db.scalar(
                select(LeaveAlert)
                .where(
                    LeaveAlert.alert_id == alert_id,
                    LeaveAlert.employee_id == employee_id,
                )
                .with_for_update()
            )
            if alert is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
            alert.is_read = True

        return {"id": alert_id, "read": True}
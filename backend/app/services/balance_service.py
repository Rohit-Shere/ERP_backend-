from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.employee import Employee
from backend.app.models.leave_entitlement import LeaveEntitlement
from backend.app.models.leave_record import LeaveRecord
from backend.app.models.leave_type import LeaveType


def academic_year_for(day: date) -> str:
    start_year = day.year if day.month >= 6 else day.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


class BalanceService:
    @staticmethod
    def calculate_remaining(entitled_days: float, used_days: float, carry_forward_days: float = 0) -> float:
        return entitled_days + carry_forward_days - used_days

    @classmethod
    async def get_employee_balance(
        cls, db: AsyncSession, employee_id: int, as_of: date | None = None
    ) -> list[dict]:
        as_of = as_of or date.today()
        employee = await db.scalar(select(Employee).where(Employee.employee_id == employee_id))
        if employee is None:
            return []

        used_subquery = (
            select(
                LeaveRecord.leave_type_id,
                func.coalesce(func.sum(LeaveRecord.calculated_days), 0).label("used"),
            )
            .where(
                LeaveRecord.employee_id == employee_id,
                LeaveRecord.status == "TAKEN",
                LeaveRecord.start_date <= as_of,
            )
            .group_by(LeaveRecord.leave_type_id)
            .subquery()
        )
        result = await db.execute(
            select(LeaveEntitlement, LeaveType.leave_name, func.coalesce(used_subquery.c.used, 0))
            .join(LeaveType, LeaveType.leave_type_id == LeaveEntitlement.leave_type_id)
            .outerjoin(used_subquery, used_subquery.c.leave_type_id == LeaveEntitlement.leave_type_id)
            .where(
                LeaveEntitlement.category_id == employee.category_id,
                LeaveEntitlement.academic_year == academic_year_for(as_of),
                LeaveEntitlement.is_active.is_(True),
            )
        )
        balances = []
        for entitlement, leave_name, used in result.all():
            entitled = float(entitlement.entitled_days)
            carry_forward = float(entitlement.carry_forward_days)
            used_days = float(used)
            balances.append(
                {
                    "leave_type_id": entitlement.leave_type_id,
                    "leave_type": leave_name,
                    "entitled": entitled,
                    "carry_forward": carry_forward,
                    "used": used_days,
                    "remaining": cls.calculate_remaining(entitled, used_days, carry_forward),
                }
            )
        return balances

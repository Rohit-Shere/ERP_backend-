from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class LeaveRecord(Base):
    __tablename__ = "leave_record"

    leave_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("leave_application.application_id"), unique=True, nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.employee_id"), nullable=False)
    leave_type_id: Mapped[int] = mapped_column(ForeignKey("leave_type.leave_type_id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    calculated_days: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="TAKEN")
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

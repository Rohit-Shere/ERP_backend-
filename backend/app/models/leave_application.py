from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, TIMESTAMP, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class LeaveApplication(Base):
    __tablename__ = "leave_application"

    application_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.employee_id"), nullable=False)
    leave_type_id: Mapped[int] = mapped_column(ForeignKey("leave_type.leave_type_id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    requested_days: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    calculated_days: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    station_leaving: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    station_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    station_contact_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING_DEPARTMENT_HEAD")
    submitted_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

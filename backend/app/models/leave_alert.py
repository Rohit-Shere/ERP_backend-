from sqlalchemy import Boolean, ForeignKey, Numeric, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class LeaveAlert(Base):
    __tablename__ = "leave_alert"

    alert_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.employee_id"), nullable=False)
    leave_type_id: Mapped[int] = mapped_column(ForeignKey("leave_type.leave_type_id"), nullable=False)
    leave_id: Mapped[int | None] = mapped_column(ForeignKey("leave_record.leave_id"), nullable=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold_value: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    actual_value: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_sent_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    resolved_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

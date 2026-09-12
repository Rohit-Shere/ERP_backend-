from datetime import datetime

from sqlalchemy import ForeignKey, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ApprovalHistory(Base):
    __tablename__ = "approval_history"

    approval_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("leave_application.application_id", ondelete="CASCADE"),
        nullable=False,
    )
    approver_id: Mapped[int] = mapped_column(ForeignKey("employee.employee_id"), nullable=False)
    approver_role: Mapped[str] = mapped_column(String(30), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    comments: Mapped[str | None] = mapped_column(String, nullable=True)
    action_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
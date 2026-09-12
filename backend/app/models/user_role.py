from uuid import UUID

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class UserRole(Base):
    __tablename__ = "user_role"

    user_role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("user_account.user_id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.role_id"), nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("department.department_id"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
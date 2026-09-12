from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, TIMESTAMP, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class UserAccount(Base):
    __tablename__ = "user_account"

    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.employee_id"), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
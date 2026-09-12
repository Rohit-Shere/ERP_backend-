from sqlalchemy import Boolean, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class EmployeeCategory(Base):
    __tablename__ = "employee_category"

    category_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    category_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

from sqlalchemy import Boolean, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Department(Base):
    __tablename__ = "department"

    department_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    department_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

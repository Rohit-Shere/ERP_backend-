from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class LeaveEntitlement(Base):
    __tablename__ = "leave_entitlement"

    entitlement_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("employee_category.category_id"), nullable=False)
    leave_type_id: Mapped[int] = mapped_column(ForeignKey("leave_type.leave_type_id"), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    entitled_days: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    max_days: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    carry_forward_days: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    warning_threshold: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "leave_type_id",
            "academic_year",
            name="uq_entitlement_category_type_year",
        ),
    )

from datetime import date

from sqlalchemy import Date, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class Employee(Base):
    __tablename__ = "employee"

    employee_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.department_id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("employee_category.category_id"), nullable=False)
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    department = relationship("Department")
    category = relationship("EmployeeCategory")

from sqlalchemy import ForeignKey, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class LeaveAttachment(Base):
    __tablename__ = "leave_attachment"

    attachment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("leave_application.application_id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    uploaded_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

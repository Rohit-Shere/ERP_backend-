from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    alert_type: str
    severity: str
    title: str
    message: str
    read: bool
    created_at: datetime
    leave_type_id: int
    leave_id: int | None = None
    academic_year: str
    threshold_value: float | None = None
    actual_value: float


class AlertReadResponse(BaseModel):
    id: int
    read: bool
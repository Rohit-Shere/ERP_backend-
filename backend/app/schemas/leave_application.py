from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class LeaveApplicationCreate(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str | None = None
    station_leaving: bool = False
    station_name: str | None = None
    station_contact_number: str | None = None


class LeaveApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    requested_days: float
    calculated_days: float
    status: str
    submitted_at: datetime
    reason: str | None = None
    station_leaving: bool = False
    station_name: str | None = None
    station_contact_number: str | None = None
    employee_name: str | None = None
    employee_code: str | None = None
    employee_email: str | None = None
    employee_phone: str | None = None
    designation: str | None = None
    department_name: str | None = None
    category_name: str | None = None
    leave_type: str | None = None

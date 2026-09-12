from pydantic import BaseModel, ConfigDict


class EmployeeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    employee_code: str
    first_name: str
    last_name: str | None = None
    email: str
    department_id: int
    designation: str | None = None


class LeaveBalanceResponse(BaseModel):
    leave_type_id: int
    leave_type: str
    entitled: float
    carry_forward: float
    used: float
    remaining: float

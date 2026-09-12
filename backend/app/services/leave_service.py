from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.approval_history import ApprovalHistory
from backend.app.models.employee import Employee
from backend.app.models.department import Department
from backend.app.models.employee_category import EmployeeCategory
from backend.app.models.leave_application import LeaveApplication
from backend.app.models.leave_record import LeaveRecord
from backend.app.models.leave_type import LeaveType
from backend.app.schemas.leave_application import LeaveApplicationCreate


class LeaveService:
    @staticmethod
    def _application_details(application, employee, department, category, leave_type):
        return {
            "application_id": application.application_id,
            "employee_id": application.employee_id,
            "leave_type_id": application.leave_type_id,
            "start_date": application.start_date,
            "end_date": application.end_date,
            "requested_days": application.requested_days,
            "calculated_days": application.calculated_days,
            "status": application.status,
            "submitted_at": application.submitted_at,
            "reason": application.reason,
            "station_leaving": application.station_leaving,
            "station_name": application.station_name,
            "station_contact_number": application.station_contact_number,
            "employee_name": f"{employee.first_name} {employee.last_name or ''}".strip(),
            "employee_code": employee.employee_code,
            "employee_email": employee.email,
            "employee_phone": employee.phone,
            "designation": employee.designation,
            "department_name": department.department_name if department else None,
            "category_name": category.category_name if category else None,
            "leave_type": leave_type.leave_name if leave_type else None,
        }

    @staticmethod
    async def _list_application_details(db: AsyncSession, statement):
        result = await db.execute(
            statement
            .with_only_columns(
                LeaveApplication,
                Employee,
                Department,
                EmployeeCategory,
                LeaveType,
            )
            .join(Employee, Employee.employee_id == LeaveApplication.employee_id)
            .outerjoin(Department, Department.department_id == Employee.department_id)
            .outerjoin(EmployeeCategory, EmployeeCategory.category_id == Employee.category_id)
            .outerjoin(LeaveType, LeaveType.leave_type_id == LeaveApplication.leave_type_id)
        )
        return [
            LeaveService._application_details(application, employee, department, category, leave_type)
            for application, employee, department, category, leave_type in result.all()
        ]

    @staticmethod
    def calculate_requested_days(start_date: date, end_date: date) -> float:
        if end_date < start_date:
            raise ValueError("End date cannot be before start date.")
        return (end_date - start_date).days + 1

    @staticmethod
    def validate_dates(start_date: date, end_date: date) -> None:
        if end_date < start_date:
            raise ValueError("End date cannot be before start date.")

    @classmethod
    async def create_application(
        cls,
        db: AsyncSession,
        employee_id: int,
        payload: LeaveApplicationCreate,
    ) -> LeaveApplication:
        cls.validate_dates(payload.start_date, payload.end_date)
        employee = await db.scalar(
            select(Employee).where(
                Employee.employee_id == employee_id,
                Employee.employment_status == "ACTIVE",
            )
        )
        if employee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active employee not found.")
        if payload.station_leaving is False and (
            payload.station_name is not None or payload.station_contact_number is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Station details require station_leaving=true.",
            )

        days = cls.calculate_requested_days(payload.start_date, payload.end_date)
        application = LeaveApplication(
            employee_id=employee_id,
            leave_type_id=payload.leave_type_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            requested_days=days,
            calculated_days=days,
            reason=payload.reason,
            station_leaving=payload.station_leaving,
            station_name=payload.station_name,
            station_contact_number=payload.station_contact_number,
        )
        db.add(application)
        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def list_employee_applications(db: AsyncSession, employee_id: int) -> list[LeaveApplication]:
        statement = select(LeaveApplication).where(
            LeaveApplication.employee_id == employee_id
        ).order_by(LeaveApplication.submitted_at.desc())
        return await LeaveService._list_application_details(db, statement)

    @staticmethod
    async def list_department_applications(
        db: AsyncSession, department_id: int
    ) -> list[LeaveApplication]:
        statement = select(LeaveApplication).where(
            Employee.department_id == department_id,
            LeaveApplication.status == "PENDING_DEPARTMENT_HEAD",
        ).order_by(LeaveApplication.submitted_at.asc())
        return await LeaveService._list_application_details(db, statement)

    @staticmethod
    async def list_pending_admin_applications(db: AsyncSession) -> list[LeaveApplication]:
        statement = select(LeaveApplication).where(
            LeaveApplication.status == "PENDING_ADMIN",
        ).order_by(LeaveApplication.submitted_at.asc())
        return await LeaveService._list_application_details(db, statement)

    @staticmethod
    async def record_decision(
        db: AsyncSession,
        application_id: int,
        approver_id: int,
        role: str,
        action: str,
        comments: str | None,
    ) -> LeaveApplication:
        if db.in_transaction():
            await db.commit()

        async with db.begin():
            application = await db.scalar(
                select(LeaveApplication)
                .where(LeaveApplication.application_id == application_id)
                .with_for_update()
            )
            if application is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

            expected_status = {
                "DEPARTMENT_HEAD": "PENDING_DEPARTMENT_HEAD",
                "ADMIN": "PENDING_ADMIN",
            }[role]
            if application.status != expected_status:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Application is not awaiting {role.lower().replace('_', ' ')} action.",
                )

            history = ApprovalHistory(
                application_id=application_id,
                approver_id=approver_id,
                approver_role=role,
                action=action,
                comments=comments,
            )
            db.add(history)
            application.status = (
                "PENDING_ADMIN" if role == "DEPARTMENT_HEAD" and action == "APPROVED"
                else "DEPARTMENT_REJECTED" if role == "DEPARTMENT_HEAD"
                else "ADMIN_APPROVED" if action == "APPROVED"
                else "ADMIN_REJECTED"
            )
            if role == "ADMIN" and action == "APPROVED":
                db.add(
                    LeaveRecord(
                        application_id=application.application_id,
                        employee_id=application.employee_id,
                        leave_type_id=application.leave_type_id,
                        start_date=application.start_date,
                        end_date=application.end_date,
                        calculated_days=application.calculated_days,
                        status="TAKEN",
                    )
                )
            return application


from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings
from backend.app.models.employee import Employee
from backend.app.models.user_account import UserAccount
from backend.app.models.user_role import UserRole
from backend.app.schemas.auth import LoginRequest, SignUpRequest


class AuthService:
    @staticmethod
    def _auth_url(settings: Settings, endpoint: str) -> str:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Auth is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.",
            )
        return f"{settings.supabase_url.rstrip('/')}/auth/v1/{endpoint}"

    @classmethod
    async def _request(cls, endpoint: str, payload: dict, settings: Settings) -> dict:
        url = cls._auth_url(settings, endpoint)
        headers = {
            "apikey": settings.supabase_anon_key,
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.RequestError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Auth could not be reached.",
            ) from error

        if response.is_error:
            try:
                detail = response.json().get("msg") or response.json().get("error_description")
            except ValueError:
                detail = None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED if response.status_code in (400, 401) else 502,
                detail=detail or "Supabase Auth request failed.",
            )
        return response.json()

    @classmethod
    async def login(cls, payload: LoginRequest, settings: Settings) -> dict:
        return await cls._request(
            "token?grant_type=password",
            {"email": str(payload.email), "password": payload.password},
            settings,
        )

    @classmethod
    async def signup(cls, db: AsyncSession, payload: SignUpRequest, settings: Settings) -> dict:
        employee = await db.scalar(
            select(Employee).where(
                Employee.employee_id == payload.employee_id,
                Employee.employment_status == "ACTIVE",
            )
        )
        if employee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active employee not found.")
        employee_id = employee.employee_id
        employee_email = employee.email
        if employee_email.casefold() != str(payload.email).casefold():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Signup email must match the employee email.",
            )

        auth_data = await cls._request(
            "signup",
            {
                "email": str(payload.email),
                "password": payload.password,
                "data": {"employee_id": payload.employee_id},
            },
            settings,
        )
        user_data = auth_data.get("user") or auth_data
        user_id = user_data.get("id")
        if not user_id:
            raise HTTPException(status_code=502, detail="Supabase did not return a user id.")

        await db.rollback()
        db.add(UserAccount(user_id=UUID(user_id), employee_id=employee_id))
        db.add(UserRole(user_id=UUID(user_id), role="EMPLOYEE"))
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Supabase user was created, but the employee account link already exists or is invalid.",
            ) from None

        return auth_data
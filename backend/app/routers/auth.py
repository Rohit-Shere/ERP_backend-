from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.core.security import CurrentUser, get_current_user
from backend.app.schemas.auth import AuthResponse, LoginRequest, LogoutResponse, SignUpRequest
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _auth_response(data: dict) -> AuthResponse:
    user = data.get("user") or {}
    return AuthResponse(
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        expires_in=data.get("expires_in"),
        user_id=user.get("id"),
        requires_email_confirmation=not bool(data.get("access_token")),
    )


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(payload: SignUpRequest, db: AsyncSession = Depends(get_db)):
    data = await AuthService.signup(db, payload, get_settings())
    return _auth_response(data)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    data = await AuthService.login(payload, get_settings())
    return _auth_response(data)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Supabase access tokens are stateless JWTs; the client should discard them.
    return LogoutResponse(message="Logged out successfully.")


@router.get("/me")
async def auth_me(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "employee_id": current_user.employee_id,
        "roles": list(current_user.roles),
    }
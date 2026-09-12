from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import InvalidTokenError
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.models.employee import Employee
from backend.app.models.user_account import UserAccount
from backend.app.models.user_role import UserRole
from backend.app.models.role import Role

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    employee_id: int
    roles: tuple[str, ...]

    @property
    def role(self) -> str:
        return self.roles[0]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    settings = get_settings()
    if settings.environment == "development" and credentials is None:
        return CurrentUser(user_id="development-user", employee_id=101, roles=("EMPLOYEE",))

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase JWT validation is not configured.",
        )

    try:
        claims = await decode_supabase_token_async(credentials.credentials, settings)
        user_id = UUID(claims["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    account = await db.scalar(
        select(UserAccount).where(UserAccount.user_id == user_id, UserAccount.is_active.is_(True))
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not linked to an employee.")

    employee = await db.scalar(
        select(Employee).where(
            Employee.employee_id == account.employee_id,
            Employee.employment_status == "ACTIVE",
        )
    )
    if employee is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee account is inactive.")

    roles = tuple(
        await db.scalars(
            select(Role.role_code)
            .join(UserRole, UserRole.role_id == Role.role_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.is_active.is_(True),
                Role.is_active.is_(True),
            )
            .order_by(Role.role_code)
        )
    )
    if not roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No application role is assigned.")

    return CurrentUser(user_id=str(user_id), employee_id=account.employee_id, roles=roles)


def decode_supabase_token(token: str, settings, signing_key: str | None = None) -> dict:
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else None
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")
    if algorithm == "ES256" and not signing_key:
        raise InvalidTokenError("An ES256 signing key is required.")
    kwargs = {
        "key": signing_key or settings.supabase_jwt_secret,
        "algorithms": [algorithm] if algorithm in {"HS256", "ES256"} else [],
        "audience": settings.supabase_jwt_audience,
        "leeway": 10,
    }
    if issuer:
        kwargs["issuer"] = issuer
    return jwt.decode(token, **kwargs)


async def decode_supabase_token_async(token: str, settings) -> dict:
    header = jwt.get_unverified_header(token)
    if header.get("alg") != "ES256":
        return decode_supabase_token(token, settings)

    if not settings.supabase_url or not settings.supabase_anon_key:
        raise InvalidTokenError("Supabase JWKS configuration is missing.")

    jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(jwks_url, headers={"apikey": settings.supabase_anon_key})
            response.raise_for_status()
            keys = response.json().get("keys", [])
    except (httpx.HTTPError, ValueError) as error:
        raise InvalidTokenError("Supabase signing keys could not be loaded.") from error

    matching_key = next((key for key in keys if key.get("kid") == header.get("kid")), None)
    if matching_key is None:
        raise InvalidTokenError("No matching Supabase signing key was found.")

    ec_algorithm = jwt.algorithms.get_default_algorithms()["ES256"]
    return decode_supabase_token(token, settings, ec_algorithm.from_jwk(matching_key))


def require_role(*allowed_roles: str):
    async def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not any(role in allowed_roles for role in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return dependency

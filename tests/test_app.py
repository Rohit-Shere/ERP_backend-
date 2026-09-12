from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import Settings
from backend.app.core.security import decode_supabase_token
from backend.app.services.balance_service import BalanceService, academic_year_for
from backend.app.services.leave_service import LeaveService
from datetime import date, datetime, timedelta, timezone

import jwt


def test_app_starts():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_leave_duration_is_inclusive():
    assert LeaveService.calculate_requested_days(date(2026, 9, 10), date(2026, 9, 12)) == 3


def test_balance_and_academic_year_rules():
    assert BalanceService.calculate_remaining(12, 10, 2) == 4
    assert academic_year_for(date(2026, 5, 31)) == "2025-26"
    assert academic_year_for(date(2026, 6, 1)) == "2026-27"


def test_supabase_token_claims_are_verified():
    settings = Settings(supabase_jwt_secret="test-secret-with-at-least-32-bytes-long")
    token = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "aud": "authenticated",
            "iss": "https://nexdcrgeouaphbdyabjk.supabase.co/auth/v1",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    claims = decode_supabase_token(token, settings)
    assert claims["sub"] == "00000000-0000-0000-0000-000000000001"

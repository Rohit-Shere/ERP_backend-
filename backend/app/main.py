from fastapi import FastAPI

from backend.app.core.config import get_settings
from backend.app.routers import admin, alerts, auth, hod, leave_applications, me

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")

app.include_router(me.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(alerts.router, prefix=settings.api_v1_prefix)
app.include_router(leave_applications.router, prefix=settings.api_v1_prefix)
app.include_router(hod.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}


@app.get("/")
def root():
    return {"message": "Academic ERP Leave Management API is running."}

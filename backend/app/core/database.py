from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import get_settings
from backend.app import models  # noqa: F401

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args={"statement_cache_size": 0},
)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

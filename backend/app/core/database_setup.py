from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import AsyncSessionLocal


async def create_all_tables() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(text("SELECT 1"))


async def init_db() -> None:
    await create_all_tables()

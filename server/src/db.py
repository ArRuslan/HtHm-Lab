from os import environ

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .models import Base

Engine = create_async_engine(f'sqlite+aiosqlite:///{environ.get("SQLITE_PATH", "idkchat.db")}')
async_session = sessionmaker(bind=Engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with Engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
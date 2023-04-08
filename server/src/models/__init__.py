from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

async def create(self, session: AsyncSession) -> None:
    session.add(self)
    await session.flush()
    await session.refresh(self)

setattr(Base, "create", create)
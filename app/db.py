from sqlmodel import create_engine, SQLModel, Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/shitzer_recommendation"

engine = create_engine(DATABASE_URL, echo=True)

async_engine = AsyncEngine(engine)

async def get_db():
    async with AsyncSession(async_engine) as session:
        yield session
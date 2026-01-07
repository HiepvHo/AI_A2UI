"""
Database connection setup
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

# Database URL tu env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("kiem tra DB_URL trong env")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base for models
Base = declarative_base()


async def get_db():
    """Dependency để lấy database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Khởi tạo database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Xóa tất cả tables (chỉ dùng khi dev)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


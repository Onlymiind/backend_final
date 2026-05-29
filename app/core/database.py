from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core import config


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_async_session: async_sessionmaker | None = None


def _ensure_initialized():
    global _engine, _async_session
    if _engine is None:
        _engine = create_async_engine(config.get_config().DATABASE_URL)
    if _async_session is None:
        _async_session = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    _ensure_initialized()
    assert _async_session is not None

    async with _async_session() as session:
        yield session

import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.main import app
from app.core import database
from fastapi.testclient import TestClient
from app.core import config


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(config.get_config().DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    async with async_sessionmaker(engine)() as session:
        yield session


@pytest.fixture
def test_client(db_session) -> TestClient:

    async def get_db():
        yield db_session

    app.dependency_overrides[database.get_db] = get_db

    client = TestClient(app)
    return client

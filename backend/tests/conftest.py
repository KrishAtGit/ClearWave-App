from collections.abc import AsyncIterator
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.config import Settings
from app.db import Base
from app.main import create_app

# AsyncCliet: lets tests send http requests asynchronously
# ASGITransport : connectes HTTPX directly to FastAPI application

# fixture : explicit async markers so the tests also run when pytest is started outside backend/.
@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    async with app.router.lifespan_context(app):
        engine = app.state.sessionmaker.kw["bind"]
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            yield http
from collections.abc import AsyncIterator
import pytest
import pytest_asyncio
# AsyncCliet: lets tests send http requests asynchronously
# ASGITransport : connectes HTTPX directly to FastAPI application
from httpx import ASGITransport, AsyncClient
from app.config import Settings
from app.db import Base
from app.main import create_app
from app.storage import MemoryAudioStore
from app.matching import FakeMatcher


class FakeMailer:
    # keeps sign-in links in a list instead of sending them, so tests can click them

    def __init__(self) -> None:
        self.links: list[str] = []

    async def send_login_link(self, email: str, link: str) -> None:
        self.links.append(link)


@pytest.fixture
def mailer() -> FakeMailer:
    return FakeMailer()

@pytest.fixture                                                
def store() -> MemoryAudioStore:
    return MemoryAudioStore()

@pytest.fixture
def matcher() -> FakeMatcher:
    return FakeMatcher()

# fixture : explicit async markers so the tests also run when pytest is started outside backend/.
@pytest_asyncio.fixture
async def client(mailer: FakeMailer, store: MemoryAudioStore, matcher: FakeMatcher) -> AsyncIterator[AsyncClient]:
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    async with app.router.lifespan_context(app):
        engine = app.state.sessionmaker.kw["bind"]
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # swap the real mailer for the fake one, so tests can read the links
        app.state.mailer = mailer
        app.state.audio_store = store  
        app.state.matcher = matcher    
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            yield http


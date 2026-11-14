from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.auth import router as auth_router
from app.api.routes import router
from app.config import Settings, get_settings
from app.db import make_sessionmaker
from app.mail import ConsoleMailer
from app.api.claims import router as claims_router
from app.storage import BlobAudioStore
from app.matching import FakeMatcher, Matcher
from app.acrcloud import ACRCloudMatcher
from app.mail import ConsoleMailer, Mailer, ResendMailer

def make_matcher(settings: Settings) -> Matcher:
    if settings.matcher == "fake":
        return FakeMatcher()
    secret = settings.acr_access_secret.get_secret_value()
    if not (settings.acr_host and settings.acr_access_key and secret):
        raise RuntimeError("CLEARWAVE_MATCHER=acrcloud needs ACR_HOST, ACR_ACCESS_KEY and ACR_ACCESS_SECRET")
    return ACRCloudMatcher(
        settings.acr_host,
        settings.acr_access_key,
        secret
    )

def make_mailer(settings: Settings) -> Mailer:
    if settings.mailer == "console":
        return ConsoleMailer()
    key = settings.resend_api_key.get_secret_value()
    if not key:
        raise RuntimeError("CLEARWAVE_MAILER=resend needs CLEARWAVE_RESEND_API_KEY")
    return ResendMailer(key, settings.mail_from)

# parameter can be either a settings object or none
def create_app(settings: Settings | None = None) -> FastAPI:
    # if settings is None, call get_settings() to retrieve the default config 
    settings= settings or get_settings()

    # decorator used to allow an asynchronous func to behave like an asynchronous context manager
    @asynccontextmanager
    # receive fastapi application instance and yield a value of type None
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # creating the database engine
        engine, app.state.sessionmaker = make_sessionmaker(settings.database_url)
        # shared by every request: the settings, and whatever sends sign-in links (prints them for now)
        app.state.settings = settings
        app.state.mailer = make_mailer(settings)
        app.state.matcher = make_matcher(settings)

        app.state.audio_store=BlobAudioStore(
            settings.storage_connection_string,
            settings.storage_container
        )
        # dividing between application startup and shutdown
        yield 
        await app.state.matcher.close()
        # dispose the engine 
        await engine.dispose()
        await app.state.audio_store.close()
        await app.state.mailer.close()

    # creating the fastapi application 
    app = FastAPI(
        title="ClearWave API",
        version="0.1.0",
        description="Find released songs that use your sample. research the right holders and estimate royalties owed to you.",
        # using own lifespan function to manage startup/shutdown
        lifespan=lifespan,
    )

    # configuring CORS->cross origin resource sharing 
    # needed for frontend and backend on different ports so cors allows backend to explicitly permit certain cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        # allowing frotend origin
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
        allow_headers=["Content-Type"],
    )
    # registering the routers
    app.include_router(router)
    app.include_router(auth_router)
    app.include_router(claims_router)


    # root endpoint -> endpoint for the root url
    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    return app

app = create_app()
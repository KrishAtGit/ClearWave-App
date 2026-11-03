from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.routes import router
from app.config import Settings, get_settings
from app.db import make_sessionmaker

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
        # dividing between application startup and shutdown
        yield 
        # dispose the engine 
        await engine.dispose()

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
    # registering the router
    app.include_router(router)

    # root endpoint -> endpoint for the root url
    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    return app

app = create_app()
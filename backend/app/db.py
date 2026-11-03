from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

# defining the model base
# creaes the base class that the db model inherits from
# Base inherits from SQLAlchemy's DeclarativeBase
class Base(DeclarativeBase):
    pass

# session factory function
# creates db engine and session factory
# return type : tuple 
# consists : AsyncEngine (database engine), AsycSession (factory creating AsyncSession objects)
def make_sessionmaker(database_url: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    # checking whether the db is in-memory SQLite
    if ":memory:" in database_url:
        # every new connection to an in-memory SQLite DB starts empty, so tests share a single one
        engine = create_async_engine(database_url, poolclass=StaticPool)
    else:
        # create the engine for other databases, executes when the datase URL doesnt contain ":memory:"
        engine = create_async_engine(database_url, pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False)

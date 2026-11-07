from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool
from sqlalchemy import event 

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

    # PRAGMA foreign_keys=ON lasts only for one connection, so everytime the app opens a new connection its off again
    # this setting tells SQLite to enforce foreign keys (inc ON DELETE CASCADE) everytime a new connection is opened.
    if database_url.startswith("sqlite"):
        @event.listens_for(engine.sync_engine, "connect")
        def enable_sqlite_fk(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
    return engine, async_sessionmaker(engine, expire_on_commit=False)

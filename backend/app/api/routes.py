import logging
from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.schemas import Health

# creating a logger for the current py module
log = logging.getLogger(__name__)
# api router to organise api endpoiints
router = APIRouter(prefix="/api")

# registering the health endpoint 
@router.get("/health", response_model=Health, tags=["meta"])
# ansychronous function so that the database doesnt pause during multiple requests
async def health(request: Request) -> Health:
    try:
        # handling asynchronous cleanup and creating a database session -> retrieving db session factory and creating a session 
        async with request.app.state.sessionmaker() as session:
            # checking the database and executing a simple SQL query
            await session.execute(text("SELECT 1"))
        database = True
    except (SQLAlchemyError, OSError) as error:
        log.warning("Health check could not reach the database: %s", error)
        database = False
    return Health(status="ok", database=database)


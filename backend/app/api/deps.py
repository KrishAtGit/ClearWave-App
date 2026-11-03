from collections.abc import AsyncIterator
from typing import Annotated
from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Session, User
from app.security import SESSION_COOKIE, hash_token, now

async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessionmaker() as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db)]

async def current_user(
    db: DbSession, 
    session_token: Annotated[str|None, Cookie(alias=SESSION_COOKIE)] = None
) -> User:
    if session_token:
        user = await db.scalar(
            select(User).join(Session, Session.user_id == User.id)
            .where(Session.token_hash == hash_token(session_token),
                   Session.expires_at > now())
        )
        if user:
            return user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Signed In!")

CurrentUser = Annotated[User, Depends(current_user)]
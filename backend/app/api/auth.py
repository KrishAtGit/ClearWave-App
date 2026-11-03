from typing import Annotated

from fastapi import APIRouter, Cookie, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select, update

from app.api.deps import CurrentUser, DbSession
from app.models import LoginToken, Session, User
from app.schemas import LinkRequest, Message, UserOut
from app.security import (
    LOGIN_LINK_LIFETIME,
    SESSION_COOKIE,
    SESSION_LIFETIME,
    hash_token,
    new_token,
    now,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/request-link", status_code=status.HTTP_202_ACCEPTED, response_model=Message)
async def request_link(body: LinkRequest, request: Request, db: DbSession) -> Message:
    """Emails a one-time sign-in link. Signing in for the first time creates the account."""
    email = body.email.lower()
    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email)
        db.add(user)
        await db.flush()  # sends the INSERT now, so user.id is available below

    token = new_token()
    db.add(LoginToken(user_id=user.id, token_hash=hash_token(token), expires_at=now() + LOGIN_LINK_LIFETIME))
    await db.commit()

    link = f"{request.app.state.settings.frontend_origin}/api/auth/verify?token={token}"
    await request.app.state.mailer.send_login_link(email, link)
    return Message(message="Check your email for a sign-in link.")


@router.get("/verify")
async def verify(token: str, request: Request, db: DbSession) -> RedirectResponse:
    """Where the emailed link points. A valid link signs you in and sends you to the app."""
    frontend = request.app.state.settings.frontend_origin

    # Claim the token in one statement: only an unused, unexpired token matches, and it's marked used at the
    # same moment, so two clicks at once can't both succeed.
    user_id = await db.scalar(
        update(LoginToken)
        .where(
            LoginToken.token_hash == hash_token(token),
            LoginToken.used_at.is_(None),
            LoginToken.expires_at > now(),
        )
        .values(used_at=now())
        .returning(LoginToken.user_id)
    )
    if user_id is None:
        return RedirectResponse(f"{frontend}/?signin=expired", status_code=status.HTTP_303_SEE_OTHER)

    session_token = new_token()
    db.add(Session(user_id=user_id, token_hash=hash_token(session_token), expires_at=now() + SESSION_LIFETIME))
    await db.commit()

    response = RedirectResponse(f"{frontend}/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,  # JavaScript can't read it, so an XSS bug can't steal it
        secure=request.app.state.settings.cookie_secure,  # HTTPS only in production
        samesite="lax",  # not sent on cross-site form posts
    )
    return response


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    """Who's signed in. 401 when nobody is."""
    return UserOut(id=user.id, email=user.email)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    db: DbSession, session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None
) -> Response:
    """Ends this browser's session, server side as well as in the browser."""
    if session_token:
        await db.execute(delete(Session).where(Session.token_hash == hash_token(session_token)))
        await db.commit()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE)
    return response

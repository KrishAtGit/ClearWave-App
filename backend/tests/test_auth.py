from datetime import timedelta
from urllib.parse import urlsplit
from httpx import AsyncClient
from sqlalchemy import update
from app.models import LoginToken
from app.security import SESSION_COOKIE
from tests.conftest import FakeMailer


async def request_link(client: AsyncClient, mailer: FakeMailer, email: str = "krish@example.com") -> str:
    """Asks for a sign-in link and returns the path to 'click', e.g. /api/auth/verify?token=..."""
    response = await client.post("/api/auth/request-link", json={"email": email})
    assert response.status_code == 202
    link = urlsplit(mailer.links[-1])
    return f"{link.path}?{link.query}"


async def test_signing_in_with_a_link(client: AsyncClient, mailer: FakeMailer) -> None:
    path = await request_link(client, mailer)

    response = await client.get(path)
    assert response.status_code == 303
    assert response.headers["location"] == "http://localhost:5173/"
    cookie = response.headers["set-cookie"]
    assert SESSION_COOKIE in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie

    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "krish@example.com"


async def test_email_is_case_insensitive(client: AsyncClient, mailer: FakeMailer) -> None:
    await client.get(await request_link(client, mailer, "Krish@Example.com"))
    first = (await client.get("/api/auth/me")).json()["id"]
    await client.post("/api/auth/logout")
    await client.get(await request_link(client, mailer, "krish@example.com"))
    assert (await client.get("/api/auth/me")).json()["id"] == first


async def test_signed_out_is_401(client: AsyncClient) -> None:
    assert (await client.get("/api/auth/me")).status_code == 401
    client.cookies.set(SESSION_COOKIE, "made-up-token")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_a_link_works_only_once(client: AsyncClient, mailer: FakeMailer) -> None:
    path = await request_link(client, mailer)
    await client.get(path)
    client.cookies.clear()

    again = await client.get(path)
    assert again.headers["location"] == "http://localhost:5173/?signin=expired"
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_an_expired_link_fails(client: AsyncClient, mailer: FakeMailer) -> None:
    path = await request_link(client, mailer)
    # Age the token past its 15 minutes.
    sessionmaker = client._transport.app.state.sessionmaker  # type: ignore[attr-defined]
    async with sessionmaker() as db:
        await db.execute(update(LoginToken).values(expires_at=LoginToken.expires_at - timedelta(minutes=16)))
        await db.commit()

    response = await client.get(path)
    assert response.headers["location"].endswith("?signin=expired")


async def test_logout_ends_the_session(client: AsyncClient, mailer: FakeMailer) -> None:
    await client.get(await request_link(client, mailer))
    old_cookie = client.cookies[SESSION_COOKIE]

    assert (await client.post("/api/auth/logout")).status_code == 204
    assert (await client.get("/api/auth/me")).status_code == 401

    # The old cookie no longer works either, because the session was deleted on the server.
    client.cookies.set(SESSION_COOKIE, old_cookie)
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_invalid_email_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/auth/request-link", json={"email": "not-an-email"})
    assert response.status_code == 422

import json
import httpx
import pytest
from httpx import AsyncClient
from app.mail import RESEND_URL, MailError, ResendMailer
from tests.conftest import FakeMailer

def mailer_replying(status: int, seen: list[httpx.Request]) -> ResendMailer:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json = {"id" : "email-123"})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ResendMailer("re-test", "ClearWave <test@example.com>", client)

async def test_sends_the_link_to_resend() -> None:
    seen: list[httpx.Request] = []
    mailer = mailer_replying(200, seen)
    await mailer.send_login_link("x@example.com",  "http://app/verify?token=abc")

    assert len(seen) == 1
    request = seen[0]
    assert str(request.url) == RESEND_URL
    assert RESEND_URL.startswith("https://")
    assert request.headers["Authorization"] == "Bearer re-test"
    body = json.loads(request.content)
    assert body["to"] == ["x@example.com"]
    assert body["from"] == "ClearWave <test@example.com>"
    assert "http://app/verify?token=abc" in body["text"]
    await mailer.close()


async def test_a_rejected_email_raises() -> None:
    mailer = mailer_replying(422, [])
    with pytest.raises(MailError):
        await mailer.send_login_link("a@example.com", "http://app/verify?token=abc")
    await mailer.close()


async def test_request_link_sends_exactly_one_email(client: AsyncClient, mailer: FakeMailer) -> None:
    response = await client.post("/api/auth/request-link", json={"email": "a@example.com"})
    assert response.status_code == 202
    assert len(mailer.links) == 1


async def test_a_failed_send_returns_503(client: AsyncClient, mailer: FakeMailer, monkeypatch: pytest.MonkeyPatch) -> None:
    async def broken(email: str, link: str) -> None:
        raise MailError("down")

    monkeypatch.setattr(mailer, "send_login_link", broken)
    response = await client.post("/api/auth/request-link", json={"email": "a@example.com"})
    assert response.status_code == 503
    assert "try again" in response.json()["detail"]

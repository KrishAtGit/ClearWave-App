from urllib.parse import urlsplit

from httpx import AsyncClient

from app.security import SESSION_COOKIE
from app.storage import MemoryAudioStore
from tests.conftest import FakeMailer

# The smallest valid-looking WAV header: enough for the server to recognise it as audio.
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 64


async def sign_in(client: AsyncClient, mailer: FakeMailer, email: str) -> str:
    """Signs in as `email` and returns the session cookie, so tests can switch between users."""
    client.cookies.clear()
    await client.post("/api/auth/request-link", json={"email": email})
    link = urlsplit(mailer.links[-1])
    await client.get(f"{link.path}?{link.query}")
    return client.cookies[SESSION_COOKIE]


async def upload(client: AsyncClient, data: bytes = WAV, title: str = "Dusty loop", name: str = "loop.wav"):
    return await client.post("/api/claims", data={"title": title}, files={"file": (name, data, "audio/wav")})


async def test_upload_and_list(client: AsyncClient, mailer: FakeMailer, store: MemoryAudioStore) -> None:
    await sign_in(client, mailer, "a@example.com")
    response = await upload(client)
    assert response.status_code == 201
    claim = response.json()
    assert claim["title"] == "Dusty loop"
    assert claim["status"] == "uploaded"
    assert claim["size_bytes"] == len(WAV)

    # Stored under a name we chose, not the uploaded filename.
    [key] = store.files
    assert key.endswith(f"/{claim['id']}.wav")

    listed = (await client.get("/api/claims")).json()
    assert [c["id"] for c in listed] == [claim["id"]]

    detail = (await client.get(f"/api/claims/{claim['id']}")).json()
    assert detail["audio_url"].startswith("https://storage.test/")


async def test_rejects_files_that_are_not_audio(client: AsyncClient, mailer: FakeMailer, store: MemoryAudioStore) -> None:
    await sign_in(client, mailer, "a@example.com")
    # A text file renamed to .wav is still rejected: the content is checked, not the name.
    response = await upload(client, data=b"just some text, not audio", name="fake.wav")
    assert response.status_code == 415
    assert store.files == {}


async def test_rejects_files_that_are_too_big(client: AsyncClient, mailer: FakeMailer, store: MemoryAudioStore) -> None:
    await sign_in(client, mailer, "a@example.com")
    client._transport.app.state.settings.max_upload_mb = 1  # type: ignore[attr-defined]
    response = await upload(client, data=WAV + b"\x00" * (1024 * 1024))
    assert response.status_code == 413
    assert store.files == {}


async def test_users_only_see_their_own_claims(client: AsyncClient, mailer: FakeMailer) -> None:
    await sign_in(client, mailer, "a@example.com")
    claim_id = (await upload(client)).json()["id"]

    await sign_in(client, mailer, "b@example.com")
    assert (await client.get("/api/claims")).json() == []
    # Someone else's claim looks exactly like one that doesn't exist.
    assert (await client.get(f"/api/claims/{claim_id}")).status_code == 404
    assert (await client.delete(f"/api/claims/{claim_id}")).status_code == 404


async def test_delete_removes_the_claim_and_its_file(
    client: AsyncClient, mailer: FakeMailer, store: MemoryAudioStore
) -> None:
    await sign_in(client, mailer, "a@example.com")
    claim_id = (await upload(client)).json()["id"]

    assert (await client.delete(f"/api/claims/{claim_id}")).status_code == 204
    assert store.files == {}
    assert (await client.get(f"/api/claims/{claim_id}")).status_code == 404


async def test_claims_need_sign_in(client: AsyncClient) -> None:
    assert (await client.get("/api/claims")).status_code == 401
    assert (await upload(client)).status_code == 401

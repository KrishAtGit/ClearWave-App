import base64, hashlib, hmac, time, httpx
from typing import Any
from app.matching import MatcherError, SongMatch

IDENTIFY_PATH = "/v1/identify"

def parse_song(item: dict[str, Any]) -> SongMatch:
    external = item.get("external_metadata") or {}
    spotify_track=(external.get("spotify") or {}).get("track") or {}
    youtube = external.get("youtube") or {}
    contributors = item.get("contributors") or {}
    isrc = (item.get("external_ids") or {}).get("isrc")

    if isinstance(isrc, list):
        isrc = isrc[0] if isrc else None

    offset_ms = item.get("play_offset_ms")

    return SongMatch(
        title=item.get("title") or "Unknown title",
        artists=[artist["name"] for artist in item.get("artists") or [] if artist.get("name")],
        album=(item.get("album") or {}).get("name"),
        label=item.get("label") or None,
        release_date=item.get("release_date") or None,
        isrc=isrc,
        score=int(item.get("score") or 0),
        offset_seconds=offset_ms / 1000 if offset_ms is not None else None,
        spotify_track_id=spotify_track.get("id"),
        youtube_video_id=youtube.get("vid"),
        composers=list(contributors.get("composers") or [])
    )

class ACRCloudMatcher:
    def __init__(
            self, 
            host: str,
            access_key: str,
            access_secret: str,
            client: httpx.AsyncClient | None = None
    ) -> None:
        self._url= f"https://{host}{IDENTIFY_PATH}"
        self._access_key = access_key
        self._access_secret = access_secret.encode()
        self._client = client or httpx.AsyncClient(timeout=30)

    def _sign(self, timestamp: str) -> str:
        string_to_sign = "\n".join(
            ["POST", IDENTIFY_PATH, self._access_key, "audio", "1", timestamp]
        )
        digest = hmac.new(
            self._access_secret,
            string_to_sign.encode(),
            hashlib.sha1
        ).digest()

        return base64.b64encode(digest).decode()

    async def find_matches(self, audio: bytes) -> list[SongMatch]:
        timestamp = str(int(time.time()))
        form = {
            "access_key": self._access_key,
            "data_type": "audio",
            "signature_version": "1",
            "signature": self._sign(timestamp),
            "timestamp": timestamp,
            "sample_bytes": str(len(audio)),
        }

        try:
            response = await self._client.post(
                self._url,
                data=form,
                files={"sample": ("sample", audio)}
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise MatcherError(f"Could not reach ACRCloud: {error}") from error

        status = body.get("status") or {}
        code = status.get("code")
        if code == 1001:
            return []

        if code != 0:
            raise MatcherError(f"ACRCloud error {code}: {status.get("msg")}")

        music = (body.get("metadata") or {}).get("music") or []
        return [parse_song(item) for item in music]

    async def close(self) -> None:
        await self._client.aclose()

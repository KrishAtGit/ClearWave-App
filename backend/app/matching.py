from dataclasses import dataclass, field
from typing import Protocol

@dataclass(frozen=True)
class SongMatch:
    title: str
    artists: list[str]
    album: str | None = None
    label: str | None = None
    release_date: str | None = None
    isrc: str | None = None
    score: int = 0
    offset_seconds: float | None = None
    spotify_track_id: str | None = None
    youtube_video_id: str | None = None
    # dataclass calls it everytime a new object is created 
    composers: list[str] = field(default_factory=list)

class MatcherError(Exception):
    """----"""

class Matcher(Protocol):
    async def find_matches(self, audio: bytes) -> list[SongMatch]: ...
    async def close(self) -> None: ...

class FakeMatcher:
    # this returns the same made-up songs everytime, so dev and tests never call the acrcloud
    async def find_matches(self, audio: bytes) -> list[SongMatch]:
        return[
            SongMatch(
                title="Song 1",
                artists=["X-Band"],
                album="X-album",
                label="X-Label",
                release_date="12-12-12",
                isrc="ABCDEGHIJKLMNOP",
                score=81,
                offset_seconds=29.1,
                composers=["A. IDK-1, B. IDK-2"],

            ),
            SongMatch(
                title="Loop Theory",
                artists=["DJ Placeholder", "MC Sample"],
                album=None,
                label="Demo Music Group",
                release_date="2022-09-30",
                isrc="XYXYXYXYYXYXYXY",
                score=81,
                offset_seconds=12.0,
            )
        ]
    async def close(self) -> None: ...
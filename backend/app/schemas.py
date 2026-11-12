from typing import Literal
import uuid 
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# health check endpoint return to frontend values
class Health(BaseModel):
    # value must specifically be the string ok
    status: Literal["ok"]
    database: bool

class LinkRequest(BaseModel):
    email: EmailStr

class Message(BaseModel):
    message: str

class UserOut(BaseModel):
    id: uuid.UUID
    email: str

class ClaimOut(BaseModel):
    id: uuid.UUID
    title: str
    original_filename: str
    size_bytes: int
    status: Literal["uploaded", "matching", "matched", "failed"]
    created_at: datetime


class MatchOut(BaseModel):
    id: uuid.UUID
    title: str
    artists: list[str]
    album: str | None
    label: str | None
    release_date: str | None
    isrc: str | None
    score: int 
    offset_seconds: float | None
    spotify_track_id: str | None
    youtube_video_id: str | None
    composers: list[str]
    streams: int | None
    share_percent: float | None
    estimated_value: float | None = None 

class ClaimDetail(ClaimOut):
    audio_url: str
    matches: list[MatchOut]
    audio_url: str
    matches: list[MatchOut]
    payout_per_stream: float
    payout_source: str

class EstimateIn(BaseModel):
    # ge = greater than or eq, le = less than or eq
    # anything outside of [0, 100,000,000,000] is rejected
    streams: int | None = Field(
        default=None,
        ge=0,
        le=100_000_000_000
    )
    share_percent: float | None = Field(
        default=None,
        ge=0,
        le=100
    )






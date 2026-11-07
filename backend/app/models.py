import uuid
from datetime import datetime
from sqlalchemy import JSON, Float, DateTime, ForeignKey, String, func, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4
        )
    email: Mapped[str] = mapped_column(
        String(320), 
        unique=True, 
        index=True
        )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
        )

class LoginToken(Base):
    __tablename__ = "login_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4
        )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True
        )
    token_hash: Mapped[str] = mapped_column(
        String(64), 
        unique=True
        )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class Session(Base):

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), 
        unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        # deleting one user deletes their claims -> cascade feature -> every claim belongs to one usr
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(200)
    )
    original_filename: Mapped[str] = mapped_column(
        String(255)
    )
    audio_key: Mapped[str] = mapped_column(
        String(300), 
        unique=True
    )
    content_type: Mapped[str] = mapped_column(
        String(50)
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer
    )
    status: Mapped[str] = mapped_column(
        String(20), 
        default="uploaded"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class Match(Base):
    __tablename__ = "matches"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    artists: Mapped[list[str]] = mapped_column(JSON)
    album: Mapped[str | None] = mapped_column(String(300))
    label: Mapped[str | None] = mapped_column(String(300))
    release_date: Mapped[str| None] = mapped_column(String(10))
    isrc: Mapped[str | None] = mapped_column(String(20))
    score: Mapped[int] = mapped_column(Integer)
    offset_seconds: Mapped[float | None] = mapped_column(Float)
    spotify_track_id: Mapped[str | None] = mapped_column(String(50))
    youtube_video_id: Mapped[str | None] = mapped_column(String(50))
    composers: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

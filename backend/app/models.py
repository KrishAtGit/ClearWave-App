import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func, Integer
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

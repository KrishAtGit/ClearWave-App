import hashlib 
import secrets
from datetime import UTC, datetime, timedelta

LOGIN_LINK_LIFETIME = timedelta(minutes=15)
SESSION_LIFETIME = timedelta(days=30)
SESSION_COOKIE = "clearwave_session"

def new_token() -> str:
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def now() -> datetime:
    return datetime.now(UTC)

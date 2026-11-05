from typing import Literal
import uuid 
from pydantic import BaseModel, EmailStr
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

class ClaimDetail(ClaimOut):
    audio_url: str



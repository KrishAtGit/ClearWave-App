from typing import Literal
import uuid 
from pydantic import BaseModel, EmailStr

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
    


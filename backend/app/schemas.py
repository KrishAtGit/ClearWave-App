from typing import Literal

from pydantic import BaseModel

# health check endpoint return to frontend values
class Health(BaseModel):
    # value must specifically be the string ok
    status: Literal["ok"]
    database: bool

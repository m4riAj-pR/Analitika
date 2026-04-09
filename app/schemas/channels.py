from pydantic import BaseModel
from typing import Optional


class Channel(BaseModel):
    id_channel: Optional[int] = None
    name: str
    description: Optional[str] = None
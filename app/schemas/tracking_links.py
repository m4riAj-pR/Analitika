from pydantic import BaseModel
from typing import Optional


class TrackingLink(BaseModel):
    id_link: Optional[int] = None
    id_campaign: int
    destination: str
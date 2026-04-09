from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Click(BaseModel):
    id_click: Optional[int] = None
    id_link: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    country: Optional[str] = None
    clicked_at: datetime = datetime.utcnow()
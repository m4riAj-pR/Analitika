from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Click(BaseModel):
    id_click: Optional[int] = None
    id_link: int
    ip_address_hash: Optional[str] = None
    consent_given: Optional[bool] = False
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    country: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    clicked_at: datetime = datetime.utcnow()
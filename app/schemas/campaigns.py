from pydantic import BaseModel
from datetime import date
from typing import Optional
from enum import Enum
from decimal import Decimal

class CampaignStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    finished = "finished"


class Campaign(BaseModel):
    id_campaign: Optional[int] = None
    id_company: int
    name: str
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.draft
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    spent: Optional[Decimal] = Decimal("0.00")
    budget: Optional[Decimal] = Decimal("0.00")
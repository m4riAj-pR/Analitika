from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class Conversion(BaseModel):
    id_conversion: Optional[int] = None
    id_campaign: int
    id_click: Optional[int] = None
    revenue: Decimal = Decimal("0.00")
    type: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
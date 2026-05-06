from pydantic import BaseModel
from decimal import Decimal
from typing import Optional

from enum import Enum

class ConversionType(str, Enum):
    sale = 'sale'
    lead = 'lead'
    signup = 'signup'
    download = 'download'
    contact = 'contact'
    other = 'other'

class Conversion(BaseModel):
    id_conversion: Optional[int] = None
    id_click: int
    revenue: Decimal = Decimal("0.00")
    type: ConversionType = ConversionType.other
    source: Optional[str] = None
    notes: Optional[str] = None
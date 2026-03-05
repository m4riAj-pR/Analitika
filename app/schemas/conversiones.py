from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional

class Conversion(BaseModel):
    id_conversion: int
    campana_id: int
    ingreso: Decimal
    fecha_hora: datetime
    canal_id: Optional[int] = None
    origen: Optional[str] = None
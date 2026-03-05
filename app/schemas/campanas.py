from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional

class Campana(BaseModel):
    id_campana: int
    usuario_id: int
    nombre: str
    presupuesto: Optional[Decimal] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
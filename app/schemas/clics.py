from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Clic(BaseModel):
    id_clics: int
    campana_id: int
    fecha_hora: datetime
    dispositivo: Optional[str] = None
    canal_id: int

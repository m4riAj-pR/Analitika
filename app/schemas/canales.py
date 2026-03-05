from pydantic import BaseModel
from typing import Optional

class Canal(BaseModel):
    id_canal: int
    nombre: str
    tipo: Optional[str] = None

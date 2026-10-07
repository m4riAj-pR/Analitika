from pydantic import BaseModel
from typing import Optional


class Person(BaseModel):
    id_person: Optional[int] = None
    name: str
    lastname: Optional[str] = None  # Opcional para retrocompatibilidad
    email: str
    phone: Optional[str] = None
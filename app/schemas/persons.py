from pydantic import BaseModel
from typing import Optional


class Person(BaseModel):
    id_person: Optional[int] = None
    name: str
    lastname: Optional[str] = None
    email: str
    phone: Optional[str] = None
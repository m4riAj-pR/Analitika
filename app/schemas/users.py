from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    id_user: Optional[int] = None
    id_person: int
    id_company: Optional[int] = None
    id_role: int
    password_hash: str
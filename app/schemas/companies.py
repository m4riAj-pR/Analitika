from pydantic import BaseModel
from typing import Optional


class Company(BaseModel):
    id_company: Optional[int] = None
    id_user: Optional[int] = None
    name: str
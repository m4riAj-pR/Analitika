from pydantic import BaseModel
from typing import Optional


class Permission(BaseModel):
    id_permissions: Optional[int] = None
    name: str
    description: Optional[str] = None
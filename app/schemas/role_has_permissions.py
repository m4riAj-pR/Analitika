from pydantic import BaseModel
from typing import Optional


class RoleHasPermission(BaseModel):
    id_role_permission: Optional[int] = None
    id_role: int
    id_permission: int
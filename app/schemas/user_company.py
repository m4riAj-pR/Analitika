from pydantic import BaseModel
from typing import Optional


class UserCompany(BaseModel):
    id_user_company: Optional[int] = None
    id_user: int
    id_company: int
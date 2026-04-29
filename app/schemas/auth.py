from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    id_user: int
    id_person: int
    id_company: Optional[int] = None
    id_role: int
    name: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserPublic] = None

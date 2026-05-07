from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(LoginRequest):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None


class UserPublic(BaseModel):
    id_user: int
    id_person: int
    id_company: Optional[int] = None
    id_role: int
    name: str
    email: str
    companies: Optional[list] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserPublic] = None

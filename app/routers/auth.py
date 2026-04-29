from fastapi import APIRouter, HTTPException, status

from app.db.database import run_query
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token, verify_password

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login_for_access_token(data: LoginRequest):
    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email y password son requeridos")

    result = run_query(
        """
        SELECT u.id_user, u.id_person, u.id_company, u.id_role, u.password_hash,
               p.name, p.lastname, p.email
        FROM users u
        JOIN persons p ON u.id_person = p.id_person
        WHERE LOWER(p.email) = LOWER(%s)
        """,
        (data.email,),
        fetch=True
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    user = result[0]
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    token = create_access_token({"sub": user["email"], "id_user": user["id_user"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_user": user["id_user"],
            "id_person": user["id_person"],
            "id_company": user.get("id_company"),
            "id_role": user["id_role"],
            "name": f"{user['name']} {user['lastname']}".strip(),
            "email": user["email"],
        },
    }

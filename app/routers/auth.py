from fastapi import APIRouter, HTTPException, status
import logging

from app.db.database import run_query
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token, verify_password, pwd_context

logger = logging.getLogger(__name__)
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

    try:
        is_valid_password = verify_password(data.password, user["password_hash"])
        if not is_valid_password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al verificar contraseña para {data.email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    try:
        token = create_access_token({"sub": user["email"], "id_user": user["id_user"]})
    except Exception as e:
        logger.error(f"Error al crear token JWT para {data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar token de autenticación"
        )

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


@router.post("/register", status_code=201)
def register_user(data: LoginRequest):
    """
    Endpoint público de registro. No requiere token JWT.
    Recibe: email, password, first_name (opcional), last_name (opcional), phone (opcional), company (opcional)
    Crea persona + usuario con contraseña hasheada en bcrypt y devuelve token listo para usar.
    """
    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email y password son requeridos")

    # 1. Verificar que el email no exista ya
    existing = run_query(
        "SELECT id_person FROM persons WHERE LOWER(email) = LOWER(%s)",
        (data.email,),
        fetch=True
    )
    if existing:
        raise HTTPException(status_code=400, detail="Este correo ya está registrado")

    # 2. Crear persona
    name = getattr(data, "first_name", None) or data.email.split("@")[0]
    lastname = getattr(data, "last_name", None) or ""
    phone = getattr(data, "phone", None) or ""

    run_query(
        "INSERT INTO persons (name, lastname, email, phone) VALUES (%s, %s, %s, %s)",
        (name, lastname, data.email, phone)
    )

    # 3. Obtener id_person recién creado
    person = run_query(
        "SELECT id_person FROM persons WHERE LOWER(email) = LOWER(%s)",
        (data.email,),
        fetch=True
    )
    if not person:
        raise HTTPException(status_code=500, detail="Error al crear el perfil")

    id_person = person[0]["id_person"]

    # 4. Hashear contraseña y crear usuario con rol 2 (user)
    hashed = pwd_context.hash(data.password)
    id_user = run_query(
        "INSERT INTO users (id_person, id_company, id_role, password_hash) VALUES (%s, %s, %s, %s)",
        (id_person, None, 2, hashed),
        return_lastrowid=True
    )

    # 5. Devolver token para login automático post-registro
    token = create_access_token({"sub": data.email, "id_user": id_user})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_user": id_user,
            "id_person": id_person,
            "id_company": None,
            "id_role": 2,
            "name": f"{name} {lastname}".strip(),
            "email": data.email,
        },
    }

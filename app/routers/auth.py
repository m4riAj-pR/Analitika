import json
import logging
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status

from app.db.database import run_query
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token, hash_password, verify_and_upgrade_password

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])


def build_login_request(payload: dict) -> LoginRequest:
    email = payload.get("email") or payload.get("username")
    password = payload.get("password")

    if email is None or password is None:
        raise HTTPException(status_code=400, detail="Email y password son requeridos")

    return LoginRequest(email=str(email), password=str(password))


def parse_form_encoded_body(raw_body: bytes) -> dict[str, str]:
    body_text = raw_body.decode("utf-8")
    parsed = parse_qs(body_text, keep_blank_values=True)
    return {
        key: values[0] if isinstance(values, list) and values else ""
        for key, values in parsed.items()
    }


async def parse_login_request(request: Request) -> LoginRequest:
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(status_code=400, detail="Email y password son requeridos")

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    parsers = ["json", "form"] if content_type != "application/x-www-form-urlencoded" else ["form", "json"]

    for parser_name in parsers:
        try:
            if parser_name == "json":
                payload = json.loads(raw_body.decode("utf-8"))
            else:
                payload = parse_form_encoded_body(raw_body)

            if isinstance(payload, dict):
                return build_login_request(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, HTTPException, ValueError, TypeError):
            continue

    raise HTTPException(status_code=400, detail="Email y password son requeridos")


@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(request: Request):
    data = await parse_login_request(request)
    email = data.email.strip()

    if not email or not data.password:
        raise HTTPException(status_code=400, detail="Email y password son requeridos")

    result = run_query(
        """
        SELECT u.id_user, u.id_person, u.id_company, u.id_role, u.password_hash,
               p.name, p.lastname, p.email
        FROM users u
        JOIN persons p ON u.id_person = p.id_person
        WHERE LOWER(p.email) = LOWER(%s)
        """,
        (email,),
        fetch=True
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    user = result[0]

    try:
        is_valid_password, upgraded_hash = verify_and_upgrade_password(
            data.password,
            user["password_hash"]
        )
        if not is_valid_password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al verificar contrasena para {email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    if upgraded_hash:
        try:
            # Actualiza hashes heredados sin bloquear el login si la migracion falla.
            run_query(
                "UPDATE users SET password_hash = %s WHERE id_user = %s",
                (upgraded_hash, user["id_user"])
            )
        except Exception as e:
            logger.warning(
                "No se pudo migrar a bcrypt la contrasena del usuario %s: %s",
                email,
                str(e)
            )

    try:
        token = create_access_token({"sub": user["email"], "id_user": user["id_user"]})
    except Exception as e:
        logger.error(f"Error al crear token JWT para {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar token de autenticacion"
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
    Endpoint publico de registro. No requiere token JWT.
    Recibe: email, password, first_name (opcional), last_name (opcional), phone (opcional), company (opcional)
    Crea persona + usuario con contrasena hasheada en bcrypt y devuelve token listo para usar.
    """
    email = data.email.strip()

    if not email or not data.password:
        raise HTTPException(status_code=400, detail="Email y password son requeridos")

    existing = run_query(
        "SELECT id_person FROM persons WHERE LOWER(email) = LOWER(%s)",
        (email,),
        fetch=True
    )
    if existing:
        raise HTTPException(status_code=400, detail="Este correo ya esta registrado")

    name = getattr(data, "first_name", None) or email.split("@")[0]
    lastname = getattr(data, "last_name", None) or ""
    phone = getattr(data, "phone", None) or ""

    run_query(
        "INSERT INTO persons (name, lastname, email, phone) VALUES (%s, %s, %s, %s)",
        (name, lastname, email, phone)
    )

    person = run_query(
        "SELECT id_person FROM persons WHERE LOWER(email) = LOWER(%s)",
        (email,),
        fetch=True
    )
    if not person:
        raise HTTPException(status_code=500, detail="Error al crear el perfil")

    id_person = person[0]["id_person"]

    hashed = hash_password(data.password)
    id_user = run_query(
        "INSERT INTO users (id_person, id_company, id_role, password_hash) VALUES (%s, %s, %s, %s)",
        (id_person, None, 2, hashed),
        return_lastrowid=True
    )

    token = create_access_token({"sub": email, "id_user": id_user})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_user": id_user,
            "id_person": id_person,
            "id_company": None,
            "id_role": 2,
            "name": f"{name} {lastname}".strip(),
            "email": email,
        },
    }

import json
import logging
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.db.database import run_query
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
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
async def login_for_access_token(request: Request, response: Response):
    data = await parse_login_request(request)
    email = data.email.strip()

    if not email or not data.password:
        raise HTTPException(status_code=400, detail="Email y password son requeridos")

    try:
        result = run_query(
            """
            SELECT
                u.id_user,
                u.id_person,
                u.id_role,
                u.password_hash,
                p.name,
                p.lastname,
                p.email
            FROM persons p
            JOIN users u ON p.id_person = u.id_person
            WHERE LOWER(p.email) = LOWER(%s)
            """,
            (email,),
            fetch=True
        )

    except Exception as e:
        print("LOGIN DB ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Database connection failed")

    if not result:
        print("401 ERROR: Usuario no encontrado o result vacío.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico no registrado o credenciales inválidas"
        )

    user = result[0]

    try:
        is_valid_password, upgraded_hash = verify_and_upgrade_password(
            data.password,
            user["password_hash"]
        )
        if not is_valid_password:
            print("401 ERROR: La contraseña es inválida tras verificación.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="La contraseña es incorrecta. Por favor, inténtalo de nuevo."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al verificar contrasena para {email}: {str(e)}")
        print(f"401 ERROR EXCEPTION: Falló la verificación de contraseña para {email}. Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al validar la contraseña. Por favor, intenta más tarde."
        )

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

    # Obtener empresas asociadas al usuario
    try:
        companies_result = run_query(
            """
            SELECT c.id_company, c.name
            FROM companies c
            JOIN user_company uc ON c.id_company = uc.id_company
            WHERE uc.id_user = %s
            """,
            (user["id_user"],),
            fetch=True
        )
        companies = [{"id_company": c["id_company"], "name": c["name"]} for c in companies_result]
        print(f"DEBUG: Empresas encontradas para user {user['id_user']}: {companies}")
    except Exception as e:
        print(f"DEBUG ERROR: Al obtener empresas - {str(e)}")
        companies = []

    # Insert login notification
    try:
        run_query(
            "INSERT INTO notifications (id_user, title, message, type) VALUES (%s, %s, %s, %s)",
            (user["id_user"], "Bienvenido", f"Bienvenido {user['name']} {user['lastname']}".strip(), "info")
        )
    except Exception as e:
        logger.error(f"Error creating login notification: {e}")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_user": user["id_user"],
            "id_person": user["id_person"],
            "id_role": user["id_role"],
            "name": f"{user['name']} {user['lastname']}".strip(),
            "email": user["email"],
            "companies": companies,
        },
    }


@router.post("/register", status_code=201)
def register_user(data: RegisterRequest):
    """
    Endpoint publico de registro. No requiere token JWT.
    Recibe: email, password, first_name (opcional), last_name (opcional), phone (opcional).
    Crea persona + usuario con contrasena hasheada en bcrypt y devuelve token listo para usar.
    Nota: id_company NO se incluye en el INSERT para evitar FK violations;
    el usuario queda sin empresa hasta crearla o ser invitado.
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

    # CORRECCIÓN: la tabla users real requiere columna 'username' (NOT NULL UNIQUE)
    # Usamos la parte local del email como username
    username = email.split('@')[0]
    hashed = hash_password(data.password)
    id_user = run_query(
        "INSERT INTO users (id_person, id_role, username, password_hash) VALUES (%s, %s, %s, %s)",
        (id_person, 2, username, hashed),
        return_lastrowid=True
    )

    # Crear empresa para el usuario
    input_company = getattr(data, "company", None)
    company_name = input_company.strip() if input_company and input_company.strip() else f"Empresa de {name}"
    id_company = run_query(
        "INSERT INTO companies (id_user, name) VALUES (%s, %s)",
        (id_user, company_name),
        return_lastrowid=True
    )

    # Asociar en la tabla intermedia
    run_query(
        "INSERT INTO user_company (id_user, id_company) VALUES (%s, %s)",
        (id_user, id_company)
    )

    # Notificación de bienvenida (owner/management)
    try:
        run_query(
            "INSERT INTO notifications (id_user, title, message, type) VALUES (%s, %s, %s, %s)",
            (id_user, "Bienvenido", f"Bienvenido {name}, ahora podras empezar a analisar tus campañas digitales", "system")
        )
    except Exception as e:
        logger.error(f"Error creating welcome notification: {e}")


    token = create_access_token({"sub": email, "id_user": id_user})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_user": id_user,
            "id_person": id_person,
            "id_role": 2,
            "name": f"{name} {lastname}".strip(),
            "email": email,
            "companies": [{"id_company": id_company, "name": company_name}],
        },
    }

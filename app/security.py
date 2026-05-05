import hashlib
import logging
import os
import re
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.db.database import run_query

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError(
        "ERROR CRÍTICO: JWT_SECRET no está configurada en las variables de entorno. "
        "Verifica tu archivo .env o las variables en Railway."
    )

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")
MD5_RE = re.compile(r"^[a-fA-F0-9]{32}$")


def is_bcrypt_hash(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith(BCRYPT_PREFIXES)


def is_md5_hash(value: str | None) -> bool:
    return isinstance(value, str) and bool(MD5_RE.fullmatch(value))


def hash_password(password: str) -> str:
    """Normaliza el password antes de guardarlo en BD."""
    if password is None:
        raise ValueError("Password no puede ser nulo")
    if is_bcrypt_hash(password):
        return password
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica la contrasena contra el hash almacenado."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error en verify_password - posible hash mal formateado: {str(e)}")
        raise


def verify_and_upgrade_password(plain_password: str, stored_password: str | None) -> tuple[bool, str | None]:
    """Verifica credenciales heredadas y devuelve un hash bcrypt nuevo si toca migrar."""
    if stored_password is None:
        return False, None

    normalized_password = stored_password.strip()

    if is_bcrypt_hash(normalized_password):
        is_valid = verify_password(plain_password, normalized_password)
        if is_valid and normalized_password != stored_password:
            return True, pwd_context.hash(plain_password)
        return is_valid, None

    if plain_password == stored_password:
        logger.warning("Se detecto una contrasena almacenada en texto plano; sera migrada a bcrypt.")
        return True, pwd_context.hash(plain_password)

    if is_md5_hash(normalized_password):
        logger.warning("Se detecto una contrasena almacenada en MD5; sera migrada a bcrypt.")
        candidate_hash = hashlib.md5(plain_password.encode("utf-8")).hexdigest()
        if candidate_hash.lower() == normalized_password.lower():
            return True, pwd_context.hash(plain_password)

    return False, None


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un token JWT."""
    if not SECRET_KEY:
        logger.error("JWT_SECRET no esta configurado en variables de entorno")
        raise ValueError("JWT_SECRET no configurado en el servidor")

    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Error al crear token JWT: {str(e)}")
        raise


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET no configurado"
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise credentials_exception from exc

    id_user = payload.get("id_user")
    if not id_user:
        raise credentials_exception

    result = run_query(
        """
        SELECT u.id_user, u.id_person, u.id_company, u.id_role, p.name, p.lastname, p.email
        FROM users u
        JOIN persons p ON u.id_person = p.id_person
        WHERE u.id_user = %s
        """,
        (id_user,),
        fetch=True
    )

    if not result:
        raise credentials_exception

    user = result[0]
    return {
        "id_user": user["id_user"],
        "id_person": user["id_person"],
        "id_company": user.get("id_company"),
        "id_role": user["id_role"],
        "name": f"{user['name']} {user['lastname']}".strip(),
        "email": user["email"],
    }

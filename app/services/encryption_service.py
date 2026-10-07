import os
import base64
import hashlib
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

_fernet_instance = None


def get_fernet() -> Fernet:
    """
    Retorna la instancia singleton de Fernet para cifrado/descifrado simétrico.
    La clave maestra se obtiene de la variable de entorno ENCRYPTION_KEY.
    Si no está configurada, deriva una clave válida a partir de JWT_SECRET
    para entornos de desarrollo/pruebas.
    """
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    raw_key = os.getenv("ENCRYPTION_KEY")
    if raw_key:
        try:
            # Validar formato de clave Fernet
            _fernet_instance = Fernet(raw_key.encode("utf-8"))
            return _fernet_instance
        except Exception as e:
            logger.warning(f"ENCRYPTION_KEY inválida ({e}), derivando clave alternativa...")

    # Fallback seguro para desarrollo: derivar clave base64 urlsafe de 32 bytes desde JWT_SECRET
    jwt_secret = os.getenv("JWT_SECRET", "analitika_default_dev_secret_key_32bytes!")
    derived = hashlib.sha256(jwt_secret.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    _fernet_instance = Fernet(fernet_key)
    logger.info("Instancia de cifrado Fernet inicializada correctamente.")
    return _fernet_instance


def encrypt_token(plain_token: str | None) -> str | None:
    """Cifra un token sensible (access_token, refresh_token) antes de guardarlo en la base de datos."""
    if not plain_token:
        return None
    fernet = get_fernet()
    encrypted = fernet.encrypt(plain_token.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_token(cipher_text: str | None) -> str | None:
    """Descifra un token cifrado almacenado en la base de datos para su uso en llamadas a la API."""
    if not cipher_text:
        return None
    fernet = get_fernet()
    decrypted = fernet.decrypt(cipher_text.encode("utf-8"))
    return decrypted.decode("utf-8")

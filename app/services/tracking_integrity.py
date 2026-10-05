"""
app/services/tracking_integrity.py

Capa de integridad de datos para los endpoints públicos de tracking:
  - Generación y validación de tokens firmados HMAC para vincular clics con conversiones
  - Deduplicación de clics por IP+link en ventana de tiempo corta
  - Detección básica de bots por User-Agent

Esta capa es independiente de autenticación JWT (los endpoints siguen siendo públicos).
"""
import hashlib
import hmac
import logging
import os
import time
import re

from app.db.database import run_query

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración — ajustable vía variables de entorno
# ---------------------------------------------------------------------------

_SECRET = os.getenv("JWT_SECRET", "")  # Reutilizamos JWT_SECRET para HMAC
DEDUP_WINDOW_SECONDS: int = int(os.getenv("DEDUP_WINDOW_SECONDS", "30"))
CONVERSION_WINDOW_HOURS: int = int(os.getenv("CONVERSION_WINDOW_HOURS", "48"))

# ---------------------------------------------------------------------------
# Patrones de User-Agent de bots conocidos (lista conservadora)
# ---------------------------------------------------------------------------
_BOT_UA_PATTERNS = re.compile(
    r"(bot|crawl|spider|slurp|curl|wget|python-requests|axios|go-http|java/"
    r"|scrapy|httpclient|libwww|lwp|mechanize|guzzle|okhttp|apachehttpclient"
    r"|phantomjs|headless|selenium|puppeteer|playwright|facebookexternalhit)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# HMAC token: generación y validación
# ---------------------------------------------------------------------------

def _build_hmac(id_click: int, timestamp: int) -> str:
    """Genera la firma HMAC-SHA256 para un par (id_click, timestamp)."""
    message = f"{id_click}:{timestamp}".encode()
    secret = _SECRET.encode() if _SECRET else b"analitika-fallback-secret"
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def generate_click_token(id_click: int) -> str:
    """
    Genera un token de un solo uso que vincula un id_click con la conversión.
    Formato: "{id_click}:{timestamp}:{hmac}"
    El timestamp permite verificar expiración sin consultar la BD.
    """
    ts = int(time.time())
    sig = _build_hmac(id_click, ts)
    return f"{id_click}:{ts}:{sig}"


def validate_click_token(token: str) -> tuple[bool, int, str]:
    """
    Valida un token de clic.

    Retorna: (es_valido, id_click, motivo_de_rechazo)
      - Si válido: (True, id_click, "")
      - Si inválido: (False, 0, "motivo")
    """
    if not token or not isinstance(token, str):
        return False, 0, "token_ausente"

    parts = token.split(":")
    if len(parts) != 3:
        return False, 0, "token_malformado"

    try:
        id_click = int(parts[0])
        timestamp = int(parts[1])
        received_sig = parts[2]
    except (ValueError, IndexError):
        return False, 0, "token_malformado"

    # 1. Verificar firma (timing-safe)
    expected_sig = _build_hmac(id_click, timestamp)
    if not hmac.compare_digest(expected_sig, received_sig):
        logger.warning(
            "Token de conversión con firma inválida — id_click=%s ip_hint=desconocida",
            id_click,
        )
        return False, 0, "firma_invalida"

    # 2. Verificar ventana de tiempo
    age_seconds = time.time() - timestamp
    max_age = CONVERSION_WINDOW_HOURS * 3600
    if age_seconds > max_age:
        logger.warning(
            "Token de conversión expirado — id_click=%s age_hours=%.1f",
            id_click,
            age_seconds / 3600,
        )
        return False, 0, "token_expirado"

    if age_seconds < 0:
        # Timestamp futuro → manipulación
        return False, 0, "token_invalido"

    return True, id_click, ""


def is_conversion_already_registered(id_click: int) -> bool:
    """
    Verifica si ya existe al menos una conversión para este id_click.
    Previene que el mismo token genere múltiples conversiones.
    """
    result = run_query(
        "SELECT id_conversion FROM conversions WHERE id_click = %s LIMIT 1",
        (id_click,),
        fetch=True,
    )
    return bool(result)


def is_click_valid(id_click: int) -> bool:
    """Verifica que el id_click existe en la tabla clicks."""
    result = run_query(
        "SELECT id_click FROM clicks WHERE id_click = %s LIMIT 1",
        (id_click,),
        fetch=True,
    )
    return bool(result)


# ---------------------------------------------------------------------------
# Deduplicación de clics
# ---------------------------------------------------------------------------

def is_duplicate_click(ip_hash: str, id_link: int, window_seconds: int = None) -> bool:
    """
    Verifica si ya existe un clic del mismo ip_hash + id_link
    dentro de la ventana de tiempo de deduplicación.

    Returns True si es duplicado (no insertar), False si es único.
    """
    window = window_seconds if window_seconds is not None else DEDUP_WINDOW_SECONDS
    result = run_query(
        """
        SELECT id_click FROM clicks
        WHERE ip_address_hash = %s
          AND id_link = %s
          AND clicked_at >= NOW() - INTERVAL %s SECOND
        LIMIT 1
        """,
        (ip_hash, id_link, window),
        fetch=True,
    )
    if result:
        logger.info(
            "Clic duplicado detectado — ip_hash=%s id_link=%s ventana=%ss",
            ip_hash[:8],
            id_link,
            window,
        )
        return True
    return False


# ---------------------------------------------------------------------------
# Detección básica de bots
# ---------------------------------------------------------------------------

def is_bot_user_agent(user_agent: str | None) -> bool:
    """
    Detecta los casos más evidentes de bots por User-Agent.
    Capa 1 de defensa: no pretende ser exhaustiva.
    Returns True si el UA parece ser un bot.
    """
    if not user_agent or not user_agent.strip():
        logger.info("Petición sin User-Agent recibida en endpoint público")
        return True

    if _BOT_UA_PATTERNS.search(user_agent):
        logger.info(
            "UA de bot detectado — ua_fragment='%s'",
            user_agent[:60],
        )
        return True

    return False

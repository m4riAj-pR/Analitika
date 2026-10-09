import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import httpx
from jose import jwt, JWTError

from app.db.database import run_query
from app.services.encryption_service import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v19.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
META_OAUTH_URL = f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth"


class MetaApiError(Exception):
    """Excepción base para errores de la API de Meta."""
    pass


class MetaAuthError(MetaApiError):
    """Excepción cuando el token ha expirado o es inválido."""
    pass


class MetaRateLimitError(MetaApiError):
    """Excepción cuando se alcanza el límite de solicitudes de Meta (Rate Limit)."""
    pass


def get_meta_config() -> Dict[str, str]:
    """Obtiene y valida la configuración requerida de Meta Ads."""
    app_id = os.getenv("META_APP_ID", "").strip()
    app_secret = os.getenv("META_APP_SECRET", "").strip()
    redirect_uri = os.getenv("META_REDIRECT_URI", "http://localhost:8000/analitika/ad-connections/meta/callback").strip()

    if not app_id or app_id in ("YOUR_META_APP_ID", "tu_app_id"):
        raise MetaAuthError("El ID de la aplicación de Meta (META_APP_ID) no está configurado o es inválido en las variables de entorno.")

    return {
        "app_id": app_id,
        "app_secret": app_secret,
        "redirect_uri": redirect_uri
    }


def generate_meta_auth_url(id_company: int, id_user: int, custom_redirect_uri: Optional[str] = None) -> Tuple[str, str]:
    """
    Genera la URL de autorización OAuth 2.0 para que el Owner conecte su cuenta de Meta.
    Crea un parámetro 'state' firmado con JWT para prevenir ataques CSRF.
    """
    config = get_meta_config()
    redirect_uri = custom_redirect_uri or config["redirect_uri"]

    jwt_secret = os.getenv("JWT_SECRET", "meta_oauth_secret_key_default")
    state_payload = {
        "id_company": id_company,
        "id_user": id_user,
        "provider": "meta",
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    state = jwt.encode(state_payload, jwt_secret, algorithm="HS256")

    scopes = "ads_read,read_insights"
    auth_url = (
        f"{META_OAUTH_URL}?"
        f"client_id={config['app_id']}&"
        f"redirect_uri={redirect_uri}&"
        f"state={state}&"
        f"scope={scopes}&"
        f"response_type=code"
    )

    return auth_url, state


def verify_oauth_state(state: str) -> Dict[str, Any]:
    """Valida y decodifica el token 'state' del callback de OAuth."""
    jwt_secret = os.getenv("JWT_SECRET", "meta_oauth_secret_key_default")
    try:
        payload = jwt.decode(state, jwt_secret, algorithms=["HS256"])
        if payload.get("provider") != "meta":
            raise ValueError("Proveedor de estado inválido")
        return payload
    except JWTError as e:
        raise MetaAuthError(f"Estado de autorización inválido o expirado: {e}")


def _execute_meta_request(url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Dict[str, Any]:
    """
    Ejecuta una petición HTTP a Meta Graph API con reintentos y backoff exponencial ante rate limits.
    """
    params = params or {}
    backoff = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=params)

            # Verificar Rate Limits en cabeceras o cuerpo
            if response.status_code == 429:
                if attempt == max_retries:
                    raise MetaRateLimitError("Meta Rate Limit alcanzado tras múltiples reintentos.")
                logger.warning(f"Meta 429 Rate Limit detectado. Reintentando en {backoff:.1f}s...")
                time.sleep(backoff)
                backoff *= 2
                continue

            data = response.json()
            if "error" in data:
                err = data["error"]
                err_code = err.get("code")
                err_subcode = err.get("error_subcode")
                err_msg = err.get("message", "Error desconocido de Meta API")

                # Error 17 / 613: Rate Limit
                if err_code in (17, 613) or err_subcode == 2446079:
                    if attempt == max_retries:
                        raise MetaRateLimitError(f"Meta Rate Limit excedido: {err_msg}")
                    logger.warning(f"Meta Rate Limit (código {err_code}). Reintentando en {backoff:.1f}s...")
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                # Error 190 / 102: Token o App Secret inválido / expirado
                if err_code in (190, 102):
                    raise MetaAuthError(f"Token o autorización de Meta inválida/expirada (Código {err_code}): {err_msg}")

                # Error de App no configurada o modo desarrollo (Subcódigos 1349048, 1349057)
                if err_subcode in (1349048, 1349057) or err_code == 101:
                    raise MetaAuthError(f"Aplicación de Meta no configurada o en modo desarrollo. Verifica el App ID y Testers (Código {err_code}, Subcódigo {err_subcode}): {err_msg}")

                raise MetaApiError(f"Error Meta API (Código {err_code}, Subcódigo {err_subcode}): {err_msg}")

            return data

        except httpx.RequestError as e:
            if attempt == max_retries:
                raise MetaApiError(f"Fallo de conexión con Meta API: {e}")
            time.sleep(backoff)
            backoff *= 2

    raise MetaApiError("Fallo inesperado al conectar con Meta API")


def exchange_code_for_tokens(code: str, custom_redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """
    Intercambia el código de autorización por un access_token de corta duración
    y luego lo canjea por un access_token de larga duración (60 días).
    """
    config = get_meta_config()
    redirect_uri = custom_redirect_uri or config["redirect_uri"]

    # 1. Intercambio por short-lived token
    token_url = f"{GRAPH_BASE_URL}/oauth/access_token"
    token_params = {
        "client_id": config["app_id"],
        "client_secret": config["app_secret"],
        "redirect_uri": redirect_uri,
        "code": code
    }
    short_lived_data = _execute_meta_request(token_url, params=token_params)
    short_token = short_lived_data.get("access_token")
    if not short_token:
        raise MetaAuthError("No se recibió access_token de Meta")

    # 2. Canje por long-lived token (duración típica: 60 días)
    exchange_params = {
        "grant_type": "fb_exchange_token",
        "client_id": config["app_id"],
        "client_secret": config["app_secret"],
        "fb_exchange_token": short_token
    }
    long_lived_data = _execute_meta_request(token_url, params=exchange_params)
    long_token = long_lived_data.get("access_token", short_token)
    expires_in_seconds = long_lived_data.get("expires_in", 60 * 24 * 3600)  # Por defecto 60 días
    token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)

    return {
        "access_token": long_token,
        "token_expires_at": token_expires_at
    }


def get_user_ad_accounts(access_token: str) -> List[Dict[str, Any]]:
    """Consulta las cuentas publicitarias accesibles para el usuario con este token."""
    url = f"{GRAPH_BASE_URL}/me/adaccounts"
    params = {
        "fields": "id,name,account_id,account_status,currency",
        "access_token": access_token
    }
    data = _execute_meta_request(url, params=params)
    return data.get("data", [])


def get_account_campaigns(external_account_id: str, access_token: str) -> List[Dict[str, Any]]:
    """Consulta las campañas publicitarias existentes en la cuenta publicitaria de Meta."""
    # Asegurar prefijo act_
    act_id = external_account_id if external_account_id.startswith("act_") else f"act_{external_account_id}"
    url = f"{GRAPH_BASE_URL}/{act_id}/campaigns"
    params = {
        "fields": "id,name,status,objective",
        "limit": 100,
        "access_token": access_token
    }
    data = _execute_meta_request(url, params=params)
    return data.get("data", [])


def fetch_campaign_insights(external_campaign_id: str, access_token: str, date_preset: str = "last_30d") -> List[Dict[str, Any]]:
    """
    Consulta métricas (impresiones, gasto, clics externos, alcance) desglosadas por día
    desde el endpoint de Insights de Meta Marketing API.
    """
    url = f"{GRAPH_BASE_URL}/{external_campaign_id}/insights"
    params = {
        "fields": "impressions,spend,clicks,reach,date_start,date_stop",
        "time_increment": 1,  # Desglose diario
        "date_preset": date_preset,
        "access_token": access_token
    }
    data = _execute_meta_request(url, params=params)
    raw_insights = data.get("data", [])

    results = []
    for item in raw_insights:
        results.append({
            "metric_date": item.get("date_start"),
            "impressions": int(item.get("impressions") or 0),
            "spend": float(item.get("spend") or 0.0),
            "external_clicks": int(item.get("clicks") or 0),
            "reach": int(item.get("reach") or 0)
        })

    return results


def save_connection(
    id_company: int,
    id_user: int,
    external_account_id: str,
    account_name: str,
    access_token: str,
    token_expires_at: datetime
) -> int:
    """Guarda o actualiza la conexión de Meta Ads con el token cifrado con Fernet."""
    encrypted_token = encrypt_token(access_token)
    
    # Comprobar si ya existe
    existing = run_query("""
        SELECT id_connection FROM ad_account_connections
        WHERE id_company = %s AND provider = 'meta' AND external_account_id = %s
    """, (id_company, external_account_id), fetch=True)

    if existing:
        id_conn = existing[0]["id_connection"]
        run_query("""
            UPDATE ad_account_connections
            SET account_name = %s,
                access_token = %s,
                token_expires_at = %s,
                status = 'active',
                status_message = NULL,
                connected_by = %s,
                updated_at = NOW()
            WHERE id_connection = %s
        """, (account_name, encrypted_token, token_expires_at, id_user, id_conn))
        return id_conn
    else:
        id_conn = run_query("""
            INSERT INTO ad_account_connections (
                id_company, provider, external_account_id, account_name,
                access_token, token_expires_at, status, connected_by, connected_at
            ) VALUES (%s, 'meta', %s, %s, %s, %s, 'active', %s, NOW())
        """, (
            id_company, external_account_id, account_name,
            encrypted_token, token_expires_at, id_user
        ), return_lastrowid=True)
        return id_conn


def refresh_meta_connection_token(id_connection: int) -> bool:
    """Refresca el token de una conexión de Meta si está próximo a expirar (dentro de 7 días)."""
    conn_row = run_query("""
        SELECT id_connection, access_token, token_expires_at
        FROM ad_account_connections
        WHERE id_connection = %s
    """, (id_connection,), fetch=True)

    if not conn_row:
        return False

    current_token = decrypt_token(conn_row[0]["access_token"])
    expires_at = conn_row[0]["token_expires_at"]

    # Si expira en más de 7 días, aún no requiere refresco
    if expires_at and isinstance(expires_at, datetime) and expires_at > datetime.utcnow() + timedelta(days=7):
        return True

    config = get_meta_config()
    token_url = f"{GRAPH_BASE_URL}/oauth/access_token"
    exchange_params = {
        "grant_type": "fb_exchange_token",
        "client_id": config["app_id"],
        "client_secret": config["app_secret"],
        "fb_exchange_token": current_token
    }

    try:
        new_data = _execute_meta_request(token_url, params=exchange_params)
        new_token = new_data.get("access_token")
        if not new_token:
            return False

        expires_in = new_data.get("expires_in", 60 * 24 * 3600)
        new_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        encrypted_new_token = encrypt_token(new_token)

        run_query("""
            UPDATE ad_account_connections
            SET access_token = %s,
                token_expires_at = %s,
                status = 'active',
                status_message = NULL,
                updated_at = NOW()
            WHERE id_connection = %s
        """, (encrypted_new_token, new_expires_at, id_connection))
        return True

    except MetaAuthError as e:
        logger.error(f"Fallo al refrescar token de conexión {id_connection}: {e}")
        run_query("""
            UPDATE ad_account_connections
            SET status = 'expired', status_message = %s, updated_at = NOW()
            WHERE id_connection = %s
        """, (str(e), id_connection))
        return False
    except Exception as e:
        logger.error(f"Error inesperado refrescando token {id_connection}: {e}")
        return False


def sync_connection_metrics(id_connection: int, date_preset: str = "last_30d") -> Dict[str, Any]:
    """
    Sincroniza todas las campañas mapeadas bajo una conexión activa de Meta.
    Guarda las métricas (impresiones, gasto, clics externos) en campaign_external_metrics
    sin sobrescritura destructiva, preservando series temporales y auditoría.
    Maneja excepciones y rate limits de forma aislada.
    """
    conn_row = run_query("""
        SELECT id_connection, id_company, external_account_id, access_token, status
        FROM ad_account_connections
        WHERE id_connection = %s
    """, (id_connection,), fetch=True)

    if not conn_row:
        return {"ok": False, "error": "Conexión no encontrada"}

    conn = conn_row[0]
    if conn["status"] not in ("active", "error"):
        return {"ok": False, "error": f"La conexión está en estado '{conn['status']}'"}

    # Refrescar token si es necesario
    refresh_meta_connection_token(id_connection)

    # Volver a leer token actualizado
    token_data = run_query("SELECT access_token FROM ad_account_connections WHERE id_connection = %s", (id_connection,), fetch=True)
    decrypted_token = decrypt_token(token_data[0]["access_token"])

    # Obtener campañas mapeadas con sincronización habilitada
    mappings = run_query("""
        SELECT id_mapping, id_campaign, external_campaign_id, external_campaign_name
        FROM campaign_external_mapping
        WHERE id_connection = %s AND sync_enabled = 1
    """, (id_connection,), fetch=True)

    synced_count = 0
    total_metrics_recorded = 0
    errors = []

    try:
        for mapping in mappings:
            ext_camp_id = mapping["external_campaign_id"]
            id_mapping = mapping["id_mapping"]

            try:
                insights = fetch_campaign_insights(ext_camp_id, decrypted_token, date_preset=date_preset)
                for item in insights:
                    metric_date = item["metric_date"]
                    impressions = item["impressions"]
                    spend = item["spend"]
                    ext_clicks = item["external_clicks"]
                    reach = item["reach"]

                    # Inserción histórica para trazabilidad y auditoría
                    run_query("""
                        INSERT INTO campaign_external_metrics (
                            id_mapping, metric_date, impressions, spend,
                            external_clicks, reach, fetched_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (id_mapping, metric_date, impressions, spend, ext_clicks, reach))
                    total_metrics_recorded += 1

                synced_count += 1

            except MetaRateLimitError as rle:
                logger.warning(f"Rate limit en campaña externa {ext_camp_id}: {rle}")
                errors.append(f"Campaña {ext_camp_id}: {rle}")
                # Si una campaña da rate limit, no continuar saturando
                break
            except Exception as e:
                logger.error(f"Error sincronizando campaña {ext_camp_id}: {e}")
                errors.append(f"Campaña {ext_camp_id}: {str(e)}")

        # Actualizar fecha de última sincronización
        new_status = "error" if (errors and synced_count == 0) else "active"
        status_msg = "; ".join(errors) if errors else None

        run_query("""
            UPDATE ad_account_connections
            SET last_sync_at = NOW(),
                status = %s,
                status_message = %s,
                updated_at = NOW()
            WHERE id_connection = %s
        """, (new_status, status_msg, id_connection))

        return {
            "ok": True,
            "id_connection": id_connection,
            "synced_campaigns": synced_count,
            "total_metrics_recorded": total_metrics_recorded,
            "errors": errors
        }

    except MetaAuthError as mae:
        logger.error(f"Error de autenticación en conexión {id_connection}: {mae}")
        run_query("""
            UPDATE ad_account_connections
            SET status = 'expired', status_message = %s, updated_at = NOW()
            WHERE id_connection = %s
        """, (str(mae), id_connection))
        return {"ok": False, "error": str(mae)}

    except MetaRateLimitError as mrle:
        logger.warning(f"Rate limit general en conexión {id_connection}: {mrle}")
        run_query("""
            UPDATE ad_account_connections
            SET status = 'error', status_message = %s, updated_at = NOW()
            WHERE id_connection = %s
        """, (str(mrle), id_connection))
        return {"ok": False, "error": str(mrle)}

    except Exception as e:
        logger.error(f"Fallo inesperado sincronizando conexión {id_connection}: {e}")
        run_query("""
            UPDATE ad_account_connections
            SET status = 'error', status_message = %s, updated_at = NOW()
            WHERE id_connection = %s
        """, (str(e), id_connection))
        return {"ok": False, "error": str(e)}


def revoke_meta_connection(id_connection: int) -> bool:
    """Marca la conexión como revocada en base de datos e intenta revocar permisos en Meta."""
    conn = run_query("""
        SELECT access_token FROM ad_account_connections WHERE id_connection = %s
    """, (id_connection,), fetch=True)

    if not conn:
        return False

    try:
        token = decrypt_token(conn[0]["access_token"])
        if token:
            # Intentar revocar permiso en Meta vía DELETE /me/permissions
            revoke_url = f"{GRAPH_BASE_URL}/me/permissions"
            with httpx.Client(timeout=5.0) as client:
                client.delete(revoke_url, params={"access_token": token})
    except Exception as e:
        logger.warning(f"No se pudo revocar el token en el servidor de Meta ({e}), revocando localmente.")

    run_query("""
        UPDATE ad_account_connections
        SET status = 'revoked', status_message = 'Desconectado por el usuario', updated_at = NOW()
        WHERE id_connection = %s
    """, (id_connection,))

    return True

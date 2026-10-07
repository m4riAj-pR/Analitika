import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from fastapi.responses import HTMLResponse

from app.db.database import run_query
from app.security import get_current_user, require_role
from app.services.a_service import (
    ensure_company_access,
    ensure_campaign_access,
    get_user_company_ids
)
from app.services.meta_ads_service import (
    generate_meta_auth_url,
    verify_oauth_state,
    exchange_code_for_tokens,
    get_user_ad_accounts,
    get_account_campaigns,
    save_connection,
    sync_connection_metrics,
    revoke_meta_connection
)
from app.services.encryption_service import decrypt_token
from app.schemas.ad_connections import (
    AdConnectionPublic,
    OAuthConnectResponse,
    ExternalCampaignItem,
    CampaignExternalMappingCreate,
    CampaignExternalMappingPublic,
    CampaignExternalMetricPublic,
    SyncResultResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analitika", tags=["Ad Account Connections"])


# -------------------------------------------------------------------------
# CONEXIONES DE CUENTAS PUBLICITARIAS (Solo Owner id_role=2 o Super_Admin id_role=1)
# -------------------------------------------------------------------------

@router.get("/companies/{id_company}/ad-connections", response_model=List[AdConnectionPublic])
def list_company_ad_connections(
    id_company: int,
    current_user: dict = Depends(require_role([1, 2]))
):
    """
    Retorna la lista de conexiones publicitarias de la empresa.
    SEGURIDAD: Nunca expone access_token ni refresh_token.
    """
    ensure_company_access(current_user["id_user"], id_company, current_user.get("id_role"))

    connections = run_query("""
        SELECT 
            id_connection, id_company, provider, external_account_id,
            account_name, status, status_message, connected_by,
            connected_at, last_sync_at
        FROM ad_account_connections
        WHERE id_company = %s
        ORDER BY id_connection DESC
    """, (id_company,), fetch=True)

    return connections or []


@router.post("/companies/{id_company}/ad-connections/meta/connect", response_model=OAuthConnectResponse)
def start_meta_oauth_connection(
    id_company: int,
    current_user: dict = Depends(require_role([1, 2]))
):
    """
    Inicia el flujo OAuth 2.0 con Meta Marketing API.
    Devuelve la URL a la que debe redirigirse el Owner para autorizar el acceso.
    """
    ensure_company_access(current_user["id_user"], id_company, current_user.get("id_role"))

    auth_url, state = generate_meta_auth_url(id_company=id_company, id_user=current_user["id_user"])
    return {
        "auth_url": auth_url,
        "provider": "meta",
        "state": state
    }


@router.get("/ad-connections/meta/callback")
def meta_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """
    Endpoint de retorno de OAuth 2.0 desde Meta.
    Intercambia el código por tokens de larga duración, los cifra y registra la conexión.
    """
    if error:
        logger.warning(f"Error devuelto por Meta en OAuth callback: {error} - {error_description}")
        return HTMLResponse(
            f"<h3>Error al conectar con Meta</h3><p>{error_description or error}</p>",
            status_code=400
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Faltan parámetros 'code' o 'state'")

    # Validar y extraer payload del state
    try:
        state_payload = verify_oauth_state(state)
        id_company = state_payload["id_company"]
        id_user = state_payload["id_user"]
    except Exception as e:
        logger.error(f"Fallo verificando state de Meta: {e}")
        raise HTTPException(status_code=400, detail=f"Estado de autorización inválido: {e}")

    try:
        # Intercambiar código por token de larga duración
        token_info = exchange_code_for_tokens(code)
        access_token = token_info["access_token"]
        token_expires_at = token_info["token_expires_at"]

        # Obtener cuentas publicitarias asociadas
        accounts = get_user_ad_accounts(access_token)
        if not accounts:
            account_id = "act_unknown"
            account_name = "Meta Ad Account Principal"
        else:
            primary_acc = accounts[0]
            account_id = primary_acc.get("id", primary_acc.get("account_id", "act_unknown"))
            account_name = primary_acc.get("name", "Meta Ad Account")

        # Guardar conexión cifrada
        id_conn = save_connection(
            id_company=id_company,
            id_user=id_user,
            external_account_id=account_id,
            account_name=account_name,
            access_token=access_token,
            token_expires_at=token_expires_at
        )

        return HTMLResponse(f"""
            <html>
            <head><title>Conexión exitosa | Analitika</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2 style="color: #4f46e5;">¡Cuenta de Meta Ads conectada exitosamente!</h2>
                <p>Cuenta: <strong>{account_name}</strong> ({account_id})</p>
                <p>Ya puedes cerrar esta ventana y regresar al Dashboard de Analitika.</p>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{ type: 'META_AUTH_SUCCESS', id_connection: {id_conn} }}, '*');
                        setTimeout(() => window.close(), 2500);
                    }}
                </script>
            </body>
            </html>
        """)

    except Exception as e:
        logger.error(f"Error procesando callback de Meta: {e}", exc_info=True)
        return HTMLResponse(
            f"<h3>Error procesando autorización de Meta</h3><p>{str(e)}</p>",
            status_code=500
        )


@router.delete("/companies/{id_company}/ad-connections/{id_connection}")
def disconnect_ad_connection(
    id_company: int,
    id_connection: int,
    current_user: dict = Depends(require_role([1, 2]))
):
    """
    Desconecta y revoca una cuenta publicitaria. Solo permitido para el Owner.
    """
    ensure_company_access(current_user["id_user"], id_company, current_user.get("id_role"))

    conn = run_query("""
        SELECT id_connection FROM ad_account_connections
        WHERE id_connection = %s AND id_company = %s
    """, (id_connection, id_company), fetch=True)

    if not conn:
        raise HTTPException(status_code=404, detail="Conexión publicitaria no encontrada")

    revoke_meta_connection(id_connection)
    return {"ok": True, "message": "Cuenta publicitaria desconectada correctamente"}


@router.post("/companies/{id_company}/ad-connections/{id_connection}/sync", response_model=SyncResultResponse)
def trigger_ad_connection_sync(
    id_company: int,
    id_connection: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role([1, 2]))
):
    """
    Inicia una sincronización bajo demanda de la cuenta publicitaria en segundo plano.
    No bloquea la respuesta del endpoint.
    """
    ensure_company_access(current_user["id_user"], id_company, current_user.get("id_role"))

    conn = run_query("""
        SELECT id_connection, status FROM ad_account_connections
        WHERE id_connection = %s AND id_company = %s
    """, (id_connection, id_company), fetch=True)

    if not conn:
        raise HTTPException(status_code=404, detail="Conexión publicitaria no encontrada")

    if conn[0]["status"] not in ("active", "error"):
        raise HTTPException(
            status_code=400,
            detail=f"La conexión se encuentra en estado '{conn[0]['status']}'. Reconéctala para sincronizar."
        )

    # Ejecutar en segundo plano
    background_tasks.add_task(sync_connection_metrics, id_connection)

    return {
        "ok": True,
        "id_connection": id_connection,
        "synced_campaigns": 0,
        "total_metrics_recorded": 0,
        "errors": []
    }


@router.get("/companies/{id_company}/ad-connections/{id_connection}/campaigns", response_model=List[ExternalCampaignItem])
def list_external_meta_campaigns(
    id_company: int,
    id_connection: int,
    current_user: dict = Depends(require_role([1, 2]))
):
    """
    Lista las campañas existentes en la cuenta publicitaria de Meta conectada,
    para que el Owner pueda seleccionar cuál mapear con su campaña interna en Analitika.
    """
    ensure_company_access(current_user["id_user"], id_company, current_user.get("id_role"))

    conn = run_query("""
        SELECT external_account_id, access_token, status
        FROM ad_account_connections
        WHERE id_connection = %s AND id_company = %s
    """, (id_connection, id_company), fetch=True)

    if not conn:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")

    if conn[0]["status"] != "active":
        raise HTTPException(status_code=400, detail="La conexión no está activa")

    decrypted_token = decrypt_token(conn[0]["access_token"])
    try:
        campaigns = get_account_campaigns(conn[0]["external_account_id"], decrypted_token)
        return [
            ExternalCampaignItem(
                id=c["id"],
                name=c["name"],
                status=c.get("status"),
                objective=c.get("objective")
            )
            for c in campaigns
        ]
    except Exception as e:
        logger.error(f"Error consultando campañas de Meta para conexión {id_connection}: {e}")
        raise HTTPException(status_code=502, detail=f"Error consultando la API de Meta: {e}")


# -------------------------------------------------------------------------
# MAPEO DE CAMPAÑAS (Interna <-> Externa)
# -------------------------------------------------------------------------

@router.post("/campaigns/{id_campaign}/map-external", response_model=CampaignExternalMappingPublic)
def map_campaign_to_external_ad(
    id_campaign: int,
    data: CampaignExternalMappingCreate,
    current_user: dict = Depends(require_role([1, 2]))
):
    """
    Asocia una campaña interna de Analitika con un external_campaign_id de una conexión de Meta/Google/TikTok.
    """
    ensure_campaign_access(current_user["id_user"], id_campaign, current_user.get("id_role"))

    # Validar que la conexión exista y pertenezca a la misma empresa que la campaña
    camp_row = run_query("SELECT id_company FROM campaigns WHERE id_campaign = %s", (id_campaign,), fetch=True)
    if not camp_row:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    id_company = camp_row[0]["id_company"]

    conn_row = run_query("""
        SELECT id_connection, provider, external_account_id
        FROM ad_account_connections
        WHERE id_connection = %s AND id_company = %s
    """, (data.id_connection, id_company), fetch=True)

    if not conn_row:
        raise HTTPException(status_code=400, detail="La conexión publicitaria no pertenece a la misma empresa de la campaña")

    # Insertar o actualizar mapeo
    existing = run_query("""
        SELECT id_mapping FROM campaign_external_mapping
        WHERE id_campaign = %s AND id_connection = %s
    """, (id_campaign, data.id_connection), fetch=True)

    if existing:
        id_mapping = existing[0]["id_mapping"]
        run_query("""
            UPDATE campaign_external_mapping
            SET external_campaign_id = %s,
                external_campaign_name = %s,
                sync_enabled = 1,
                updated_at = NOW()
            WHERE id_mapping = %s
        """, (data.external_campaign_id, data.external_campaign_name, id_mapping))
    else:
        id_mapping = run_query("""
            INSERT INTO campaign_external_mapping (
                id_campaign, id_connection, external_campaign_id,
                external_campaign_name, sync_enabled
            ) VALUES (%s, %s, %s, %s, 1)
        """, (
            id_campaign, data.id_connection, data.external_campaign_id,
            data.external_campaign_name
        ), return_lastrowid=True)

    conn_info = conn_row[0]
    return CampaignExternalMappingPublic(
        id_mapping=id_mapping,
        id_campaign=id_campaign,
        id_connection=data.id_connection,
        provider=conn_info["provider"],
        external_account_id=conn_info["external_account_id"],
        external_campaign_id=data.external_campaign_id,
        external_campaign_name=data.external_campaign_name,
        sync_enabled=True
    )


@router.get("/campaigns/{id_campaign}/external-mapping", response_model=Optional[CampaignExternalMappingPublic])
def get_campaign_external_mapping(
    id_campaign: int,
    current_user: dict = Depends(get_current_user)
):
    """Retorna el mapeo publicitario externo de la campaña si existe."""
    ensure_campaign_access(current_user["id_user"], id_campaign, current_user.get("id_role"))

    mapping = run_query("""
        SELECT 
            m.id_mapping, m.id_campaign, m.id_connection,
            c.provider, c.external_account_id,
            m.external_campaign_id, m.external_campaign_name,
            m.sync_enabled, m.created_at, c.last_sync_at
        FROM campaign_external_mapping m
        JOIN ad_account_connections c ON m.id_connection = c.id_connection
        WHERE m.id_campaign = %s
    """, (id_campaign,), fetch=True)

    if not mapping:
        return None

    row = mapping[0]
    return CampaignExternalMappingPublic(
        id_mapping=row["id_mapping"],
        id_campaign=row["id_campaign"],
        id_connection=row["id_connection"],
        provider=row["provider"],
        external_account_id=row["external_account_id"],
        external_campaign_id=row["external_campaign_id"],
        external_campaign_name=row["external_campaign_name"],
        sync_enabled=bool(row["sync_enabled"]),
        created_at=row.get("created_at"),
        last_sync_at=row.get("last_sync_at")
    )


@router.delete("/campaigns/{id_campaign}/map-external")
def delete_campaign_external_mapping(
    id_campaign: int,
    current_user: dict = Depends(require_role([1, 2]))
):
    """Elimina el mapeo publicitario externo de la campaña."""
    ensure_campaign_access(current_user["id_user"], id_campaign, current_user.get("id_role"))

    run_query("DELETE FROM campaign_external_mapping WHERE id_campaign = %s", (id_campaign,))
    return {"ok": True, "message": "Mapeo publicitario eliminado correctamente"}


@router.get("/campaigns/{id_campaign}/external-metrics", response_model=List[CampaignExternalMetricPublic])
def get_campaign_external_metrics_history(
    id_campaign: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna el historial de métricas diarias sincronizadas para la campaña.
    Permite series temporales y auditoría de sincronizaciones.
    """
    ensure_campaign_access(current_user["id_user"], id_campaign, current_user.get("id_role"))

    metrics = run_query("""
        SELECT 
            cem.id_metric, cem.id_mapping,
            CAST(cem.metric_date AS CHAR) as metric_date,
            cem.impressions, cem.spend, cem.external_clicks,
            cem.reach, cem.fetched_at
        FROM campaign_external_metrics cem
        JOIN campaign_external_mapping map ON cem.id_mapping = map.id_mapping
        WHERE map.id_campaign = %s
        ORDER BY cem.metric_date ASC, cem.id_metric ASC
    """, (id_campaign,), fetch=True)

    return metrics or []

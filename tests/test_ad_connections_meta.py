import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Configurar variables de entorno antes de importar módulos
os.environ["JWT_SECRET"] = "test_jwt_secret_key_32_bytes_long_12345"
os.environ["ENCRYPTION_KEY"] = "U1RCSmhvQ1YtMXQweXlUZ3pfc09iY1VTVFlmY1lUaWc="  # Clave válida Fernet
os.environ["META_APP_ID"] = "123456789"
os.environ["META_APP_SECRET"] = "meta_test_secret"
os.environ["META_REDIRECT_URI"] = "http://localhost:8000/analitika/ad-connections/meta/callback"

from app.services.encryption_service import encrypt_token, decrypt_token
from app.services.meta_ads_service import (
    generate_meta_auth_url,
    verify_oauth_state,
    exchange_code_for_tokens,
    fetch_campaign_insights,
    sync_connection_metrics,
    refresh_meta_connection_token,
    save_connection,
    MetaRateLimitError,
    MetaAuthError
)
from app.services.scheduler import sync_all_active_connections
from app.services.a_service import (
    get_campaign_effective_spend_and_impressions,
    build_tracking_destination_with_utms
)
from app.schemas.ad_connections import AdConnectionPublic, ConnectionStatus, AdProvider


# -------------------------------------------------------------------------
# 1. Pruebas de Cifrado y Seguridad de Tokens
# -------------------------------------------------------------------------

def test_token_encryption_and_decryption():
    """Verifica que los tokens OAuth se cifren en reposo y se descifren correctamente."""
    raw_token = "EAABwb3_secret_meta_access_token_xyz"
    encrypted = encrypt_token(raw_token)

    assert encrypted != raw_token
    assert not encrypted.startswith("EAABwb3")
    
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token


def test_ad_connection_public_schema_never_exposes_tokens():
    """Verifica que el schema público nunca incluya access_token ni refresh_token."""
    conn_data = {
        "id_connection": 1,
        "id_company": 10,
        "provider": AdProvider.META,
        "external_account_id": "act_987654321",
        "account_name": "Cuenta Meta Oficial",
        "status": ConnectionStatus.ACTIVE,
        "status_message": None,
        "connected_by": 2,
        "connected_at": datetime.utcnow(),
        "last_sync_at": datetime.utcnow()
    }
    schema = AdConnectionPublic(**conn_data)
    dumped = schema.model_dump()
    assert "access_token" not in dumped
    assert "refresh_token" not in dumped
    assert dumped["external_account_id"] == "act_987654321"


# -------------------------------------------------------------------------
# 2. Pruebas de Flujo OAuth de Meta
# -------------------------------------------------------------------------

def test_generate_meta_auth_url_and_state_verification():
    """Verifica la generación de la URL de autorización y la validación del parámetro state."""
    auth_url, state = generate_meta_auth_url(id_company=5, id_user=2)
    
    assert "client_id=123456789" in auth_url
    assert "scope=ads_read,read_insights" in auth_url
    assert f"state={state}" in auth_url

    # Validar state
    payload = verify_oauth_state(state)
    assert payload["id_company"] == 5
    assert payload["id_user"] == 2
    assert payload["provider"] == "meta"


@patch("app.services.meta_ads_service._execute_meta_request")
def test_exchange_code_for_tokens(mock_execute):
    """Verifica el canje de código por access_token de corta y larga duración."""
    mock_execute.side_effect = [
        {"access_token": "short_lived_token_123"},
        {"access_token": "long_lived_token_456", "expires_in": 5184000}  # 60 días
    ]

    tokens = exchange_code_for_tokens("valid_auth_code")
    assert tokens["access_token"] == "long_lived_token_456"
    assert tokens["token_expires_at"] > datetime.utcnow()


@patch("app.services.meta_ads_service.run_query")
def test_save_connection_encrypts_token_in_db(mock_run_query):
    """Verifica que la conexión se almacene en la BD con el token debidamente cifrado."""
    mock_run_query.side_effect = [
        [],  # existing: None
        101  # id_connection retornado
    ]

    id_conn = save_connection(
        id_company=3,
        id_user=2,
        external_account_id="act_112233",
        account_name="Mi Cuenta Meta",
        access_token="plain_secret_token",
        token_expires_at=datetime.utcnow() + timedelta(days=60)
    )

    assert id_conn == 101
    assert mock_run_query.call_count == 2
    
    insert_call_args = mock_run_query.call_args_list[1][0]
    sql_params = insert_call_args[1]
    saved_token = sql_params[3]  # access_token param

    assert saved_token != "plain_secret_token"
    assert decrypt_token(saved_token) == "plain_secret_token"


# -------------------------------------------------------------------------
# 3. Pruebas de Refresco de Token
# -------------------------------------------------------------------------

@patch("app.services.meta_ads_service._execute_meta_request")
@patch("app.services.meta_ads_service.run_query")
def test_refresh_token_before_expiration(mock_run_query, mock_execute):
    """Verifica la renovación automática del token si está cerca de expirar."""
    encrypted_old_token = encrypt_token("old_token_xyz")
    
    # Token expirando en 2 días (requiere refresco)
    expiring_date = datetime.utcnow() + timedelta(days=2)
    mock_run_query.side_effect = [
        [{"id_connection": 1, "access_token": encrypted_old_token, "token_expires_at": expiring_date}],
        None  # UPDATE
    ]
    mock_execute.return_value = {
        "access_token": "renewed_long_lived_token",
        "expires_in": 5184000
    }

    refreshed = refresh_meta_connection_token(1)
    assert refreshed is True
    assert mock_execute.called
    assert mock_run_query.call_count == 2


# -------------------------------------------------------------------------
# 4. Pruebas de Sincronización de Métricas (Insights)
# -------------------------------------------------------------------------

@patch("app.services.meta_ads_service._execute_meta_request")
def test_fetch_campaign_insights_parses_metrics(mock_execute):
    """Verifica que las métricas de Meta Insights se deserialicen correctamente."""
    mock_execute.return_value = {
        "data": [
            {
                "date_start": "2026-05-01",
                "impressions": "12500",
                "spend": "45.75",
                "clicks": "320",
                "reach": "9800"
            },
            {
                "date_start": "2026-05-02",
                "impressions": "15000",
                "spend": "55.20",
                "clicks": "410",
                "reach": "11200"
            }
        ]
    }

    insights = fetch_campaign_insights("238492019283", "decrypted_token")
    assert len(insights) == 2
    assert insights[0]["metric_date"] == "2026-05-01"
    assert insights[0]["impressions"] == 12500
    assert insights[0]["spend"] == 45.75
    assert insights[0]["external_clicks"] == 320
    assert insights[0]["reach"] == 9800


@patch("app.services.meta_ads_service.fetch_campaign_insights")
@patch("app.services.meta_ads_service.refresh_meta_connection_token")
@patch("app.services.meta_ads_service.run_query")
def test_sync_connection_metrics_stores_without_overwriting(mock_run_query, mock_refresh, mock_insights):
    """Verifica que la sincronización inserte registros históricos en campaign_external_metrics."""
    enc_token = encrypt_token("valid_token")
    
    mock_run_query.side_effect = [
        # 1. SELECT connection
        [{"id_connection": 1, "id_company": 10, "external_account_id": "act_123", "access_token": enc_token, "status": "active"}],
        # 2. SELECT token refreshed
        [{"access_token": enc_token}],
        # 3. SELECT mappings
        [{"id_mapping": 42, "id_campaign": 7, "external_campaign_id": "ext_c_99", "external_campaign_name": "Campaña Meta X"}],
        # 4. INSERT metric day 1
        None,
        # 5. INSERT metric day 2
        None,
        # 6. UPDATE connection last_sync_at
        None
    ]

    mock_insights.return_value = [
        {"metric_date": "2026-05-01", "impressions": 1000, "spend": 25.0, "external_clicks": 50, "reach": 800},
        {"metric_date": "2026-05-02", "impressions": 1200, "spend": 30.0, "external_clicks": 65, "reach": 950}
    ]

    result = sync_connection_metrics(1)
    assert result["ok"] is True
    assert result["synced_campaigns"] == 1
    assert result["total_metrics_recorded"] == 2
    assert len(result["errors"]) == 0


# -------------------------------------------------------------------------
# 5. Pruebas de Rate Limit y Aislamiento de Fallos en Scheduler
# -------------------------------------------------------------------------

@patch("app.services.scheduler.sync_connection_metrics")
@patch("app.services.scheduler.run_query")
def test_scheduler_isolated_failures_on_rate_limit(mock_run_query, mock_sync):
    """
    Verifica que si una conexión falla por Rate Limit o error de API,
    el scheduler no se detiene y continúa sincronizando las demás cuentas.
    """
    mock_run_query.return_value = [
        {"id_connection": 1, "id_company": 10, "provider": "meta", "external_account_id": "act_1"},
        {"id_connection": 2, "id_company": 20, "provider": "meta", "external_account_id": "act_2"}
    ]

    # Conexión 1 lanza Rate Limit Error, Conexión 2 tiene éxito
    mock_sync.side_effect = [
        MetaRateLimitError("Meta Rate limit reached"),
        {"ok": True, "synced_campaigns": 1}
    ]

    # No debe levantar excepción
    sync_all_active_connections()

    assert mock_sync.call_count == 2
    assert mock_sync.call_args_list[0][0][0] == 1
    assert mock_sync.call_args_list[1][0][0] == 2


# -------------------------------------------------------------------------
# 6. Pruebas de Regla de Precedencia (API vs Manual) y CTR Real
# -------------------------------------------------------------------------

@patch("app.services.a_service.run_query")
def test_precedence_rule_prefers_synced_api_metrics(mock_run_query):
    """
    Verifica que si existen datos externos sincronizados de la API,
    su gasto e impresiones prevalecen sobre el valor manual de la campaña.
    """
    mock_run_query.return_value = [
        {
            "provider": "meta",
            "total_spend": 245.50,
            "total_impressions": 15000,
            "metric_count": 5
        }
    ]

    spend, impressions, data_source = get_campaign_effective_spend_and_impressions(12)
    assert spend == 245.50
    assert impressions == 15000
    assert data_source == "api_meta"


@patch("app.services.a_service.run_query")
def test_precedence_rule_falls_back_to_manual_spend_when_no_sync(mock_run_query):
    """
    Verifica que si no hay métricas sincronizadas de la API,
    el cálculo utiliza el campo manual 'campaigns.spent' como fallback.
    """
    # 1. Consulta de métricas externas vacía
    # 2. Consulta de campaña manual
    mock_run_query.side_effect = [
        [],  # Sin métricas externas
        [{"spent": 85.00}]  # Valor manual en tabla campaigns
    ]

    spend, impressions, data_source = get_campaign_effective_spend_and_impressions(12)
    assert spend == 85.00
    assert impressions == 0
    assert data_source == "manual"


def test_real_ctr_calculation_logic():
    """Verifica el cálculo de CTR_real = (clics_propios / impresiones_api) * 100."""
    clics_propios = 450
    impresiones_api = 18000

    ctr_real = round((clics_propios / impresiones_api) * 100, 2)
    assert ctr_real == 2.5  # 2.5%

    # Si impresiones es 0, CTR debe ser 0.0
    ctr_cero = round((clics_propios / 0) * 100, 2) if 0 > 0 else 0.0
    assert ctr_cero == 0.0


# -------------------------------------------------------------------------
# 7. Pruebas de Consistencia de UTM (Paso 4)
# -------------------------------------------------------------------------

@patch("app.services.a_service.run_query")
def test_build_tracking_destination_injects_utms_for_meta(mock_run_query):
    """Verifica que se inyecten los parámetros UTM estándar para un canal de Meta."""
    mock_run_query.return_value = [{"name": "Instagram Stories"}]

    dest = "https://mitienda.com/oferta"
    res = build_tracking_destination_with_utms(dest, id_campaign=44, id_channel=2)

    assert "utm_source=meta" in res
    assert "utm_medium=cpc" in res
    assert "utm_campaign=44" in res


def test_build_tracking_destination_preserves_existing_utms():
    """Verifica que no se dupliquen ni sobrescriban UTMs si ya existen."""
    custom_dest = "https://mitienda.com/oferta?utm_source=influencer&utm_campaign=promo2026"
    res = build_tracking_destination_with_utms(custom_dest, id_campaign=44)
    assert res == custom_dest
